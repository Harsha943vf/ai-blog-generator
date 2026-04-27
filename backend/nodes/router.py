"""
Router node — analyses the topic and decides the pipeline mode.

Outputs:
    mode        – closed_book | hybrid | open_book
    category    – inferred topic domain
    target_audience – beginner / intermediate / expert / general
    tone        – writing tone best suited for the domain
"""

from __future__ import annotations
import logging

from backend.config import get_llm
from backend.models import GraphState
from backend.utils import extract_json, retry

logger = logging.getLogger("blog_gen.router")

ROUTER_PROMPT = """\
You are an expert editorial strategist. Given a blog topic, perform the
following analysis and return ONLY a JSON object (no extra text, no markdown):

{{
  "category": "sports",
  "target_audience": "general",
  "tone": "informative",
  "complexity": "moderate",
  "needs_research": true,
  "mode": "hybrid"
}}

For the given topic, determine:
1. category: One of [tech, finance, health, travel, lifestyle, education, business, science, food, sports, entertainment, general]
2. target_audience: One of [beginner, intermediate, expert, general]
3. tone: One of [educational, storytelling, persuasive, analytical, conversational, descriptive]
4. complexity: One of [simple, moderate, complex]
5. needs_research: true or false (bool, no quotes)
6. mode: One of [closed_book, hybrid, open_book]

Guidelines:
- closed_book  → topic is simple/general and well-known; no live data needed.
- hybrid       → moderate complexity; a few sources would add depth (top 3).
- open_book    → complex, data-heavy, or rapidly-evolving; full research (5-8 sources).

Respond with ONLY the JSON object, nothing else.

Topic: {topic}
"""


@retry()
def _invoke_router(topic: str) -> dict:
    llm = get_llm(temperature=0.3)
    raw = llm.invoke(ROUTER_PROMPT.format(topic=topic))
    result = extract_json(raw)
    
    # Validate result is a dict (not a number, list, etc.)
    if not isinstance(result, dict):
        logger.warning("Router returned non-dict JSON: %s", type(result))
        raise ValueError(f"Router must return a JSON object, got {type(result).__name__}")
    
    return result


def router_node(state: GraphState) -> GraphState:
    """Classify the topic and set the pipeline mode."""
    topic = state["topic"]
    logger.info("Router: classifying topic → %s", topic)

    try:
        result = _invoke_router(topic)
        return {
            "mode": result.get("mode", "closed_book"),
            "category": result.get("category", "general"),
            "target_audience": result.get("target_audience", "general"),
            "tone": result.get("tone", "educational"),
        }
    except Exception as exc:
        logger.error("Router failed, defaulting to closed_book: %s", exc)
        return {
            "mode": "closed_book",
            "category": "general",
            "target_audience": "general",
            "tone": "educational",
            "errors": state.get("errors", []) + [f"Router error: {exc}"],
        }
