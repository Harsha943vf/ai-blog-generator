"""
Structured Pipeline - Implements the 5-step blog generation workflow
with plain text output format (STEP: format)

This is a sequential, strictly-ordered pipeline:
1. Router → Parse topic and extract parameters
2. Planner → Create section table structure
3. Research → Gather supporting information
4. Generator → Write full blog following plan
5. Editor → Polish and refine

No parallel processing, no JSON output, plain text only.
"""

from __future__ import annotations
import logging
import re
from backend.config import get_llm, TAVILY_API_KEY
from backend.models import GraphState
from backend.structured_prompts import (
    STRUCTURED_ROUTER_PROMPT,
    STRUCTURED_PLANNER_PROMPT,
    STRUCTURED_RESEARCH_PROMPT,
    STRUCTURED_GENERATOR_PROMPT,
    STRUCTURED_EDITOR_PROMPT,
)
from backend.tavily_utils import describe_tavily_error, tavily_is_configured

logger = logging.getLogger("blog_gen.structured_pipeline")

# ---------------------------------------------------------------------------
# STEP 1: ROUTER
# ---------------------------------------------------------------------------

def structured_router_node(state: GraphState) -> GraphState:
    """Parse topic and determine tone/depth parameters."""
    topic = state.get("topic", "").strip()
    
    logger.info("STRUCTURED ROUTER: Processing topic - %s", topic)
    
    # Infer tone and depth from context
    if any(word in topic.lower() for word in ["how", "tutorial", "guide", "learn"]):
        tone = "informative"
    elif any(word in topic.lower() for word in ["fun", "cool", "awesome"]):
        tone = "casual"
    elif any(word in topic.lower() for word in ["business", "enterprise", "corporate"]):
        tone = "professional"
    elif any(word in topic.lower() for word in ["algorithm", "code", "technical", "api"]):
        tone = "technical"
    else:
        tone = "informative"
    
    depth = "medium"  # Default
    
    prompt = STRUCTURED_ROUTER_PROMPT.format(
        topic=topic,
        tone=tone,
        depth=depth
    )
    
    llm = get_llm(temperature=0.2)
    router_output = llm.invoke(prompt).strip()
    
    logger.info("ROUTER OUTPUT:\n%s", router_output)
    
    return {
        "router_output": router_output,
        "tone": tone,
        "depth": depth,
        "mode": "structured",
    }


# ---------------------------------------------------------------------------
# STEP 2: PLANNER
# ---------------------------------------------------------------------------

def structured_planner_node(state: GraphState) -> GraphState:
    """Create structured blog plan in table format."""
    topic = state.get("topic", "")
    tone = state.get("tone", "informative")
    depth = state.get("depth", "medium")
    
    logger.info("STRUCTURED PLANNER: Creating plan for %s", topic)
    
    prompt = STRUCTURED_PLANNER_PROMPT.format(
        topic=topic,
        tone=tone,
        depth=depth,
    )
    
    llm = get_llm(temperature=0.4)
    planner_output = llm.invoke(prompt).strip()
    
    logger.info("PLANNER OUTPUT:\n%s", planner_output)
    
    # Extract sections from the table output
    sections = _extract_sections_from_table(planner_output)
    
    return {
        "planner_output": planner_output,
        "sections": sections,
    }


def _extract_sections_from_table(table_text: str) -> list[str]:
    """Extract section names from the markdown table."""
    lines = table_text.split("\n")
    sections = []
    in_table = False
    
    for line in lines:
        if "| Section No |" in line:
            in_table = True
            continue
        if in_table and line.strip().startswith("|") and "---" not in line:
            # Parse table row: | num | name | desc | points |
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                section_name = parts[2]
                if section_name and section_name not in ["Section Name", ""]:
                    sections.append(section_name)
    
    return sections


# ---------------------------------------------------------------------------
# STEP 3: RESEARCH
# ---------------------------------------------------------------------------

