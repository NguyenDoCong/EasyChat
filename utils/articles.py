"""
Article Scraper - Scrape blog posts, news articles, guides
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from datetime import datetime


class ArticleScraper:
    """
    Scraper for articles, blog posts, news
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        }
    
    def scrape(self, url: str) -> Dict:
        """
        Scrape article from URL
        """
        try:
            print(f"📰 Scraping article: {url}")
            
            # Fetch HTML
            html = self._fetch(url)
            if not html:
                return {"error": "Cannot fetch URL", "url": url}
            
            # Parse
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data
            article = {}
            
            # 1. Try Article schema (JSON-LD)
            json_ld = self._extract_json_ld(soup)
            if json_ld:
                article.update(json_ld)
            
            # 2. Extract from meta tags
            meta_data = self._extract_meta_tags(soup)
            if meta_data:
                for key, value in meta_data.items():
                    if key not in article or not article[key]:
                        article[key] = value
            
            # 3. Extract from HTML
            html_data = self._extract_html(soup)
            if html_data:
                for key, value in html_data.items():
                    if key not in article or not article[key]:
                        article[key] = value
            
            # Clean up
            article = self._clean(article)
            article['url'] = url
            
            print(f"✅ Success: {article.get('title', 'Unknown')[:50]}")
            return article
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"error": str(e), "url": url}
    
    def _fetch(self, url: str) -> Optional[str]:
        """
        Fetch HTML from URL
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"Fetch error: {e}")
            return None
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict:
        """
        Extract from Article JSON-LD schema
        """
        result = {}
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                
                # Check for Article, NewsArticle, BlogPosting
                if data.get('@type') in ['Article', 'NewsArticle', 'BlogPosting']:
                    result['title'] = data.get('headline') or data.get('name')
                    result['description'] = data.get('description')
                    result['content'] = data.get('articleBody')
                    result['author'] = self._extract_author(data.get('author'))
                    result['date_published'] = data.get('datePublished')
                    result['date_modified'] = data.get('dateModified')
                    
                    # Image
                    if 'image' in data:
                        img = data['image']
                        if isinstance(img, dict):
                            result['image'] = img.get('url')
                        elif isinstance(img, list):
                            result['image'] = img[0] if img else None
                        else:
                            result['image'] = img
                    
                    # Category/Tags
                    if 'keywords' in data:
                        keywords = data['keywords']
                        if isinstance(keywords, str):
                            result['tags'] = [k.strip() for k in keywords.split(',')]
                        elif isinstance(keywords, list):
                            result['tags'] = keywords
                    
                    break
            except:
                continue
        
        return result
    
    def _extract_author(self, author_data) -> Optional[str]:
        """Extract author name from various formats"""
        if not author_data:
            return None
        
        if isinstance(author_data, str):
            return author_data
        elif isinstance(author_data, dict):
            return author_data.get('name')
        elif isinstance(author_data, list) and author_data:
            first = author_data[0]
            if isinstance(first, dict):
                return first.get('name')
            return str(first)
        
        return None
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """
        Extract from Open Graph and meta tags
        """
        result = {}
        
        # Open Graph
        og_props = {
            'og:title': 'title',
            'og:description': 'description',
            'og:image': 'image',
            'og:type': 'type',
            'article:published_time': 'date_published',
            'article:modified_time': 'date_modified',
            'article:author': 'author',
            'article:tag': 'tags',
        }
        
        for prop, field in og_props.items():
            tag = soup.find('meta', property=prop)
            if tag and tag.get('content'):
                if field == 'tags':
                    result.setdefault('tags', []).append(tag['content'])
                else:
                    result[field] = tag['content']
        
        # Twitter Card
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and 'title' not in result:
            result['title'] = twitter_title.get('content')
        
        # Standard meta
        description = soup.find('meta', attrs={'name': 'description'})
        if description and 'description' not in result:
            result['description'] = description.get('content')
        
        return result
    
    def _extract_html(self, soup: BeautifulSoup) -> Dict:
        """
        Extract from HTML structure
        """
        result = {}
        
        # Title
        if not result.get('title'):
            # Try h1
            h1 = soup.find('h1')
            if h1:
                result['title'] = h1.get_text(strip=True)
            # Try title tag
            elif soup.title:
                result['title'] = soup.title.get_text(strip=True)
        
        # Author
        for selector in [
            '[rel="author"]',
            '[class*="author"]',
            '[itemprop="author"]',
            '.post-author',
            '.article-author'
        ]:
            author = soup.select_one(selector)
            if author:
                result['author'] = author.get_text(strip=True)
                break
        
        # Date
        for selector in [
            'time',
            '[class*="date"]',
            '[class*="time"]',
            '[itemprop="datePublished"]',
            '.post-date',
            '.article-date'
        ]:
            date = soup.select_one(selector)
            if date:
                date_text = date.get('datetime') or date.get_text(strip=True)
                result['date_published'] = date_text
                break
        
        # Content - try multiple selectors
        content_selectors = [
            'article',
            '[class*="content"]',
            '[class*="article"]',
            '[class*="post-content"]',
            '.entry-content',
            'main',
            '#content',
        ]
        
        content_element = None
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                content_element = elem
                break
        
        if content_element:
            # Remove unwanted elements
            for tag in content_element.find_all(['script', 'style', 'nav', 'aside', 'footer']):
                tag.decompose()
            
            # Extract paragraphs
            paragraphs = content_element.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol'])
            
            # Get full content
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:  # Skip very short paragraphs
                    content_parts.append(text)
            
            if content_parts:
                result['content'] = '\n\n'.join(content_parts)
                
                # Calculate reading time (words per minute)
                word_count = len(' '.join(content_parts).split())
                result['word_count'] = word_count
                result['reading_time'] = max(1, round(word_count / 200))  # 200 WPM
        
        # Image
        if not result.get('image'):
            # Try featured image
            for selector in [
                '[class*="featured"]',
                '[class*="thumbnail"]',
                'article img',
                '.post-image img'
            ]:
                img = soup.select_one(selector)
                if img:
                    result['image'] = img.get('src') or img.get('data-src')
                    break
        
        # Category/Tags
        if not result.get('tags'):
            tags = []
            for selector in [
                '[rel="tag"]',
                '[class*="tag"]',
                '[class*="category"]',
                '.post-tags a',
                '.article-tags a'
            ]:
                tag_elements = soup.select(selector)
                for tag in tag_elements:
                    tag_text = tag.get_text(strip=True)
                    if tag_text and len(tag_text) < 50:
                        tags.append(tag_text)
            
            if tags:
                result['tags'] = tags[:10]  # Max 10 tags
        
        return result
    
    def _clean(self, data: Dict) -> Dict:
        """
        Clean and normalize data
        """
        cleaned = {}
        
        for key, value in data.items():
            if not value:
                continue
            
            if isinstance(value, str):
                # Remove extra whitespace
                value = ' '.join(value.split())
                
                # Remove HTML
                value = re.sub(r'<[^>]+>', '', value)
            
            # Clean content
            if key == 'content':
                value = self._clean_content(value)
            
            # Clean title
            if key == 'title':
                value = self._clean_title(value)
            
            # Format dates
            if key in ['date_published', 'date_modified']:
                value = self._parse_date(value)
            
            cleaned[key] = value
        
        return cleaned
    
    def _clean_content(self, text: str) -> str:
        """
        Clean article content
        """
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove very short lines (likely UI elements)
        lines = text.split('\n')
        clean_lines = [line for line in lines if len(line.strip()) > 15 or line.strip() == '']
        
        return '\n'.join(clean_lines).strip()
    
    def _clean_title(self, title: str) -> str:
        """
        Clean article title
        """
        # Remove site name (usually after | or -)
        title = re.split(r'\s+[-|]\s+', title)[0]
        
        return title.strip()
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse and normalize date
        """
        if not date_str:
            return None
        
        # Already ISO format
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str[:10]  # Return just YYYY-MM-DD
        
        # Try common Vietnamese date formats
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
                else:  # DD-MM-YYYY
                    return f"{groups[2]}-{groups[1].zfill(2)}-{groups[0].zfill(2)}"
        
        return date_str  # Return as-is if can't parse
    
    def scrape_multiple(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple articles
        """
        import time
        
        articles = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]")
            article = self.scrape(url)
            articles.append(article)
            
            if i < len(urls):
                time.sleep(1)
        
        return articles
    
    def save_json(self, data, filename: str = 'articles.json'):
        """
        Save to JSON file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to {filename}")
    
    def save_markdown(self, article: Dict, filename: str = None):
        """
        Save article as Markdown
        """
        if not filename:
            # Generate filename from title
            title = article.get('title', 'article')
            filename = re.sub(r'[^\w\s-]', '', title)
            filename = re.sub(r'[-\s]+', '-', filename)
            filename = filename[:50] + '.md'
        
        md = f"# {article.get('title', 'Untitled')}\n\n"
        
        if article.get('author'):
            md += f"**Tác giả:** {article['author']}\n\n"
        
        if article.get('date_published'):
            md += f"**Ngày đăng:** {article['date_published']}\n\n"
        
        if article.get('reading_time'):
            md += f"**Thời gian đọc:** ~{article['reading_time']} phút\n\n"
        
        if article.get('tags'):
            md += f"**Tags:** {', '.join(article['tags'])}\n\n"
        
        md += "---\n\n"
        
        if article.get('description'):
            md += f"*{article['description']}*\n\n"
        
        if article.get('content'):
            md += article['content']
        
        md += f"\n\n---\n\n**Nguồn:** [{article.get('url')}]({article.get('url')})"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"✅ Saved to {filename}")


