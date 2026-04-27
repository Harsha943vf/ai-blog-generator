"""
Orchestrator node — produces a detailed, structured blog plan that the
worker nodes will follow section by section.
"""

from __future__ import annotations
import logging

from backend.config import get_llm
from backend.models import GraphState
from backend.utils import extract_json, normalize_dict_list, retry

logger = logging.getLogger("blog_gen.orchestrator")

PLAN_PROMPT = """\
You are a senior content strategist. Create a structured blog plan for the
topic below. Return ONLY a JSON object — no extra text.

Topic       : {topic}
Category    : {category}
Audience    : {target_audience}
Tone        : {tone}
Research    : {research_summary}

Return format:
{{
  "title": "<compelling blog title>",
  "category": "{category}",
  "target_audience": "{target_audience}",
  "tone": "{tone}",
  "estimated_word_count": <integer between 800 and 2000>,
  "sections": [
    {{
      "heading": "<section heading>",
      "goal": "<1-sentence purpose of this section>",
      "bullet_points": ["<key point 1>", "<key point 2>", "..."]
    }}
  ]
}}

Guidelines:
- 4-7 sections (including intro & conclusion).
- Each section should have 2-5 bullet points covering key ideas.
- Intro should hook the reader; conclusion should leave a lasting impression.
- If research is available, weave evidence into the plan naturally.
- Adapt depth and jargon to the target audience.
"""


def _normalize_plan(plan: dict, topic: str, category: str, audience: str, tone: str) -> dict:
    """Sanitize planner output before it reaches worker and UI layers."""
    sections_raw = normalize_dict_list(plan.get("sections", []), "plan sections")
    sections: list[dict] = []

    for idx, section in enumerate(sections_raw, start=1):
        heading = str(section.get("heading", "")).strip() or f"Section {idx}"
        goal = str(section.get("goal", "")).strip()

        bullet_points_raw = section.get("bullet_points", [])
        if isinstance(bullet_points_raw, str):
            bullet_points = [bullet_points_raw.strip()] if bullet_points_raw.strip() else []
        elif isinstance(bullet_points_raw, list):
            bullet_points = [
                str(point).strip() for point in bullet_points_raw if str(point).strip()
            ]
        else:
            bullet_points = []

        if not bullet_points:
            fallback_point = goal or f"Key ideas for {heading.lower()}."
            bullet_points = [fallback_point]

        sections.append({
            "heading": heading,
            "goal": goal,
            "bullet_points": bullet_points,
        })

    if not sections:
        raise ValueError("Planner returned no valid section objects")

    estimated_word_count = plan.get("estimated_word_count", 1200)
    if not isinstance(estimated_word_count, int):
        try:
            estimated_word_count = int(estimated_word_count)
        except (TypeError, ValueError):
            estimated_word_count = 1200
    estimated_word_count = max(800, min(2000, estimated_word_count))

    return {
        "title": str(plan.get("title", "")).strip() or f"Blog: {topic}",
        "category": str(plan.get("category", "")).strip() or category,
        "target_audience": str(plan.get("target_audience", "")).strip() or audience,
        "tone": str(plan.get("tone", "")).strip() or tone,
        "estimated_word_count": estimated_word_count,
        "sections": sections,
    }


@retry()
def _invoke_planner(topic: str, category: str, audience: str,
                    tone: str, research: list[dict]) -> dict:
    safe_research = normalize_dict_list(research, "research context")
    research_summary = "None available." if not safe_research else "\n".join(
        f"- {r.get('title','')}: {r.get('summary','')}" for r in safe_research
    )
    prompt = PLAN_PROMPT.format(
        topic=topic,
        category=category,
        target_audience=audience,
        tone=tone,
        research_summary=research_summary,
    )
    llm = get_llm(temperature=0.5)
    raw = llm.invoke(prompt)
    result = extract_json(raw)
    
    # Validate result is a dict
    if not isinstance(result, dict):
        raise ValueError(f"Planner must return a JSON object, got {type(result).__name__}")

    return _normalize_plan(result, topic, category, audience, tone)


def orchestrator_node(state: GraphState) -> GraphState:
    """Generate the blog plan from topic metadata + research."""
    topic = state["topic"]
    logger.info("Orchestrator: planning blog for '%s'", topic)

    try:
        plan = _invoke_planner(
            topic=topic,
            category=state.get("category", "general"),
            audience=state.get("target_audience", "general"),
            tone=state.get("tone", "educational"),
            research=state.get("research_data", []),
        )
        logger.info("Orchestrator: plan has %d sections", len(plan.get("sections", [])))
        return {"plan": plan}

    except Exception as exc:
        logger.error("Orchestrator failed: %s", exc)
        # Minimal fallback plan so the pipeline can still produce something
        fallback = {
            "title": f"Blog: {topic}",
            "category": state.get("category", "general"),
            "target_audience": state.get("target_audience", "general"),
            "tone": state.get("tone", "educational"),
            "estimated_word_count": 1000,
            "sections": [
                {"heading": "Introduction", "goal": "Introduce the topic.", "bullet_points": ["Overview of the topic"]},
                {"heading": "Main Discussion", "goal": "Core content.", "bullet_points": ["Key ideas and insights"]},
                {"heading": "Conclusion", "goal": "Wrap up.", "bullet_points": ["Summary and takeaways"]},
            ],
        }
        return {
            "plan": fallback,
            "errors": state.get("errors", []) + [f"Orchestrator error: {exc}"],
        }
