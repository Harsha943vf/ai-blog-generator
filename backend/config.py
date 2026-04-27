"""
Configuration module — centralizes LLM instantiation, API keys, and constants.
"""

from __future__ import annotations

import os
import logging
import warnings
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

try:
    from langchain_openai import ChatOpenAI
    HAS_OPENAI = True
except (ImportError, ModuleNotFoundError):
    HAS_OPENAI = False

# Suppress harmless resource warnings from unclosed sockets (Ollama HTTP client)
warnings.filterwarnings("ignore", category=ResourceWarning)

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("blog_gen")

# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------
# Tavily Search API (get free key at https://tavily.com)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
# OpenAI API key (optional fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# LLM — Ollama (local, unlimited usage) + Fallback support
# ---------------------------------------------------------------------------
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# User-selectable LLM provider (ollama, openai, auto)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()

def get_llm(temperature: float = 0.7, provider: str | None = None):
    """
    Return an LLM instance with intelligent fallback.
    
    Attempts:
      1. If provider == "ollama" or auto-detected: try Ollama first
      2. If Ollama fails or provider == "openai": try OpenAI
      3. Raise error if all fail
    """
    provider = provider or LLM_PROVIDER
    
    # Try Ollama first (if provider is "ollama" or "auto")
    if provider in ("ollama", "auto"):
        try:
            logger.info("Initializing Ollama LLM (model=%s)", OLLAMA_MODEL)
            return OllamaLLM(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=temperature,
                num_predict=4096,
                timeout=300.0,  # 5 min timeout for long generations
            )
        except Exception as e:
            logger.warning("Ollama initialization failed: %s", e)
            if provider == "ollama":
                raise
            # Fall through to try OpenAI if auto
    
    # Try OpenAI as fallback (if provider is "openai" or auto-fallback)
    if provider in ("openai", "auto") and HAS_OPENAI and OPENAI_API_KEY:
        try:
            logger.info("Falling back to OpenAI LLM")
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=OPENAI_API_KEY,
                temperature=temperature,
                max_tokens=4096,
                timeout=300.0,
            )
        except Exception as e:
            logger.warning("OpenAI initialization failed: %s", e)
            if provider == "openai" or (provider == "auto" and HAS_OPENAI and OPENAI_API_KEY):
                raise
    
    # No providers available
    raise RuntimeError(
        "No LLM provider available. Ensure Ollama is running or set OPENAI_API_KEY."
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

# Blog generation preferences
BLOG_LENGTH_OPTIONS = {"short": (500, 800), "medium": (1000, 1500), "long": (2000, 3000)}
BLOG_TONE_OPTIONS = ["educational", "storytelling", "persuasive", "technical", "casual"]
BLOG_FORMAT_OPTIONS = ["standard", "seo-optimized", "listicle", "how-to", "opinion"]
TARGET_AUDIENCE_OPTIONS = ["beginner", "intermediate", "expert", "general"]