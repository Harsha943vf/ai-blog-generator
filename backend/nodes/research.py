"""
Research node — queries Tavily, deduplicates, filters for relevance,
and produces concise evidence summaries.

Activated only in hybrid / open_book modes.
"""

from __future__ import annotations
import logging
from duckduckgo_search import DDGS

from backend.config import get_llm
from backend.models import GraphState
from backend.utils import retry

logger = logging.getLogger("blog_gen.research")

# ---------------------------------------------------------------------------
# DuckDuckGo search wrapper (FREE, no API key needed)
# ---------------------------------------------------------------------------

@retry()
def _search_tavily(query: str, max_results: int) -> list[dict]:
    """Search using DuckDuckGo (free, no API key required)."""
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        # Convert DuckDuckGo format to Tavily-like format
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "content": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.error("DuckDuckGo search failed: %s", e)
        return []


def _deduplicate(results: list[dict]) -> list[dict]:
    """Remove entries with duplicate URLs."""
    seen_urls: set[str] = set()
    unique = []
    for r in results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(r)
    return unique


@retry()
def _summarize_results(results: list[dict], topic: str) -> list[dict]:
    """Ask the LLM to create concise, relevant summaries of each source."""
    if not results:
        return []

    sources_text = "\n\n".join(
        f"[{i+1}] {r.get('title','Untitled')}\nURL: {r.get('url','')}\nSnippet: {r.get('content','')}"
        for i, r in enumerate(results)
    )

    prompt = (
        f"You are a research assistant. The topic is: \"{topic}\".\n\n"
        f"Below are search results. For EACH result, produce a 2-3 sentence "
        f"summary focused on facts relevant to the topic. Drop any result that "
        f"is clearly irrelevant. Return ONLY a JSON array:\n"
        f'[{{"title":"...","url":"...","summary":"..."}}]\n\n'
        f"Sources:\n{sources_text}"
    )

    llm = get_llm(temperature=0.2)
    raw = llm.invoke(prompt)

    from backend.utils import extract_json
    return extract_json(raw.content)


# ---------------------------------------------------------------------------
# Node entry point
# ---------------------------------------------------------------------------

def research_node(state: GraphState) -> GraphState:
    """Fetch and process research data based on mode."""
    topic = state["topic"]
    mode = state.get("mode", "hybrid")
    max_results = 3 if mode == "hybrid" else 8

    logger.info("Research: mode=%s, fetching up to %d sources for '%s'", mode, max_results, topic)

    try:
        raw_results = _search_tavily(topic, max_results=max_results)
        unique = _deduplicate(raw_results)
        evidence = _summarize_results(unique, topic)
        logger.info("Research: produced %d evidence items", len(evidence))
        return {"research_data": evidence}

    except Exception as exc:
        logger.error("Research failed — falling back to closed_book: %s", exc)
        return {
            "research_data": [],
            "mode": "closed_book",
            "errors": state.get("errors", []) + [f"Research error: {exc}"],
        }
