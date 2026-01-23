from crawl4ai.deep_crawling.filters import FilterChain, SEOFilter, ContentRelevanceFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DFSDeepCrawlStrategy, BestFirstCrawlingStrategy
import os
import asyncio
import json
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig,
)
from crawl4ai import LLMExtractionStrategy, JsonXPathExtractionStrategy
from dotenv import load_dotenv
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from pathlib import Path
from crawl4ai.content_filter_strategy import PruningContentFilter
from langchain_core.documents import Document

load_dotenv()


##################### test deep crawl ##################################

async def test_deep_crawl(root: str, query: str) -> List[Document]:

    # Create an SEO filter that looks for specific keywords in page metadata
    seo_filter = SEOFilter(
        threshold=0.3,  # Minimum score (0.0 to 1.0)
        keywords=[query]
    )

    # Create a content relevance filter
    relevance_filter = ContentRelevanceFilter(
        query=query,
        threshold=0.3  # Minimum similarity score (0.0 to 1.0)
    )

    # Create a scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=[query],
        weight=0.3
    )

    cache_dir = Path("./schema_cache")
    cache_dir.mkdir(exist_ok=True)
    schema_file = cache_dir / f"product_schema_{root[8:]}.json"

    # 1. Generate or load schema
    if schema_file.exists():
        xpath_schema = json.load(schema_file.open())
        print(f"Using cached schema: {xpath_schema}")

    xpath_strategy = JsonXPathExtractionStrategy(xpath_schema)

    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=FilterChain([relevance_filter, seo_filter]),
            # Maximum number of pages to crawl (optional)
            max_pages=100,
            # score_threshold=0.3,       # Minimum score for URLs to be crawled (optional)
            url_scorer=keyword_scorer,
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True,
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=xpath_strategy,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()  # For fit_markdown support
        ),
    )

    results = []

    final_results = []

    try:

        async with AsyncWebCrawler() as crawler:
            try:
                results = await crawler.arun(root, config=config)
            except Exception as e:
                print(f"Error during crawling: {e}")

            print(f"Crawled {len(results)} pages in total")


            # Access individual results
            for result in results:  # Show first 3 results
                if result.success:
                
                    print(f"URL: {result.url}")
                    print(f"Depth: {result.metadata.get('depth', 0)}")
                    if result.success:
                        print(f"Extracted Content: {result.extracted_content}")
                        # print(f"Extracted Content Type: {type(result.extracted_content)}")
                        # print(f"Number of content items: {len(result.extracted_content)}")
                        if result.extracted_content == "[]":
                            print(f"No content extracted for {result.url}")
                            continue
                        print("Extracted content not empty!!!")

                        import ast
                        res = ast.literal_eval(result.extracted_content)

                        for r in res:
                            final_result = {}
                            print(f"Extracted item: {r}")
                            try:
                                print(f"Title: {r['title']}")
                                final_result["name"] = r["title"]
                            except Exception as e:
                                print(f"Error retrieving title metadata: {str(e)}")
                                final_result["name"] = None
                                continue
                            try:
                                print(f"URL: {result.url}")
                                final_result["link"] = result.url
                            except Exception as e:
                                print(f"Error retrieving URL: {str(e)}")
                                final_result["link"] = None
                                continue
                            try:
                                print(f"Price: {r['price']}")
                                final_result["price"] = r["price"]
                            except Exception as e:
                                print(
                                    f"Error parsing extracted price content: {str(e)}")
                                final_result["price"] = None
                                continue
                            try:
                                print(f"Description: {r['description']}")
                                # Truncate long description
                                final_result["description"] = r["description"][:200]
                            except Exception as e:
                                print(
                                    f"Error retrieving description metadata: {str(e)}")
                                final_result["description"] = None
                                continue
                            try:
                                print(f"Image: {r['image_url']}")
                                final_result["image"] = r["image_url"]
                            except Exception as e:
                                print(f"Error retrieving image metadata: {str(e)}")
                                final_result["image"] = None
                                continue
                            # print(f"Raw Markdown Length: {len(result.markdown.raw_markdown)}")
                            # print(
                            #     f"Citations Markdown Length: {len(result.markdown.markdown_with_citations)}"
                            # )

                            print(f"Appending {final_result}")

                            document = Document(
                                page_content=final_result['name'] +
                                final_result['description'],
                                metadata={"title": final_result['name'],
                                        "url": final_result['link'],
                                        "price": final_result['price'],
                                        "image_url": final_result['image'],
                                        "description": final_result['description']}
                            )

                            final_results.append(document)
                            print(
                                f"Number of final results so far: {len(final_results)}")
                            # if len(final_results) > 10:
                            #     print(
                            #         "More than 10 final results, stopping further processing.")
                            #     break

        return final_results

    except Exception as e:
        print(f"Error during deep crawl: {e}")
        return final_results

#####################################################################


class Product(BaseModel):
    name: str
    price: str
    description: str
    img_src: str


async def main():
    # 1. Define the LLM extraction strategy
    llm_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="gemini/gemini-3-flash-preview",
            api_token="env:GOOGLE_API_KEY",
        ),
        schema=Product.model_json_schema(),  # Or use model_json_schema()
        extraction_type="schema",
        instruction="Extract the product price from the content.",
        chunk_token_threshold=1000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="html",  # or "html", "fit_markdown"
        extra_args={"temperature": 0.0, "max_tokens": 800},
    )

    # 2. Build the crawler config
    crawl_config = CrawlerRunConfig(
        # extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS
    )

    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            # e.g. pass html2text style options
            options={"citations": True, "body_width": 80}
        )
    )

    # 3. Create a browser config if needed
    browser_cfg = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # 4. Let's say we want to crawl a single page
        result = await crawler.arun(
            url="https://www.google.com/search?q=vscode+debugger+python+example&sca_esv=540cd09fb70162eb&ei=KSVvaY7KFtj21e8P4qPWmQo&oq=vscode+debugger+py+example&gs_lp=Egxnd3Mtd2l6LXNlcnAiGnZzY29kZSBkZWJ1Z2dlciBweSBleGFtcGxlKgIIADIIECEYoAEYwwQyCBAhGKABGMMEMggQIRigARjDBDIIECEYoAEYwwRI9x5QwQ5Y4BRwAngBkAEAmAFpoAGPAqoBAzIuMbgBA8gBAPgBAZgCBaACnALCAgoQABhHGNYEGLADwgIGEAAYBxgewgIEEAAYHsICCxAAGIAEGIoFGIYDwgIFEAAY7wXCAggQABiABBiiBJgDAIgGAZAGCJIHAzQuMaAHhw6yBwMyLjG4B5cCwgcDMC41yAcHgAgB&sclient=gws-wiz-serp",
            # config=config,
        )

        md_res = result.markdown  # or eventually 'result.markdown'

        if result.success:
            # 5. The extracted content is presumably JSON
            # data = json.loads(result)
            print("Extracted items:", result)
            print(md_res.raw_markdown[:500])
            print(md_res.markdown_with_citations)
            print(md_res.references_markdown)
            with open("test_crawl4ai.html", "w", encoding="utf-8") as f:
                f.write(str(result))

            # # 6. Show usage stats
            # llm_strategy.show_usage()  # prints token usage
        else:
            print("Error:", result.error_message)


if __name__ == "__main__":
    asyncio.run(test_deep_crawl("https://rangdongstore.vn"))
