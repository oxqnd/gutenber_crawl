import aiohttp
import asyncio
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

async def fetch_page(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.text()
        else:
            print(f"Failed to fetch {url}: Status code {response.status}")
            return None

async def count_books_on_page(session, base_url, start_index):
    url = f"{base_url}{start_index}"
    html = await fetch_page(session, url)
    if not html:
        print(f"No HTML returned for URL: {url}")
        return 0
    soup = BeautifulSoup(html, 'html.parser')
    book_elements = soup.select('li.booklink a[href]')
    if not book_elements:
        print(f"No book links found at URL: {url}")
        return 0

    english_books_count = 0
    for link in book_elements:
        book_id = link['href'].split('/')[-1]
        metadata_url = f"https://www.gutenberg.org/ebooks/{book_id}"
        metadata_html = await fetch_page(session, metadata_url)
        if metadata_html:
            metadata_soup = BeautifulSoup(metadata_html, 'html.parser')
            language_element = metadata_soup.find('table', class_='bibrec').find('th', string="Language").find_next_sibling('td')
            if language_element and 'English' in language_element.text:
                english_books_count += 1
        else:
            print(f"Failed to fetch metadata for book ID: {book_id}")

    return english_books_count

async def get_total_english_books():
    base_url = "https://www.gutenberg.org/ebooks/search/?sort_order=downloads&languages=en&start_index="
    start_index = 1
    total_english_books = 0
    async with aiohttp.ClientSession() as session:
        while True:
            url = f"{base_url}{start_index}"
            response = await session.get(url)
            if response.status == 400:
                print(f"Failed to fetch page at start_index={start_index}: HTTP 400 Bad Request")
                break
            html = await response.text()
            if not html:
                print(f"No more pages to process, stopping at start_index={start_index}")
                break
            soup = BeautifulSoup(html, 'html.parser')
            book_elements = soup.select('li.booklink a[href]')
            if not book_elements:
                print("No more books found, stopping the process.")
                break
            for link in book_elements:
                book_id = link['href'].split('/')[-1]
                metadata_url = f"https://www.gutenberg.org/ebooks/{book_id}"
                metadata_html = await fetch_page(session, metadata_url)
                metadata_soup = BeautifulSoup(metadata_html, 'html.parser')
                language_element = metadata_soup.find('table', class_='bibrec').find('th', string="Language").find_next_sibling('td')
                if language_element and 'English' in language_element.text:
                    total_english_books += 1
            start_index += 25
            print(f"Processed {start_index} books so far, total English books counted: {total_english_books}")

    return total_english_books

if __name__ == "__main__":
    total_english_books = asyncio.run(get_total_english_books())
    print(f"Total number of English books: {total_english_books}")

