"""
Worker node — generates markdown for each section defined in the plan.

Sections are written in parallel using ThreadPoolExecutor for speed.
Each worker receives the full plan context so it can maintain coherence.
"""

from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.config import get_llm
from backend.models import GraphState
from backend.utils import normalize_dict_list, retry

logger = logging.getLogger("blog_gen.worker")

SECTION_PROMPT = """\
You are an expert {category} writer. Write the following section of a blog post.

Blog title     : {title}
Overall tone   : {tone}
Target audience: {target_audience}
Section index  : {index} of {total}

Section heading: {heading}
Section goal   : {goal}
Key points to cover:
{bullet_points}

Research context (use if relevant):
{research}

Rules:
- Write in markdown (use ## for the heading).
- Match the tone precisely.
- Include examples, analogies, or mini-stories where appropriate.
- Be concise but substantive — no filler.
- If this is the introduction, open with a compelling hook.
- If this is the conclusion, end with a memorable takeaway.
- Target roughly {words_per_section} words for this section.
- Do NOT include a title line — just the section heading and body.
"""


@retry()
def _write_section(
    section: dict,
    index: int,
    total: int,
    plan: dict,
    research: list[dict],
) -> str:
    """Generate markdown for a single section."""
    bullet_text = "\n".join(f"  - {bp}" for bp in section.get("bullet_points", []))
    research_text = "\n".join(
        f"- {r.get('title','')}: {r.get('summary','')}" for r in research
    ) if research else "None."

    est_words = plan.get("estimated_word_count", 1200)
    words_per_section = max(100, est_words // max(total, 1))

    prompt = SECTION_PROMPT.format(
        category=plan.get("category", "general"),
        title=plan.get("title", ""),
        tone=plan.get("tone", "educational"),
        target_audience=plan.get("target_audience", "general"),
        index=index + 1,
        total=total,
        heading=section.get("heading", "Section"),
        goal=section.get("goal", ""),
        bullet_points=bullet_text,
        research=research_text,
        words_per_section=words_per_section,
    )

    llm = get_llm(temperature=0.7)
    raw = llm.invoke(prompt)
    return raw.strip()


def worker_node(state: GraphState) -> GraphState:
    """Generate all sections concurrently."""
    plan = state.get("plan", {})
    sections_spec = normalize_dict_list(plan.get("sections", []), "worker sections")
    research = normalize_dict_list(state.get("research_data", []), "worker research")
    total = len(sections_spec)

    logger.info("Worker: generating %d sections in parallel", total)

    results: dict[int, str] = {}
    errors: list[str] = list(state.get("errors", []))

    if total == 0:
        logger.warning("Worker: no valid sections available to generate")
        return {
            "sections": [],
            "errors": errors + ["Worker error: no valid sections available to generate"],
        }

    with ThreadPoolExecutor(max_workers=min(total, 4)) as pool:
        future_map = {
            pool.submit(_write_section, sec, i, total, plan, research): i
            for i, sec in enumerate(sections_spec)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                results[idx] = future.result()
                logger.info("Worker: section %d/%d done", idx + 1, total)
            except Exception as exc:
                logger.error("Worker: section %d failed: %s", idx + 1, exc)
                heading = sections_spec[idx].get("heading", f"Section {idx+1}")
                results[idx] = f"## {heading}\n\n*Content generation failed.*\n"
                errors.append(f"Section {idx+1} error: {exc}")

    ordered = [results[i] for i in range(total)]
    return {"sections": ordered, "errors": errors}
