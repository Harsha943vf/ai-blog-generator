"""
Data models — GraphState (TypedDict for LangGraph) and supporting Pydantic schemas.
"""

from __future__ import annotations
from typing import TypedDict, Any


class GraphState(TypedDict, total=False):
    """Shared state that flows through every LangGraph node."""
    topic: str
    enable_images: bool
    mode: str                     # closed_book | hybrid | open_book
    category: str                 # tech, finance, health, travel …
    target_audience: str          # beginner / intermediate / expert / general
    tone: str                     # educational, storytelling, persuasive …
    research_data: list[dict]     # [{title, url, summary}, …]
    plan: dict[str, Any]          # structured blog plan
    sections: list[str]           # rendered markdown per section
    final_markdown: str           # polished combined output
    images: list[dict]            # [{path, alt, placement}, …]
    errors: list[str]             # accumulated non-fatal errors
