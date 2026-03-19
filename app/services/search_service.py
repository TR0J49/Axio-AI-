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


def image_search(query, num_images=6):
    """Search for images related to the query"""
    print(f"[IMAGE SEARCH] Searching images for: {query}")

    # Method 1: Google Custom Search API with image search
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        images = image_search_google_api(query, num_images)
        if images:
            print(f"[OK] Google image search returned {len(images)} images")
            return images

    # Method 2: DuckDuckGo image proxy (no API key needed)
    images = image_search_duckduckgo(query, num_images)
    if images:
        print(f"[OK] DuckDuckGo image search returned {len(images)} images")
        return images

    print("[IMAGE SEARCH] No images found")
    return []


def image_search_google_api(query, num_images=6):
    """Search images using Google Custom Search API"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'searchType': 'image',
            'num': min(num_images, 10),
            'safe': 'active'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        images = []
        for item in data.get('items', []):
            images.append({
                'url': item.get('link', ''),
                'thumbnail': item.get('image', {}).get('thumbnailLink', item.get('link', '')),
                'title': item.get('title', ''),
                'source': item.get('displayLink', ''),
                'context_link': item.get('image', {}).get('contextLink', '')
            })
        return images
    except Exception as e:
        print(f"[ERROR] Google image search failed: {str(e)}")
        return []


def image_search_duckduckgo(query, num_images=6):
    """Search images using DuckDuckGo"""
    try:
        # Get vqd token first
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        token_response = requests.get(
            f"https://duckduckgo.com/?q={query}&iax=images&ia=images",
            headers=headers, timeout=10
        )

        import re
        vqd_match = re.search(r'vqd=["\']([^"\']+)["\']', token_response.text)
        if not vqd_match:
            # Fallback: try to get token from another endpoint
            vqd_match = re.search(r'vqd=(\d+-\d+(?:-\d+)*)', token_response.text)

        if not vqd_match:
            print("[IMAGE SEARCH] Could not get DuckDuckGo token")
            return []

        vqd = vqd_match.group(1)

        # Fetch images
        img_url = "https://duckduckgo.com/i.js"
        params = {
            'l': 'us-en',
            'o': 'json',
            'q': query,
            'vqd': vqd,
            'f': ',,,,,',
            'p': '1'
        }

        img_response = requests.get(img_url, params=params, headers=headers, timeout=10)
        img_data = img_response.json()

        images = []
        for result in img_data.get('results', [])[:num_images]:
            images.append({
                'url': result.get('image', ''),
                'thumbnail': result.get('thumbnail', result.get('image', '')),
                'title': result.get('title', ''),
                'source': result.get('source', ''),
                'context_link': result.get('url', '')
            })
        return images
    except Exception as e:
        print(f"[ERROR] DuckDuckGo image search failed: {str(e)}")
        return []


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
