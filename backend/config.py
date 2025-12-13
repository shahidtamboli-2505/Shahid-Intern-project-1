# backend/config.py
# Case 1 — GOOGLE PLACES ONLY configuration

import os

# -----------------------------
# Case 1 defaults
# -----------------------------
# Fallback location if UI empty
DEFAULT_LOCATION = os.getenv("CASE1_DEFAULT_LOCATION", "India")

# -----------------------------
# Google Places API
# -----------------------------
# ❌ DO NOT hardcode API key here
# ✔ It is read from environment variable in scraper.py
#
# Required env var:
#   GOOGLE_PLACES_API_KEY
#
# Example (PowerShell):
#   $env:GOOGLE_PLACES_API_KEY="YOUR_KEY"

# -----------------------------
# GPT (OPTIONAL, disabled by default)
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# GPT enabled only if key exists
GPT_ENABLED = bool(OPENAI_API_KEY)