# ===== USAGE EXAMPLE =====
if __name__ == "__main__":
    
    # Create scraper
    scraper = ArticleScraper()
    
    # Example 1: Scrape single article
    url = "https://rangdongstore.vn/cam-nang-chuyen-dung/chieu-sang-cong-nghiep/nhung-uu-diem-khi-chieu-sang-duong-pho-bang-led-chieu-duong-100w"
    
    article = scraper.scrape(url)
    
    # Print result
    print("\n" + "="*80)
    print("📰 ARTICLE:")
    print("="*80)
    print(f"Title: {article.get('title')}")
    print(f"Author: {article.get('author', 'N/A')}")
    print(f"Date: {article.get('date_published', 'N/A')}")
    print(f"Reading time: ~{article.get('reading_time', 'N/A')} minutes")
    print(f"Word count: {article.get('word_count', 'N/A')}")
    
    if article.get('tags'):
        print(f"Tags: {', '.join(article['tags'])}")
    
    if article.get('content'):
        print(f"\nContent preview:")
        print(article['content'][:300] + "...")
    
    print("="*80)
    
    # Save to JSON
    scraper.save_json(article, 'article.json')
    
    # Save to Markdown
    scraper.save_markdown(article, 'article.md')
    
    # Example 2: Scrape multiple articles
    # urls = [
    #     "https://example.com/article1",
    #     "https://example.com/article2",
    # ]
    # articles = scraper.scrape_multiple(urls)
    # scraper.save_json(articles, 'articles.json')