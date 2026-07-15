from duckduckgo_search import DDGS
with DDGS() as ddgs:
    results = list(ddgs.text("Python programming", max_results=5))
    print(len(results))
