# backend/config.py
# Case 1 + Case 2 — GOOGLE PLACES ONLY configuration
# 🔒 Exam-safe | Future-ready | No hardcoded secrets

import os


# =========================================================
# Case 1 — Primary Search (Google Places)
# =========================================================

# Default location if user does not provide one in UI
DEFAULT_LOCATION = os.getenv("CASE1_DEFAULT_LOCATION", "India").strip()

# Default number of results (Top-N) shown/exported
DEFAULT_TOP_N = int(os.getenv("CASE1_DEFAULT_TOP_N", "20"))

# Absolute safety cap (UI + backend should respect this)
# NOTE: Even if user enters more, backend must clamp
TOP_N_CAP = int(os.getenv("CASE1_TOP_N_CAP", "200"))


# =========================================================
# Case 2 — Intelligence Layer (BASE CONFIG)
# =========================================================

# Master switch for Case-2 logic (env controlled)
# Example:
#   set CASE2_ENABLED=true
CASE2_ENABLED = os.getenv("CASE2_ENABLED", "false").lower() == "true"

# Enable deeper secondary search (website / team pages)
# ❌ Disabled by default for safety
CASE2_ENABLE_SECONDARY_SEARCH = (
    os.getenv("CASE2_ENABLE_SECONDARY_SEARCH", "false").lower() == "true"
)

# Time window (hours) to limit deep scraping per organization
CASE2_TIME_WINDOW_HOURS = int(os.getenv("CASE2_TIME_WINDOW_HOURS", "72"))

# Maximum organizations allowed for secondary (deep) analysis
# Prevents over-scraping
CASE2_MAX_SECONDARY_ORGS = int(os.getenv("CASE2_MAX_SECONDARY_ORGS", "50"))


# ---------------------------------------------------------
# Top-Level Management (Normalization Rules)
# ---------------------------------------------------------

# Always extract only a fixed number of leadership roles
CASE2_MAX_MANAGEMENT_ROLES = int(os.getenv("CASE2_MAX_MANAGEMENT_ROLES", "5"))

# Fixed leadership buckets (DOCUMENT-ALIGNED)
# ⚠️ Do not change order unless document is updated
CASE2_MANAGEMENT_ROLES = [
    "Executive Leadership",
    "Technology / Operations",
    "Finance / Administration",
    "Business Development / Growth",
    "Marketing / Branding",
]


# =========================================================
# Case 2 — Website Scraping (Safe Defaults)
# =========================================================

# HTTP timeout for each request
CASE2_TIMEOUT_SECS = int(os.getenv("CASE2_TIMEOUT_SECS", "12"))

# Per website max pages to fetch (team/about/leadership)
CASE2_MAX_PAGES = int(os.getenv("CASE2_MAX_PAGES", "6"))

# Safety cap to avoid downloading huge pages
CASE2_MAX_BYTES = int(os.getenv("CASE2_MAX_BYTES", "1500000"))

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
#
# Required env var:
#   GOOGLE_PLACES_API_KEY
#
# Example (PowerShell):
#   $env:GOOGLE_PLACES_API_KEY="YOUR_API_KEY"


# =========================================================
# GPT (OPTIONAL – DISABLED BY DEFAULT)
# =========================================================

# GPT config kept only for architectural completeness
# GPT calls are NOT used in current project

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# GPT is considered enabled ONLY if key exists
GPT_ENABLED = bool(OPENAI_API_KEY)
