# Structured Blog Generation Pipeline

## Overview

Your AI Blog Generator now supports a **strict 5-step structured pipeline** that generates blogs through carefully sequenced, non-parallel steps with plain text output.

```
Topic Input
    ↓
[1. ROUTER] - Classify topic and extract parameters
    ↓
[2. PLANNER] - Create blog structure in table format
    ↓
[3. RESEARCH] - Gather facts, statistics, insights
    ↓
[4. GENERATOR] - Write full blog following plan
    ↓
[5. EDITOR] - Polish and refine (structure-preserving)
    ↓
Final Blog Output
```

---

## Quick Start

### Run from Command Line

```bash
python structured_blog_demo.py "Your blog topic here"
```

Example:
```bash
python structured_blog_demo.py "Quantum Computing Explained"
python structured_blog_demo.py "How to Learn Machine Learning"
python structured_blog_demo.py "The Future of AI"
```

### Output

The demo script will:
1. Execute all 5 steps sequentially
2. Display each step's output in real-time
3. Save the complete output to `structured_blog_output.txt`
4. Show elapsed time

---

## Step Details

### STEP 1: ROUTER
**Purpose:** Classify the topic and determine writing parameters

**Output Format:**
```
STEP: Router

Task: blog
Topic: <your topic>
Tone: <informative/casual/professional/technical>
Depth: <short/medium/long>
```

**What it does:**
- Analyzes the topic
- Determines most appropriate tone
- Estimates required depth
- Sets baseline parameters

---

### STEP 2: PLANNER
**Purpose:** Create a structured outline in markdown table format

**Output Format:**
```
STEP: Planner

| Section No | Section Name | Description | Key Points Included |
|--|--|--|--|
| 1 | Introduction | ... | ... |
| 2 | ... | ... | ... |
```

**What it does:**
- Creates 5-8 sections tailored to the topic
- Provides clear descriptions for each section
- Lists key points to cover
- Ensures structure (Introduction → Body → Conclusion)

---

### STEP 3: RESEARCH
**Purpose:** Gather supporting facts, statistics, and insights

**Output Format:**
```
STEP: Research

Key Facts:
- Fact 1
- Fact 2

Statistics:
- Statistic 1

Insights:
- Insight 1

Search Queries Used:
- Query 1
```

**What it does:**
- Uses Tavily API to fetch real research data (if configured)
- Organizes findings into categories
- Provides source queries used
- Prepares data for the Generator step

---

### STEP 4: GENERATOR
**Purpose:** Write the complete blog following the Planner structure

**Output Format:**
```
STEP: Generator

# Blog Title

## Section 1 Name
Content (150-300 words)...

## Section 2 Name
Content (150-300 words)...

## ... (all sections)
```

**What it does:**
- Writes each section following the plan exactly
- Uses Research data where relevant
- Maintains consistent tone throughout
- Covers all bullet points from Planner
- Each section: 150-300 words

---

### STEP 5: EDITOR
**Purpose:** Polish and refine while preserving structure

**Output Format:**
```
STEP: Editor

# Blog Title

## Section 1 Name
Polished content...

## Section 2 Name
Polished content...

## ... (final sections)
```

**What it does:**
- Improves clarity and flow
- Fixes grammar and spelling
- Enhances examples
- Adds smooth transitions
- Ensures consistent formatting
- Makes content publication-ready

**Important:** Does NOT change structure or remove sections

---

## Programmatic Usage

### Using the Service

```python
from backend.structured_service import generate_structured_blog

result = generate_structured_blog("Your blog topic")

if result["status"] == "success":
    print(result["router_output"])
    print(result["planner_output"])
    print(result["research_output"])
    print(result["generator_output"])
    print(result["final_blog"])  # Clean markdown
    print(f"Time: {result['elapsed_seconds']}s")
else:
    print(f"Error: {result['error']}")
```

### Result Dictionary

```python
{
    "status": "success" | "error",
    "topic": "Your topic",
    "router_output": "STEP: Router\n...",
    "planner_output": "STEP: Planner\n...",
    "research_output": "STEP: Research\n...",
    "generator_output": "STEP: Generator\n...",
    "final_output": "STEP: Editor\n...",
    "final_blog": "# Title\n## Section\n...",  # Clean markdown
    "sections": ["Introduction", "Section 2", ...],
    "elapsed_seconds": 45.2,
}
```

---

## Configuration

### Environment Variables

