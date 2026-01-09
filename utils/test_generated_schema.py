from crawl4ai import (
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
    LLMConfig,
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from pathlib import Path
import json

import asyncio
from dotenv import load_dotenv

load_dotenv()


async def run_extraction(crawler: AsyncWebCrawler, url: str, strategy, name: str):
    """Helper function to run extraction with proper configuration"""
    try:
        # Configure the crawler run settings
        config = CrawlerRunConfig(
            verbose=True,
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=strategy,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter()  # For fit_markdown support
            ),
        )

        # Run the crawler
        result = await crawler.arun(url=url, config=config)

        if result.success:
            print(f"\n=== {name} Results ===")
            print(f"Extracted Content: {result.extracted_content}")
            print(f"Title: {result.metadata["title"]}")
            import ast
            res = ast.literal_eval(result.extracted_content)
            print(f"Price: {res[0]["price"]}")
            print(f"Description: {result.metadata["description"]}")
            print(f"Image: {result.metadata["og:image"]}")
            
            print(f"Raw Markdown Length: {len(result.markdown.raw_markdown)}")
            print(
                f"Citations Markdown Length: {len(result.markdown.markdown_with_citations)}"
            )
            if result.extracted_content:
                for item in res:
                    # print(type(item),item)
                    for key, value in item.items():
                        print(f"{key}: {value}")
            with open("result.txt", "w") as f:
                f.write(str(result.metadata["title"]))
        
        else:
            print(f"Error in {name}: Crawl failed")

    except Exception as e:
        print(f"Error in {name}: {str(e)}")


async def extract_with_generated_schema():
    cache_dir = Path("./schema_cache")
    cache_dir.mkdir(exist_ok=True)
    schema_file = cache_dir / "product_schema.json"

    # 1. Generate or load schema
    if schema_file.exists():
        xpath_schema = json.load(schema_file.open())
        print(f"Using cached schema: {xpath_schema}")
    else:
        print("Generating schema via LLM...")

        run_config = CrawlerRunConfig(
            only_text=False,  # If True, tries to remove non-text elements
        )

        # Get sample HTML for context
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                "https://rangdongstore.vn/am-dien-sieu-toc-17l-rd-ast17-p1-p-221223003166",
                config=run_config,
            )
            html = result.fit_html
        try:
            with open("html.html", "w") as f:
                f.write(html)
            print("Sample HTML written to html.html for reference.")
        except Exception as e:
            print(f"Error writing HTML to file: {str(e)}")

        # # Option 1: Using OpenAI (requires API token)
        # css_schema = JsonCssExtractionStrategy.generate_schema(
        #     html,
        #     schema_type="css",
        #     # llm_config=LLMConfig(provider="openai/gpt-4o-mini",
        #     #                      api_token="env:OPENAI_API_KEY",
        #     #                      ),
        #     llm_config=LLMConfig(provider="gemini/gemini-2.5-flash",
        #                         api_token="env:GOOGLE_API_KEY",
        #                         ),
        # )

        target_json_example = {
            "name": "Product Cards",
            "baseSelector": "//div[@class='product-card']",
            "fields": [
                
                {
                    "name": "price",
                    "selector": ".//span[@class='price']",
                    "type": "text",
                },

            ],
        }

        target_json_example = str(target_json_example)

        # Option 2: Using Ollama (open source, no token needed)
        xpath_schema = JsonXPathExtractionStrategy.generate_schema(
            html,
            query="Product price",
            schema_type="xpath",
            target_json_example=target_json_example,
            llm_config=LLMConfig(
                provider="gemini/gemini-3-flash-preview",
                api_token="env:GOOGLE_API_KEY",
            ),
        )

        # Cache pattern for future use
        json.dump(xpath_schema, schema_file.open("w"), indent=2)

    xpath_strategy = JsonXPathExtractionStrategy(xpath_schema)

    with open("xpath_schema.txt", "w") as f:
        for key in xpath_schema:
            f.write(f"{key}: {xpath_schema[key]}\n")

    # print("Generated strategy:", css_schema)
    async with AsyncWebCrawler() as crawler:
        await run_extraction(
            crawler,
            "https://rangdongstore.vn/den-led-op-tran-ln29n-300x30024w-6500k-p-240820004148",
            xpath_strategy,
            "XPath Extraction",
        )


if __name__ == "__main__":
    asyncio.run(extract_with_generated_schema())
