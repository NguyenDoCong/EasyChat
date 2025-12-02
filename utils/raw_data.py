from langchain_core.documents import Document
from pydantic import BaseModel
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from utils.crawl import crawl
from utils.url_validator import filter_valid_urls
from utils.web_crawler import crawl_webpage
import asyncio


class Data(BaseModel):
    href: str

async def sem_crawl(href):
    sem = asyncio.Semaphore()
    async with sem:
        return await crawl_webpage(href)

async def get_data(href: str) -> list[Document]:
    """Get all data."""

    url, content, links, img = await crawl_webpage(href)
    print(f"Crawled {url}: {len(content)} characters, {len(links)} links")
    parsed = urlparse(url)
    valid_links = filter_valid_urls(links, [parsed.hostname])
    filtered_links = list(set(valid_links))
    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     results = executor.map(crawl_webpage, filtered_links)

    results = await asyncio.gather(*[sem_crawl(link) for link in filtered_links])

    documents = []

    for result in results:
        # print("-------------------")
        # print(f"url:{result[0]}")
        # print(f"content:{result[1][:50]}")
        if "Giá bán lẻ đề xuất" not in result[1]:
            continue
        document = Document(
            page_content=result[1], metadata={"source": result[0], "image": result[3]}
        )
        documents.append(document)

    # pprint.pprint(results)
    return documents
