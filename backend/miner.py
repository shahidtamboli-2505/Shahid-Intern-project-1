# backend/miner.py
# GOOGLE PLACES ONLY miner (clean + dedupe)
# ✅ Case-2 ready: Top Level Management placeholders + case2 payload slot

from __future__ import annotations

from typing import List, Dict, Any, Tuple
import re


def _norm_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _norm_phone(p: str) -> str:
    p = (p or "").strip()
    p = re.sub(r"[^\d+]", "", p)
    return p


def _norm_email(e: str) -> str:
    return (e or "").strip().lower()


def _norm_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    if u.startswith("www."):
        u = "https://" + u
    return u


def _has_website_fallback(w: str) -> bool:
    w = (w or "").strip()
    return bool(w) and ("." in w)


def _to_float(x):
    try:
        if x is None:
            return None
        s = str(x).strip()
        return float(s) if s else None
    except Exception:
        return None


def _to_int(x):
    try:
        if x is None:
            return None
        s = str(x).strip()
        return int(float(s)) if s else None
    except Exception:
        return None


def _infer_city_state_from_address(addr: str) -> Tuple[str, str]:
    a = (addr or "").strip()
    if not a:
        return "", ""
    parts = [p.strip() for p in a.split(",") if p.strip()]
    if len(parts) >= 2:
        state = re.sub(r"\b\d{6}\b", "", parts[-1]).strip()
        city = re.sub(r"\b\d{6}\b", "", parts[-2]).strip()
        return city, state
    return "", ""


def mine_case1_records(
    raw_records: List[Dict[str, Any]],
    gpt_client=None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Case-1 Miner (Google Places only)

    Case-2 READY:
    - Adds Top-Level Management columns (empty placeholders)
    - Adds `case2_management` + `case2_meta` slots (for backend fill)
    """

    cleaned: List[Dict[str, Any]] = []
    seen = set()

    for r in raw_records:
        name = _norm_text(r.get("name", ""))
        addr = _norm_text(r.get("address", ""))
        phone = _norm_phone(r.get("phone", ""))
        email = _norm_email(r.get("email", ""))
        website = _norm_url(r.get("website", ""))

        raw_cat = _norm_text(r.get("raw_category", "")) or "Business / Services"
        source_name = _norm_text(r.get("source_name", "google_places"))
        source_url = _norm_url(r.get("source_url", ""))

        rating = _to_float(r.get("google_rating"))
        rating_count = _to_int(r.get("google_rating_count"))

        has_web_flag = r.get("has_website")
        has_website_bool = has_web_flag if isinstance(has_web_flag, bool) else _has_website_fallback(website)
        has_website_str = "Yes" if has_website_bool else "No"

        if not name and not source_url:
            continue

        dedupe_key = (name.lower(), addr.lower(), phone, website.lower())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        city, state = _infer_city_state_from_address(addr)

        cleaned.append({
            # -----------------------------
            # Case-1 Core Fields
            # -----------------------------
            "Name": name or "Unknown",
            "Primary Category": raw_cat,
            "Address": addr,
            "City": city,
            "State": state,
            "Phone": phone,
            "Email": email,
            "Website": website,

            # Case-2 base fields (already decided)
            "Has Website": has_website_str,
            "Has Website (Bool)": has_website_bool,  # internal use (optional)
            "Google Rating": rating if rating is not None else "",
            "Google Rating Count": rating_count if rating_count is not None else "",

            "Source Name": source_name,
            "Source URL": source_url,

            # -----------------------------
            # Case-2 payload slots (NOT exported directly)
            # Excel utils will read `case2_management` and fill columns
            # -----------------------------
            "case2_management": {},   # {bucket: {name, designation, email, phone, linkedin}}
            "case2_meta": {},         # debug/meta like counts, pages visited etc.

            # -----------------------------
            # Case-2: Top Level Management (PLACEHOLDERS)
            # (kept for exam-safe / visible schema)
            # -----------------------------
            "Executive Name": "",
            "Executive Designation": "",
            "Executive Email": "",
            "Executive Phone": "",
            "Executive LinkedIn": "",

            "Tech/Ops Name": "",
            "Tech/Ops Designation": "",
            "Tech/Ops Email": "",
            "Tech/Ops Phone": "",
            "Tech/Ops LinkedIn": "",

            "Finance/Admin Name": "",
            "Finance/Admin Designation": "",
            "Finance/Admin Email": "",
            "Finance/Admin Phone": "",
            "Finance/Admin LinkedIn": "",

            "Business/Growth Name": "",
            "Business/Growth Designation": "",
            "Business/Growth Email": "",
            "Business/Growth Phone": "",
            "Business/Growth LinkedIn": "",

            "Marketing/Brand Name": "",
            "Marketing/Brand Designation": "",
            "Marketing/Brand Email": "",
            "Marketing/Brand Phone": "",
            "Marketing/Brand LinkedIn": "",
        })

    stats = {
        "raw_count": len(raw_records),
        "clean_count": len(cleaned),
        "with_website": sum(1 for x in cleaned if x.get("Has Website") == "Yes"),
        "with_rating": sum(1 for x in cleaned if str(x.get("Google Rating", "")).strip()),
    }

    return cleaned, stats
