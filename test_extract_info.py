from openai import OpenAI
import os
from pydantic import BaseModel, Field
from utils.crawl_request_html import crawl_webpage as crawl_request_html
from bs4 import BeautifulSoup
import asyncio
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse, unquote
import re
from langchain_core.documents import Document
from chain import initialize_retriever, store_search
import pprint
from concurrent.futures import ThreadPoolExecutor
from utils.crawl import crawl

load_dotenv()

class ExtractedInfos(BaseModel):
    price: str = Field(description="giá")
    specs: str = Field(description="đặc điểm")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)    

def extract_filename_from_url(url: str) -> str:
    p = urlparse(url)
    path = p.path  # /2204005211/2022/04/11/bong-led-...jpeg
    fname = os.path.basename(path)  # bong-led-...jpeg
    fname = unquote(fname)  # decode %20, %2F...
    return fname

def normalize_filename(fname: str) -> str:
    s = fname.lower().strip()
    # remove characters you don't want (optional)
    s = re.sub(r'[^a-z0-9\-\._]', '-', s)
    s = re.sub(r'-{2,}', '-', s)
    return s

def finalize_name(img):
    raw_name = extract_filename_from_url(img.get('src') )
    norm_name = normalize_filename(raw_name)
    info = norm_name + " " + str(img.get('alt'))
    document = Document(page_content=info, metadata = {"src": img.get('src')})
    return document

async def extract_info():
    try:
        # result, _ = await crawl_request_html("https://rangdongstore.vn/den-led-bulb-tru-60w-tr135nd1-p-221223002875")

        # clean_text = result.html.text
        r = requests.get("https://rangdongstore.vn/den-duong-led-100w-csd06-p-221223003048")

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()
        # print(text)
        # imgs = soup.find_all("img")

        # filtered_imgs = []
        # filtered_imgs = [image for image in imgs if "rangdongstore.vn" in image['src']]

        # set_imgs =  list(set(filtered_imgs))

        # documents = []
        
        # # Extract src URLs from img tags
        # # img_urls = [img.get('src') for img in set_imgs if img.get('src')]

        # with ThreadPoolExecutor(max_workers=4) as executor:
        #     documents = list(executor.map(finalize_name, set_imgs))
        
        # # for img in imgs:
        # #     print("-------------------------------")
            
        # #     print(norm_name)
        #     # print(img['src'])
        #     # print(img['alt'])
        # # document = Document(page_content=norm_name, metadata = {"url": img['src']})

        # # documents.append(document)
        # pprint.pprint(documents)

        # await initialize_retriever(documents)

        # doc = store_search("Đèn LED Bulb Trụ 60W TR135NĐ1")

        # pprint.pprint(doc)

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

        print("price", infos.price)
        print("specs", infos.specs)
    except Exception as e:
        print(e)

if __name__=="__main__":
    asyncio.run(extract_info())
