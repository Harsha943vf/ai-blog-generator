"""
Pipeline — defines the LangGraph StateGraph, wires all nodes, and exposes
a compiled graph ready for invocation.

Flow:
  START → router → (research if needed) → orchestrator → worker → reducer → image_node → END
"""

from __future__ import annotations
import logging

from langgraph.graph import StateGraph, START, END

from backend.models import GraphState
from backend.nodes.router import router_node
from backend.nodes.research import research_node
from backend.nodes.orchestrator import orchestrator_node
from backend.nodes.worker import worker_node
from backend.nodes.reducer import reducer_node
from backend.nodes.images import image_node

logger = logging.getLogger("blog_gen.pipeline")


# ---------------------------------------------------------------------------
# Conditional edge helpers
# ---------------------------------------------------------------------------

def _route_after_router(state: GraphState) -> str:
    """Decide whether to do research or skip straight to planning."""
    mode = state.get("mode", "closed_book")
    if mode in ("hybrid", "open_book"):
        return "research"
    return "orchestrator"


def _route_after_reducer(state: GraphState) -> str:
    """Decide whether to generate images or finish."""
    if state.get("enable_images", False):
        return "image_node"
    return END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and return the compiled LangGraph pipeline."""
    graph = StateGraph(GraphState)

    # Register nodes
    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("worker", worker_node)
    graph.add_node("reducer", reducer_node)
    graph.add_node("image_node", image_node)

    # Edges
    graph.add_edge(START, "router")

    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {"research": "research", "orchestrator": "orchestrator"},
    )
    graph.add_edge("research", "orchestrator")
    graph.add_edge("orchestrator", "worker")
    graph.add_edge("worker", "reducer")

    graph.add_conditional_edges(
        "reducer",
        _route_after_reducer,
        {"image_node": "image_node", END: END},
    )
    graph.add_edge("image_node", END)

    logger.info("Pipeline graph compiled successfully.")
    return graph.compile()


# Module-level compiled graph (singleton)
compiled_graph = build_graph()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_pipeline(mode: str = "open_book"):
    """
    Create and return the blog generation pipeline.
    
    Args:
        mode: "open_book" (with research), "hybrid", or "closed_book" (LLM only)
    
    Returns:
        Compiled LangGraph pipeline ready to invoke
    """
    logger.info("Pipeline created with mode=%s", mode)
    return compiled_graph
