# Implementation Notes for Backend Nodes

## Overview
The 4 improvements have been fully integrated at the service and UI layer. However, **individual pipeline nodes can now leverage these new capabilities** to produce better results based on user preferences.

---

## 🔄 How Nodes Can Use New State Fields

### Current State Structure
Every node now has access to:
```python
state: GraphState = {
    # Original fields
    "topic": str,
    "enable_images": bool,
    "mode": str,                          # "closed_book"|"hybrid"|"open_book"
    "category": str,
    "target_audience": str,               # NEW FIELD ✨
    "tone": str,                          # NEW FIELD ✨
    
    # NEW PREFERENCE FIELDS ✨
    "blog_length": str,                   # "short" | "medium" | "long"
    "blog_format": str,                   # "standard" | "seo-optimized" | "listicle" | "how-to" | "opinion"
    "llm_provider": str,                  # "auto" | "ollama" | "openai"
    
    # Pipeline data
    "research_data": list[dict],
    "plan": dict,
    "sections": list[str],
    "final_markdown": str,
    "images": list[dict],
    "errors": list[str],
    
    # NEW CALLBACK FIELD ✨
    "progress_callback": Callable[[str, dict], None] | None,
}
```

---

## 📝 Example: Using Preferences in Node Implementation

### Router Node Enhancement
**Current**: Determines if research is needed based on topic complexity
**Opportunity**: Factor in user's `blog_format` and `blog_length`

```python
def router_node(state: GraphState) -> GraphState:
    """Determine blog generation mode."""
    topic = state["topic"]
    blog_length = state.get("blog_length", "medium")
    blog_format = state.get("blog_format", "standard")
    
    # Listicles benefit from more research
    if blog_format == "listicle":
        mode = "hybrid"  # More structured research
    
    # Long-form content needs deeper research
    elif blog_length == "long":
        mode = "open_book"  # Extensive research
    
    # Short articles can skip research
    elif blog_length == "short":
        mode = "closed_book"  # Knowledge-based only
    
    else:
        mode = "hybrid"  # Default
    
    state["mode"] = mode
    return state
```

### Orchestrator/Planner Node Enhancement
**Current**: Creates blog structure
**Opportunity**: Tailor plan format based on `blog_format` preference

```python
def plan_node(state: GraphState) -> GraphState:
    """Create blog plan matching user's format preference."""
    blog_format = state.get("blog_format", "standard")
    
    # Add format-specific instructions to prompt
    format_instructions = {
        "standard": "Create a well-structured blog with introduction, body, conclusion.",
        "seo-optimized": "Create blog optimized for search engines: include target keywords, meta descriptions, header hierarchy.",
        "listicle": "Create numbered or bulleted list format: e.g., '5 Ways to...', '10 Tips for...'",
        "how-to": "Create step-by-step guide format with clear, actionable steps.",
        "opinion": "Create thought-provoking opinion piece with strong voice and perspective."
    }
    
    instruction = format_instructions.get(blog_format, format_instructions["standard"])
    
    # Use in prompts when generating plan
    # ... pass instruction to LLM prompt ...
    
    return state
```

### Writer Node Enhancement
**Current**: Generates section content
**Opportunity**: Adjust tone, complexity, and structure based on preferences

```python
def writer_node(state: GraphState) -> GraphState:
    """Generate blog sections with preference-aware prompting."""
    tone = state.get("tone", "educational")
    target_audience = state.get("target_audience", "general")
    blog_length = state.get("blog_length", "medium")
    
    # Calculate word budget per section
    length_budget = {
        "short": (500, 800),
        "medium": (1000, 1500),
        "long": (2000, 3000)
    }
    total_words = sum(length_budget[blog_length])
    words_per_section = total_words // len(state.get("plan", {}).get("sections", []))
    
    for section in state["plan"]["sections"]:
        # Build tone-specific prompt prefix
        tone_instructions = {
            "educational": "Explain clearly and comprehensively. Use examples and analogies.",
            "storytelling": "Use narrative and anecdotes. Engage readers emotionally.",
            "persuasive": "Make convincing arguments. Include CTAs and compelling evidence.",
            "technical": "Use precise terminology. Include code/diagrams where relevant.",
            "casual": "Use conversational tone. Be friendly and approachable."
        }
        
        # Build audience-specific prompt prefix
        audience_instructions = {
            "beginner": "Assume no prior knowledge. Explain terminology.",
            "intermediate": "Assume some familiarity. Focus on depth.",
            "expert": "Assume deep expertise. Skip basics, focus on nuances.",
            "general": "Balance accessibility with depth."
        }
        
        # Combine with word count target
        prompt = f"""
        {tone_instructions[tone]}
        {audience_instructions[target_audience]}
        Generate section '{section['heading']}' in approximately {words_per_section} words.
        ...
        """
        
        # Generate with informed prompt
        # ...
    
    return state
```

