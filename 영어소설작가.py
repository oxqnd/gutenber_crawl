import aiohttp
import asyncio
from bs4 import BeautifulSoup
import os
import logging

# 로깅 설정
logging.basicConfig(filename='download_authors.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

async def fetch_text(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                logging.error(f"Failed to fetch {url}: Status code {response.status}")
                return None
    except Exception as e:
        logging.error(f"Error fetching {url}: {str(e)}")
        return None

async def get_book_metadata(session, book_id):
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    metadata = {'author': "Unknown", 'language': "Unknown"}
    text = await fetch_text(session, url)
    if text:
        soup = BeautifulSoup(text, 'html.parser')
        metadata_table = soup.find('table', class_='bibrec')
        if metadata_table:
            for row in metadata_table.find_all('tr'):
                th_text = row.find('th').get_text() if row.find('th') else ''
                td_text = row.find('td').get_text() if row.find('td') else ''
                if 'Author' in th_text:
                    metadata['author'] = td_text.strip()
                if 'Language' in th_text:
                    metadata['language'] = td_text.strip()
    return metadata

async def collect_authors(session, book):
    book_id = book.a['href'].split('/')[-1]
    metadata = await get_book_metadata(session, book_id)
    if metadata['language'].lower() == 'english':
        return metadata['author']
    return None

async def get_authors_list():
    index_url = "https://www.gutenberg.org/ebooks/search/?sort_order=downloads&languages=en"
    authors = []
    async with aiohttp.ClientSession() as session:
        while True:
            text = await fetch_text(session, index_url)
            if text:
                soup = BeautifulSoup(text, 'html.parser')
                book_elements = soup.select('li.booklink')
                if not book_elements:
                    break
                tasks = [collect_authors(session, book) for book in book_elements]
                results = await asyncio.gather(*tasks)
                authors.extend([result for result in results if result])
                next_button = soup.find('a', string='Next')
                if next_button:
                    index_url = "https://www.gutenberg.org" + next_button['href']
                else:
                    break
    return authors

def save_authors_to_file(authors):
    with open('gutenberg_authors.txt', 'w', encoding='utf-8') as file:
        for author in set(authors):  # Remove duplicates and save
            file.write(f"{author}\n")

if __name__ == "__main__":
    if not os.path.exists('gutenberg_authors.txt'):
        authors_list = asyncio.run(get_authors_list())
        save_authors_to_file(authors_list)
    else:
        print("Author list already downloaded.")
