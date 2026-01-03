# backend/config.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os


# ---------------------------------------------------------
# Helper functions for environment variables
# ---------------------------------------------------------
def _env_int(key: str, default: int) -> int:
    try:
        return int(str(os.getenv(key, default)).strip())
    except Exception:
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(str(os.getenv(key, default)).strip())
    except Exception:
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    return str(os.getenv(key, str(default))).strip().lower() in {"true", "1", "yes", "y"}


def _env_str(key: str, default: str = "") -> str:
    try:
        return str(os.getenv(key, default) or default).strip()
    except Exception:
        return default


# ---------------------------------------------------------
# 🤖 Hugging Face LLM Settings (For Case 2 Agent)
# ---------------------------------------------------------
HUGGINGFACE_TOKEN = _env_str("HUGGINGFACE_TOKEN", "")  # Tumhara token .env mein dalega

# Model selection (choose one)
HF_MODEL_NAME = _env_str("HF_MODEL_NAME", "meta-llama/Llama-2-7b-chat-hf")
# Alternatives:
# "mistralai/Mistral-7B-Instruct-v0.2"  # Faster
# "microsoft/phi-2"  # Lightweight

# Model loading settings
USE_4BIT_QUANTIZATION = _env_bool("USE_4BIT_QUANTIZATION", True)  # RAM bachane ke liye
MAX_NEW_TOKENS = _env_int("MAX_NEW_TOKENS", 512)
LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", 0.7)

# Device settings (auto-detect karta hai)
FORCE_CPU = _env_bool("FORCE_CPU", False)  # True karo agar GPU nahi hai


# ---------------------------------------------------------
# 💡 NEW: Scraper Base Settings (Added as requested)
# ---------------------------------------------------------
REQUEST_TIMEOUT = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ---------------------------------------------------------
# Case 1: Search Settings (Google Places)
# ---------------------------------------------------------
DEFAULT_LOCATION = _env_str("DEFAULT_LOCATION", "Pune, Maharashtra")
DEFAULT_TOP_N = _env_int("DEFAULT_TOP_N", 20)

# ✅ UI hard cap (what user can request); scraper may have its own caps.
TOP_N_CAP = _env_int("TOP_N_CAP", 300)

# Google Places API key
GOOGLE_PLACES_API_KEY = _env_str("GOOGLE_PLACES_API_KEY", "")


# ---------------------------------------------------------
# Case 2: Leadership Extraction (Scraping-first)
# ---------------------------------------------------------
CASE2_ENABLED = _env_bool("CASE2_ENABLED", True)

# (Legacy) Output cap; some old modules still read this
CASE2_MAX_LEADERS = _env_int("CASE2_MAX_LEADERS", 5)

# Per-company timeout seconds (default ~25s)
CASE2_TIMEOUT_SECS = _env_int("CASE2_TIMEOUT_SECS", 25)

# (Legacy) Max pages to try (older scraper used this)
CASE2_MAX_PAGES = _env_int("CASE2_MAX_PAGES", 8)

# Max HTML bytes to keep per page (avoid huge pages)
CASE2_MAX_BYTES = _env_int("CASE2_MAX_BYTES", 900_000)

# UA for both requests + Playwright contexts
CASE2_USER_AGENT = _env_str(
    "CASE2_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
)

# Multiple User Agents for rotation (bot detection bypass)
USER_AGENTS_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# ---------------------------------------------------------
# 🤖 Agent Decision Making Settings
# ---------------------------------------------------------
AGENT_MAX_RETRIES = _env_int("AGENT_MAX_RETRIES", 3)
AGENT_RETRY_DELAY_MIN = _env_int("AGENT_RETRY_DELAY_MIN", 2)  # seconds
AGENT_RETRY_DELAY_MAX = _env_int("AGENT_RETRY_DELAY_MAX", 5)

# Alternate URL paths to try
AGENT_ALTERNATE_PATHS = _env_str(
    "AGENT_ALTERNATE_PATHS",
    "/about,/about-us,/team,/our-team,/leadership,/management,/people,/company"
).split(",")

# -----------------------------
# NEW: internal crawling controls (FINAL)
# -----------------------------
CASE2_MAX_INTERNAL_PAGES = _env_int("CASE2_MAX_INTERNAL_PAGES", 8)
CASE2_MAX_CRAWL_DEPTH = _env_int("CASE2_MAX_CRAWL_DEPTH", 2)
CASE2_MIN_CONFIDENCE = _env_float("CASE2_MIN_CONFIDENCE", 0.65)

# -----------------------------
# Optional toggles for fallbacks
# -----------------------------
CASE2_ENABLE_PLAYWRIGHT = _env_bool("CASE2_ENABLE_PLAYWRIGHT", True)
CASE2_PLAYWRIGHT_HEADLESS = _env_bool("CASE2_PLAYWRIGHT_HEADLESS", True)
CASE2_PLAYWRIGHT_NAV_TIMEOUT_MS = _env_int("CASE2_PLAYWRIGHT_NAV_TIMEOUT_MS", 20_000)
CASE2_PLAYWRIGHT_WAIT_UNTIL = _env_str("CASE2_PLAYWRIGHT_WAIT_UNTIL", "domcontentloaded")
CASE2_ENABLE_XHR = _env_bool("CASE2_ENABLE_XHR", True)

# Role keywords (comma-separated)
CASE2_ROLE_KEYWORDS = _env_str(
    "CASE2_ROLE_KEYWORDS",
    ",".join([
        "ceo", "chief executive", "founder", "co-founder", "managing director",
        "director", "owner", "president", "cto", "cfo", "chairman", "coo",
        "vp", "vice president", "head of", "principal", "dean", "chancellor",
        "vice chancellor", "registrar", "partner", "executive", "lead"
    ]),
)

# Discovery blocklist
CASE2_DISCOVERY_BLOCKLIST = _env_str(
    "CASE2_DISCOVERY_BLOCKLIST",
    ",".join([
        "privacy", "terms", "cookie", "careers", "jobs", "blog", "news",
        "press", "events", "webinar", "login", "signup", "register",
        "support", "help", "docs", "documentation", "pricing", "partners",
        "solutions", "products", "services"
    ]),
)


# ---------------------------------------------------------
# OpenAI (OPTIONAL fallback ONLY)
# ---------------------------------------------------------
OPENAI_API_KEY = _env_str("OPENAI_API_KEY", "")


# ---------------------------------------------------------
# Debugging & Reliability
# ---------------------------------------------------------
DEBUG_MODE = _env_bool("DEBUG_MODE", True)
MAX_RETRIES = _env_int("MAX_RETRIES", 2)


# ---------------------------------------------------------
# Legacy / Backward Compatibility (DO NOT TOUCH)
# ---------------------------------------------------------
CASE2_TOTAL_TIMEOUT_SECS = _env_int("CASE2_TOTAL_TIMEOUT_SECS", 600)
CASE2_MAX_SECONDARY_ORGS = _env_int("CASE2_MAX_SECONDARY_ORGS", 100)