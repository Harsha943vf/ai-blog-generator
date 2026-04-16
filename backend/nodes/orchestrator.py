"""
Orchestrator node — produces a detailed, structured blog plan that the
worker nodes will follow section by section.
"""

from __future__ import annotations
import logging

from backend.config import get_llm
from backend.models import GraphState
from backend.utils import extract_json, retry

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


@retry()
def _invoke_planner(topic: str, category: str, audience: str,
                    tone: str, research: list[dict]) -> dict:
    research_summary = "None available." if not research else "\n".join(
        f"- {r.get('title','')}: {r.get('summary','')}" for r in research
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
    return extract_json(raw.content)


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
