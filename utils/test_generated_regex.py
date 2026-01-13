import json
import asyncio
from pathlib import Path
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    RegexExtractionStrategy,
    LLMConfig,
)
from dotenv import load_dotenv

load_dotenv()


async def extract_with_generated_pattern():
    cache_dir = Path("./pattern_cache")
    cache_dir.mkdir(exist_ok=True)
    pattern_file = cache_dir / "price_pattern.json"

    # 1. Generate or load pattern
    if pattern_file.exists():
        pattern = json.load(pattern_file.open())
        print(f"Using cached pattern: {pattern}")
    else:
        print("Generating pattern via LLM...")

        # Configure LLM
        llm_config = LLMConfig(
            provider="gemini/gemini-3-flash-preview",
            api_token="env:GOOGLE_API_KEY",
        )

        # Get sample HTML for context
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                "https://www.dienmayxanh.com/may-loc-khong-khi/xiaomi-smart-air-purifier-4-compact-eu-bhr5860eu-27w?itm_source=home&itm_medium=product_card&itm_campaign=viewed"
            )
            html = result.fit_html

            with open("regex.html", "w") as f:
                f.write(str(html))

        examples = ["248.300 ₫","214.000 VNĐ", "117.000₫"]
        # Generate pattern (one-time LLM usage)
        pattern = RegexExtractionStrategy.generate_pattern(
            label="price",
            html=html,
            # query="Giá",
            llm_config=llm_config,
            examples=examples,
        )

        # Cache pattern for future use
        json.dump(pattern, pattern_file.open("w"), indent=2)

    # 2. Use pattern for extraction (no LLM calls)
    strategy = RegexExtractionStrategy(custom=pattern)
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://rangdong.com.vn/vot-bat-muoi-vbm-rd-03-pr2398.html",
            config=config,
        )

        if result.success:
            data = json.loads(result.extracted_content)
            for item in data[:100]:
                print(f"Extracted: {item['value']}")
            print(f"Total matches: {len(data)}")
            print(f"URL: {result.url}")
            print(f"Title: {result.metadata["title"]}")
            import ast
            res = ast.literal_eval(result.extracted_content)
            print(f"Description: {result.metadata["description"]}")
            print(f"Image: {result.metadata["og:image"]}")
            with open("result.txt", "w") as f:
                f.write(str(result))            


asyncio.run(extract_with_generated_pattern())
