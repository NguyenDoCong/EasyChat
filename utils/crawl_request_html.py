from requests_html import AsyncHTMLSession
from bs4 import BeautifulSoup

async def crawl_webpage(url):
    session = AsyncHTMLSession()
    try:
        r = await session.get(url)
        await r.html.arender()  # Render JavaScript content
        await session.close()

        # r.html.render(timeout=20)

        # return r, url

        text = r.html.text

        # links = list(r.html.absolute_links)

        # images = r.html.find('img')
        # img_src = [img.attrs.get('src') for img in images if img.attrs.get('src')]
        # image = img_src[0] if img_src else ""

        return text
    except Exception as e:
        print(f"Error crawling {url}: {e}")

        return None, ""

        return url, "", [], ""
    
if __name__ == "__main__":
    import asyncio

    async def main():
        test_url = "https://www.thegioididong.com/dtdd/realme-14t-5g-8gb?utm_flashsale=1"

        clean_text = await crawl_webpage(test_url)

        if clean_text:
            # print(f"Page text length: {len(r.html.text)}")
            # print(f"First 500 characters of text:\n{clean_text}")

            # print(f"\nFound {len(r.html.absolute_links)} unique links:")
            # for link in list(r.html.absolute_links)[:5]:
            #     print(f"  {link}")

            # images = r.html.find('img')
            # print(f"\nFound {len(images)} images:")
            # for img in images[:5]:
            #     print(f"  {img.attrs.get('src')}")
            soup = BeautifulSoup(clean_text, 'html.parser')
            print(soup.get_text())

    asyncio.run(main())