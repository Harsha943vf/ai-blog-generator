"""
Service layer — wraps the LangGraph pipeline with caching, timing, and a
clean return contract.

Public function:
    generate_blog(topic, enable_images) -> dict
"""

from __future__ import annotations
import time
import logging

from backend.pipeline import compiled_graph
from backend.utils import get_cached, set_cached

logger = logging.getLogger("blog_gen.service")


def generate_blog(topic: str, enable_images: bool = False) -> dict:
    """
    Generate a blog post for the given topic.

    Returns
    -------
    dict with keys:
        mode, plan, sections, final_markdown, images, errors, elapsed_seconds
    """
    topic = topic.strip()
    if not topic:
        return {"error": "Topic cannot be empty."}

    # ── Cache check ──────────────────────────────────────────────────────
    cache_topic = f"{topic}::img={enable_images}"
    cached = get_cached(cache_topic)
    if cached:
        return cached

    # ── Run pipeline ─────────────────────────────────────────────────────
    logger.info("=== Starting blog generation for: %s ===", topic)
    t0 = time.time()

    initial_state = {
        "topic": topic,
        "enable_images": enable_images,
        "mode": "",
        "category": "",
        "target_audience": "",
        "tone": "",
        "research_data": [],
        "plan": {},
        "sections": [],
        "final_markdown": "",
        "images": [],
        "errors": [],
    }

    try:
        final_state = compiled_graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Pipeline crashed: %s", exc)
        return {"error": str(exc)}

    elapsed = round(time.time() - t0, 2)
    logger.info("=== Blog generated in %.2fs ===", elapsed)

    result = {
        "mode": final_state.get("mode", "unknown"),
        "category": final_state.get("category", ""),
        "target_audience": final_state.get("target_audience", ""),
        "tone": final_state.get("tone", ""),
        "plan": final_state.get("plan", {}),
        "sections": final_state.get("sections", []),
        "final_markdown": final_state.get("final_markdown", ""),
        "images": final_state.get("images", []),
        "errors": final_state.get("errors", []),
        "elapsed_seconds": elapsed,
    }

    # ── Cache result ─────────────────────────────────────────────────────
    set_cached(cache_topic, result)
    return result
