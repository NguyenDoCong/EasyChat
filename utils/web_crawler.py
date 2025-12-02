from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def crawl_webpage(url):
    """
    Crawl webpage to extract markdown content and all links using crawl4ai.
    This is an async function that should be awaited in async contexts.
    """
    # crawl4ai uses playwright, which may need to be installed via:
    # pip install playwright
    # python -m playwright install
    
    # Configure the crawler to wait for network idle, which is better for
    # dynamic pages that load content with JavaScript.
    config = CrawlerRunConfig(
        # wait_until="networkidle"
    )
    
    async with AsyncWebCrawler() as crawler:
        try: 
            result = await crawler.arun(url=url, config=config)
            
            if not result or not result.success:
                raise Exception(f"Failed to crawl {url}. Error: {result.error_message if result else 'Unknown error'}")
                
            # The main content is in result.markdown
            clean_text = result.markdown

            # Links are in result.links, categorized. Extract just the href.
            all_link_objects = result.links.get('internal', []) + result.links.get('external', [])
            links = [link.get('href') for link in all_link_objects if link.get('href')]

            # Get images
            images_info = result.media.get("images", [])

            for i, img in enumerate(images_info[:3]):  # Inspect just the first 3
                print(f"[Image {i}] URL: {img['src']}")
                print(f"           Alt text: {img.get('alt', '')}")
                print(f"           Score: {img.get('score')}")
                print(f"           Description: {img.get('desc', '')}\n")

            print(f"Found {len(images_info)} images in total.")
            img_src = [img['src'] for img in images_info]
            for img in img_src:
                print(f"Image URL: {img}")
            image = img_src[0] if img_src else ""
        
            return url, clean_text, links, image
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return url, "", [], ""

if __name__ == "__main__":
    import asyncio
    
    async def main():
        test_url = "https://rangdong.com.vn/category/den-led-chieu-sang"
        
        url, content, links, img = await crawl_webpage(test_url)
        
        if content:
            print(f"Content length: {len(content)}")
            print(f"Content preview: {content[:100000]}{'...' if len(content) > 100000 else ''}")
        
        if links:
            print(f"\nFound {len(links)} unique links:")
            for link in links[:5]:
                print(f"  {link}")
            
            if len(links) > 5:
                print(f"  ... and {len(links) - 5} more")

        # if imgs:
        #     print(f"\nFound {len(imgs)} images:")
        #     for img in imgs[:5]:
        #         print(f"  {img}")
            
        #     if len(imgs) > 5:
        #         print(f"  ... and {len(imgs) - 5} more")

        if img:
            print(f"\nFirst image URL: {img}")
    
    asyncio.run(main()) 