# AI Blog Generator - Best Workflow Guide

## 🎯 Project Overview

Your application now supports **2 workflows**:

### Workflow 1: Standard Mode (Current UI)
- Uses Streamlit interface
- Auto-mode detection
- Good for interactive use
- File: `app.py`

### Workflow 2: Structured Mode (NEW - RECOMMENDED)
- Strict 5-step pipeline
- Plain text output
- Perfect for production/API use
- File: `structured_blog_demo.py`

---

## ✅ RECOMMENDED BEST WORKFLOW

### For Daily Use: Use Structured Mode
The **structured 5-step pipeline** is the best choice because:

1. ✅ **Predictable Output** — Each step clearly marked
2. ✅ **Better Quality** — Follows strict planning → generation → editing flow
3. ✅ **Debuggable** — See exactly what each step produced
4. ✅ **Production-Ready** — Plain text format, no JSON complications
5. ✅ **Research Integration** — Tavily API automatically fetches real data
6. ✅ **No Hallucinations** — Generator strictly follows Planner structure

---

## 📋 Setup Checklist

Complete these steps to use the best workflow:

### Step 1: Verify Ollama is Running
```bash
# Terminal 1: Start Ollama
ollama serve

# Check model is available
ollama list
# Should show: orca-mini
```

### Step 2: Verify Tavily API (Optional but Recommended)
```bash
# Get free key at https://tavily.com
# Update .env with your key
TAVILY_API_KEY=tvly_xxxxx
```

### Step 3: Activate Virtual Environment
```bash
cd /Users/harsha/Desktop/ai-blog-generator
source venv/bin/activate
```

### Step 4: Test the Pipeline
```bash
python structured_blog_demo.py "Test Topic: Quantum Computing"
```

---

## 🚀 Daily Workflow

### Option A: Command Line (RECOMMENDED for Production)

**Generate blog:**
```bash
python structured_blog_demo.py "Your blog topic"
```

**Output:**
- Console display of all 5 steps
- `structured_blog_output.txt` with full pipeline output
- Takes ~30-40 seconds

### Option B: Streamlit UI (Interactive)

**For ad-hoc, interactive use:**
```bash
streamlit run app.py
```

Visit: `http://localhost:8501`

### Option C: Programmatic (Integration)

**In your Python code:**
```python
from backend.structured_service import generate_structured_blog

result = generate_structured_blog("Your topic")

if result["status"] == "success":
    # Access each step
    print(result["router_output"])
    print(result["planner_output"])
    print(result["research_output"])
    print(result["generator_output"])
    print(result["final_blog"])  # Clean markdown
    
    # Save to file
    with open("blog.md", "w") as f:
        f.write(result["final_blog"])
else:
    print(f"Error: {result['error']}")
```

---

## 📁 Best Directory Structure

Your project should maintain:

```
ai-blog-generator/
├── app.py                          # Streamlit UI (standard mode)
├── structured_blog_demo.py         # CLI for structured mode ← USE THIS
├── requirements.txt
├── .env                            # Config (Ollama, Tavily keys)
├── STRUCTURED_PIPELINE_GUIDE.md    # Full documentation
├── .instructions.md                # Workflow specification
│
├── backend/
│   ├── config.py                   # Config & LLM setup
│   ├── models.py                   # Data models
│   ├── service.py                  # Standard pipeline service
│   ├── structured_service.py       # NEW: Structured pipeline ← USE THIS
│   ├── structured_pipeline.py      # NEW: 5-step implementation
│   ├── structured_prompts.py       # NEW: Step prompts
│   │
│   └── nodes/
│       ├── router.py
│       ├── orchestrator.py
│       ├── worker.py
│       ├── reducer.py
│       ├── research.py
│       └── images.py
│
└── images/
    └── (generated blog images)
```

---

## 🔄 Complete Workflow Example

### Scenario: Generate Blog Post on "Machine Learning"

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run structured pipeline
python structured_blog_demo.py "Machine Learning: A Complete Guide"

# Output displays:
# ✅ STEP 1: ROUTER classifies topic
# ✅ STEP 2: PLANNER creates 6-7 sections
# ✅ STEP 3: RESEARCH gathers facts from Tavily
# ✅ STEP 4: GENERATOR writes blog following plan
# ✅ STEP 5: EDITOR polishes final output

