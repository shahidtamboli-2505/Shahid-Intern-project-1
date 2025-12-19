# backend/config.py
# Case 1 + Case 2 — GOOGLE PLACES ONLY configuration
# 🔒 Exam-safe | Startup-ready | No hardcoded secrets

import os


def _env_int(key: str, default: int) -> int:
    try:
        return int(str(os.getenv(key, str(default))).strip())
    except Exception:
        return default


def _env_bool(key: str, default: str = "false") -> bool:
    return str(os.getenv(key, default)).strip().lower() == "true"


# =========================================================
# Case 1 — Primary Search (Google Places)
# =========================================================

DEFAULT_LOCATION = os.getenv("CASE1_DEFAULT_LOCATION", "India").strip()
DEFAULT_TOP_N = _env_int("CASE1_DEFAULT_TOP_N", 20)

# ✅ LOCKED: 100 max
TOP_N_CAP = _env_int("CASE1_TOP_N_CAP", 100)
TOP_N_CAP = max(1, min(TOP_N_CAP, 100))


# =========================================================
# Case 2 — Intelligence Layer (Website Leadership Extraction)
# =========================================================

# Master switch for Case-2 logic
CASE2_ENABLED = _env_bool("CASE2_ENABLED", "false")

# Names-only mode (no emails/phones/linkedin)
CASE2_NAMES_ONLY = _env_bool("CASE2_NAMES_ONLY", "true")

# ✅ Maximum leaders to output per org (1..5)
CASE2_MAX_LEADERS = _env_int("CASE2_MAX_LEADERS", 5)
CASE2_MAX_LEADERS = max(1, min(CASE2_MAX_LEADERS, 5))

# ✅ How many orgs to run Case-2 on (avoid long runs)
# Example: set CASE2_MAX_SECONDARY_ORGS=20
CASE2_MAX_SECONDARY_ORGS = _env_int("CASE2_MAX_SECONDARY_ORGS", 20)
CASE2_MAX_SECONDARY_ORGS = max(1, min(CASE2_MAX_SECONDARY_ORGS, 100))

# ✅ Overall time cap for Case-2 (prevents hanging forever)
# Example: set CASE2_TOTAL_TIMEOUT_SECS=90
CASE2_TOTAL_TIMEOUT_SECS = _env_int("CASE2_TOTAL_TIMEOUT_SECS", 90)
CASE2_TOTAL_TIMEOUT_SECS = max(20, min(CASE2_TOTAL_TIMEOUT_SECS, 600))


# =========================================================
# Case 2 — Website Scraping (Safe Defaults)
# =========================================================
# IMPORTANT:
# - Fast mode by default (startup UX)
# - You can override via ENV any time

# HTTP timeout for each request (fast default)
CASE2_TIMEOUT_SECS = _env_int("CASE2_TIMEOUT_SECS", 8)  # 12 -> 8
CASE2_TIMEOUT_SECS = max(4, min(CASE2_TIMEOUT_SECS, 25))

# Per website max pages to fetch
CASE2_MAX_PAGES = _env_int("CASE2_MAX_PAGES", 3)  # 6 -> 3
CASE2_MAX_PAGES = max(1, min(CASE2_MAX_PAGES, 10))

# Safety cap to avoid downloading huge pages
CASE2_MAX_BYTES = _env_int("CASE2_MAX_BYTES", 900000)  # 1500000 -> 900000
CASE2_MAX_BYTES = max(200000, min(CASE2_MAX_BYTES, 4000000))

# User-Agent (avoid getting blocked)
CASE2_USER_AGENT = os.getenv(
    "CASE2_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123 Safari/537.36",
).strip()


# =========================================================
# Google Places API
# =========================================================
# ❌ DO NOT hardcode API key here
# ✔ API key is read from environment variable in scraper.py
# Required:
#   GOOGLE_PLACES_API_KEY


# =========================================================
# GPT (OPTIONAL – DISABLED BY DEFAULT)
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
GPT_ENABLED = bool(OPENAI_API_KEY)
