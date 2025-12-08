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
        logger.info("Crawling data...")
        crawled_data = crawl(info.href)
        logger.info(f"Crawl successful, data length: {len(crawled_data)}")
        clean = re.sub(r"<think>.*?</think>", "", crawled_data, flags=re.DOTALL).strip()
        logger.info(f"Cleaned data length: {len(clean)}")
        return {"result": clean}
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
    price: str = Field(description="price of the product")
    specs: str = Field(description="description of the product")


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# client = genai.Client()


async def extract_product_info(r, url, root, query):
    try:
        name_element = r.html.find("title", first=True)
        name = name_element.text if name_element else "Unknown"

        # first_element = r.html.find("base", first=True)
        # link = first_element.attrs.get("href")

        link = url

        print("Đang lấy thông tin của url:", link)

        clean_text = r.html.text
        soup = BeautifulSoup(clean_text, "html.parser")
        text = soup.get_text()

        # links = list(r.html.absolute_links)

        images = r.html.find("img")
        # img_src = [img.attrs.get("src") for img in images if img.attrs.get("src")]
        # img_alt = [img.attrs.get("alt") for img in images if img.attrs.get("alt")]
        image = ""

        documents = []
        for i in images:
            # print("-------------------------------")
            # alt = i.attrs.get("alt")
            # print(alt)
            # if str(query).lower() in str(alt).lower():
            #     image = i.attrs.get("src")
            document = Document(page_content=str(i.attrs.get("alt")), metadata={"src":str(i.attrs.get("src"))})
            documents.append(document)

        # print(f"Img src is {image} with root {root}")

        await create_store(documents)

        doc = store_search(name)

        print("image -------------------------------------------------------")

        pprint.pprint(doc)

        image = doc[0].metadata["src"]

        # product = {}

        # if re.search("giá", text, re.IGNORECASE):
            # name = url["title"]
            # crawled_pages.append((page_data))
            # s = ''.join(clean_text)
            # s = text[:10000]  # Giới hạn độ dài văn bản đầu vào

        response = client.responses.parse(
            model="openai/gpt-oss-20b:free",
            input=[
                {"role": "system", "content": "Extract the product information."},
                {
                    "role": "user",
                    "content": text,
                },
            ],
            text_format=ExtractedInfos,
        )
        infos = response.output_parsed

        # response = client.models.generate_content(
        #     model="gemini-2.0-flash",
        #     contents=f"Extract the product information from the following text:\n {text}",
        #     config={
        #         "response_mime_type": "application/json",
        #         "response_json_schema": ExtractedInfos.model_json_schema(),
        #     },
        # )

        # infos = ExtractedInfos.model_validate_json(response.text)

        # for i, m in enumerate(result["messages"]):
        #     logger.debug(f"Message {i}: {type(m).__name__}")
        #     m.pretty_print()

        # # Extract the last message content
        # last_message = result["messages"][-1]
        # logger.info(f"Last message type: {type(last_message).__name__}")

        # response_content = getattr(last_message, "content", str(last_message))
        # # json_content = json.loads(response_content)
        # # print("Response Content:", json_content)
        # pattern = r"(\w+)\s*=\s*'([^']*)'"
        # result = dict(re.findall(pattern, response_content))

        # if not re.search("N/A", infos.price, re.IGNORECASE):

        try:

            product = {
                "name": name,
                "price": infos.price,
                "specs": infos.specs,
                "link": link,
                "image": image,
            }

        except Exception as e:
            print("Lỗi lấy thông tin sản phẩm", e)

        # products.append({
        #             "name": name,
        #             "price": infos.price,
        #             "specs": infos.specs,
        #             "link": link,
        #             "image": image
        #         })

        return product  # ADD THIS LINE

    except Exception as e:
        logger.error(f"Error processing crawled data: {str(e)}", exc_info=True)


def print_result(r):
    first_element = r.html.find("base", first=True)

    link = first_element.attrs.get("href")
    print(link)


class Data(BaseModel):
    message: str
    url: str
    root: str

class Answer(BaseModel):
    bool_value: bool

