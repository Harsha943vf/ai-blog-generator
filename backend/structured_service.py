"""
Structured Blog Service - Orchestrates the 5-step pipeline in strict order
"""

from __future__ import annotations
import time
import logging
from backend.structured_pipeline import (
    structured_router_node,
    structured_planner_node,
    structured_research_node,
    structured_generator_node,
    structured_editor_node,
    extract_final_blog,
)
from backend.models import GraphState

logger = logging.getLogger("blog_gen.structured_service")


def generate_structured_blog(topic: str) -> dict:
    """
    Generate a blog using the strict 5-step structured pipeline.
    
    Pipeline:
    1. Router → Classify topic and extract parameters
    2. Planner → Create section structure in table format
    3. Research → Gather facts and statistics
    4. Generator → Write full blog following plan
    5. Editor → Polish and refine output
    
    Returns:
        dict with keys:
            - topic
            - router_output
            - planner_output
            - research_output
            - generator_output
            - final_output
            - elapsed_seconds
            - status
    """
    
    topic = topic.strip()
    if not topic:
        return {"error": "Topic cannot be empty.", "status": "error"}
    
    logger.info("=== STRUCTURED PIPELINE: Starting for topic: %s ===", topic)
    t0 = time.time()
    
    # Initialize state
    state: GraphState = {
        "topic": topic,
        "enable_images": False,
        "mode": "structured",
        "category": "",
        "target_audience": "general",
        "tone": "informative",
        "research_data": [],
        "plan": {},
        "sections": [],
        "final_markdown": "",
        "images": [],
        "errors": [],
    }
    
    try:
        # ─────────────────────────────────────────────────────────────────
        # STEP 1: ROUTER
        # ─────────────────────────────────────────────────────────────────
        logger.info("STEP 1: ROUTER - Classifying topic...")
        
        state.update(structured_router_node(state))
        router_output = state.get("router_output", "")
        
        if not router_output or "STEP: Router" not in router_output:
            raise ValueError("Router failed to produce valid output")
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 2: PLANNER
        # ─────────────────────────────────────────────────────────────────
        logger.info("STEP 2: PLANNER - Creating blog structure...")
        
        state.update(structured_planner_node(state))
        planner_output = state.get("planner_output", "")
        sections = state.get("sections", [])
        
        if not planner_output or "STEP: Planner" not in planner_output:
            raise ValueError("Planner failed to produce valid output")
        
        if not sections:
            raise ValueError("Planner failed to extract sections")
        
        logger.info("Planner created %d sections: %s", len(sections), sections)
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 3: RESEARCH
        # ─────────────────────────────────────────────────────────────────
        logger.info("STEP 3: RESEARCH - Gathering supporting data...")
        
        state.update(structured_research_node(state))
        research_output = state.get("research_output", "")
        
        if not research_output or "STEP: Research" not in research_output:
            raise ValueError("Research failed to produce valid output")
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 4: GENERATOR
        # ─────────────────────────────────────────────────────────────────
        logger.info("STEP 4: GENERATOR - Writing blog content...")
        
        state.update(structured_generator_node(state))
        generator_output = state.get("generator_output", "")
        
        if not generator_output or "STEP: Generator" not in generator_output:
            raise ValueError("Generator failed to produce valid output")
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 5: EDITOR
        # ─────────────────────────────────────────────────────────────────
        logger.info("STEP 5: EDITOR - Polishing and refining...")
        
        state.update(structured_editor_node(state))
        final_output = state.get("final_output", "")
        
        if not final_output or "STEP: Editor" not in final_output:
            raise ValueError("Editor failed to produce valid output")
        
        elapsed = time.time() - t0
        
        # ─────────────────────────────────────────────────────────────────
        # SUCCESS
        # ─────────────────────────────────────────────────────────────────
        logger.info("=== STRUCTURED PIPELINE: COMPLETED in %.1fs ===", elapsed)
        
        final_clean = extract_final_blog(final_output)
        
        return {
            "status": "success",
            "topic": topic,
            "router_output": router_output,
            "planner_output": planner_output,
            "research_output": research_output,
            "generator_output": generator_output,
            "final_output": final_output,
            "final_blog": final_clean,  # Clean markdown without STEP: prefix
            "sections": sections,
            "elapsed_seconds": round(elapsed, 2),
        }
    
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error("STRUCTURED PIPELINE FAILED: %s", exc, exc_info=True)
        
        return {
            "status": "error",
            "error": str(exc),
            "topic": topic,
            "elapsed_seconds": round(elapsed, 2),
            "partial_state": {
                "router_output": state.get("router_output", ""),
                "planner_output": state.get("planner_output", ""),
                "research_output": state.get("research_output", ""),
                "generator_output": state.get("generator_output", ""),
                "final_output": state.get("final_output", ""),
            }
        }
