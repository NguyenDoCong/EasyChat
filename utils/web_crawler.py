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
        result = await crawler.arun(url=url, config=config)
        
        if not result or not result.success:
            raise Exception(f"Failed to crawl {url}. Error: {result.error_message if result else 'Unknown error'}")
            
        # The main content is in result.markdown
        clean_text = result.markdown

        # Links are in result.links, categorized. Extract just the href.
        all_link_objects = result.links.get('internal', []) + result.links.get('external', [])
        links = [link.get('href') for link in all_link_objects if link.get('href')]
        
        return clean_text, links

if __name__ == "__main__":
    import asyncio
    
    async def main():
        test_url = "https://hanoikids.org/"
        
        content, links = await crawl_webpage(test_url)
        
        if content:
            print(f"Content length: {len(content)}")
            print(f"Content preview: {content[:100000]}{'...' if len(content) > 100000 else ''}")
        
        if links:
            print(f"\nFound {len(links)} unique links:")
            for link in links[:5]:
                print(f"  {link}")
            
            if len(links) > 5:
                print(f"  ... and {len(links) - 5} more")
    
    asyncio.run(main()) 