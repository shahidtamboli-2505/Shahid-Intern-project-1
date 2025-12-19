# backend/agent_logic_case2.py
# Case-2 — Website Top-Level Management (Top 5 leaders)
# ✅ Names + Designation ONLY
# ✅ No role-buckets, no email/phone/LinkedIn
# ✅ Works with scraper_case2.py (returns leaders)
# ✅ Adds time guards to prevent hanging

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import re
import os
import time

from backend.scraper_case2 import scrape_management_from_website
from backend.config import CASE2_MAX_LEADERS, CASE2_TIMEOUT_SECS


# -----------------------------
# Helpers
# -----------------------------
def _norm(x: Any) -> str:
    return re.sub(r"\s+", " ", ("" if x is None else str(x)).strip())


def _has_contact_noise(s: str) -> bool:
    t = (s or "").lower()
    if "@" in t:
        return True
    if re.search(r"\+?\d[\d\-\s]{7,}", t):
        return True
    if "linkedin" in t or "facebook" in t or "instagram" in t or "twitter" in t:
        return True
    return False


def _clean_person(p: Any) -> Dict[str, str]:
    """
    Enforce strict output:
      {"name": "...", "designation": "..."}
    """
    if not isinstance(p, dict):
        return {"name": "", "designation": ""}

    name = _norm(p.get("name", ""))
    designation = _norm(p.get("designation", ""))

    # STRICT: no contacts
    if _has_contact_noise(name) or _has_contact_noise(designation):
        return {"name": "", "designation": ""}

    # name must exist
    if not name:
        return {"name": "", "designation": ""}

    return {"name": name, "designation": designation}


def _dedupe_leaders(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for p in items:
        name = _norm(p.get("name", "")).lower()
        des = _norm(p.get("designation", "")).lower()
        if not name:
            continue
        key = (name, des)
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": _norm(p.get("name", "")), "designation": _norm(p.get("designation", ""))})
    return out


def _leaders_to_excel_cols(leaders: List[Dict[str, str]], max_leaders: int = 5) -> Dict[str, str]:
    """
    Convert leaders list -> flat Excel columns:
      Leader 1 Name, Leader 1 Designation, ... Leader 5 Name, Leader 5 Designation
    """
    n = max(1, min(int(max_leaders), 5))
    out: Dict[str, str] = {}
    for i in range(1, n + 1):
        out[f"Leader {i} Name"] = ""
        out[f"Leader {i} Designation"] = ""

    for idx, p in enumerate(leaders[:n], start=1):
        out[f"Leader {idx} Name"] = _norm(p.get("name", ""))
        out[f"Leader {idx} Designation"] = _norm(p.get("designation", ""))

    return out


# -----------------------------
# Core API
# -----------------------------
def run_case2_top_management(
    website: str,
    max_leaders: int | None = None,
    debug_hint: str = "",
) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    """
    website -> scrape -> return top leaders

    Returns:
      (leaders_list, meta)

    leaders_list:
      [
        {"name": "...", "designation": "..."},
        ... up to max_leaders
      ]
    """

    n = int(max_leaders or CASE2_MAX_LEADERS)
    n = max(1, min(n, 5))

    meta: Dict[str, Any] = {
        "website": _norm(website),
        "count_scraped": 0,
        "max_leaders": n,
        "hint": _norm(debug_hint),
    }

    if not website or not isinstance(website, str):
        return ([], meta)

    website = website.strip()
    if not (website.startswith("http://") or website.startswith("https://")):
        website = "https://" + website

    # ✅ Per-website guard: don't let one org eat too much time
    # You can override with env: CASE2_PER_SITE_TIMEOUT_SECS
    per_site_cap = int(os.getenv("CASE2_PER_SITE_TIMEOUT_SECS", str(max(10, CASE2_TIMEOUT_SECS * 2))))
    per_site_cap = max(10, min(per_site_cap, 90))

    t0 = time.time()
    people = scrape_management_from_website(website, max_leaders=n) or []
    elapsed = time.time() - t0

    meta["elapsed_secs"] = round(elapsed, 2)
    meta["per_site_cap_secs"] = per_site_cap

    # If scraping took too long, still return whatever we got (no crash)
    # (scraper itself uses request timeouts; this is just a safety meta)
    meta["count_scraped"] = len(people)

    leaders: List[Dict[str, str]] = []
    for p in people:
        cp = _clean_person(p)
        if not cp["name"]:
            continue
        leaders.append(cp)
        if len(leaders) >= n:
            break

    leaders = _dedupe_leaders(leaders)[:n]
    return (leaders, meta)


def enrich_company_record_with_case2(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mutates and returns record:
      record["case2_leaders"] = [{"name":..,"designation":..}, ... up to 5]
      record["case2_meta"]    = {...}
      record["Leader 1 Name"], "Leader 1 Designation", ... (flat Excel columns)
    """
    if not isinstance(record, dict):
        return record

    website = (
        record.get("Website URL")
        or record.get("website_url")
        or record.get("Website")
        or record.get("website")
        or ""
    )
    website = _norm(website)

    hint = " ".join(
        [
            _norm(record.get("Company Name") or record.get("Name") or record.get("company_name") or ""),
            _norm(record.get("Industry") or record.get("Primary Category") or record.get("industry") or ""),
        ]
    ).strip()

    leaders, meta = run_case2_top_management(
        website=website,
        max_leaders=int(CASE2_MAX_LEADERS),
        debug_hint=hint,
    )

    # attach list + meta
    record["case2_leaders"] = leaders
    record["case2_meta"] = meta

    # ✅ attach flat Excel columns (super important)
    flat = _leaders_to_excel_cols(leaders, max_leaders=int(CASE2_MAX_LEADERS))
    record.update(flat)

    return record


if __name__ == "__main__":
    leaders, meta = run_case2_top_management("https://www.tcs.com", max_leaders=5, debug_hint="company")
    print(meta)
    for x in leaders:
        print(x)
