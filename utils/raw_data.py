from langchain_core.documents import Document
from pydantic import BaseModel
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from utils.crawl import crawl
from utils.url_validator import filter_valid_urls

class Data(BaseModel):
    href: str

def get_data(href: str) -> list[Document]:
    """Get all data."""

    url, content, links, _ = crawl(href)
    print(f"Crawled {url}: {len(content)} characters, {len(links)} links")
    parsed = urlparse(url)
    valid_links = filter_valid_urls(links, [parsed.hostname])
    filtered_links = list(set(valid_links))
    with ThreadPoolExecutor(max_workers=500) as executor:
        results = executor.map(crawl, filtered_links)

    documents = []

    for result in results:
        # print("-------------------")
        # print(f"url:{result[0]}")  
        # print(f"content:{result[1][:50]}")  
        if "Giá bán lẻ đề xuất" not in result[1]:
            continue
        document = Document(page_content=result[1], metadata={"source": result[0], "image": result[3]})
        documents.append(document)

    # pprint.pprint(results)
    return documents