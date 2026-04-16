"""
Configuration module — centralizes LLM instantiation, API keys, and constants.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("blog_gen")

# ---------------------------------------------------------------------------
# API keys — No longer needed! Using local Ollama
# ---------------------------------------------------------------------------
# Ollama runs locally on http://localhost:11434
# No API keys required.

# ---------------------------------------------------------------------------
# LLM — Ollama (local, unlimited usage)
# ---------------------------------------------------------------------------
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_llm(temperature: float = 0.7):
    """Return an OllamaLLM instance (runs locally, no API key needed)."""
    return OllamaLLM(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_predict=4096,
    )

# ---------------------------------------------------------------------------
# Pipeline constants
# ---------------------------------------------------------------------------
MAX_RETRIES = 3
RETRY_DELAY = 2          # seconds
REQUEST_TIMEOUT = 60     # seconds
MIN_WORD_COUNT = 800
MAX_WORD_COUNT = 2000
CACHE_TTL = 3600          # 1 hour