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
from utils.test_generated_schema import extract_with_generated_schema, create_xpath_strategy
import requests

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

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)    

manager = ConnectionManager()

@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print("Received data via WebSocket:", data)
            
            # Parse JSON từ frontend
            payload = json.loads(data)
            search_query = payload.get("message", "")
            root_url = payload.get("root", "https://www.thegioididong.com")
            
            start_time = time.perf_counter()
            logger.info(f"Received crawl request: {search_query} for site: {root_url}")
            print(f"Received crawl request: {search_query} for site: {root_url}")

            try:
                package = {"status": "success", "message": "Searching for products..."}
                await websocket.send_json(package)
                print("Message sent: Searching for products...")                
                
                results = DDGS().text(
                    f"{search_query} site:{root_url}", max_results=20
                )
                
                # selected_urls = []

                urls = []     

                for result in results:

                    print("link:", result['href'])

                    # document = Document(page_content=result['title'], metadata = {"url": result['href']})

                    # documents.append(document)
                    # if result['href'] not in urls:

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

                # scraper = UniversalProductScraper(
                #     use_llm=False,  # Set True nếu muốn dùng LLM
                #     llm_api_key="your-api-key-here"  # Thêm API key nếu dùng LLM
                # )

                # products = await asyncio.gather(
                #     *[extract_with_generated_schema(r, data.root) for r in urls if r]
                # )

                tmp=0
                
                try:
                    for i, url in enumerate(urls):
                        x=requests.get(url)
                        if x.status_code == 200:
                            tmp=i
                            break
                except Exception as e:
                    print("Error requesting URL:", str(e))

                package = {"status": "success", "message": "Generating schema..."}

                await websocket.send_json(package)

                await create_xpath_strategy(urls[tmp], root_url, overwrite=False)

                package = {"status": "success", "message": "Extracting results..."}

                await websocket.send_json(package)

                products = await extract_with_generated_schema(urls[:10], root_url)

                print(f"Number of products: {len(products)}")

                if len(products)<1:
                    package = {"status": "success", "message": "Generating another schema..."}

                    await websocket.send_json(package)

                    await create_xpath_strategy(urls[tmp+1], root_url, overwrite=True)

                    package = {"status": "success", "message": "Extracting results..."}

                    await websocket.send_json(package)

                    products = await extract_with_generated_schema(urls[:10], root_url)

                # for doc in docs[:5]:
                #     urls.append(doc.metadata["url"])

                # with ThreadPoolExecutor(max_workers=4) as executor:
                #     products = list(executor.map(scraper.scrape, urls))

                # final_products = list((product for product in products if product))

                # try:

                #     unique = list({item["link"]: item for item in final_products}.values())
                # except Exception as e:
                #     print("Error deduplicating products:", str(e))
                #     unique = final_products


                # print("number of final_products:", len(unique))

                # for item in unique:
                #     print("product:", item)

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

                # return {"status": "success", "type": "products", "data": products}
                package = {"status": "success", "type": "products", "data": products}

                await websocket.send_json(package)
                

            except Exception as e:
                logger.error(f"Error in /crawl endpoint: {str(e)}", exc_info=True)
                # raise HTTPException(status_code=500, detail=str(e))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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

