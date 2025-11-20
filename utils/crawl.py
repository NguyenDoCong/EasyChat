from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
import openai

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

client = OpenAI()

def crawl(url):
    try:
        r = requests.get(url)
        html_doc = r.text
        soup = BeautifulSoup(html_doc, "html.parser")

        text = soup.get_text(strip=True)
        # The client gets the API key from the environment variable `GEMINI_API_KEY`.
        # response = client.responses.create(
        #     model="gpt-4o-mini",
        #     input=f"Summarize the following content in Vietnamese in 10 words:\n\n{text}",
        # )

        links = []

        for link in soup.find_all('a'):
            # print(link.get('href'))
            links.append(link.get('href'))

        # print(response.output_text)
        # return response.output_text
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        text = ""
        links = []

    return url, text, links
