import re
from ddgs import DDGS

# Fact checking domains or trusted sources
TRUSTED_DOMAINS = [
    'snopes.com', 'politifact.com', 'factcheck.org', 'reuters.com',
    'apnews.com', 'bbc.com', 'altnews.in', 'boomlive.in', 'pib.gov.in',
    'newschecker.in', 'vishvasnews.com', 'factly.in', 'afp.com',
    'leadstories.com', 'logically.ai', 'fullfact.org', 'msn.com'
]

# Keywords that indicate a claim is false
DEBUNK_KEYWORDS = [
    'false', 'debunked', 'misleading', 'fake', 'hoax', 'altered', 
    'deepfake', 'digitally altered', 'untrue', 'did not say', 
    'never said', 'falsely claiming'
]

def search_and_verify(text):
    """
    Search the web for the claim and return a fact-check analysis.
    Uses duckduckgo-search (ddgs).
    """
    # Extract a short query from the text (first sentence or up to 100 chars)
    clean_text = re.sub(r'breaking:?|viral social media|whatsapp forward', '', text, flags=re.IGNORECASE).strip()
    query = clean_text[:120].strip()
    
    if not query:
        return {'status': 'error', 'message': 'Query too short'}
        
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} fact check", max_results=5))
            
        if not results:
            return {'status': 'unverified', 'message': 'No relevant fact-check results found.'}
            
        debunk_score = 0
        total_results = len(results)
        sources_used = []
        
        for r in results:
            title = r.get('title', '').lower()
            snippet = r.get('body', '').lower()
            url = r.get('href', '')
            
            combined_text = title + " " + snippet
            sources_used.append({'title': r.get('title'), 'url': url})
            
            # If a trusted fact checking site explicitly calls it false
            is_trusted = any(domain in url for domain in TRUSTED_DOMAINS)
            
            has_debunk = any(keyword in combined_text for keyword in DEBUNK_KEYWORDS)
            
            if has_debunk:
                if is_trusted:
                    debunk_score += 2 # Trusted sources carry more weight
                else:
                    debunk_score += 1
                    
            # Check for numerical contradictions (e.g. claim says '6' but sources say '11')
            claim_numbers = set(re.findall(r'\b\d+\b', query))
            if claim_numbers:
                result_numbers = set(re.findall(r'\b\d+\b', combined_text))
                # Ignore common years like 2023, 2024 to prevent false positives
                result_numbers = {n for n in result_numbers if len(n) < 4}
                claim_numbers_filtered = {n for n in claim_numbers if len(n) < 4}
                if claim_numbers_filtered and result_numbers and not claim_numbers_filtered.intersection(result_numbers):
                    debunk_score += 1  # Contradicting numerical facts
                    
        # Decision logic
        if debunk_score >= 2:
            return {
                'status': 'debunked',
                'message': 'Live Web Search: Claim has been debunked by fact-checkers.',
                'sources': sources_used[:3]
            }
        elif debunk_score == 0 and total_results >= 3:
            # Lots of results, no debunks. Check if there's wikipedia or trusted news
            trusted_count = sum(1 for src in sources_used if any(d in src['url'] for d in TRUSTED_DOMAINS + ['wikipedia.org', 'cnn.com', 'britannica.com']))
            if trusted_count >= 1:
                return {
                    'status': 'verified',
                    'message': 'Live Web Search: Claim is supported by credible sources.',
                    'sources': sources_used[:3]
                }
                
        return {
            'status': 'unverified',
            'message': 'Live Web Search: Results found, but inconclusive.',
            'sources': sources_used[:3]
        }
            
    except Exception as e:
        print(f"Web Search Error: {e}")
        return {'status': 'error', 'message': f'Search failed: {str(e)}'}