@app.post("/crawl")
async def crawl_url(data: Data):
    logger.info(f"Received crawl request {data.message} for URL: {data.url} from {data.root}")
    print(f"Received crawl request {data.message} for URL: {data.url} from {data.root}")

    try:
        results = DDGS().text(
            f"{data.message} site:{data.url}", max_results=1, region="vi-vn"
        )

        selected_urls = []
        documents = []

        for result in results:

            document = Document(page_content=result['body'], metadata = {"url": result['href']})

            documents.append(document)

            # response = client.responses.parse(
            #     model="openai/gpt-oss-20b:free",
            #     input=[
            #         {"role": "system", "content": "Decide if the content is about a product or not."},
            #         {
            #             "role": "user",
            #             "content": result['body'],
            #         },
            #     ],
            #     text_format=Answer,
            # )
            # answer = response.output_parsed

            # response = client.models.generate_content(
            #     model="gemini-2.0-flash",
            #     contents=f"Extract the product information from the following text:\n {text}",
            #     config={
            #         "response_mime_type": "application/json",
            #         "response_json_schema": ExtractedInfos.model_json_schema(),
            #     },
            # )

            # infos = ExtractedInfos.model_validate_json(response.text)

            # if answer:         
            # # if re.search(re.escape(data.message), result["title"], re.IGNORECASE):
            #     selected_urls.append(result)
            #     print(f"Selected URL based on title match: {result['href']}")

            # print(response.text)
            # if "yes" in response.text.lower():
            #     selected_urls.append(result["href"])

        await create_store(documents)

        doc = store_search(f"sản phẩm {data.message}")

        pprint.pprint(doc)
        selected_urls.append(doc[0].metadata["url"])

        # crawled_pages = []

        # results = await asyncio.gather(
        #     *[crawl_request_html(url) for url in selected_urls[:1]]
        # )

        # products = await asyncio.gather(
        #     *[extract_product_info(r[0], r[1], data.root, data.message) for r in results if r]
        # )

        result = await crawl_request_html(doc[0].metadata["url"])

        product = await extract_product_info(result[0], result[1], data.root, data.message)

        products =[]

        products.append(product)

        # # for r in results:
        # #     # print(f"Selected URL: {url['href']}")
        # #     # link, clean_text, links, image = await crawl_request_html(url["href"])
        # #     try:
        # #         name_element = r.html.find('title', first=True)
        # #         name = name_element.text if name_element else "Unknown"

        # #         first_element = r.html.find('base', first=True)

        # #         link = first_element.attrs.get('href')

        # #         clean_text = r.html.text
        # #         soup = BeautifulSoup(clean_text, 'html.parser')
        # #         text = soup.get_text()

        # #         # links = list(r.html.absolute_links)

        # #         images = r.html.find('img')
        # #         img_src = [img.attrs.get('src') for img in images if img.attrs.get('src')]
        # #         image = img_src[0] if img_src else ""

        # #         if re.search("giá", text, re.IGNORECASE):

        # #             # name = url["title"]
        # #             # crawled_pages.append((page_data))
        # #             # s = ''.join(clean_text)
        # #             s = clean_text[:10000]  # Giới hạn độ dài văn bản đầu vào

        # #             # response = client.responses.parse(
        # #             #     model="openai/gpt-oss-20b:free",
        # #             #     input=[
        # #             #         {"role": "system", "content": "Extract the product information."},
        # #             #         {
        # #             #             "role": "user",
        # #             #             "content": s,
        # #             #         },
        # #             #     ],
        # #             #     text_format=ExtractedInfos,
        # #             # )

        # #             response = client.models.generate_content(
        # #                 model="gemini-2.0-flash",
        # #                 contents=f"Extract the product information from the following text:\n {s}",
        # #                 config={
        # #                     "response_mime_type": "application/json",
        # #                     "response_json_schema": ExtractedInfos.model_json_schema(),
        # #                 },
        # #             )

        # #             # infos = response.output_parsed
        # #             infos = ExtractedInfos.model_validate_json(response.text)

        # #             # for i, m in enumerate(result["messages"]):
        # #             #     logger.debug(f"Message {i}: {type(m).__name__}")
        # #             #     m.pretty_print()

        # #             # # Extract the last message content
        # #             # last_message = result["messages"][-1]
        # #             # logger.info(f"Last message type: {type(last_message).__name__}")

        # #             # response_content = getattr(last_message, "content", str(last_message))
        # #             # # json_content = json.loads(response_content)
        # #             # # print("Response Content:", json_content)
        # #             # pattern = r"(\w+)\s*=\s*'([^']*)'"
        # #             # result = dict(re.findall(pattern, response_content))

        # #             # if not re.search("N/A", infos.price, re.IGNORECASE):

        # #             products.append({
        # #                         "name": name,
        # #                         "price": infos.price,
        # #                         "specs": infos.specs,
        # #                         "link": link,
        # #                         "image": image
        # #                     })
        # #     except Exception as e:
        # #         logger.error(f"Error processing crawled data: {str(e)}", exc_info=True)
        # #         continue

        return {"status": "success", "type": "products", "data": products}

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

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    pass

