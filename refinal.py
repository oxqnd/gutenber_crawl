import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import re
import os
import logging

# 로깅 설정
logging.basicConfig(filename='download_books.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def get_book_data(book_id):
    base_url = f"https://www.gutenberg.org/files/{book_id}"
    urls = [
        f"{base_url}/{book_id}-0.txt",
        f"{base_url}/{book_id}.txt",
        f"{base_url}/{book_id}-0.txt.utf8",
        f"{base_url}/{book_id}-pdf.pdf",
        f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8",
        f"https://www.gutenberg.org/ebooks/{book_id}.epub.noimages",
        f"https://www.gutenberg.org/ebooks/{book_id}.html.noimages"
    ]
    try:
        with requests.Session() as session:
            for url in urls:
                response = session.get(url)
                if response.status_code == 200:
                    return response.text
    except requests.RequestException as e:
        logging.error(f"Book ID {book_id}: Failed to download text, {e}")
    logging.warning(f"Book ID {book_id}: All URL patterns failed.")
    return None

def get_book_metadata(book_id):
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    metadata = {'year': "Unknown", 'language': "Unknown"}
    try:
        with requests.Session() as session:
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            metadata_table = soup.find('table', class_='bibrec')
            if metadata_table:
                for row in metadata_table.find_all('tr'):
                    th_text = row.find('th').get_text() if row.find('th') else ''
                    td_text = row.find('td').get_text() if row.find('td') else ''
                    if 'Release Date' in th_text:
                        year_match = re.search(r'\d{4}', td_text)
                        if year_match:
                            metadata['year'] = year_match.group(0)
                    if 'Language' in th_text:
                        metadata['language'] = td_text.strip()
    except requests.RequestException as e:
        logging.error(f"Book ID {book_id}: Failed to retrieve metadata, {e}")
    return metadata

def download_books(book):
    book_id = book.a['href'].split('/')[-1]
    metadata = get_book_metadata(book_id)
    if metadata['language'].lower() != 'english':
        return None  # 영어가 아닌 책은 건너뜁니다.
    title = book.select_one('span.title').text if book.select_one('span.title') else "No Title"
    author = book.select_one('span.subtitle').text if book.select_one('span.subtitle') else "Unknown Author"
    text = get_book_data(book_id)
    if text:
        return {
            'ID': book_id,
            'Title': title,
            'Author': author,
            'Year': metadata['year'],
            'Text': text
        }

def get_books_list():
    index_url = "https://www.gutenberg.org/ebooks/search/?sort_order=downloads&languages=en"
    books = []
    while True:
        response = requests.get(index_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        book_elements = soup.select('li.booklink')
        if not book_elements:
            break  # 책이 더 이상 없으면 중단합니다.
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(tqdm(executor.map(download_books, book_elements), total=len(book_elements), desc="Downloading books"))
            books.extend([result for result in results if result])
        next_button = soup.find('a', string='Next')
        if next_button:
            index_url = "https://www.gutenberg.org" + next_button['href']
        else:
            break
    return books

def clean_text(text):
    """Remove or replace illegal characters that might cause Excel to fail."""
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # ASCII 외 문자 제거
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)  # 제어 문자 제거
    return text

def save_to_excel(books):
    df = pd.DataFrame(books)
    df['Text'] = df['Text'].apply(clean_text)
    df.to_excel('gutenberg_books.xlsx', index=False, engine='openpyxl')

if __name__ == "__main__":
    if not os.path.exists('gutenberg_books.xlsx'):
        books = get_books_list()
        save_to_excel(books)
    else:
        print("Data already downloaded.")
