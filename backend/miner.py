# backend/miner.py
# GOOGLE PLACES ONLY miner (clean + dedupe)
# ✅ Startup output schema (Excel-ready)
# ✅ Case-2 ready: keeps case2_leaders slot (list of dicts)
# ✅ Works with BOTH old scraper keys AND new scraper keys

from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional
import re


# -----------------------------
# Normalizers
# -----------------------------
def _norm_text(s: Any) -> str:
    s = "" if s is None else str(s)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _norm_url(u: Any) -> str:
    """
    Normalize website URL so scraper_case2 works reliably.
    - adds https:// if missing
    - converts www.* to https://www.*
    """
    u = _norm_text(u)
    if not u:
        return ""
    if u.startswith("www."):
        u = "https://" + u
    if not (u.startswith("http://") or u.startswith("https://")):
        # handle "example.com" style
        u = "https://" + u
    return u


def _to_float(x: Any) -> Optional[float]:
    if x in (None, ""):
        return None
    try:
        s = _norm_text(x).replace(",", "")
        return float(s) if s else None
    except Exception:
        return None


def _to_int(x: Any) -> Optional[int]:
    if x in (None, ""):
        return None
    try:
        s = _norm_text(x).replace(",", "")
        return int(float(s)) if s else None
    except Exception:
        return None


def _has_website_fallback(w: str) -> bool:
    w = _norm_text(w)
    return bool(w) and ("." in w)


def _infer_city_state_from_address(addr: str) -> Tuple[str, str]:
    a = _norm_text(addr)
    if not a:
        return "", ""
    parts = [p.strip() for p in a.split(",") if p.strip()]
    if len(parts) >= 2:
        state = re.sub(r"\b\d{6}\b", "", parts[-1]).strip()
        city = re.sub(r"\b\d{6}\b", "", parts[-2]).strip()
        return city, state
    return "", ""


def _as_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = _norm_text(v).lower()
    if s in {"yes", "true", "1"}:
        return True
    if s in {"no", "false", "0"}:
        return False
    return None


def _pick_first(*vals: Any) -> Any:
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return ""


# -----------------------------
# Case-2 leaders normalization
# -----------------------------
def _norm_leaders(value: Any) -> List[Dict[str, str]]:
    """
    Accepts:
      - [] (already ok)
      - {"leaders":[...]} wrapper
      - [{"name":..,"designation":..}, ...]
    Returns max 5 leaders.
    """
    if not value:
        return []

    if isinstance(value, dict) and "leaders" in value:
        value = value.get("leaders")

    if not isinstance(value, list):
        return []

    out: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        nm = _norm_text(item.get("name", ""))
        ds = _norm_text(item.get("designation", ""))
        if not nm:
            continue

        # strict: ignore contact-like garbage
        if "@" in nm or "@" in ds:
            continue

        out.append({"name": nm, "designation": ds})
        if len(out) >= 5:
            break
    return out


# -----------------------------
# Main miner
# -----------------------------
def mine_case1_records(
    raw_records: List[Dict[str, Any]],
    gpt_client=None,  # kept for future (unused)
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    FINAL output per company (Excel-friendly):
      Company Name, Industry,
      Google Rating, Rating Count,
      Has Website, Website URL,
      Leader 1..5 Name/Designation,
      Source Name, Source URL,
      (keeps case2_leaders slot)
    """
    cleaned: List[Dict[str, Any]] = []
    seen = set()

    for r in (raw_records or []):
        # identity
        company_name = _norm_text(_pick_first(r.get("company_name"), r.get("name"), r.get("Name")))
        industry = _norm_text(
            _pick_first(
                r.get("industry"),
                r.get("raw_category"),
                r.get("Primary Category"),
                r.get("Category"),
            )
        ) or "Business / Services"

        # website
        website = _norm_url(_pick_first(r.get("website_url"), r.get("website"), r.get("Website"), r.get("websiteUri")))

        # optional location
        addr = _norm_text(_pick_first(r.get("address"), r.get("Address"), r.get("formattedAddress")))

        # source
        source_name = _norm_text(_pick_first(r.get("source_name"), r.get("Source Name"), "Google Places"))
        source_url = _norm_url(_pick_first(r.get("source_url"), r.get("url"), r.get("Source URL"), r.get("googleMapsUri")))

        # IDs (best dedupe)
        place_id = _norm_text(_pick_first(r.get("google_place_id"), r.get("place_id"), r.get("id")))

        # rating
        rating = _to_float(_pick_first(r.get("google_rating"), r.get("Google Rating"), r.get("rating")))
        rating_count = _to_int(
            _pick_first(
                r.get("rating_count"),
                r.get("google_rating_count"),
                r.get("Google Rating Count"),
                r.get("userRatingCount"),
            )
        )

        # has website
        has_web_flag = _as_bool(_pick_first(r.get("has_website"), r.get("Has Website")))
        has_website_bool = has_web_flag if has_web_flag is not None else _has_website_fallback(website)
        has_website_str = "Yes" if has_website_bool else "No"

        # leaders (Case-2)
        leaders = _norm_leaders(_pick_first(r.get("case2_leaders"), r.get("leaders")))

        if not company_name and not source_url and not place_id:
            continue

        # Dedup:
        # 1) prefer place_id if present
        # 2) else use company_name + website + address
        if place_id:
            dedupe_key = ("pid", place_id.lower())
        else:
            dedupe_key = ("fallback", company_name.lower(), website.lower(), addr.lower())

        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        city, state = _infer_city_state_from_address(addr)

        # Flatten leaders to fixed cols
        leader_cols: Dict[str, Any] = {}
        for i in range(5):
            nm = leaders[i]["name"] if i < len(leaders) else ""
            ds = leaders[i]["designation"] if i < len(leaders) else ""
            leader_cols[f"Leader {i+1} Name"] = nm
            leader_cols[f"Leader {i+1} Designation"] = ds

        cleaned.append(
            {
                "Company Name": company_name or "Unknown",
                "Industry": industry,

                "Google Rating": rating if rating is not None else "",
                "Rating Count": rating_count if rating_count is not None else "",

                "Has Website": has_website_str,
                "Website URL": website,

                # optional (safe)
                "Address": addr,
                "City": city,
                "State": state,

                **leader_cols,

                "Source Name": source_name,
                "Source URL": source_url,

                # keep internal slots
                "google_place_id": place_id,
                "case2_leaders": leaders,
            }
        )

    stats = {
        "raw_count": len(raw_records or []),
        "clean_count": len(cleaned),
        "with_website": sum(1 for x in cleaned if x.get("Has Website") == "Yes"),
        "no_website": sum(1 for x in cleaned if x.get("Has Website") == "No"),
        "with_rating": sum(1 for x in cleaned if str(x.get("Google Rating", "")).strip()),
        "with_any_leaders": sum(
            1
            for x in cleaned
            if any(str(x.get(f"Leader {i} Name", "")).strip() for i in range(1, 6))
        ),
    }

    return cleaned, stats
