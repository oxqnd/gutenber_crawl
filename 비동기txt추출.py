import pandas as pd
import os
import asyncio
import aiofiles
from tqdm import tqdm

async def save_text_to_file(id, title, text, base_path='texts'):
    file_path = os.path.join(base_path, f"{id}_{title}.txt")
    try:
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as file:
            await file.write(text)
        print(f"Saved {file_path}")
    except Exception as e:
        print(f"Failed to save {file_path}: {e}")

async def save_texts_to_files():
    df = pd.read_csv('gutenberg_books.tsv', delimiter='\t')

    if not os.path.exists('texts'):
        os.makedirs('texts')

    tasks = []
    for index, row in df.iterrows():
        title = ''.join([c for c in row['Title'] if c.isalnum() or c in " _.,"])[:50]
        task = save_text_to_file(row['ID'], title, row['Text'])
        tasks.append(task)
    
    for chunk in tqdm([tasks[i:i+10] for i in range(0, len(tasks), 10)], desc="Saving books"):
        await asyncio.gather(*chunk)

if __name__ == "__main__":
    asyncio.run(save_texts_to_files())
