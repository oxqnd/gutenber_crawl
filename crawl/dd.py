import pandas as pd
import requests
import os
import time
import logging
from tqdm import tqdm  # tqdm 라이브러리 가져오기

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
download_dir = './책 다운로드'
os.makedirs(download_dir, exist_ok=True)

# 순차 파일 다운로드 함수
def download_file(url, title, download_dir, max_retries=10, delay_between_retries=10):
    filename = f"{title.replace(' ', '_').replace('/', '_')}.pdf"
    file_path = os.path.join(download_dir, filename)
    
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                #print(f"Downloaded: {title}")
                break
            else:
                raise Exception(f"Failed to download {title}: {response.status_code}")
        except Exception as e:
            retries += 1
            logging.error(f"Attempt {retries} failed for {title} with error: {e}")
            #print(f"Retrying {title} in {delay_between_retries} seconds...")
            time.sleep(delay_between_retries)
    else:
        print(f"Failed to download {title} after {max_retries} attempts.")

# 모든 파일을 순차적으로 다운로드 (tqdm 추가)
for url, title in tqdm(zip(download_links, titles), total=len(download_links), desc='Downloading books'):
    download_file(url, title, download_dir)

print("All downloads completed.")
