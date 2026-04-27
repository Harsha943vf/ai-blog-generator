"""
Research node — queries Tavily Search API, deduplicates, filters for relevance,
and produces concise evidence summaries with reference images.

Activated only in hybrid / open_book modes.
"""

from __future__ import annotations
import logging
from tavily import TavilyClient

from backend.config import get_llm, TAVILY_API_KEY
from backend.models import GraphState
from backend.tavily_utils import describe_tavily_error, tavily_is_configured
from backend.utils import normalize_dict_list, retry

logger = logging.getLogger("blog_gen.research")


class TavilySearchError(RuntimeError):
    """Raised when Tavily search is unavailable and research must fall back."""

# ---------------------------------------------------------------------------
# Tavily Search API wrapper
# ---------------------------------------------------------------------------

@retry()
def _search_tavily(query: str, max_results: int) -> list[dict]:
    """Search using Tavily API with images (free tier available at https://tavily.com)."""
    if not tavily_is_configured(TAVILY_API_KEY):
        logger.warning("Tavily API key not set. Set TAVILY_API_KEY in .env file.")
        return []
    
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query, max_results=max_results, include_images=True)
        
        results = []
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "image_url": result.get("image_url", ""),  # Reference image from search result
            })
        logger.info("Tavily search returned %d results", len(results))
        return results
    except Exception as e:
        message = describe_tavily_error(e)
        logger.error(message)
        raise TavilySearchError(message) from e


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
        f"TASK: Extract summaries from search results.\n"
        f"Topic: {topic}\n\n"
        f"Return ONLY valid JSON. No other text. Start with [ and end with ].\n\n"
        f"Format:\n"
        f'[{{"title":"source title","url":"source url","summary":"2-3 sentence summary"}}]\n\n'
        f"Search Results:\n{sources_text}\n\n"
        f"Output JSON Array:"
    )

    llm = get_llm(temperature=0.1)  # Lower temperature for more deterministic output
    raw = llm.invoke(prompt)

    from backend.utils import extract_json
    
    try:
        result = extract_json(raw)
        
        # Validate result is a list
        if not isinstance(result, list):
            logger.warning("Research summarizer returned non-list JSON: %s", type(result))
            # Fall back to basic summaries from original results
            return _create_basic_summaries(results, topic)

        normalized = normalize_dict_list(result, "research summary")
        if not normalized:
            logger.warning("Research summarizer returned no valid source objects")
            return _create_basic_summaries(results, topic)

        return normalized
    
    except ValueError as e:
        logger.warning("Failed to extract JSON from research summarizer: %s", str(e)[:100])
        # Fall back to basic summaries from original results
        return _create_basic_summaries(results, topic)


def _create_basic_summaries(results: list[dict], topic: str) -> list[dict]:
    """Create basic summaries from search results when LLM fails."""
    summaries = []
    for r in results[:3]:
        title = r.get("title", "")
        url = r.get("url", "")
        content = r.get("content", "")
        
        # Use first 200 chars of content as summary
        summary = content[:200] if content else f"Information about {title}"
        
        summaries.append({
            "title": title,
            "url": url,
            "summary": summary
        })
    
    logger.info("Created basic summaries for %d results", len(summaries))
    return summaries


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

    except TavilySearchError as exc:
        logger.warning("Research unavailable, continuing without live sources: %s", exc)
        return {
            "research_data": [],
            "mode": "closed_book",
            "errors": state.get("errors", []) + [str(exc)],
        }

    except Exception as exc:
        logger.error("Research failed — falling back to closed_book: %s", exc)
        return {
            "research_data": [],
            "mode": "closed_book",
            "errors": state.get("errors", []) + [f"Research error: {exc}"],
        }
