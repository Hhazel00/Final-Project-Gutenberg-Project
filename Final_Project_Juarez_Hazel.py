
"""
Hazel Juarez
May 16, 2025

Final Project: eBooks

This GUI program allows a users to:
1. Search Project Gutenberg books by title or URL
2. Analyze the top 10 most frequent words
3. Save results locally to a data file called Saved_Data.db
"""

import tkinter as tk
import urllib.request
import urllib.parse
import re
import sqlite3
from html.parser import HTMLParser
from collections import Counter

Book_File = 'Saved_Data.db'

# Database Creation
def start_database():
    """
    Creates Saved_Data.db and adds two tables.
    One for the book, and the other for the frequency of words.
    """
    connection = sqlite3.connect(Book_File)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Book_Titles (
                    book_by_number INTEGER PRIMARY KEY,
                    title TEXT UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Frequency_of_Top_Ten (
                    book_by_number INTEGER,
                    word TEXT,
                    frequency INTEGER,
                    FOREIGN KEY (book_by_number) REFERENCES Book_Titles(book_by_number))''')
    connection.commit()
    connection.close()

def save_book(title, frequency):
    """
    Saves a book title and its top 10 word frequencies. 
    """
    connection = sqlite3.connect(Book_File)
    cursor = connection.cursor()

# Creates next number for book_by_number (if not already saved)
    cursor.execute("SELECT book_by_number FROM Book_Titles WHERE title = ?", (title,))
    result = cursor.fetchone()
    if result:
        book_by_number = result[0]
    else:
        cursor.execute("SELECT MAX(book_by_number) FROM Book_Titles")
        max_number = cursor.fetchone()[0]
        book_by_number = (max_number + 1) if max_number else 1
        cursor.execute("INSERT INTO Book_Titles (book_by_number, title) VALUES (?, ?)", (book_by_number, title))

# Saves Top 10 word frequencies in data.db
    cursor.execute("DELETE FROM Frequency_of_Top_Ten WHERE book_by_number = ?", (book_by_number,))
    for word, freq in frequency:
        cursor.execute("INSERT INTO Frequency_of_Top_Ten (book_by_number, word, frequency) VALUES (?, ?, ?)",
                    (book_by_number, word, freq))

    connection.commit()
    connection.close()

def get_saved_book(title):
    """
    Looks up the book title in the local database.
    if found, returns a list of its top 10 most frequent words.
    """
    connection = sqlite3.connect(Book_File)
    cursor = connection.cursor()
    cursor.execute("SELECT book_by_number FROM Book_Titles WHERE title = ?", (title,))
    result = cursor.fetchone()
    if not result:
        connection.close()
        return None
    book_by_number = result[0]
    cursor.execute("SELECT word, frequency FROM Frequency_of_Top_Ten WHERE book_by_number = ? ORDER BY frequency DESC", (book_by_number,))
    results = cursor.fetchall()
    connection.close()
    return results

def get_top_10_from_ebook(text, num=10):
    """
    Takes the eBook text from A-Z and makes it lower case. Two letter words and up.
    """
    words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
    counter = Counter(words)
    return counter.most_common(num)

# HTML 
class Gutenberg_HTML_Search(HTMLParser):
    """
    Find HTML link from the website and extracts the link.
    Double checks that it is a proper link and not a bookshelf link.
    """
    def __init__(self):
        super().__init__()
        self.links = []
        self.record = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'li' and 'booklink' in attrs.get('class', ''):
            self.record = True
        elif self.record and tag == 'a' and 'href' in attrs:
            href = attrs['href']
            if href.startswith('/ebooks/') and 'bookshelf' not in href:
                self.links.append(href)
                self.record = False

# Book Search
def find_book_by_title(title):
    """
    Finds HTML link from Project Gutenberg. Goes to Gutenberg_HTML_Search() and 
    finds the first book link.
    """
    try:
        search_for = urllib.parse.quote(title)
        search_for_url = f"https://www.gutenberg.org/ebooks/search/?query={search_for}"
        response = urllib.request.urlopen(search_for_url)
        html = response.read().decode()

        parser = Gutenberg_HTML_Search()
        parser.feed(html)

        if not parser.links:
            raise ValueError("Oh No! No book found with that title.")

        ebook_id = parser.links[0].split("/")[-1]
        book_url = f"https://www.gutenberg.org/ebooks/{ebook_id}" 
        return book_url 

    except Exception as e:
        raise RuntimeError(f"Looks like the search for {e} has failed")
    
# URL Search Function
def find_book_from_url(url):
    """
    From the given URL, it goes through the book and returns the title
    and the top 10 most frequent words.
    """
    try:
        response = urllib.request.urlopen(url)
        raw = response.read().decode('utf-8', errors='ignore')

        title = "Unknown Title"
        for line in raw.splitlines():
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
                break

        if title == "Unknown Title":
            for line in raw.splitlines()[:300]:
                stripped = line.strip()
                if stripped.isupper() and 5 < len(stripped) < 100:
                    title = stripped
                    break

        top_words = get_top_10_from_ebook(raw)
        return title, top_words
    except Exception as e:
        raise RuntimeError(f"Failed to load book from URL: {e}")

# Gui 'ENTER BOOK TITLE' Function
def search_and_analyze_title():
    """
    When looking for a book Title, it searches in the local database first.
    If the book is not found in the local data base it will go to def find_book_by_title().
    """
    title = title_entry_box.get().strip()
    output.delete("1.0", tk.END)

    if not title:
        output.insert(tk.END, "Please enter a book title.")
        return

    local_result = get_saved_book(title)
    if local_result:
        output.insert(tk.END, f"Top 10 Most Frequent Words in '{title}':\n\n")
        for i, (word, freq) in enumerate(local_result, start=1):
            output.insert(tk.END, f"{i}) {word}: {freq}\n")
        return

    try:
        book_url = find_book_by_title(title)
        output.insert(tk.END, f"Book Found Online:\n{book_url}\n\n")
        output.insert(tk.END, "Copy and paste the link above into your browser\n")
    except Exception as e:
        output.insert(tk.END, f"Error: {e}")

def fetch_and_analyze_url():
    """
    Helps def find_book_from_url() display book title,
    frequency of the words and numbers them in descending order.
    """
    url = url_entry.get().strip()
    output.delete("1.0", tk.END)

    if not url:
        output.insert(tk.END, "Please enter a Project Gutenberg URL.")
        return

    try:
        title, top_words = find_book_from_url(url)
        save_book(title, top_words)
        output.insert(tk.END, f"{title}\n\nTop 10 Most Frequent Words:\n\n")
        for i, (word, freq) in enumerate(top_words, start=1):
            output.insert(tk.END, f"{i}) {word}: {freq}\n")
    except Exception as e:
        output.insert(tk.END, f"Error: {e}")

# GUI Set Up
start_database()

gui = tk.Tk()
gui.title("Final Project: eBooks")
gui.geometry("640x540")

tk.Label(gui, text="Final Project: eBooks", font=("Helvetica", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=(15, 10))

# URL Search Section
tk.Label(gui, text="Enter Gutenberg URL:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="e", padx=(10, 5), pady=5)
url_entry = tk.Entry(gui, width=40)
url_entry.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=5)
tk.Button(gui, text="Find Book", command=fetch_and_analyze_url).grid(row=2, column=1, sticky="w", padx=(0, 10), pady=5)

# Title Search Section
tk.Label(gui, text="Enter Book Title:", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky="e", padx=(10, 5), pady=(15, 5))
title_entry_box = tk.Entry(gui, width=40)
title_entry_box.grid(row=3, column=1, sticky="w", padx=(0, 10), pady=(15, 5))
tk.Button(gui, text="Search", command=search_and_analyze_title).grid(row=4, column=1, sticky="w", padx=(0, 10), pady=5)

# Output Box
output = tk.Text(gui, height=20, width=70)
output.grid(row=5, column=0, columnspan=2, padx=10, pady=15)

gui.mainloop()