def structured_research_node(state: GraphState) -> GraphState:
    """Gather research data and supporting information."""
    topic = state.get("topic", "")
    
    logger.info("STRUCTURED RESEARCH: Gathering data for %s", topic)
    
    # Fetch from Tavily if available
    research_summary, research_error = _fetch_tavily_research(topic)
    
    prompt = STRUCTURED_RESEARCH_PROMPT.format(
        topic=topic,
        research_data=research_summary,
    )
    
    llm = get_llm(temperature=0.3)
    research_output = llm.invoke(prompt).strip()
    
    logger.info("RESEARCH OUTPUT:\n%s", research_output)
    
    update: GraphState = {
        "research_output": research_output,
        "research_data": research_summary,
    }
    if research_error:
        update["errors"] = state.get("errors", []) + [research_error]
    return update


def _fetch_tavily_research(topic: str) -> tuple[str, str | None]:
    """Fetch research from Tavily API."""
    if not tavily_is_configured(TAVILY_API_KEY):
        logger.warning("Tavily API key not configured, using generic knowledge")
        return "Research data not available. Using model knowledge.", None
    
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(topic, max_results=5)
        
        results = response.get("results", [])
        summary_lines = []
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "")
            content = result.get("content", "")[:200]
            summary_lines.append(f"{i}. {title}: {content}")
        
        research_text = "\n".join(summary_lines) if summary_lines else "No research data found."
        return research_text, None
    except Exception as e:
        message = describe_tavily_error(e)
        logger.error(message)
        return "Research data unavailable. Using model knowledge only.", message


# ---------------------------------------------------------------------------
# STEP 4: GENERATOR
# ---------------------------------------------------------------------------

def structured_generator_node(state: GraphState) -> GraphState:
    """Write the full blog following the planner structure."""
    topic = state.get("topic", "")
    tone = state.get("tone", "informative")
    sections = state.get("sections", [])
    research_data = state.get("research_data", "")
    
    logger.info("STRUCTURED GENERATOR: Writing blog with %d sections", len(sections))
    
    sections_text = "\n".join([f"- {s}" for s in sections])
    
    prompt = STRUCTURED_GENERATOR_PROMPT.format(
        topic=topic,
        tone=tone,
        sections=sections_text,
        research_data=research_data,
    )
    
    llm = get_llm(temperature=0.6)
    generator_output = llm.invoke(prompt).strip()
    
    logger.info("GENERATOR OUTPUT (first 500 chars):\n%s", generator_output[:500])
    
    return {
        "generator_output": generator_output,
    }


# ---------------------------------------------------------------------------
# STEP 5: EDITOR
# ---------------------------------------------------------------------------

def structured_editor_node(state: GraphState) -> GraphState:
    """Polish and refine the blog (structure-preserving only)."""
    generator_output = state.get("generator_output", "")
    
    logger.info("STRUCTURED EDITOR: Polishing content")
    
    prompt = STRUCTURED_EDITOR_PROMPT.format(
        blog_content=generator_output,
    )
    
    llm = get_llm(temperature=0.3)
    editor_output = llm.invoke(prompt).strip()
    
    logger.info("EDITOR OUTPUT (first 500 chars):\n%s", editor_output[:500])
    
    return {
        "final_output": editor_output,
        "editor_output": editor_output,
    }


# ---------------------------------------------------------------------------
# Utility: Process full structured output
# ---------------------------------------------------------------------------

def extract_final_blog(final_output: str) -> str:
    """Extract clean markdown blog from 'STEP: Editor' output."""
    # Remove the "STEP: Editor" prefix if present
    lines = final_output.split("\n")
    
    # Find the line starting with "STEP: Editor" and skip it
    start_idx = 0
    for i, line in enumerate(lines):
        if "STEP: Editor" in line:
            start_idx = i + 1
            break
    
    clean_output = "\n".join(lines[start_idx:]).strip()
    return clean_output
