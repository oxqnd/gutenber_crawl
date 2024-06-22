import pandas as pd
import requests
import os
import time
import logging
from tqdm import tqdm
from urllib.parse import urlparse

# 로그 설정
logging.basicConfig(
    filename='sequential_download_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# CSV 파일 경로 및 읽기
file_path = 'english_books_final.csv'
df = pd.read_csv(file_path)

# 다운로드 링크와 책 제목을 매칭
download_links = df['Download Link'].tolist()
titles = df['Title'].tolist()

# 다운로드 디렉토리 설정
download_dir = './test'
os.makedirs(download_dir, exist_ok=True)

# 파일 확장자 추출 함수
def get_extension(url):
    parsed_url = urlparse(url)
    _, ext = os.path.splitext(parsed_url.path)
    return ext if ext else '.dat'  # 확장자가 없으면 기본으로 '.dat' 사용

# 순차 파일 다운로드 함수
def download_file(url, title, download_dir, max_retries=10, delay_between_retries=10):
    extension = get_extension(url)
    filename = f"{title.replace(' ', '_').replace('/', '_')}{extension}"
    file_path = os.path.join(download_dir, filename)
    
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                content_length = response.headers.get('Content-Length')
                content_type = response.headers.get('Content-Type')
                
                # 로그에 Content-Length 및 Content-Type 기록
                logging.info(f"Downloading {title} - Content-Length: {content_length}, Content-Type: {content_type}")
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                # 파일 크기 확인 (빈 파일 여부)
                file_size = os.path.getsize(file_path)
                if file_size < 1024:  # 예를 들어, 1KB 미만인 경우 빈 파일로 간주
                    raise Exception(f"Downloaded file {filename} is too small, likely empty. Size: {file_size} bytes.")
                
                break  # 정상적으로 다운로드 완료 시 루프 종료
            else:
                raise Exception(f"Failed to download {title}: HTTP {response.status_code}")
        except Exception as e:
            retries += 1
            logging.error(f"Attempt {retries} failed for {title} with error: {e}")
            time.sleep(delay_between_retries)
            if retries == max_retries:
                # 최종 시도에서도 실패한 경우 빈 파일 삭제
                if os.path.exists(file_path):
                    os.remove(file_path)
                logging.error(f"Final attempt failed. {title} not downloaded successfully.")

# 모든 파일을 순차적으로 다운로드 (tqdm 추가)
for url, title in tqdm(zip(download_links, titles), total=len(download_links), desc='Downloading books'):
    download_file(url, title, download_dir)

print("All downloads completed.")