### Editor/Reducer Node Enhancement
**Current**: Final pass and formatting
**Opportunity**: Adjust editing passes based on format and length

```python
def reducer_node(state: GraphState) -> GraphState:
    """Polish and finalize blog based on preferences."""
    blog_format = state.get("blog_format", "standard")
    
    final_markdown = state.get("final_markdown", "")
    
    # Format-specific post-processing
    if blog_format == "seo-optimized":
        # Add SEO meta info
        final_markdown = add_seo_metadata(final_markdown)
        # Ensure keyword density
        final_markdown = optimize_keywords(final_markdown)
    
    elif blog_format == "listicle":
        # Ensure numbered list format
        final_markdown = enforce_listicle_format(final_markdown)
    
    elif blog_format == "how-to":
        # Ensure step numbering and clarity
        final_markdown = enforce_how_to_format(final_markdown)
    
    state["final_markdown"] = final_markdown
    return state
```

---

## 🔊 Using the Progress Callback

Nodes can report progress to streaming updates:

```python
def research_node(state: GraphState) -> GraphState:
    """Research topic with progress updates."""
    callback = state.get("progress_callback")
    
    # Start research
    if callback:
        callback("research", {"status": "Searching for sources..."})
    
    research_data = search_topic(state["topic"])
    
    # Update progress
    if callback:
        callback("research", {
            "status": f"Found {len(research_data)} sources",
            "research_data": research_data
        })
    
    state["research_data"] = research_data
    return state
```

---

## 💾 Multi-LLM Support in Nodes

Nodes automatically use the correct LLM based on provider preference:

```python
from backend.config import get_llm

def any_node(state: GraphState) -> GraphState:
    """Example node using LLM with fallback support."""
    
    # Get LLM respecting user's provider choice
    llm_provider = state.get("llm_provider", "auto")
    llm = get_llm(temperature=0.7, provider=llm_provider)
    
    # Use LLM normally - fallback handled internally
    response = llm.invoke("Generate blog section...")
    
    return state
```

---

## 🎯 Priority Implementation Order

### High Priority (Core UX)
1. **Router Node**: Adjust mode selection based on `blog_format`
2. **Planner Node**: Include format-specific structure in plan
3. **Writer Nodes**: Use tone + audience in section generation

### Medium Priority (Refinement)
4. **Editor Node**: Format-specific post-processing
5. **Research Node**: Add progress callback updates
6. **Orchestrator**: Advanced preference handling

### Low Priority (Polish)
7. **Image Node**: Use preferences for image descriptions
8. **Error Handling**: Preference-aware recovery strategies

---

## 🧪 Testing New Features

### Test 1: Verify Cache Hits
```python
# Turn OFF "⚡ Real-time Streaming" in sidebar
# Generate blog with same topic/preferences twice
# Second generation should show ⚡ (cached) badge
```

### Test 2: Verify Streaming
```python
# Turn ON "⚡ Real-time Streaming" in sidebar
# Generate blog
# Should see progress updates and plan/section updates
```

### Test 3: Verify Preferences Are Passed
```python
# In any node, add debugging:
print(f"Blog length: {state.get('blog_length')}")
print(f"Format: {state.get('blog_format')}")
print(f"Tone: {state.get('tone')}")
print(f"Audience: {state.get('target_audience')}")

# Generate blog with different settings
# Verify values appear in logs
```

### Test 4: Verify Multi-LLM Fallback
```python
# Stop Ollama service
# Set OPENAI_API_KEY in .env
# Select LLM Provider = "auto"
# Generate blog
# Should fallback to OpenAI without error
```

---

## 📚 References

- [GraphState Definition](backend/models.py)
- [Config & LLM Details](backend/config.py)
- [Service Layer](backend/service.py)
- [UI Integration](app.py)
- [Main Guide](IMPROVEMENTS_GUIDE.md)

---

## ❓ Questions?

Each node can independently decide how to utilize these new fields. The system is designed to **gracefully degrade** - if a node doesn't use a preference field, generation still works fine with default behavior.

**The key principle**: Preferences enrich the generation process but don't break existing logic.

