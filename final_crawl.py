import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import re
import os

def get_book_data(book_id):
    url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    try:
        with requests.Session() as session:
            response = session.get(url)
            response.raise_for_status()
            return response.text
    except requests.RequestException:
        return None

def get_book_metadata(book_id):
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    try:
        with requests.Session() as session:
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            metadata_table = soup.find('table', class_='bibrec')
            year = "Unknown"
            if metadata_table:
                for row in metadata_table.find_all('tr'):
                    if 'Release Date' in row.find('th').get_text() if row.find('th') else '':
                        year_match = re.search(r'\d{4}', row.find('td').get_text() if row.find('td') else '')
                        if year_match:
                            year = year_match.group(0)
                            break
            return year
    except requests.RequestException:
        return "Unknown"

def download_books(book):
    title = book.select_one('span.title').text if book.select_one('span.title') else "No Title"
    author = book.select_one('span.subtitle').text if book.select_one('span.subtitle') else "Unknown Author"
    book_id = book.a['href'].split('/')[-1]
    text = get_book_data(book_id)
    year = get_book_metadata(book_id)
    if text:
        return {
            'ID': book_id,
            'Title': title,
            'Author': author,
            'Year': year,
            'Text': text
        }

def get_books_list():
    index_url = "https://www.gutenberg.org/ebooks/search/?sort_order=downloads&languages=en"
    books = []
    while True:
        response = requests.get(index_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        book_elements = soup.select('li.booklink')
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(tqdm(executor.map(download_books, book_elements), total=len(book_elements), desc="Downloading books"))
            books.extend([result for result in results if result])
        next_button = soup.find('a', string='Next')
        if next_button:
            index_url = "https://www.gutenberg.org" + next_button['href']
        else:
            break
    return books

def save_to_excel(books):
    df = pd.DataFrame(books)
    df.to_excel('gutenberg_books.xlsx', index=False, engine='openpyxl')

if __name__ == "__main__":
    if not os.path.exists('gutenberg_books.xlsx'):
        books = get_books_list()
        save_to_excel(books)
    else:
        print("Data already downloaded.")
