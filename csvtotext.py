import pandas as pd
import os
from tqdm import tqdm

def save_texts_to_files():
    # Excel 파일에서 데이터를 로드합니다.
    df = pd.read_excel('gutenberg_books.tsv')

    # 'texts' 디렉토리가 없다면 생성합니다.
    if not os.path.exists('texts'):
        os.makedirs('texts')

    # 각 책의 본문을 별도의 파일로 저장합니다.
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Saving books"):
        try:
            # 파일 이름 생성 시 특수 문자 제거 및 길이 제한
            title = ''.join([c for c in row['Title'] if c.isalnum() or c in " _.,"])[:50]
            file_path = os.path.join('texts', f"{row['ID']}_{title}.txt")
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(row['Text'])
            print(f"Saved {file_path}")
        except Exception as e:
            print(f"Failed to save {file_path}: {e}")

if __name__ == "__main__":
    save_texts_to_files()
