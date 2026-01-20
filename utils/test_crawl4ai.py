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
from crawl4ai import LLMExtractionStrategy
from dotenv import load_dotenv
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

load_dotenv()

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
            options={"citations": True, "body_width": 80}  # e.g. pass html2text style options
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
    asyncio.run(main())
