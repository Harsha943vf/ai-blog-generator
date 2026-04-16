"""
Image node — uses Pollinations.ai (free, no API key) to generate
illustrative images for the blog, saves them to /images, and inserts
references into the final markdown.

If image generation fails for any reason the blog is returned as-is.
"""

from __future__ import annotations
import os
import re
import logging
import uuid
import time
import urllib.parse

import requests

from backend.config import get_llm
from backend.models import GraphState
from backend.utils import extract_json, retry

logger = logging.getLogger("blog_gen.images")

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "images")

# ---------------------------------------------------------------------------
# Decide image placements
# ---------------------------------------------------------------------------

PLACEMENT_PROMPT = """\
You are an editor deciding where images would improve a blog post.
Given the section headings below, pick 1-3 sections that would benefit
most from an illustrative image. For each, write a concise image prompt
(suitable for an AI image generator) describing what the image should show.
Make prompts vivid and specific — describe the scene, style, and mood.

Sections:
{headings}

Return ONLY a JSON array:
[{{"heading": "...", "image_prompt": "..."}}]
"""


@retry()
def _decide_placements(plan: dict) -> list[dict]:
    headings = "\n".join(
        f"- {s.get('heading', '')}" for s in plan.get("sections", [])
    )
    llm = get_llm(temperature=0.3)
    raw = llm.invoke(PLACEMENT_PROMPT.format(headings=headings))
    return extract_json(raw.content)


# ---------------------------------------------------------------------------
# Generate image via Pollinations.ai (FREE — no API key required)
# ---------------------------------------------------------------------------

@retry(max_attempts=2)
def _generate_image(prompt: str) -> str | None:
    """Generate an image via Pollinations.ai and save it to IMAGES_DIR."""

    encoded_prompt = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=1024&height=576&nologo=true&seed={int(time.time())}"
    )

    logger.info("Pollinations request: %s", url[:120])
    response = requests.get(url, timeout=90)

    if response.status_code != 200:
        logger.warning("Pollinations returned status %d", response.status_code)
        return None

    if len(response.content) < 1000:
        logger.warning("Pollinations returned suspiciously small payload (%d bytes)", len(response.content))
        return None

    os.makedirs(IMAGES_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:10]}.png"
    filepath = os.path.join(IMAGES_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(response.content)

    logger.info("Image saved: %s (%d KB)", filepath, len(response.content) // 1024)
    return filepath


# ---------------------------------------------------------------------------
# Insert image references into markdown
# ---------------------------------------------------------------------------

def _insert_images(markdown: str, image_map: dict[str, str]) -> str:
    """Insert ![alt](path) right after the matching ## heading line."""
    for heading, path in image_map.items():
        escaped = re.escape(heading)
        pattern = rf"(##\s*{escaped}[^\n]*\n)"
        replacement = rf"\1\n![{heading}]({path})\n"
        markdown = re.sub(pattern, replacement, markdown, count=1, flags=re.IGNORECASE)
    return markdown


# ---------------------------------------------------------------------------
# Node entry point
# ---------------------------------------------------------------------------

def image_node(state: GraphState) -> GraphState:
    """Optionally generate and insert images."""
    if not state.get("enable_images", False):
        logger.info("Images: disabled, skipping.")
        return {}

    plan = state.get("plan", {})
    final_md = state.get("final_markdown", "")
    errors: list[str] = list(state.get("errors", []))

    logger.info("Images: deciding placements …")

    try:
        placements = _decide_placements(plan)
    except Exception as exc:
        logger.error("Image placement decision failed: %s", exc)
        return {"errors": errors + [f"Image placement error: {exc}"]}

    image_records: list[dict] = []
    image_map: dict[str, str] = {}

    for p in placements:
        heading = p.get("heading", "")
        prompt = p.get("image_prompt", "")
        if not prompt:
            continue
        try:
            path = _generate_image(prompt)
            if path:
                image_records.append({"path": path, "alt": heading, "prompt": prompt})
                image_map[heading] = path
        except Exception as exc:
            logger.warning("Image generation failed for '%s': %s", heading, exc)
            errors.append(f"Image gen error ({heading}): {exc}")

    if image_map:
        final_md = _insert_images(final_md, image_map)

    logger.info("Images: generated %d / %d requested", len(image_records), len(placements))
    return {
        "final_markdown": final_md,
        "images": image_records,
        "errors": errors,
    }