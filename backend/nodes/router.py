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
following analysis and return ONLY a JSON object (no extra text):

{{
  "category": "<one of: tech, finance, health, travel, lifestyle, education, business, science, food, sports, entertainment, general>",
  "target_audience": "<one of: beginner, intermediate, expert, general>",
  "tone": "<one of: educational, storytelling, persuasive, analytical, conversational, descriptive>",
  "complexity": "<one of: simple, moderate, complex>",
  "needs_research": <true or false>,
  "mode": "<one of: closed_book, hybrid, open_book>"
}}

Decision guidelines:
- closed_book  → topic is simple/general and well-known; no live data needed.
- hybrid       → moderate complexity; a few sources would add depth (top 3).
- open_book    → complex, data-heavy, or rapidly-evolving; full research (5-8 sources).

Tone mapping guidance:
- tech → educational or analytical
- travel → descriptive or storytelling
- finance → analytical or persuasive
- lifestyle/food → conversational or storytelling
- health → educational
- business → persuasive or analytical

Topic: {topic}
"""


@retry()
def _invoke_router(topic: str) -> dict:
    llm = get_llm(temperature=0.3)
    raw = llm.invoke(ROUTER_PROMPT.format(topic=topic))
    return extract_json(raw.content)


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
