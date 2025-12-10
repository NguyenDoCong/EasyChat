"""
Universal Product Scraper
Hỗ trợ trích xuất thông tin sản phẩm từ nhiều loại website khác nhau
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import time
import random


def get_useragent():
    """
    Generates a random user agent string mimicking the format of various software versions.

    The user agent string is composed of:
    - Lynx version: Lynx/x.y.z where x is 2-3, y is 8-9, and z is 0-2
    - libwww version: libwww-FM/x.y where x is 2-3 and y is 13-15
    - SSL-MM version: SSL-MM/x.y where x is 1-2 and y is 3-5
    - OpenSSL version: OpenSSL/x.y.z where x is 1-3, y is 0-4, and z is 0-9

    Returns:
        str: A randomly generated user agent string.
    """
    lynx_version = (
        f"Lynx/{random.randint(2, 3)}.{random.randint(8, 9)}.{random.randint(0, 2)}"
    )
    libwww_version = f"libwww-FM/{random.randint(2, 3)}.{random.randint(13, 15)}"
    ssl_mm_version = f"SSL-MM/{random.randint(1, 2)}.{random.randint(3, 5)}"
    openssl_version = (
        f"OpenSSL/{random.randint(1, 3)}.{random.randint(0, 4)}.{random.randint(0, 9)}"
    )
    return f"{lynx_version} {libwww_version} {ssl_mm_version} {openssl_version}"


class UniversalProductScraper:
    """
    Scraper tổng hợp có thể xử lý nhiều loại website
    """

    def __init__(self, use_llm: bool = False, llm_api_key: Optional[str] = None):
        self.use_llm = use_llm
        self.llm_api_key = llm_api_key

        # Headers để tránh bị block
        self.headers = {
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            "User-Agent": get_useragent(),
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            # 'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            "Accept": "*/*",

        }

        # Các pattern chung cho mọi website
        self.universal_patterns = {
            "price": [
                r"(?:VND|₫|đ)\s*([\d.,]+)",
                r"([\d.,]+)\s*(?:VND|₫|đ)",
                r"(?:Price|Giá)[:\s]*([\d.,]+)",
            ],
            "name": [
                r"<h1[^>]*>(.*?)</h1>",
                r"<title>(.*?)</title>",
            ],
        }

        # Config cho từng website cụ thể
        self.site_configs = self._load_site_configs()

    def _load_site_configs(self) -> Dict:
        """
        Config cho các website phổ biến
        """
        return {
            "shopee.vn": {
                "selectors": {
                    "name": [".product-title", "h1", '[class*="product-name"]'],
                    "price": ['[class*="price"]', ".product-price"],
                    "description": [".product-description", '[class*="description"]'],
                    "images": ['img[class*="product"]', ".product-image img"],
                },
                "json_ld": True,  # Hỗ trợ JSON-LD schema
            },
            "lazada.vn": {
                "selectors": {
                    "name": [".pdp-product-title", "h1"],
                    "price": [".pdp-price", '[class*="price"]'],
                    "description": [".detail-content"],
                },
                "json_ld": True,
            },
            "tiki.vn": {
                "selectors": {
                    "name": ['h1[class*="title"]', ".product-name"],
                    "price": ['[class*="product-price"]'],
                    "rating": ['[class*="rating"]'],
                },
                "json_ld": True,
            },
            "sendo.vn": {
                "selectors": {
                    "name": [".product_name", "h1"],
                    "price": [".product_price"],
                },
            },
            # Thêm config cho các site khác
            "default": {
                "selectors": {
                    "name": [
                        "h1",
                        '[itemprop="name"]',
                        ".product-title",
                        ".product-name",
                    ],
                    "price": [
                        '[itemprop="price"]',
                        ".price",
                        ".product-price",
                        '[class*="price"]',
                    ],
                    "description": [
                        '[itemprop="description"]',
                        ".description",
                        ".product-description",
                    ],
                    "images": [
                        '[itemprop="image"]',
                        ".product-image img",
                        'img[alt*="product"]',
                    ],
                    "sku": ['[itemprop="sku"]', ".sku", ".product-code"],
                    "brand": ['[itemprop="brand"]', ".brand"],
                },
                "json_ld": True,
            },
        }

    def _clean_redundant_text(self, text):
        # 1. Tách văn bản thành các câu dựa trên dấu chấm
        parts = [p.strip() for p in text.split(".") if p.strip()]

        unique_segments = []
        seen = set()

        for segment in parts:
            # 2. Chuẩn hóa: loại bỏ khoảng trắng dư thừa
            segment = re.sub(r"\s+", " ", segment).strip()

            # 3. Loại bỏ các mẫu "Rác" có dạng "Thông tin: ." (không có giá trị thực)
            # Regex này tìm các chuỗi kết thúc bằng dấu hai chấm và khoảng trắng/dấu chấm rỗng
            if re.search(r":\s*\.?$", segment):
                continue

            # 4. Kiểm tra trùng lặp
            if segment not in seen:
                unique_segments.append(segment)
                seen.add(segment)

        # 5. Nối lại thành đoạn văn bản hoàn chỉnh
        return ". ".join(unique_segments) + "."

    def scrape(self, url: str, method: str = "auto") -> Dict[str, Any]:
        """
        Scrape thông tin sản phẩm từ URL

        Args:
            url: URL của sản phẩm
            method: 'auto', 'html', 'json_ld', 'llm', 'hybrid'
        """
        print(f"🔍 Đang scrape: {url}")

        # Fetch HTML
        html_content = self._fetch_url(url)
        if not html_content:
            return {"error": "Failed to fetch URL"}

        # Parse HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # Xác định phương pháp scrape
        if method == "auto":
            method = self._detect_best_method(soup, url)

        print(f"📊 Sử dụng phương pháp: {method}")

        # Scrape theo phương pháp
        if method == "json_ld":
            result = self._extract_from_json_ld(soup)
        elif method == "llm" and self.use_llm:
            result = self._extract_with_llm(html_content)
        elif method == "hybrid":
            result = self._extract_hybrid(soup, html_content)
        else:  # html
            result = self._extract_from_html(soup, url)

        # Post-processing
        result = self._clean_result(result)

        final_result = {}
        try:

            specs = self._clean_redundant_text(result["description"])

            final_result = {
                "name": result["name"],
                "price": str(result["price"]) + " " + result["currency"],
                "specs": specs,
                "link": url,
                "image": result["images"][0],
            }
            # return final_result
        except Exception as e:
            print("lỗi xuất thông tin", e)
            final_result = {}

        # result['url'] = url
        # result['scrape_method'] = method

        return final_result

    def _fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch HTML từ URL với retry
        """
        max_retries = 3
        for i in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                # Fix encoding UTF-8
                response.encoding = "utf-8"
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 403:
                    print(f"⚠️  Bị chặn, thử lại lần {i + 1}...")
                    time.sleep(2)
                else:
                    print(f"❌ Status code: {response.status_code}")
                    return None
            except Exception as e:
                print(f"❌ Error: {e}")
                if i < max_retries - 1:
                    time.sleep(2)
        return None

    def _detect_best_method(self, soup: BeautifulSoup, url: str) -> str:
        """
        Tự động phát hiện phương pháp scrape tốt nhất
        """
        # Check JSON-LD
        json_ld = soup.find("script", type="application/ld+json")
        if json_ld:
            return "json_ld"

        # Check meta tags (Open Graph, Twitter Card)
        og_tags = soup.find_all("meta", property=re.compile(r"^og:"))
        if len(og_tags) >= 3:
            return "html"  # Có đủ meta tags

        # Nếu có LLM và page phức tạp
        if self.use_llm:
            return "hybrid"

        return "html"

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Dict:
        """
        Trích xuất từ JSON-LD Schema (chuẩn Schema.org)
        Đây là cách tốt nhất nếu website hỗ trợ
        """
        result = {}

        json_ld_scripts = soup.find_all("script", type="application/ld+json")

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)

                # Handle array
                if isinstance(data, list):
                    data = data[0]

                # Extract Product schema
                if data.get("@type") == "Product":
                    result["name"] = data.get("name")
                    result["description"] = data.get("description")
                    result["sku"] = data.get("sku")
                    result["brand"] = data.get("brand", {}).get("name")

                    # Price
                    if "offers" in data:
                        offers = data["offers"]
                        if isinstance(offers, list):
                            offers = offers[0]
                        result["price"] = offers.get("price")
                        result["currency"] = offers.get("priceCurrency")
                        result["availability"] = offers.get("availability")

                    # Images
                    if "image" in data:
                        images = data["image"]
                        if isinstance(images, str):
                            result["images"] = [images]
                        elif isinstance(images, list):
                            result["images"] = images

                    # Rating
                    if "aggregateRating" in data:
                        rating = data["aggregateRating"]
                        result["rating"] = rating.get("ratingValue")
                        result["review_count"] = rating.get("reviewCount")

            except json.JSONDecodeError:
                continue

        return result

    def _extract_from_html(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Trích xuất từ HTML structure và meta tags
        """
        result = {}

        # Xác định config dựa trên domain
        domain = urlparse(url).netloc
        config = self.site_configs.get(domain, self.site_configs["default"])

        # Extract theo selectors
        for field, selectors in config["selectors"].items():
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    if field == "images":
                        result[field] = [
                            img.get("src") or img.get("data-src")
                            for img in elements
                            if img.get("src") or img.get("data-src")
                        ]
                    else:
                        result[field] = elements[0].get_text(strip=True)
                    break

        # Extract từ meta tags (Open Graph, Twitter Card)
        result.update(self._extract_from_meta_tags(soup))

        # Extract từ microdata
        result.update(self._extract_from_microdata(soup))

        # Extract bằng regex patterns
        html_text = soup.get_text()
        for field, patterns in self.universal_patterns.items():
            if field not in result or not result[field]:
                for pattern in patterns:
                    match = re.search(pattern, html_text, re.IGNORECASE)
                    if match:
                        result[field] = match.group(1).strip()
                        break

        return result

    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """
        Trích xuất từ Open Graph và Twitter Card meta tags
        """
        result = {}

        # Open Graph tags
        og_mapping = {
            "og:title": "name",
            "og:description": "description",
            "og:image": "image",
            "og:price:amount": "price",
            "og:price:currency": "currency",
        }

        for og_prop, field in og_mapping.items():
            tag = soup.find("meta", property=og_prop)
            if tag and tag.get("content"):
                if field == "image":
                    result.setdefault("images", []).append(tag["content"])
                else:
                    result[field] = tag["content"]

        # Twitter Card
        twitter_mapping = {
            "twitter:title": "name",
            "twitter:description": "description",
            "twitter:image": "image",
        }

        for tw_name, field in twitter_mapping.items():
            if field not in result:
                tag = soup.find("meta", attrs={"name": tw_name})
                if tag and tag.get("content"):
                    result[field] = tag["content"]

        return result

    def _extract_from_microdata(self, soup: BeautifulSoup) -> Dict:
        """
        Trích xuất từ microdata (itemprop)
        """
        result = {}

        mapping = {
            "name": "name",
            "description": "description",
            "price": "price",
            "priceCurrency": "currency",
            "image": "image",
            "sku": "sku",
            "brand": "brand",
        }

        for itemprop, field in mapping.items():
            element = soup.find(attrs={"itemprop": itemprop})
            if element:
                if element.name == "meta":
                    value = element.get("content")
                elif element.name == "img":
                    value = element.get("src")
                else:
                    value = element.get_text(strip=True)

                if value:
                    if field == "image":
                        result.setdefault("images", []).append(value)
                    else:
                        result[field] = value

        return result

    def _extract_with_llm(self, html_content: str) -> Dict:
        """
        Sử dụng LLM (Claude/GPT) để trích xuất
        Phương pháp này đắt nhưng chính xác cao
        """
        if not self.llm_api_key:
            return {"error": "LLM API key not provided"}

        # Clean HTML
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text()
        # Limit text length to save cost
        text = text[:8000]  # ~2000 tokens

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.llm_api_key)

            prompt = f"""
Trích xuất thông tin sản phẩm từ văn bản sau và trả về JSON với các trường:
- name: Tên sản phẩm
- price: Giá (số và đơn vị)
- description: Mô tả ngắn
- brand: Thương hiệu
- sku: Mã sản phẩm
- specifications: Thông số kỹ thuật (dict)
- images: URL ảnh (array)
- availability: Tình trạng còn hàng

Văn bản:
{text}

Chỉ trả về JSON, không giải thích.
"""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            # Clean markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            return json.loads(response_text.strip())

        except Exception as e:
            print(f"❌ LLM extraction failed: {e}")
            return {"error": str(e)}

    def _extract_hybrid(self, soup: BeautifulSoup, html_content: str) -> Dict:
        """
        Kết hợp nhiều phương pháp để đạt độ chính xác cao nhất
        """
        result = {}

        # 1. JSON-LD (ưu tiên cao nhất)
        json_ld_data = self._extract_from_json_ld(soup)
        result.update(json_ld_data)

        # 2. HTML structure
        html_data = self._extract_from_html(soup, "")
        for key, value in html_data.items():
            if key not in result or not result[key]:
                result[key] = value

        # 3. LLM cho các trường còn thiếu
        if self.use_llm and len(result) < 5:
            llm_data = self._extract_with_llm(html_content)
            for key, value in llm_data.items():
                if key not in result or not result[key]:
                    result[key] = value

        return result

    def _clean_result(self, result: Dict) -> Dict:
        """
        Làm sạch và chuẩn hóa dữ liệu
        """
        cleaned = {}

        for key, value in result.items():
            if value is None or value == "":
                continue

            # Fix encoding issues
            if isinstance(value, str):
                # Try to fix common encoding problems
                try:
                    # Decode if needed
                    if "\\u" in value or "ƒ" in value or "√" in value:
                        # Try to fix mojibake
                        value = value.encode("latin1").decode("utf-8", errors="ignore")
                except:
                    pass

                # Remove extra whitespace
                value = " ".join(value.split())
                value = value.strip()

                # Remove HTML tags
                value = re.sub(r"<[^>]+>", "", value)

            # Clean price
            if key == "price" and isinstance(value, str):
                # Extract numbers
                price_match = re.search(r"([\d.,]+)", value.replace(",", ""))
                if price_match:
                    cleaned[key] = price_match.group(1)
                    # Extract currency
                    if "₫" in value or "VND" in value or "đ" in value:
                        cleaned["currency"] = "VND"
                else:
                    cleaned[key] = value
            else:
                cleaned[key] = value

        return cleaned

    def scrape_multiple(self, urls: List[str]) -> List[Dict]:
        """
        Scrape nhiều URL
        """
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n{'=' * 60}")
            print(f"📦 Sản phẩm {i}/{len(urls)}")
            result = self.scrape(url)
            results.append(result)
            time.sleep(1)  # Tránh bị ban
        return results

    def save_results(self, results: List[Dict], filename: str = "products.json"):
        """
        Lưu kết quả vào file
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Đã lưu {len(results)} sản phẩm vào {filename}")


# ===== USAGE EXAMPLES =====
if __name__ == "__main__":
    # Khởi tạo scraper
    scraper = UniversalProductScraper(
        use_llm=False,  # Set True nếu muốn dùng LLM
        llm_api_key="your-api-key-here",  # Thêm API key nếu dùng LLM
    )

    # Example 1: Scrape một sản phẩm
    url = "https://rangdongstore.vn/den-pha-led-100w-cp07-p-221223003008"
    result = scraper.scrape(url, method="auto")
    print("\n📊 KẾT QUẢ:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Example 2: Scrape nhiều sản phẩm
    urls = [
        "https://shopee.vn/product1",
        "https://tiki.vn/product2",
        "https://lazada.vn/product3",
    ]
    # results = scraper.scrape_multiple(urls)
    # scraper.save_results(results, 'products.json')

    # Example 3: Scrape với phương pháp cụ thể
    # result = scraper.scrape(url, method='json_ld')  # Chỉ dùng JSON-LD
    # result = scraper.scrape(url, method='llm')      # Chỉ dùng LLM
    # result = scraper.scrape(url, method='hybrid')   # Kết hợp tất cả
