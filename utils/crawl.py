from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
import openai
from utils.claude_crawl import UniversalProductScraper

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

# client = OpenAI()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
# def crawl(url):
#     try:
        
#         r = requests.get(url)
#         html_doc = r.text
#         soup = BeautifulSoup(html_doc, "html.parser")
#         title = soup.title.text if soup.title else ""
#         # text = soup.get_text(strip=True)
#         text = soup.get_text()

#         # The client gets the API key from the environment variable `GEMINI_API_KEY`.
#         # response = client.responses.create(
#         #     model="gpt-4o-mini",
#         #     input=f"Summarize the following content in Vietnamese in 10 words:\n\n{text}",
#         # )

#         links = []

#         for link in soup.find_all('a'):
#             # print(link.get('href'))
#             links.append(link.get('href'))

#         images = []

#         imgs = soup.find_all("img")
#         # filtered_imgs = []
#         # filtered_imgs = [image['src'] for image in imgs if image['src']]

#         set_imgs =  list(set(imgs))

#         # for image in soup.find_all('img'):
#         #     # print(link.get('href'))
#         #     if 'products' in image['src']:
#         #         images.append(image['src'])

#         image = images[0] if images else ""
        
#         # print(response.output_text)
#         # return response.output_text
#     except Exception as e:
#         print(f"Error crawling {url}: {e}")
#         url = ""
#         # text = ""
#         # title = ""
#         # set_imgs = []
#         # image = ""

    

#     return url

def crawl(url):
    r = requests.get(url)
    html_doc = r.text
    soup = BeautifulSoup(html_doc, "html.parser")

    text = soup.get_text(strip=True)
    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    response = client.responses.create(
        model="openai/gpt-oss-20b:free",
        input=f"Summarize the following content in Vietnamese in 10 words:\n\n{text}",
    )

    print(response.output_text)
    return response.output_text

if __name__ == "__main__":
    url = "https://rangdong.com.vn/den-led-am-tran-downlight-du-phong-110-9w-da-pr959.html"
    url, text, links, images = crawl(url)
    with open("demofile.txt", "a") as f:
        f.write(text)
    # print(text)
    # print(images[0])
    # for img in images:
    #     print(img)
