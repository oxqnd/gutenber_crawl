import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import os

def get_book_data(book_id):
    # 책의 텍스트 데이터를 다운로드
    url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None

def get_books_list():
    # 영어 책들의 목록을 가져오는 함수
    index_url = "https://www.gutenberg.org/ebooks/search/?sort_order=downloads&languages=en"
    books = []
    response = requests.get(index_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    book_count = len(soup.select('li.booklink'))
    tqdm_iterator = tqdm(soup.select('li.booklink'), desc="Downloading books", unit="book")

    for book in tqdm_iterator:
        title = book.select_one('span.title').text if book.select_one('span.title') else "No Title"
        author = book.select_one('span.subtitle').text if book.select_one('span.subtitle') else "Unknown Author"
        book_id = book.a['href'].split('/')[-1]
        text = get_book_data(book_id)
        if text:
            books.append({
                'ID': book_id,
                'Title': title,
                'Author': author,
                'Text': text[:5000]  # 처음 5000자만 저장
            })

    return books

def save_to_csv(books):
    # 데이터를 CSV 파일로 저장
    df = pd.DataFrame(books)
    df.to_csv('gutenberg_books.csv', index=False)

if __name__ == "__main__":
    if not os.path.exists('gutenberg_books.csv'):
        books = get_books_list()
        save_to_csv(books)
    else:
        print("Data already downloaded.")
