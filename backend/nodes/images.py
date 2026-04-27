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
from backend.utils import extract_json, normalize_dict_list, retry

logger = logging.getLogger("blog_gen.images")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")

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

Do not include explanations, markdown, or prose before or after the JSON.
If no sections need images, return [].
"""


def _match_heading(candidate: str, headings: list[str]) -> str | None:
    """Match a free-form heading candidate back to a known section heading."""
    normalized = re.sub(r"\s+", " ", candidate).strip().casefold()
    if not normalized:
        return None

    def heading_tokens(value: str) -> set[str]:
        cleaned = re.sub(r"[^a-z0-9\s]", " ", value.casefold())
        stop_words = {"a", "an", "the", "and", "of", "to", "for", "in", "on"}
        return {token for token in cleaned.split() if token and token not in stop_words}

    candidate_tokens = heading_tokens(candidate)

    for heading in headings:
        if normalized == heading.casefold():
            return heading

    for heading in headings:
        lowered = heading.casefold()
        if normalized in lowered or lowered in normalized:
            return heading

    for heading in headings:
        tokens = heading_tokens(heading)
        if candidate_tokens and tokens and (
            candidate_tokens == tokens
            or candidate_tokens.issubset(tokens)
            or tokens.issubset(candidate_tokens)
        ):
            return heading

    return None


def _markdown_image_path(path: str) -> str:
    """Convert an absolute image path into a markdown-friendly project-relative path."""
    try:
        return os.path.relpath(path, PROJECT_ROOT)
    except ValueError:
        return path


def _recover_placements_from_text(raw: str, sections: list[dict]) -> list[dict]:
    """
    Recover placements from plain-text LLM output when JSON parsing fails.

    Expected fallback patterns include:
      Section Heading
      Example image prompt: ...
    """
    known_headings = [
        str(section.get("heading", "")).strip()
        for section in sections
        if str(section.get("heading", "")).strip()
    ]
    if not known_headings:
        return []

    placements: list[dict] = []
    used_headings: set[str] = set()
    prompt_pattern = re.compile(r"(?im)^(?:example\s+)?image\s+prompt\s*:\s*(.+?)\s*$")

    for match in prompt_pattern.finditer(raw):
        prompt = match.group(1).strip(" -")
        if not prompt:
            continue

        heading: str | None = None
        previous_lines = raw[:match.start()].splitlines()

        for line in reversed(previous_lines):
            candidate = re.sub(r"^\s*(?:[-*#]+|\d+[.)])\s*", "", line).strip(" :\t")
            matched_heading = _match_heading(candidate, known_headings)
            if matched_heading and matched_heading not in used_headings:
                heading = matched_heading
                break

        if not heading:
            for fallback_heading in known_headings:
                if fallback_heading not in used_headings:
                    heading = fallback_heading
                    break

        if not heading:
            continue

        placements.append({"heading": heading, "image_prompt": prompt})
        used_headings.add(heading)

        if len(placements) >= 3:
            break

    return placements


@retry()
def _decide_placements(plan: dict) -> list[dict]:
    sections = normalize_dict_list(plan.get("sections", []), "image plan sections")
    headings = "\n".join(
        f"- {s.get('heading', '')}" for s in sections
    )
    llm = get_llm(temperature=0.3)
    raw = llm.invoke(PLACEMENT_PROMPT.format(headings=headings))
    try:
        result = extract_json(raw)
    except ValueError:
        logger.warning("Image placer returned non-JSON output; attempting plain-text recovery")
        recovered = _recover_placements_from_text(raw, sections)
        if recovered:
            logger.info("Recovered %d image placements from plain-text output", len(recovered))
        return recovered
    
    # Validate result is a list
    if not isinstance(result, list):
        logger.warning("Image placer returned non-list JSON: %s", type(result))
        return []  # Return empty list to skip image generation

    return normalize_dict_list(result, "image placements")


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
    """Insert ![alt](path) after the closest matching ## heading line."""
    lines = markdown.splitlines()
    heading_pattern = re.compile(r"^(##\s+)(.+?)\s*$")

    indexed_headings: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        match = heading_pattern.match(line)
        if match:
            indexed_headings.append((idx, match.group(2).strip()))

    if not indexed_headings:
        return markdown

    insertions: dict[int, str] = {}
    used_indexes: set[int] = set()

    for requested_heading, path in image_map.items():
        matched_idx: int | None = None

        for idx, actual_heading in indexed_headings:
            if idx in used_indexes:
                continue
            if requested_heading.casefold() == actual_heading.casefold():
                matched_idx = idx
                break

        if matched_idx is None:
            actual_headings = [heading for _, heading in indexed_headings]
            matched_heading = _match_heading(requested_heading, actual_headings)
            if matched_heading:
                for idx, actual_heading in indexed_headings:
                    if idx in used_indexes:
                        continue
                    if actual_heading == matched_heading:
                        matched_idx = idx
                        break

        if matched_idx is None:
            continue

        insertions[matched_idx] = f"![{requested_heading}]({path})"
        used_indexes.add(matched_idx)

    if not insertions:
        return markdown

    rendered_lines: list[str] = []
    for idx, line in enumerate(lines):
        rendered_lines.append(line)
        image_line = insertions.get(idx)
        if image_line:
            rendered_lines.append("")
            rendered_lines.append(image_line)

    return "\n".join(rendered_lines)


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
                markdown_path = _markdown_image_path(path)
                image_records.append({
                    "path": path,
                    "markdown_path": markdown_path,
                    "alt": heading,
                    "prompt": prompt,
                })
                image_map[heading] = markdown_path
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
