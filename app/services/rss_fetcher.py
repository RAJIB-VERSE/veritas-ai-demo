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

    # Validate URL format
    if not url or not isinstance(url, str):
        return {'title': '', 'text': '', 'error': 'Invalid URL provided.'}

    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        return {
            'title': '', 'text': '',
            'error': 'Invalid URL. Please provide a URL starting with http:// or https://'
        }

    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

        # Handle common HTTP errors with clear messages
        if response.status_code == 403:
            return {
                'title': '', 'text': '',
                'error': 'Access denied (403 Forbidden). This site blocks automated requests. Please paste the article text directly.'
            }
        if response.status_code == 404:
            return {
                'title': '', 'text': '',
                'error': 'Page not found (404). Please check the URL and try again.'
            }
        if response.status_code >= 500:
            return {
                'title': '', 'text': '',
                'error': f'The server returned an error ({response.status_code}). Please try again later.'
            }

        response.raise_for_status()
        html = response.text

        title = ''
        text = ''

        # Try BeautifulSoup if available
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Remove scripts and styles
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()

            # Get title
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

        except ImportError:
            # Fallback: basic regex extraction
            import re
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ''

            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

        # Check for JavaScript-only pages (minimal real text extracted)
        if not text or len(text.strip()) < 50:
            return {
                'title': title, 'text': '',
                'error': (
                    'Could not extract text from this URL. '
                    'The page may require JavaScript or has too little readable content. '
                    'Please paste the article text directly.'
                )
            }

        return {'title': title, 'text': text, 'error': None}

    except requests.exceptions.Timeout:
        return {
            'title': '', 'text': '',
            'error': 'Request timed out after 10 seconds. The site may be slow or unreachable. Please paste the article text directly.'
        }
    except requests.exceptions.ConnectionError:
        return {
            'title': '', 'text': '',
            'error': 'Could not connect to the URL. Please check the address and try again.'
        }
    except requests.exceptions.TooManyRedirects:
        return {
            'title': '', 'text': '',
            'error': 'Too many redirects. The URL may be invalid.'
        }
    except requests.RequestException as e:
        return {'title': '', 'text': '', 'error': f'Failed to fetch URL: {e}'}
    except Exception as e:
        return {'title': '', 'text': '', 'error': f'Unexpected error: {e}'}


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
