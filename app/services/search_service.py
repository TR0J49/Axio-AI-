"""
Search Service - Web search functionality
"""
import requests
import os
import time
import random
from bs4 import BeautifulSoup

from app.config.settings import GOOGLE_API_KEY, GOOGLE_CSE_ID


def should_search_web(message: str) -> bool:
    """Determine if the message requires a web search"""
    message_lower = message.lower()

    search_keywords = [
        'search', 'google', 'find', 'look up', 'lookup', 'what is', 'who is',
        'when did', 'where is', 'how to', 'latest', 'recent', 'news', 'current',
        'today', 'update', 'trending', '2024', '2025', 'price', 'weather',
        'definition', 'meaning', 'explain what', 'tell me about', 'information about',
        'search for', 'search the web', 'web search', 'online', 'internet'
    ]

    for keyword in search_keywords:
        if keyword in message_lower:
            return True

    question_patterns = ['what is the', 'who is the', 'when is', 'where is the', 'how do i', 'how can i']
    for pattern in question_patterns:
        if message_lower.startswith(pattern):
            return True

    return False


def web_search(query):
    """Perform web search - tries multiple methods"""
    print(f"[SEARCH] Starting web search for: {query}")

    # Method 1: Try Google Custom Search API
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        results = web_search_google_api(query)
        if results:
            print(f"[OK] Google Custom Search API returned {len(results)} results")
            return results

    # Method 2: Try DuckDuckGo
    results = web_search_duckduckgo(query)
    if results:
        print(f"[OK] DuckDuckGo returned {len(results)} results")
        return results

    # Method 3: Try googlesearch-python library
    results = web_search_googlesearch(query)
    if results:
        print(f"[OK] googlesearch-python returned {len(results)} results")
        return results

    # Method 4: Fallback to direct Google scraping
    results = web_search_google_scrape(query)
    if results:
        print(f"[OK] Google scrape returned {len(results)} results")
        return results

    print("[ERROR] All search methods failed")
    return []


def web_search_google_api(query):
    """Search using Google Custom Search JSON API"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': 5
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get('items', []):
            results.append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', '')
            })
        return results
    except Exception as e:
        print(f"[ERROR] Google API search failed: {str(e)}")
        return []


def web_search_duckduckgo(query):
    """Search using DuckDuckGo HTML"""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.post(url, data={'q': query}, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        for result in soup.select('.result')[:5]:
            title_elem = result.select_one('.result__title')
            link_elem = result.select_one('.result__url')
            snippet_elem = result.select_one('.result__snippet')

            if title_elem:
                results.append({
                    'title': title_elem.get_text(strip=True),
                    'link': link_elem.get_text(strip=True) if link_elem else '',
                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                })
        return results
    except Exception as e:
        print(f"[ERROR] DuckDuckGo search failed: {str(e)}")
        return []


def web_search_googlesearch(query):
    """Search using googlesearch-python library"""
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=5, sleep_interval=2):
            results.append({
                'title': url,
                'link': url,
                'snippet': ''
            })
        return results
    except Exception as e:
        print(f"[ERROR] googlesearch-python failed: {str(e)}")
        return []


def image_search(query, search_results=None, num_images=6):
    """Extract relevant images from the web search result pages (OG/meta images)"""
    print(f"[IMAGE SEARCH] Extracting images from search results for: {query}")

    if not search_results:
        return []

    images = []
    seen_urls = set()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for result in search_results:
        if len(images) >= num_images:
            break

        link = result.get('link', '').strip()
        if not link:
            continue
        # Ensure link has protocol
        if not link.startswith('http'):
            link = 'https://' + link

        try:
            page = requests.get(link, headers=headers, timeout=5, allow_redirects=True)
            if page.status_code != 200:
                continue

            page_soup = BeautifulSoup(page.text, 'html.parser')
            img_url = None
            title = result.get('title', '')

            # Priority 1: Open Graph image (most reliable, used by social media)
            og_img = page_soup.find('meta', property='og:image')
            if og_img:
                img_url = og_img.get('content', '')

            # Priority 2: Twitter card image
            if not img_url:
                tw_img = page_soup.find('meta', attrs={'name': 'twitter:image'})
                if tw_img:
                    img_url = tw_img.get('content', '')

            # Priority 3: First large image on the page
            if not img_url:
                for img_tag in page_soup.select('img[src]'):
                    src = img_tag.get('src', '')
                    # Skip tiny icons, tracking pixels, base64
                    if (src.startswith('http') and
                        not any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'pixel', '1x1', 'tracking', 'badge', 'button']) and
                        not src.startswith('data:')):
                        # Check for reasonable size hints
                        width = img_tag.get('width', '')
                        height = img_tag.get('height', '')
                        try:
                            if width and int(width) < 80:
                                continue
                            if height and int(height) < 80:
                                continue
                        except ValueError:
                            pass
                        img_url = src
                        break

            # Handle relative URLs
            if img_url and not img_url.startswith('http'):
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    # Build absolute URL from page domain
                    from urllib.parse import urlparse
                    parsed = urlparse(link)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"

            # Validate and add
            if img_url and img_url.startswith('http') and img_url not in seen_urls:
                seen_urls.add(img_url)
                source_domain = link.split('/')[2] if len(link.split('/')) > 2 else ''
                images.append({
                    'url': img_url,
                    'thumbnail': img_url,
                    'title': title,
                    'source': source_domain,
                    'context_link': link
                })

        except Exception as e:
            print(f"[IMAGE SEARCH] Failed to fetch {link[:50]}: {e}")
            continue

    print(f"[IMAGE SEARCH] Extracted {len(images)} images from search results")
    return images


def web_search_google_scrape(query):
    """Fallback: Direct Google scraping"""
    try:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        ]
        headers = {'User-Agent': random.choice(user_agents)}

        url = f"https://www.google.com/search?q={query}"
        time.sleep(random.uniform(1, 3))

        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        for div in soup.select('div.g')[:5]:
            title = div.select_one('h3')
            link = div.select_one('a')
            snippet = div.select_one('.VwiC3b')

            if title and link:
                results.append({
                    'title': title.get_text(strip=True),
                    'link': link.get('href', ''),
                    'snippet': snippet.get_text(strip=True) if snippet else ''
                })
        return results
    except Exception as e:
        print(f"[ERROR] Google scrape failed: {str(e)}")
        return []
