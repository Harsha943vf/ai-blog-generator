"""
Reducer node — combines individual sections into a single, polished
markdown blog post with smooth transitions and consistent formatting.
"""

from __future__ import annotations
import logging

from backend.config import get_llm
from backend.models import GraphState
from backend.utils import retry

logger = logging.getLogger("blog_gen.reducer")

REDUCER_PROMPT = """\
You are a senior editor. Below is a blog draft assembled from independently
written sections. Your job is to combine them into ONE polished markdown blog
post.

Blog title: {title}
Tone      : {tone}
Audience  : {target_audience}

--- SECTIONS ---
{sections_text}
--- END SECTIONS ---

Editing instructions:
1. Start with the title as a top-level markdown heading (# Title).
2. Ensure smooth transitions between sections.
3. Remove any repetition across sections.
4. Maintain a consistent {tone} tone throughout.
5. Fix any formatting inconsistencies (heading levels, list styles).
6. Keep the total length between {min_words} and {max_words} words.
7. Output clean markdown only — no meta-commentary.
"""


@retry()
def _invoke_reducer(title: str, tone: str, audience: str,
                    sections: list[str], min_words: int, max_words: int) -> str:
    sections_text = "\n\n---\n\n".join(sections)
    prompt = REDUCER_PROMPT.format(
        title=title,
        tone=tone,
        target_audience=audience,
        sections_text=sections_text,
        min_words=min_words,
        max_words=max_words,
    )
    llm = get_llm(temperature=0.4)
    raw = llm.invoke(prompt)
    return raw.content.strip()


def reducer_node(state: GraphState) -> GraphState:
    """Merge and polish all sections into final_markdown."""
    plan = state.get("plan", {})
    sections = state.get("sections", [])
    title = plan.get("title", state.get("topic", "Blog Post"))
    tone = state.get("tone", "educational")
    audience = state.get("target_audience", "general")

    logger.info("Reducer: merging %d sections", len(sections))

    try:
        final = _invoke_reducer(
            title=title,
            tone=tone,
            audience=audience,
            sections=sections,
            min_words=800,
            max_words=2000,
        )
        logger.info("Reducer: final blog is ~%d words", len(final.split()))
        return {"final_markdown": final}

    except Exception as exc:
        logger.error("Reducer failed, concatenating raw sections: %s", exc)
        fallback = f"# {title}\n\n" + "\n\n".join(sections)
        return {
            "final_markdown": fallback,
            "errors": state.get("errors", []) + [f"Reducer error: {exc}"],
        }
