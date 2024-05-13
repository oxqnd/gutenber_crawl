import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import os
from concurrent.futures import ThreadPoolExecutor

def get_book_data(book_id):
    url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    try:
        with requests.Session() as session:
            response = session.get(url)
            response.raise_for_status()
            return response.text
    except requests.RequestException:
        return None

def download_books(book):
    title = book.select_one('span.title').text if book.select_one('span.title') else "No Title"
    author = book.select_one('span.subtitle').text if book.select_one('span.subtitle') else "Unknown Author"
    book_id = book.a['href'].split('/')[-1]
    text = get_book_data(book_id)
    if text:
        return {
            'ID': book_id,
            'Title': title,
            'Author': author,
            'Text': text  # 전체 텍스트 저장
        }

def get_books_list():
    index_url = "https://www.gutenberg.org/ebooks/search/?sort_order=downloads&languages=en"
    books = []

    while index_url:
        response = requests.get(index_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        book_elements = soup.select('li.booklink')
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(tqdm(executor.map(download_books, book_elements), total=len(book_elements), desc="Downloading books"))
            books.extend([result for result in results if result is not None])

        next_button = soup.find('a', text='Next')  # 'Next' 링크를 찾습니다
        if next_button:
            index_url = "https://www.gutenberg.org" + next_button['href']  # 다음 페이지의 URL을 업데이트합니다
        else:
            break  # 다음 페이지가 없으면 중단합니다

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
