# ✍️ AI Blog Generator

A production-grade, multi-stage AI blog generation system built with **LangGraph**, **Grok (xAI)**, **Tavily**, and **Google Gemini**.

## Architecture

```
START → Router → [Research] → Orchestrator → Workers → Reducer → [Images] → END
```

| Node | Purpose |
|------|---------|
| **Router** | Classifies topic complexity, infers domain/tone/audience, picks pipeline mode |
| **Research** | Fetches, deduplicates, and summarizes web sources via Tavily |
| **Orchestrator** | Creates a structured section-by-section blog plan |
| **Workers** | Generate each section in parallel (ThreadPoolExecutor) |
| **Reducer** | Merges sections into a polished, flowing markdown blog |
| **Images** | Generates illustrations via Google Gemini Imagen (optional) |

### Pipeline Modes

| Mode | Trigger | Research Depth |
|------|---------|----------------|
| `closed_book` | Simple / well-known topics | None |
| `hybrid` | Moderate complexity | Top 3 sources |
| `open_book` | Complex / data-heavy / evolving | 5–8 sources |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env   # or edit .env directly
# Set: GROK_API_KEY, TAVILY_API_KEY, GOOGLE_API_KEY

# 3. Run
streamlit run app.py
```

## Project Structure

```
project/
├── app.py                  # Streamlit frontend
├── backend/
│   ├── config.py           # LLM setup, API keys, constants
│   ├── models.py           # GraphState definition
│   ├── utils.py            # Retry, JSON parsing, caching
│   ├── pipeline.py         # LangGraph wiring
│   ├── service.py          # Public generate_blog() API
│   └── nodes/
│       ├── router.py       # Topic classification
│       ├── research.py     # Tavily web research
│       ├── orchestrator.py # Blog planning
│       ├── worker.py       # Section writing
│       ├── reducer.py      # Section merging
│       └── images.py       # Gemini image generation
├── images/                 # Generated images saved here
├── .env                    # API keys (not committed)
├── requirements.txt
└── README.md
```

## Domain Adaptation

The system automatically adapts to **any** topic domain:

- **Tech** → precise, structured, educational tone
- **Finance** → clear, analytical, cautious language
- **Travel** → descriptive, engaging storytelling
- **Health** → educational, evidence-based writing
- **Lifestyle** → conversational, relatable voice
- **Business** → persuasive, professional analysis

## Reliability

- All LLM calls wrapped with automatic retry (3 attempts)
- Research failure → graceful fallback to closed_book mode
- Image generation failure → blog returned without images
- Results cached in-memory (1-hour TTL)
- Structured logging throughout the pipeline

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROK_API_KEY` | Yes | xAI Grok API key |
| `TAVILY_API_KEY` | For research | Tavily search API key |
| `GOOGLE_API_KEY` | For images | Google AI API key (Gemini) |
| `GROK_MODEL` | No | Model name (default: `grok-3-mini-beta`) |
