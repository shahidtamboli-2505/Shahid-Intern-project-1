# backend/scraper.py
# SINGLE SOURCE ONLY: Google Places API (New)
# ✅ No IndiaMART
# ✅ No data.gov.in
# ✅ No Justdial/TradeIndia
# Uses GOOGLE_PLACES_API_KEY env var (supports .env auto-load)

from __future__ import annotations

import os
import json
import time
from typing import Dict, List, Tuple, Any, Optional, Set

import requests

from backend.config import TOP_N_CAP  # extra safety alignment (optional)

RAW_DIR = os.path.join("data", "raw")

# ✅ HARD MAX = 100 (as per requirement)
MAX_CAP_RESULTS = 100

# default if caller doesn't pass
DEFAULT_MAX_RESULTS = 40

# Google Places typically returns up to 20 per page
GOOGLE_PAGE_SIZE = 20

# Request settings (safe defaults)
HTTP_TIMEOUT_SECS = int(os.getenv("CASE1_HTTP_TIMEOUT_SECS", "25"))
REGION_CODE = os.getenv("CASE1_REGION_CODE", "IN").strip() or "IN"
LANG_CODE = os.getenv("CASE1_LANGUAGE_CODE", "en").strip() or "en"

# light retry for transient API hiccups
MAX_RETRIES = int(os.getenv("CASE1_HTTP_RETRIES", "2"))


def _ensure_raw_dir() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)


def _load_dotenv_if_present() -> None:
    """
    Auto-load .env from project root if present.
    Works even if user didn't set env vars in terminal.
    No extra dependency needed.
    """
    try:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        env_path = os.path.join(root, ".env")
        if not os.path.exists(env_path):
            return

        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        return


def _clamp_max_results(max_results: int) -> int:
    """
    Hard cap:
      - project requirement: <= 100
      - optional config TOP_N_CAP (if lower)
    """
    try:
        n = int(max_results)
    except Exception:
        n = DEFAULT_MAX_RESULTS
    if n <= 0:
        n = DEFAULT_MAX_RESULTS

    # requirement cap 100
    n = min(n, MAX_CAP_RESULTS)

    # if TOP_N_CAP exists and is lower, respect it too
    try:
        n = min(n, int(TOP_N_CAP))
    except Exception:
        pass

    return n


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if not s:
            return None
        return int(float(s))
    except Exception:
        return None


def _post_with_retry(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return requests.post(url, headers=headers, json=payload, timeout=HTTP_TIMEOUT_SECS)
        except Exception as e:
            last_err = e
            # small backoff
            time.sleep(0.8 * attempt)
    raise RuntimeError(f"❌ Google Places request failed after {MAX_RETRIES} retries: {last_err}")


def scrape_google_places(
    query: str,
    location: str = "",
    place: str = "",
    max_results: int = DEFAULT_MAX_RESULTS,
    debug: bool = True,
) -> List[Dict[str, Any]]:
    _load_dotenv_if_present()  # ✅ allow .env

    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("❌ Missing env var GOOGLE_PLACES_API_KEY (set in terminal or .env)")

    max_results = _clamp_max_results(max_results)

    text_query = " ".join([query or "", place or "", location or ""]).strip()
    if not text_query:
        return []

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # ✅ nextPageToken is NOT under places.* in field mask
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.websiteUri,"
            "places.types,"
            "places.rating,"
            "places.userRatingCount,"
            "places.googleMapsUri,"
            "nextPageToken"
        ),
    }

    out: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    page_token: Optional[str] = None
    page_no = 0

    while len(out) < max_results:
        page_no += 1
        remaining = max_results - len(out)
        page_size = min(GOOGLE_PAGE_SIZE, remaining)

        payload: Dict[str, Any] = {
            "textQuery": text_query,
            "regionCode": REGION_CODE,
            "languageCode": LANG_CODE,
            "pageSize": page_size,
        }

        if page_token:
            payload["pageToken"] = page_token
            # ✅ Google token becomes valid after a short delay
            time.sleep(2.0)

        r = _post_with_retry(url, headers, payload)

        if r.status_code != 200:
            msg = r.text
            try:
                j = r.json()
                if isinstance(j, dict) and "error" in j:
                    msg = str(j["error"])
            except Exception:
                pass
            raise RuntimeError(f"❌ Google Places API failed | status={r.status_code} | {msg}")

        js = r.json()
        places = js.get("places", []) or []
        next_token = (js.get("nextPageToken") or "").strip()

        if debug:
            print(
                f"[GOOGLE] page={page_no} places={len(places)} next_token={'YES' if next_token else 'NO'} | query: {text_query}"
            )

        added_this_page = 0
        for p in places:
            pid = (p.get("id") or "").strip()
            if pid and pid in seen_ids:
                continue

            dn = p.get("displayName") or {}
            name = (dn.get("text") if isinstance(dn, dict) else str(dn)).strip()

            addr = (p.get("formattedAddress") or "").strip()
            phone = (p.get("nationalPhoneNumber") or "").strip()
            website = (p.get("websiteUri") or "").strip()

            # ✅ Case-2 base fields
            rating_val = _safe_float(p.get("rating"))
            count_val = _safe_int(p.get("userRatingCount"))
            has_website = bool(website)

            types = p.get("types") or []
            raw_cat = str(types[0]) if isinstance(types, list) and types else ""

            # ✅ cleaner source link
            maps_uri = (p.get("googleMapsUri") or "").strip()
            source_url = maps_uri or (f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else "")

            out.append(
                {
                    # Basic identity
                    "name": name,
                    "raw_category": raw_cat,
                    "address": addr,
                    "phone": phone,
                    "email": "",
                    "website": website,

                    # ✅ Case-2 base support
                    "has_website": has_website,
                    "google_rating": rating_val,
                    "google_rating_count": count_val,

                    # ✅ important for future deep-dive mapping
                    "google_place_id": pid,
                    "google_maps_uri": maps_uri,

                    # Source fields
                    "source_name": "google_places",
                    "source_url": source_url,
                }
            )

            if pid:
                seen_ids.add(pid)

            added_this_page += 1
            if len(out) >= max_results:
                break

        if len(out) >= max_results:
            break

        # If no new items came, or no token, stop
        if added_this_page == 0 or not next_token:
            break

        page_token = next_token

    if debug:
        print(f"[GOOGLE] ✅ total_collected={len(out)} (requested={max_results})")

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
        max_results=max_results,  # ✅ respects cap 100
        debug=debug,
    )

    out_path = os.path.join(RAW_DIR, f"raw_{run_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    if debug:
        print("[SCRAPER] ✅ GOOGLE ONLY MODE. raw_records:", len(raw))
        print("[SCRAPER] Saved raw:", out_path)

    return raw, out_path
