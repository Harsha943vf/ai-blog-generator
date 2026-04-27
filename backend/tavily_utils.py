"""
Helpers for Tavily integration.
"""

from __future__ import annotations


TAVILY_PLACEHOLDER_KEY = "your_tavily_api_key_here"


def tavily_is_configured(api_key: str | None) -> bool:
    """Return True when a real Tavily API key is configured."""
    return bool(api_key and api_key != TAVILY_PLACEHOLDER_KEY)


def describe_tavily_error(exc: Exception) -> str:
    """Translate low-level Tavily/request errors into user-friendly text."""
    message = str(exc).strip() or exc.__class__.__name__
    lowered = message.lower()

    if (
        "nameresolutionerror" in lowered
        or "failed to resolve" in lowered
        or "nodename nor servname provided" in lowered
        or "temporary failure in name resolution" in lowered
    ):
        return (
            "Tavily DNS lookup failed for api.tavily.com. "
            "Check internet access, DNS, VPN/proxy settings, or firewall rules."
        )

    if "401" in lowered or "unauthorized" in lowered or "invalid api key" in lowered:
        return "Tavily rejected the API key. Verify TAVILY_API_KEY in .env."

    if "403" in lowered or "forbidden" in lowered:
        return "Tavily denied the request. Check account access or quota limits."

    if "429" in lowered or "rate limit" in lowered or "too many requests" in lowered:
        return "Tavily rate limit reached. Wait and retry or check your Tavily quota."

    if (
        "timeout" in lowered
        or "timed out" in lowered
        or "readtimeout" in lowered
        or "connecttimeout" in lowered
    ):
        return "Tavily request timed out. Check connectivity and retry."

    if "ssl" in lowered or "certificate" in lowered:
        return "Tavily TLS handshake failed. Check local certificate or proxy settings."

    return f"Tavily search failed: {message}"
