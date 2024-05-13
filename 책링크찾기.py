import re
import requests
from bs4 import BeautifulSoup
import logging
from tqdm import tqdm

# 로깅 설정
logging.basicConfig(filename='check_books.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def extract_failed_book_ids(log_file):
    """로그 파일에서 실패한 책 ID를 추출합니다."""
    failed_ids = set()
    with open(log_file, 'r') as file:
        for line in file:
            match = re.search(r'Book ID (\d+): All URL patterns failed', line)
            if match:
                failed_ids.add(int(match.group(1)))
    return list(failed_ids)

def find_book_download_url(book_id):
    """구텐베르크 웹사이트에서 책의 다운로드 링크를 찾습니다. PDF, Plain Text, ePub, HTML을 검색합니다."""
    base_url = f"https://www.gutenberg.org/ebooks/{book_id}"
    formats = [
        ('pdf', f"https://www.gutenberg.org/files/{book_id}/{book_id}-pdf.pdf"),
        ('txt', f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8"),
        ('epub', f"https://www.gutenberg.org/ebooks/{book_id}.epub.noimages"),
        ('html', f"https://www.gutenberg.org/ebooks/{book_id}.html.noimages")
    ]
    
    try:
        for format_name, format_url in formats:
            response = requests.head(format_url)  # GET 대신 HEAD 요청으로 빠르게 링크 확인
            if response.status_code == 200:
                return format_url  # 성공적으로 파일을 찾으면 URL 반환
    except Exception as e:
        logging.error(f"Error retrieving book ID {book_id} for format {format_name}: {e}")

    # 기타 다운로드 링크 탐색
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # HTML 페이지에서 특정 파일 형식을 찾습니다.
            links = soup.find_all('a', href=True)
            for link in links:
                if 'html' in link['href']:
                    return f"https://www.gutenberg.org{link['href']}"
    except Exception as e:
        logging.error(f"Error retrieving book ID {book_id}: {e}")

    return None  # 링크를 찾지 못하면 None 반환

def check_failed_books(log_file):
    """실패한 책 ID를 로그 파일에서 추출하고 다운로드 링크를 검색합니다."""
    failed_book_ids = extract_failed_book_ids(log_file)
    results = {}
    for book_id in tqdm(failed_book_ids, desc="Processing books"):
        url = find_book_download_url(book_id)
        if url:
            results[book_id] = url
            logging.info(f"Book ID {book_id}: Available at {url}")
        else:
            results[book_id] = 'No available download URL found'
            logging.warning(f"Book ID {book_id}: No available download URL found")
    return results

# 로그 파일을 지정하고 스크립트 실행
log_file = 'download_books.log'
results = check_failed_books(log_file)
print(results)
