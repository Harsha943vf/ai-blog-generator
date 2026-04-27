"""
Shared utilities — retry logic, safe JSON extraction, in-memory cache.
"""

from __future__ import annotations
import json
import re
import time
import hashlib
import functools
import logging
from typing import Any, Callable

from backend.config import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger("blog_gen.utils")

# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------

def retry(max_attempts: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator that retries a function up to *max_attempts* on exception."""
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "%s attempt %d/%d failed: %s",
                        fn.__name__, attempt, max_attempts, exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# JSON extraction from LLM output
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict | list:
    """
    Best-effort extraction of JSON from an LLM response.
    Handles markdown fences, leading prose, and trailing garbage.
    
    Returns dict or list, raises ValueError if no valid JSON found.
    """
    # Try direct parse first
    text = text.strip()
    try:
        parsed = json.loads(text)
        # Validate it's a dict or list, not a primitive
        if isinstance(parsed, (dict, list)):
            return parsed
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1).strip())
            if isinstance(parsed, (dict, list)):
                return parsed
        except json.JSONDecodeError:
            pass

    # Find first { … } or [ … ] block
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == opener:
                depth += 1
            elif text[i] == closer:
                depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(text[start : i + 1])
                    if isinstance(parsed, (dict, list)):
                        return parsed
                except json.JSONDecodeError:
                    break

    raise ValueError(f"Could not extract valid JSON dict/list from LLM output:\n{text[:500]}")


def normalize_dict_list(value: Any, label: str) -> list[dict[str, Any]]:
    """
    Return only dict items from a list-like LLM response.

    This protects downstream nodes from malformed outputs such as `[1]`,
    `["oops"]`, or mixed lists.
    """
    if value is None:
        return []

    if not isinstance(value, list):
        logger.warning("%s should be a list, got %s", label, type(value).__name__)
        return []

    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(value, start=1):
        if isinstance(item, dict):
            normalized.append(item)
        else:
            logger.warning(
                "Ignoring invalid %s item %d: expected dict, got %s",
                label, idx, type(item).__name__,
            )

    return normalized


# ---------------------------------------------------------------------------
# Simple in-memory cache keyed by topic hash
# ---------------------------------------------------------------------------

_cache: dict[str, dict[str, Any]] = {}

def cache_key(topic: str) -> str:
    return hashlib.sha256(topic.strip().lower().encode()).hexdigest()[:16]

def get_cached(topic: str) -> dict | None:
    key = cache_key(topic)
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < 3600:
        logger.info("Cache hit for topic: %s", topic)
        return entry["data"]
    return None

def set_cached(topic: str, data: dict):
    _cache[cache_key(topic)] = {"data": data, "ts": time.time()}


def clear_cached():
    """Clear the in-memory generation cache."""
    _cache.clear()
