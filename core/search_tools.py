from typing import List, Dict
from ddgs import DDGS
from youtube_search import YoutubeSearch


def fetch_web_certifications(skill: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Searches DuckDuckGo for top free courses, documentation, and certifications for a given skill.
    Requires no paid API keys.
    """
    courses = []
    query = f"best free courses tutorials and certifications for {skill}"
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get("title", "")
                link = r.get("href", "")
                snippet = r.get("body", "")
                if title and link:
                    courses.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet[:120] + "..." if len(snippet) > 120 else snippet
                    })
    except Exception:
        # Fallback to direct search query links
        fallback_query = skill.replace(" ", "+")
        courses = [
            {
                "title": f"Official {skill} Documentation & Guide",
                "link": f"[https://www.google.com/search?q=](https://www.google.com/search?q=){fallback_query}+official+documentation",
                "snippet": f"Access official guides and references for {skill}."
            },
            {
                "title": f"Top Coursera & edX Certifications for {skill}",
                "link": f"[https://www.coursera.org/search?query=](https://www.coursera.org/search?query=){fallback_query}",
                "snippet": f"Explore accredited industry certifications for {skill}."
            }
        ]
    return courses


def fetch_youtube_lectures(skill: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Searches YouTube for video tutorials, deep dives, and crash courses for a given skill.
    Uses the free-tier youtube-search library.
    """
    lectures = []
    query = f"{skill} full crash course project tutorial"
    try:
        results = YoutubeSearch(query, max_results=max_results).to_dict()
        for v in results:
            lectures.append({
                "title": v.get("title", f"{skill} Tutorial"),
                "link": f"[https://www.youtube.com/watch?v=](https://www.youtube.com/watch?v=){v.get('id', '')}",
                "duration": v.get("duration", "N/A"),
                "views": v.get("views", "N/A")
            })
    except Exception:
        fallback_query = skill.replace(" ", "+")
        lectures = [
            {
                "title": f"Search '{skill}' Video Courses on YouTube",
                "link": f"[https://www.youtube.com/results?search_query=](https://www.youtube.com/results?search_query=){fallback_query}+course",
                "duration": "Playlist",
                "views": "N/A"
            }
        ]
    return lectures
