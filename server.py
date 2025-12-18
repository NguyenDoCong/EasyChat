import re
import logging
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from utils.crawl import crawl
from pydantic import BaseModel, Field
import uvicorn

# from agent import agent_builder, build_retriever
from chain import initialize_retriever, store_search
from langchain_core.messages import HumanMessage
import asyncio
from typing import Dict
import json
from chain import llm_agent
from agent import agent_builder
from ddgs import DDGS
from openai import OpenAI
from langchain_openai import ChatOpenAI
import os
from utils.web_crawler import crawl_webpage
from google import genai
from utils.crawl_request_html import crawl_webpage as crawl_request_html
from requests_html import AsyncHTMLSession
from bs4 import BeautifulSoup
import concurrent.futures
from langchain_core.documents import Document
import pprint
from concurrent.futures import ThreadPoolExecutor
from test_extract_info import finalize_name
from utils.claude_crawl import UniversalProductScraper
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


def validate_and_sanitize_input(
    question: str, instruction: str = ""
) -> tuple[str, str]:
    """Validate and sanitize user inputs for safety."""
    if len(question) > 1000:
        raise ValueError("Question must be 1000 characters or less")

    if len(instruction) > 2000:
        raise ValueError("Instruction must be 2000 characters or less")

    if not question.strip():
        raise ValueError("Question cannot be empty")

    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    combined_text = f"{question} {instruction}".lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, combined_text, re.IGNORECASE):
            raise ValueError("Input contains potentially unsafe content")

    question = question.replace("<", "&lt;").replace(">", "&gt;")
    instruction = instruction.replace("<", "&lt;").replace(">", "&gt;")

    return question.strip(), instruction.strip()

class Info(BaseModel):
    href: str

@app.post("/hover")
def receive_hover(info: Info):
    logger.info(f"User hovered: {info.href}")
    try:
        scraper = UniversalProductScraper(
            use_llm=False,  # Set True nếu muốn dùng LLM
            llm_api_key="your-api-key-here"  # Thêm API key nếu dùng LLM
        )
        logger.info("Crawling data...")
        try:
            crawled_data = scraper.scrape(info.href, method="auto")
            print("Crawled data:", crawled_data)
            # logger.info(f"Crawl successful, data length: {len(crawled_data)}")
            # clean = re.sub(r"<think>.*?</think>", "", crawled_data, flags=re.DOTALL).strip()
            # logger.info(f"Cleaned data length: {len(clean)}")
            return {"result": crawled_data['specs']}
        except Exception as crawl_error:
            return {"error": f"Failed to crawl data: {str(crawl_error)}"}
    except Exception as e:
        logger.error(f"Error in /hover endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/init")
# async def create_store(info: Info):
async def create_store(documents: Document):
    """Build vector store."""
    # logger.info(f"Initializing vector store for URL: {info.href}")
    try:
        await initialize_retriever(documents)
        logger.info("Vector store initialized successfully")
        return {"message": "Vector store created successfully."}
    except Exception as e:
        logger.error(f"Error in /init endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ExtractedInfos(BaseModel):
    price: str = Field(description="giá")
    specs: str = Field(description="đặc điểm")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# client = genai.Client()

class Data(BaseModel):
    message: str
    url: str
    root: str

class Answer(BaseModel):
    bool_value: bool

@app.post("/crawl")
async def crawl_url(data: Data):
    start_time = time.perf_counter()
    logger.info(f"Received crawl request {data.message} for URL: {data.url} from {data.root}")
    print(f"Received crawl request {data.message} for URL: {data.url} from {data.root}")

    try:
        results = DDGS().text(
            f"{data.message} site:{data.root}", max_results=20
        )

        # selected_urls = []

        urls = []     

        for result in results:

            # document = Document(page_content=result['title'], metadata = {"url": result['href']})

            # documents.append(document)

            urls.append(result['href'])

        # await create_store(documents)

        # docs = store_search(f"{data.message}")

        # pprint.pprint(doc)

        # doc_content = "\n".join([d.page_content for d in doc])

        # response = client.responses.parse(
        #         model="openai/gpt-oss-20b:free",
        #         input=[
        #             {"role": "system", "content": f"Choose the document that suits the {data.message} the most."},
        #             {
        #                 "role": "user",
        #                 "content": doc_content,
        #             },
        #         ],
        #         # text_format=Answer,
        #     )
        # best_doc = response.output_parsed

        # pprint.pprint(best_doc)

        # selected_urls.append(best_doc.metadata["url"])

        # crawled_pages = []

        # results = await asyncio.gather(
        #     *[crawl(doc.metadata["url"]) for doc in docs[:4]]
        # )

        # with ThreadPoolExecutor(max_workers=4) as executor:
        #     results = list(executor.map(crawl, docs[:4]))

        scraper = UniversalProductScraper(
            use_llm=False,  # Set True nếu muốn dùng LLM
            llm_api_key="your-api-key-here"  # Thêm API key nếu dùng LLM
        )

        # products = await asyncio.gather(
        #     *[scraper.scrape(r) for r in results if r]
        # )


        # for doc in docs[:5]:
        #     urls.append(doc.metadata["url"])

        with ThreadPoolExecutor(max_workers=4) as executor:
            products = list(executor.map(scraper.scrape, urls))

        final_products = list((product for product in products if product))

        print(len(final_products))

        # products = []

        # for doc in docs[:5]:
        #     products.append(scraper.scrape(doc.metadata["url"],method="auto"))

        # # result = await crawl_request_html(doc[0].metadata["url"])
        # url, text, title, set_imgs = crawl(doc[0].metadata["url"])
        
        # product = scraper.scrape(url, method='auto')

        # # product = await extract_product_info(url, text, title, set_imgs, data.root, data.message)

        # products =[]

        # products.append(product)

        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"Thời gian thực hiện: {execution_time} giây")

        return {"status": "success", "type": "products", "data": final_products}
        

    except Exception as e:
        logger.error(f"Error in /crawl endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # async def test():
        # results = DDGS().text(
        #     f"đèn bàn site:https://rangdongstore.vn", max_results=5
        # )
        # for r in results:
        #     print("------------------------------------------")
        #     print(r)

        # r=await crawl_request_html("https://rangdongstore.vn/den-ban-c-2201000039/")
        # clean_text = r[0].html.text
        # soup = BeautifulSoup(clean_text, 'html.parser')
        # text = soup.get_text()
        # print(clean_text)

        # product =await extract_product_info(r[0],r[1],"https://rangdongstore.vn")
        # print(product)
    # asyncio.run(test())

    uvicorn.run(app, host="0.0.0.0", port=8000)
    # pass