```bash
# Tavily Search API (for Research step)
TAVILY_API_KEY=tvly_xxxxxx...

# Ollama (for LLM)
OLLAMA_MODEL=orca-mini
OLLAMA_BASE_URL=http://localhost:11434
```

### Get Tavily API Key

1. Visit https://tavily.com
2. Sign up (free)
3. Copy your API key
4. Add to `.env`:
   ```
   TAVILY_API_KEY=your_key_here
   ```

---

## Rules & Constraints

### Global Rules (STRICT)
- ✅ Each step executes sequentially (no parallelism)
- ✅ Output must be plain text (NO JSON)
- ✅ Each step starts with `STEP: <Name>`
- ✅ Do NOT skip, merge, or jump steps
- ✅ Planner is always TABLE format
- ✅ Generator follows Planner exactly
- ✅ Editor refines WITHOUT restructuring

### Generator Rules
- ✅ Follow section order EXACTLY
- ✅ Do NOT add/remove sections
- ✅ 150-300 words per section
- ✅ Use Research data where relevant
- ✅ Maintain consistent tone
- ✅ Cover all bullet points from Planner

### Editor Rules
- ✅ Improve clarity and flow only
- ✅ Do NOT change structure
- ✅ Do NOT remove sections
- ✅ Do NOT reorder content
- ✅ Fix grammar and spelling
- ✅ Enhance examples

---

## Troubleshooting

### Error: "Router failed to produce valid output"
- Check LLM connection (Ollama running?)
- Check model: `ollama list`
- Verify `.env` OLLAMA_MODEL setting

### Error: "Planner failed to extract sections"
- The planner didn't return a valid markdown table
- Check LLM output format
- Try simpler topic name

### Research returns no data
- Tavily API key not configured
- Check `.env` TAVILY_API_KEY
- API rate limit may be exceeded

### Generator output incomplete
- LLM may have timed out
- Increase timeout in config.py
- Try shorter topic

### Editor changes structure unexpectedly
- Instruct it: "Do NOT change structure"
- The prompt should prevent this
- Report if it happens

---

## Examples

### Example 1: Simple Topic
```bash
python structured_blog_demo.py "What is Machine Learning"
```

### Example 2: Technical Topic
```bash
python structured_blog_demo.py "Building Scalable APIs with Node.js"
```

### Example 3: Business Topic
```bash
python structured_blog_demo.py "How to Start a Tech Startup"
```

---

## Output Files

The demo script saves full output to:
- `structured_blog_output.txt` - Complete pipeline output (all 5 steps)

You can also programmatically access each step's output:
```python
result = generate_structured_blog("topic")
router_out = result["router_output"]
planner_out = result["planner_output"]
research_out = result["research_output"]
generator_out = result["generator_output"]
final_blog = result["final_blog"]  # Clean markdown
```

---

## Performance

Typical execution times (with Orca-Mini on 8GB Mac):
- Router: 2-3 seconds
- Planner: 3-4 seconds
- Research: 2-3 seconds (with Tavily API)
- Generator: 10-20 seconds
- Editor: 5-8 seconds

**Total: ~25-40 seconds** depending on topic complexity and content length.

---

## Integration with Streamlit App

To add a "Structured Mode" button to the Streamlit app:

```python
if st.button("🚀 Generate (Structured Mode)"):
    from backend.structured_service import generate_structured_blog
    result = generate_structured_blog(topic)
    if result["status"] == "success":
        st.write(result["router_output"])
        st.write(result["planner_output"])
        st.write(result["research_output"])
        st.write(result["generator_output"])
        st.markdown(result["final_blog"])
```

---

## Architecture

```
structured_service.py (service layer)
    ├─ structured_router_node()
    ├─ structured_planner_node()
    ├─ structured_research_node()
    ├─ structured_generator_node()
    └─ structured_editor_node()

structured_prompts.py (system prompts)
    ├─ STRUCTURED_ROUTER_PROMPT
    ├─ STRUCTURED_PLANNER_PROMPT
    ├─ STRUCTURED_RESEARCH_PROMPT
    ├─ STRUCTURED_GENERATOR_PROMPT
    └─ STRUCTURED_EDITOR_PROMPT

structured_blog_demo.py (CLI interface)
```

---

## Notes

- This is a **strict sequential pipeline** — no parallel processing
- Each step **builds upon previous outputs**
- **Plain text format** throughout (no JSON outputs)
- **Structure preservation** enforced (especially in Editor)
- **LangChain/LLM agnostic** — works with any LLM via config

---

For questions or issues, check the logs or review the structured prompts in `backend/structured_prompts.py`.
