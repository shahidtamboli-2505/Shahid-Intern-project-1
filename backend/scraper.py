# backend/scraper.py
# SINGLE SOURCE ONLY: Google Places API (New)
# ✅ No IndiaMART
# ✅ No data.gov.in
# ✅ No Justdial/TradeIndia
# Uses GOOGLE_PLACES_API_KEY env var

from __future__ import annotations

import os
import json
import time
from typing import Dict, List, Tuple, Any

import requests

RAW_DIR = os.path.join("data", "raw")
DEFAULT_MAX_RESULTS = 40


def _ensure_raw_dir() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)


def scrape_google_places(
    query: str,
    location: str = "",
    place: str = "",
    max_results: int = DEFAULT_MAX_RESULTS,
    debug: bool = True,
) -> List[Dict[str, Any]]:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("❌ Missing env var GOOGLE_PLACES_API_KEY")

    text_query = " ".join([query or "", place or "", location or ""]).strip()
    if not text_query:
        return []

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.websiteUri,"
            "places.types"
        ),
    }

    # ✅ Add region/language bias for India
    payload = {
        "textQuery": text_query,
        "regionCode": "IN",
        "languageCode": "en",
    }

    r = requests.post(url, headers=headers, json=payload, timeout=25)

    # ✅ If blocked/denied -> show exact reason
    if r.status_code != 200:
        msg = r.text
        try:
            j = r.json()
            # common google error format
            if isinstance(j, dict) and "error" in j:
                msg = str(j["error"])
        except Exception:
            pass
        raise RuntimeError(f"❌ Google Places API failed | status={r.status_code} | {msg}")

    js = r.json()
    places = js.get("places", []) or []

    if debug:
        print("[GOOGLE] status=200 places=", len(places), "| query:", text_query)

    out: List[Dict[str, Any]] = []
    for p in places[:max_results]:
        dn = p.get("displayName") or {}
        name = (dn.get("text") if isinstance(dn, dict) else str(dn)).strip()

        addr = (p.get("formattedAddress") or "").strip()
        phone = (p.get("nationalPhoneNumber") or "").strip()
        website = (p.get("websiteUri") or "").strip()
        types = p.get("types") or []
        raw_cat = str(types[0]) if isinstance(types, list) and types else ""

        pid = (p.get("id") or "").strip()
        source_url = f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else ""

        out.append({
            "name": name,
            "raw_category": raw_cat,
            "address": addr,
            "phone": phone,
            "email": "",
            "website": website,
            "source_name": "google_places",
            "source_url": source_url,
        })

    return out


def scrape_case1_to_raw(
    query: str,
    location: str = "",
    place: str = "",
    run_id: str = "",
    max_results: int = DEFAULT_MAX_RESULTS,
    debug: bool = True,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Pipeline entry used by agent_logic_case1.py
    Returns (raw_records, saved_json_path)
    """
    _ensure_raw_dir()

    if not run_id:
        run_id = str(int(time.time()))

    q = (query or "").strip()
    loc = (location or "").strip()
    plc = (place or "").strip()

    if not q:
        out_path = os.path.join(RAW_DIR, f"raw_{run_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return [], out_path

    raw = scrape_google_places(
        query=q,
        location=loc,
        place=plc,
        max_results=max_results,
        debug=debug,
    )

    out_path = os.path.join(RAW_DIR, f"raw_{run_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    if debug:
        print("[SCRAPER] ✅ GOOGLE ONLY MODE. raw_records:", len(raw))
        print("[SCRAPER] Saved raw:", out_path)

    return raw, out_path
