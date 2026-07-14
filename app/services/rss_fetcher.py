"""
RSS feed fetcher service.
Fetches and parses news articles from RSS feeds for analysis.
"""

from datetime import datetime, timezone

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def fetch_feed(url, max_entries=20):
    """
    Fetch and parse an RSS feed.
    
    Args:
        url: RSS feed URL
        max_entries: Maximum number of entries to return
        
    Returns:
        dict: {
            'feed_title': str,
            'feed_link': str,
            'entries': list of article dicts,
            'error': str or None
        }
    """
    if not HAS_FEEDPARSER:
        return {
            'feed_title': '',
            'feed_link': url,
            'entries': [],
            'error': 'feedparser is not installed. Run: pip install feedparser'
        }

    try:
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            return {
                'feed_title': '',
                'feed_link': url,
                'entries': [],
                'error': f'Failed to parse feed: {getattr(feed, "bozo_exception", "Unknown error")}'
            }

        entries = []
        for entry in feed.entries[:max_entries]:
            # Extract published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                except Exception:
                    pass

            # Extract summary/content
            summary = ''
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'content') and entry.content:
                summary = entry.content[0].get('value', '')

            # Clean HTML from summary
            import re
            summary = re.sub(r'<[^>]+>', '', summary).strip()

            entries.append({
                'title': getattr(entry, 'title', 'Untitled'),
                'link': getattr(entry, 'link', ''),
                'summary': summary,
                'published': published,
                'source': feed.feed.get('title', url) if hasattr(feed, 'feed') else url,
            })

        return {
            'feed_title': feed.feed.get('title', '') if hasattr(feed, 'feed') else '',
            'feed_link': feed.feed.get('link', url) if hasattr(feed, 'feed') else url,
            'entries': entries,
            'error': None
        }

    except Exception as e:
        return {
            'feed_title': '',
            'feed_link': url,
            'entries': [],
            'error': str(e)
        }


def fetch_article_content(url):
    """
    Fetch the full text content of an article from its URL.
    Uses basic HTML parsing to extract main text content.
    
    Args:
        url: Article URL
        
    Returns:
        dict: {'title': str, 'text': str, 'error': str or None}
    """
    if not HAS_REQUESTS:
        return {'title': '', 'text': '', 'error': 'requests is not installed'}

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FakeNewsDetector/1.0)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        html = response.text

        # Try BeautifulSoup if available
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Remove scripts and styles
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()

            # Get title
            title = ''
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Try to find article body
            article = soup.find('article')
            if article:
                text = article.get_text(separator=' ', strip=True)
            else:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                text = ' '.join(p.get_text(strip=True) for p in paragraphs)

            return {'title': title, 'text': text, 'error': None}

        except ImportError:
            # Fallback: basic regex extraction
            import re
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ''

            # Remove HTML tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            return {'title': title, 'text': text, 'error': None}

    except requests.RequestException as e:
        return {'title': '', 'text': '', 'error': str(e)}
    except Exception as e:
        return {'title': '', 'text': '', 'error': str(e)}


def validate_feed_url(url):
    """
    Validate that a URL is a reachable RSS feed.
    
    Returns:
        dict: {'valid': bool, 'title': str, 'error': str or None}
    """
    if not url or not isinstance(url, str):
        return {'valid': False, 'title': '', 'error': 'Invalid URL'}

    if not url.startswith(('http://', 'https://')):
        return {'valid': False, 'title': '', 'error': 'URL must start with http:// or https://'}

    result = fetch_feed(url, max_entries=1)

    if result['error']:
        return {'valid': False, 'title': '', 'error': result['error']}

    return {
        'valid': True,
        'title': result['feed_title'],
        'error': None
    }
