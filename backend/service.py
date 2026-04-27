"""
Service layer — wraps the LangGraph pipeline with caching, timing, and a
clean return contract. Supports streaming via callbacks.

Public functions:
    generate_blog(topic, enable_images, **preferences) -> dict
    generate_blog_stream(topic, enable_images, callback, **preferences) -> dict
"""

from __future__ import annotations
import time
import logging
from typing import Callable, Any

from backend.pipeline import compiled_graph
from backend.utils import get_cached, set_cached

logger = logging.getLogger("blog_gen.service")


def generate_blog(
    topic: str,
    enable_images: bool = False,
    blog_length: str = "medium",
    blog_format: str = "standard",
    tone: str = "educational",
    target_audience: str = "general",
    llm_provider: str = "auto",
) -> dict:
    """
    Generate a blog post for the given topic (blocking, no streaming).

    Returns
    -------
    dict with keys:
        mode, plan, sections, final_markdown, images, errors, elapsed_seconds
    """
    return generate_blog_stream(
        topic=topic,
        enable_images=enable_images,
        callback=None,  # No streaming
        blog_length=blog_length,
        blog_format=blog_format,
        tone=tone,
        target_audience=target_audience,
        llm_provider=llm_provider,
    )


def generate_blog_stream(
    topic: str,
    enable_images: bool = False,
    callback: Callable[[str, Any], None] | None = None,
    blog_length: str = "medium",
    blog_format: str = "standard",
    tone: str = "educational",
    target_audience: str = "general",
    llm_provider: str = "auto",
) -> dict:
    """
    Generate a blog post with optional streaming callback.
    
    Callback signature: callback(stage: str, data: dict)
      - stage: "routing", "research", "planning", "writing", "editing", "images", "complete"
      - data: progress info (e.g., {"mode": "hybrid", "plan": {...}})
    """
    topic = topic.strip()
    if not topic:
        return {"error": "Topic cannot be empty."}

    # ── Cache key includes preferences ──────────────────────────────────
    cache_key_str = f"{topic}::img={enable_images}::len={blog_length}::fmt={blog_format}::tone={tone}::aud={target_audience}"
    cached = get_cached(cache_key_str)
    if cached:
        logger.info("Cache hit for: %s", topic)
        if callback:
            callback("complete", {"cached": True, **cached})
        return cached

    # ── Run pipeline with streaming ──────────────────────────────────────
    logger.info("=== Starting blog generation for: %s ===", topic)
    logger.info("Preferences: length=%s, format=%s, tone=%s, audience=%s, provider=%s",
                blog_length, blog_format, tone, target_audience, llm_provider)
    t0 = time.time()

    initial_state = {
        "topic": topic,
        "enable_images": enable_images,
        "blog_length": blog_length,
        "blog_format": blog_format,
        "tone": tone,
        "target_audience": target_audience,
        "llm_provider": llm_provider,
        "progress_callback": callback,
        # Default fields
        "mode": "",
        "category": "",
        "research_data": [],
        "plan": {},
        "sections": [],
        "final_markdown": "",
        "images": [],
        "errors": [],
    }

    try:
        # Notify: routing stage
        if callback:
            callback("routing", {"status": "Analyzing topic complexity..."})

        final_state = compiled_graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Pipeline crashed: %s", exc)
        error_msg = str(exc)
        if callback:
            callback("error", {"error": error_msg})
        return {"error": error_msg}

    elapsed = round(time.time() - t0, 2)
    logger.info("=== Blog generated in %.2fs ===", elapsed)

    result = {
        "mode": final_state.get("mode", "unknown"),
        "category": final_state.get("category", ""),
        "target_audience": final_state.get("target_audience", ""),
        "tone": final_state.get("tone", ""),
        "blog_length": blog_length,
        "blog_format": blog_format,
        "plan": final_state.get("plan", {}),
        "sections": final_state.get("sections", []),
        "final_markdown": final_state.get("final_markdown", ""),
        "images": final_state.get("images", []),
        "errors": final_state.get("errors", []),
        "elapsed_seconds": elapsed,
    }

    # ── Cache result ─────────────────────────────────────────────────────
    set_cached(cache_key_str, result)
    
    # Final callback
    if callback:
        callback("complete", result)
    
    return result