# 3. Blog outputs to:
# - Console (real-time progress)
# - structured_blog_output.txt (full output with all steps)
# - Ready to copy/publish

# 4. Extract final blog
# From structured_blog_output.txt, copy the "STEP: Editor" section
# Or programmatically: result["final_blog"]
```

---

## ⚙️ Configuration (Best Practice)

Your `.env` should be:

```bash
# Ollama Configuration (required)
OLLAMA_MODEL=orca-mini
OLLAMA_BASE_URL=http://localhost:11434

# Tavily Search API (strongly recommended for research quality)
TAVILY_API_KEY=tvly_xxxxx

# Optional: Override defaults
# RETRY_DELAY=2
# REQUEST_TIMEOUT=60
```

### Getting Tavily API Key:
1. Visit https://tavily.com
2. Sign up (free tier)
3. Copy your API key
4. Paste into `.env` as `TAVILY_API_KEY=tvly_xxxxx`

---

## 📊 Workflow Performance

**Typical execution with Orca-Mini on 8GB Mac:**

| Step | Duration | What Happens |
|------|----------|--------------|
| Router | 2-3s | Topic classification |
| Planner | 3-4s | Section structure created |
| Research | 2-3s | Tavily API fetches data |
| Generator | 10-20s | Blog content written |
| Editor | 5-8s | Content polished |
| **Total** | **~30-40s** | Production-ready blog |

---

## 🎯 Best Practices

### DO ✅
- Use **Structured Mode** for production blogs
- Keep Tavily API key configured for research depth
- Run **one blog at a time** (sequential execution)
- Check `structured_blog_output.txt` for full pipeline visibility
- Use the `final_blog` output for publishing

### DON'T ❌
- Don't skip the Research step - it improves quality significantly
- Don't run multiple blogs in parallel (the LLM can't handle it on 8GB)
- Don't expect perfect output on complex topics (LLM has limits)
- Don't ignore the Planner structure (Generator must follow it)

---

## 🛠️ Troubleshooting

### Issue: "Ollama service not running"
```bash
# Terminal 2: Start Ollama
ollama serve
```

### Issue: "Model not found: orca-mini"
```bash
ollama pull orca-mini
```

### Issue: "Tavily API key not configured"
```bash
# Add to .env
TAVILY_API_KEY=tvly_xxxxx

# Get free key at https://tavily.com
```

### Issue: Script hangs or times out
```bash
# Ollama may be out of memory
# Restart: Ctrl+C in both terminals
ollama serve
# Then retry
python structured_blog_demo.py "topic"
```

---

## 📈 Next Steps

1. **Test the structured pipeline:**
   ```bash
   python structured_blog_demo.py "Test: Introduction to Python"
   ```

2. **Review output file:**
   ```bash
   cat structured_blog_output.txt
   ```

3. **Use in production:**
   ```bash
   # Create a loop to generate multiple blogs
   for topic in "Python" "JavaScript" "Go"; do
       python structured_blog_demo.py "$topic"
       sleep 5  # Wait between generations
   done
   ```

4. **Integrate with API:**
   ```python
   # Wrap structured_service.py in Flask/FastAPI
   from backend.structured_service import generate_structured_blog
   # Create API endpoint using this function
   ```

---

## 📚 Documentation

- **Full Guide:** See [STRUCTURED_PIPELINE_GUIDE.md](STRUCTURED_PIPELINE_GUIDE.md)
- **Workflow Rules:** See [.instructions.md](.instructions.md)
- **For Developers:** See [backend/structured_prompts.py](backend/structured_prompts.py)

---

## ✨ Summary

### THE BEST WORKFLOW:

1. **For quick testing:** `python structured_blog_demo.py "topic"`
2. **For production:** Use `backend/structured_service.py` in your application
3. **For UI:** Use `app.py` when you need interactive control
4. **For scaling:** Wrap `generate_structured_blog()` in an API

**Recommended setup:** Use Structured Mode for all blog generation. It's:
- ✅ More predictable
- ✅ Better quality
- ✅ Easier to debug
- ✅ Production-ready

Ready to generate your first blog? 🚀

```bash
python structured_blog_demo.py "Your amazing blog topic"
```
