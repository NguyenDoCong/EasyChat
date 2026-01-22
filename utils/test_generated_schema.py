from crawl4ai import (
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
    LLMConfig,
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai import CrawlerMonitor, DisplayMode
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from pathlib import Path
import json

import asyncio
from dotenv import load_dotenv

load_dotenv()

async def run_extraction(crawler: AsyncWebCrawler, urls, strategy, name):
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

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=90.0,
            check_interval=1.0,
            max_session_permit=10,
            # monitor=CrawlerMonitor(display_mode=DisplayMode.DETAILED),
        )

        # # Run the crawler
        # result = await crawler.arun(url=url, config=config)
        final_results = []

        async with crawler:
            # Get all results at once
            results = await crawler.arun_many(
                urls=urls, config=config, dispatcher=dispatcher
            )

        # Process all results after completion
        for result in results:
            if result.success:
                print(f"\n=== {name} Results ===")
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
                        print(f"Error parsing extracted price content: {str(e)}")
                        final_result["price"] = None
                        continue
                    try:
                        print(f"Description: {r['description']}")
                        final_result["description"] = r["description"][:200]  # Truncate long description
                    except Exception as e:
                        print(f"Error retrieving description metadata: {str(e)}")
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

                    final_results.append(final_result)
                    print(f"Number of final results so far: {len(final_results)}")
                    if len(final_results) > 10:
                        print("More than 10 final results, stopping further processing.")
                        break

            else:
                print(f"Error in {name}: Crawl failed")

    except Exception as e:
        print(f"Error in {name}: {str(e)}")

    return final_results


async def extract_with_generated_schema(urls, root):
    # print("Extracting with generated schema for URL:", url)

    # return

    cache_dir = Path("./schema_cache")
    cache_dir.mkdir(exist_ok=True)
    schema_file = cache_dir / f"product_schema_{root[8:]}.json"

    # 1. Generate or load schema
    if schema_file.exists():
        xpath_schema = json.load(schema_file.open())
        print(f"Using cached schema: {xpath_schema}")
    # else:
    #     print("Generating schema via LLM...")

    #     run_config = CrawlerRunConfig(
    #         only_text=False,  # If True, tries to remove non-text elements
    #     )

    #     # Get sample HTML for context
    #     async with AsyncWebCrawler() as crawler:
    #         result = await crawler.arun(
    #             # "https://rangdongstore.vn/am-dien-sieu-toc-17l-rd-ast17-p1-p-221223003166",
    #             url,
    #             config=run_config,
    #         )
    #         html = result.fit_html
    #     try:
    #         with open("html.html", "w") as f:
    #             f.write(html)
    #         print("Sample HTML written to html.html for reference.")
    #     except Exception as e:
    #         print(f"Error writing HTML to file: {str(e)}")

    #     # # Option 1: Using OpenAI (requires API token)
    #     # css_schema = JsonCssExtractionStrategy.generate_schema(
    #     #     html,
    #     #     schema_type="css",
    #     #     # llm_config=LLMConfig(provider="openai/gpt-4o-mini",
    #     #     #                      api_token="env:OPENAI_API_KEY",
    #     #     #                      ),
    #     #     llm_config=LLMConfig(provider="gemini/gemini-2.5-flash",
    #     #                         api_token="env:GOOGLE_API_KEY",
    #     #                         ),
    #     # )

    #     target_json_example = {
    #         "name": "Product Cards",
    #         "baseSelector": "//div[@class='product-card']",
    #         "fields": [
    #             {
    #                 "name": "price",
    #                 "selector": ".//span[@class='price']",
    #                 "type": "text",
    #             },
    #         ],
    #     }

    #     target_json_example = str(target_json_example)

    #     # Option 2: Using Ollama (open source, no token needed)
    #     xpath_schema = JsonXPathExtractionStrategy.generate_schema(
    #         html,
    #         query="Product price",
    #         schema_type="xpath",
    #         target_json_example=target_json_example,
    #         llm_config=LLMConfig(
    #             provider="gemini/gemini-3-flash-preview",
    #             api_token="env:GOOGLE_API_KEY",
    #         ),
    #     )

    #     # Cache pattern for future use
    #     json.dump(xpath_schema, schema_file.open("w"), indent=2)

    xpath_strategy = JsonXPathExtractionStrategy(xpath_schema)

    with open("xpath_schema.txt", "w") as f:
        for key in xpath_schema:
            f.write(f"{key}: {xpath_schema[key]}\n")

    # print("Generated strategy:", css_schema)
    async with AsyncWebCrawler() as crawler:
        result = await run_extraction(
            crawler,
            # "https://dohu.vn/product",
            urls,
            xpath_strategy,
            "XPath Extraction",
        )

    # print("Final extracted results:", result)

    return result


async def create_xpath_strategy(url, root, overwrite=False):
    print("Generating schema via LLM...")

    cache_dir = Path("./schema_cache")
    cache_dir.mkdir(exist_ok=True)
    schema_file = cache_dir / f"product_schema_{root[8:]}.json"

    if schema_file.exists() and not overwrite:
        xpath_schema = json.load(schema_file.open())
        print(f"Using cached schema: {xpath_schema}")

    else:
        run_config = CrawlerRunConfig(
            only_text=False,  # If True, tries to remove non-text elements
        )

        # Get sample HTML for context
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                # "https://rangdongstore.vn/am-dien-sieu-toc-17l-rd-ast17-p1-p-221223003166",
                url,
                config=run_config,
            )
            html = result.fit_html
        try:
            with open("html.html", "w") as f:
                f.write(html)
            print("Sample HTML written to html.html for reference.")
        except Exception as e:
            print(f"Error writing HTML to file: {str(e)}")

        target_json_example = {
            "name": "Product Cards",
            "baseSelector": "//div[@class='product-card']",
            "fields": [
                {
                    "name": "title",
                    "selector": ".//h2[@class='product-name']",
                    "type": "text",
                },
                {
                    "name": "price",
                    "selector": ".//span[@class='price']",
                    "type": "text",
                },
                {
                    "name": "image_url",
                    "selector": ".//img",
                    "type": "attribute",
                    "attribute": "src",
                },
                {
                    "name": "description",
                    "selector": ".//p",
                    "type": "text",
                },
            ],
        }

        target_json_example = str(target_json_example)

        # Option 2: Using Ollama (open source, no token needed)
        xpath_schema = JsonXPathExtractionStrategy.generate_schema(
            html,
            query="Product information",
            schema_type="xpath",
            # target_json_example=target_json_example,
            llm_config=LLMConfig(
                provider="gemini/gemini-3-flash-preview",
                api_token="env:GOOGLE_API_KEY",
            ),
        )

        # Cache pattern for future use
        json.dump(xpath_schema, schema_file.open("w"), indent=2)

    xpath_strategy = JsonXPathExtractionStrategy(xpath_schema)

    return xpath_strategy


if __name__ == "__main__":
    urls = [
        "file://html.html",
    ]

    async def schema_and_extract(urls, root):
        await create_xpath_strategy(urls[0], root)
        products = await extract_with_generated_schema(urls, root)

        for item in products:
            print("product:", item)

        return

    asyncio.run(schema_and_extract(urls, root="https://rangdongstore.vn"))
