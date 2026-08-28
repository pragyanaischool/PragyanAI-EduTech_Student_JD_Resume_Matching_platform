import urllib.parse
from typing import Any, Dict, List

# Safe imports for search providers
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    from youtubesearchpython import VideosSearch
except ImportError:
    VideosSearch = None


# ==============================================================================
# Web Search Engine (DuckDuckGo with Resilient Fallback)
# ==============================================================================
def search_ddgs_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Searches DuckDuckGo for technical documentation, reference articles, and tutorials.
    Falls back gracefully to constructed documentation links if the search library fails.
    """
    results: List[Dict[str, str]] = []
    
    if DDGS:
        try:
            with DDGS() as ddgs:
                ddg_gen = ddgs.text(query, max_results=max_results)
                if ddg_gen:
                    for item in ddg_gen:
                        results.append({
                            "title": item.get("title", "Technical Documentation"),
                            "href": item.get("href", "#"),
                            "body": item.get("body", "")
                        })
        except Exception:
            # Fallback on network/rate-limit error
            pass

    # Safe Fallback if empty or search failed
    if not results:
        encoded_q = urllib.parse.quote_plus(query)
        results = [
            {
                "title": f"Official Documentation & Tutorials: {query}",
                "href": f"https://www.google.com/search?q={encoded_q}+documentation+tutorial",
                "body": f"Explore official documentation, guides, and architectural references for {query}."
            },
            {
                "title": f"GitHub Repositories & Implementations: {query}",
                "href": f"https://github.com/search?q={encoded_q}",
                "body": f"Explore open-source reference implementations, code examples, and starter templates for {query}."
            }
        ]

    return results[:max_results]


# ==============================================================================
# Video Search Engine (YouTube with Resilient Fallback)
# ==============================================================================
def search_youtube_videos(query: str, max_results: int = 2) -> List[Dict[str, str]]:
    """
    Searches YouTube for video tutorials and crash courses.
    Falls back gracefully to search links if scraping/API fails.
    """
    results: List[Dict[str, str]] = []

    if VideosSearch:
        try:
            yt_search = VideosSearch(query + " tutorial crash course", limit=max_results)
            res_dict = yt_search.result()
            for v in res_dict.get("result", []):
                results.append({
                    "title": v.get("title", "Video Crash Course"),
                    "url": v.get("link", f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"),
                    "duration": v.get("duration", "Full Course"),
                    "channel": v.get("channel", {}).get("name", "YouTube Educator")
                })
        except Exception:
            pass

    # Safe Fallback if empty or search failed
    if not results:
        encoded_q = urllib.parse.quote_plus(query)
        results = [
            {
                "title": f"Video Tutorial: {query} Comprehensive Guide",
                "url": f"https://www.youtube.com/results?search_query={encoded_q}+crash+course",
                "duration": "Comprehensive Video",
                "channel": "YouTube Tech Education"
            },
            {
                "title": f"Practical Hands-On Walkthrough: {query}",
                "url": f"https://www.youtube.com/results?search_query={encoded_q}+project+walkthrough",
                "duration": "Project Deep-Dive",
                "channel": "Developer Series"
            }
        ]

    return results[:max_results]


# ==============================================================================
# Backward-Compatible Function Aliases
# ==============================================================================
search_web = search_ddgs_web
search_duckduckgo = search_ddgs_web
search_ddg = search_ddgs_web
search_videos = search_youtube_videos
search_youtube = search_youtube_videos

