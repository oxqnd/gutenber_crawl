import pandas as pd

def process_data(input_file):
    df = pd.read_csv(input_file)
    # 데이터 처리 로직 추가 (예: 텍스트 정제, 필요한 메타데이터 추출 등)
    df['Processed_Text'] = df['Text'].apply(lambda x: x.replace('\n', ' '))  # 예시: 개행문자 제거
    df.to_csv('processed_gutenberg_books.csv', index=False)

if __name__ == "__main__":
    process_data('gutenberg_books.csv')