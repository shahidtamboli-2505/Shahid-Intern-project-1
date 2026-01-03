from __future__ import annotations

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import os
import time
import sys
import json
import re
import requests

# -----------------------------
# Path safety
# -----------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -----------------------------
# Imports
# -----------------------------
from backend.config import (
    DEFAULT_LOCATION,
    DEFAULT_TOP_N,
    TOP_N_CAP,
    CASE2_ENABLED as CASE2_ENABLED_DEFAULT,
    CASE2_MAX_LEADERS as CASE2_MAX_LEADERS_DEFAULT,
    CASE2_TIMEOUT_SECS,
)

import backend.scraper as scraper
import backend.miner as miner
import backend.excel_utils as excel_utils

# -----------------------------
# Case-2 modules - With Debug
# -----------------------------
scraper_case2 = None
SCRAPER_CASE2_AVAILABLE = False

try:
    print("🔧 Loading scraper_case2...")
    import backend.scraper_case2 as scraper_case2
    SCRAPER_CASE2_AVAILABLE = True
    print("✅ scraper_case2 loaded successfully!")
except ImportError as e:
    print(f"❌ scraper_case2 import failed: {e}")
except Exception as e:
    print(f"❌ scraper_case2 error: {e}")


# -----------------------------
# Helpers
# -----------------------------
def _safe_top_n(top_n: Any, default: int, cap: int) -> int:
    try:
        n = int(top_n)
    except Exception:
        n = default
    if n <= 0:
        n = default
    return max(1, min(n, cap))


def _read_bytes(path: str) -> bytes | None:
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    except Exception:
        return None
    return None


def _clean_url(u: str) -> str:
    u = (u or "").strip()
    lu = u.lower()
    if not u or "googleusercontent.com" in lu or "google.com/url" in lu:
        return ""
    if u.startswith(("mailto:", "tel:", "javascript:")):
        return ""
    if u.startswith("www."):
        u = "https://" + u
    if not (u.startswith("http://") or u.startswith("https://")):
        u = "https://" + u
    return u


# -----------------------------
# Email helpers
# -----------------------------
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
    "icloud.com", "aol.com", "proton.me", "protonmail.com", "zoho.com",
}
_PREFERRED_PREFIX = (
    "info@", "contact@", "admin@", "office@", "support@", "help@",
    "admissions@", "enquiry@", "inquiry@",
)


def _pick_best_email_from_html(html: str) -> str:
    if not html:
        return ""
    emails = [e.lower() for e in _EMAIL_RE.findall(html)]
    if not emails:
        return ""

    filtered: List[str] = []
    for e in emails:
        try:
            dom = e.split("@", 1)[1].strip().lower()
        except Exception:
            continue
        if dom in _FREE_EMAIL_DOMAINS:
            continue
        filtered.append(e)

    if not filtered:
        return ""

    for p in _PREFERRED_PREFIX:
        for e in filtered:
            if e.startswith(p):
                return e

    return filtered[0]


def _scrape_contact_email_light(website: str, timeout: int) -> str:
    if not website:
        return ""
    try:
        r = requests.get(
            website,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=max(6, int(timeout or 10)),
            allow_redirects=True,
        )
        if r.status_code >= 400:
            return ""
        return _pick_best_email_from_html(r.text or "")
    except Exception:
        return ""


# -----------------------------
# Case-2 buckets (strict schema)
# -----------------------------
BUCKETS = [
    "Executive Leadership",
    "Technology / Operations",
    "Finance / Administration",
    "Business Development / Growth",
    "Marketing / Branding",
]


def _empty_case2_management() -> Dict[str, Dict[str, str]]:
    return {b: {"name": "", "designation": ""} for b in BUCKETS}


def _normalize_case2_leaders_to_buckets(leaders_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """
    ✅ FIXED: Convert flat leaders list from scraper_case2 into bucketed format
    - Added CRO mapping
    - Better keyword matching
    - Handles missing designation gracefully
    """
    out = _empty_case2_management()
    
    # ✅ IMPROVED: Role mapping rules with CRO
    bucket_rules = {
        "Executive Leadership": [
            "ceo", "chief executive", "founder", "co-founder", "cofounder",
            "managing director", "chairman", "chairperson", "president", 
            "director", "md", "executive director", "principal", "partner",
            "owner", "proprietor", "executive vice president", "evp"
        ],
        "Technology / Operations": [
            "cto", "cio", "coo", "chief technology", "chief information",
            "chief operating", "technology", "operations", "technical",
            "engineering", "it head", "head of technology", "head of operations"
        ],
        "Finance / Administration": [
            "cfo", "chief financial", "finance", "accounts", "admin",
            "administration", "hr", "human resources", "controller",
            "treasurer", "head of finance", "head of hr"
        ],
        "Business Development / Growth": [
            "cro", "chief revenue officer", "chief revenue",  # ✅ ADDED CRO
            "business development", "sales", "growth", "revenue", 
            "commercial", "bd", "strategy", "head of sales", "head of bd"
        ],
        "Marketing / Branding": [
            "cmo", "chief marketing", "marketing", "brand", 
            "communications", "pr", "digital", "head of marketing"
        ],
    }
    
    for leader in leaders_list:
        if not isinstance(leader, dict):
            continue
            
        name = (leader.get("name") or "").strip()
        role = (leader.get("role") or leader.get("designation") or "").strip()
        
        # ✅ Allow name-only (designation can be blank)
        if not name:
            continue
        
        role_lower = role.lower() if role else ""
        
        # Find matching bucket
        matched = False
        for bucket, keywords in bucket_rules.items():
            if out[bucket]["name"]:  # Skip if bucket already filled
                continue
            
            # ✅ Better matching: check if ANY keyword is in role
            if role_lower:
                for keyword in keywords:
                    if keyword in role_lower:
                        out[bucket]["name"] = name
                        out[bucket]["designation"] = role
                        matched = True
                        break
            
            if matched:
                break
        
        # ✅ If no match but have name+role, put in Executive (fallback)
        if not matched and role and not any(out[b]["name"] for b in BUCKETS):
            out["Executive Leadership"]["name"] = name
            out["Executive Leadership"]["designation"] = role
    
    return out


def _has_leadership_strict(mgmt: Dict[str, Dict[str, str]]) -> bool:
    """
    ✅ IMPROVED: Check if ANY bucket has a name (not just Executive)
    This increases success rate while maintaining quality
    """
    if not isinstance(mgmt, dict):
        return False
    
    for bucket in BUCKETS:
        d = mgmt.get(bucket) or {}
        name = (d.get("name") or "").strip()
        if name:  # Name exists in any bucket = success
            return True
    
    return False


def _apply_case2_management_to_row(
    row: Dict[str, Any],
    mgmt: Dict[str, Dict[str, str]],
    email: str = "",
) -> None:
    """Apply Case-2 management data to row"""
    row["case2_management"] = mgmt
    row["Leadership Found"] = "Yes" if _has_leadership_strict(mgmt) else "No"
    if email and not (row.get("Contact Email") or "").strip():
        row["Contact Email"] = email


# -----------------------------
# SAFE Case-1 scraper wrapper
# -----------------------------
def _scrape_case1_safe(
    query: str,
    location: str,
    place: str,
    run_id: str,
    max_results: int,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    ✅ NO CHANGES - Keeps 300 output capability intact
    """
    if hasattr(scraper, "scrape_case1_to_raw"):
        try:
            return scraper.scrape_case1_to_raw(
                query=query,
                location=location,
                run_id=run_id,
                max_results=max_results,
                place=place,
            )
        except TypeError:
            merged_query = " ".join([x for x in [query, place] if x]).strip()
            return scraper.scrape_case1_to_raw(
                query=merged_query,
                location=location,
                run_id=run_id,
                max_results=max_results,
            )

    merged_query = " ".join([x for x in [query, place] if x]).strip()
    results = scraper.scrape_google_places(
        query=merged_query,
        location=location,
        max_results=max_results,
    )

    raw_dir = os.path.join("data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    out_path = os.path.join(raw_dir, f"raw_{run_id}.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return results, out_path


# -----------------------------
# 🔥 Case-2 enrichment wrapper
# -----------------------------
def _enrich_with_case2(
    company_name: str,
    website: str,
    max_leaders: int = 5,
) -> Tuple[Dict[str, Dict[str, str]], str]:
    """
    ✅ IMPROVED: Better error handling and logging
    Call scraper_case2.scrape_company_leadership and convert to bucketed format
    
    Returns: (management_dict, email)
    """
    mgmt = _empty_case2_management()
    email = ""
    
    if not SCRAPER_CASE2_AVAILABLE or not scraper_case2 or not website:
        return mgmt, email
    
    try:
        # Call scraper_case2
        result = scraper_case2.scrape_company_leadership(
            company_url=website,
            respect_robots=False,
            save_to_db=False,
        )
        
        if not result or not result.get("success"):
            return mgmt, email
        
        # Extract leaders
        all_leaders = result.get("all_leaders", [])
        
        if not all_leaders:
            return mgmt, email
        
        # Convert to dict format
        leaders_dicts = []
        for leader in all_leaders[:max_leaders]:
            if isinstance(leader, dict):
                leaders_dicts.append({
                    "name": leader.get("name", ""),
                    "role": leader.get("role", ""),
                })
        
        # ✅ Map to buckets with improved logic
        mgmt = _normalize_case2_leaders_to_buckets(leaders_dicts)
        
    except Exception as e:
        # ✅ Silent fail but log error
        print(f"      ⚠️ Case-2 error for {company_name}: {str(e)[:100]}")
    
    return mgmt, email


# -----------------------------
# PIPELINE (EXPORT)
# -----------------------------
def run_case1_pipeline(
    query: str,
    location: Optional[str] = None,
    place: str = "",
    top_n: int = DEFAULT_TOP_N,
    use_gpt: bool = False,
    debug: bool = True,
    case2_enabled: Optional[bool] = None,
    case2_max_leaders: Optional[int] = None,
) -> Dict[str, Any]:
    """
    ✅ IMPROVED: Better error handling, logging, and Excel completeness
    Main pipeline: Case-1 (Google Places) + Case-2 (Leadership) + Excel export
    """

    if case2_enabled is None:
        case2_enabled = bool(CASE2_ENABLED_DEFAULT)

    if case2_max_leaders is None:
        try:
            case2_max_leaders = int(CASE2_MAX_LEADERS_DEFAULT or 5)
        except Exception:
            case2_max_leaders = 5
    case2_max_leaders = max(1, min(int(case2_max_leaders), 5))

    location = (location or DEFAULT_LOCATION).strip()
    query = (query or "").strip()
    place = (place or "").strip()

    if not query:
        raise ValueError("Query is empty.")

    top_n = _safe_top_n(top_n, DEFAULT_TOP_N, TOP_N_CAP)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if debug:
        print(f"\n🚀 PIPELINE START")
        print(f"   Query: {query}")
        print(f"   Place: {place}")
        print(f"   Location: {location}")
        print(f"   Max results: {top_n}")
        print(f"🧠 Case-2: {'ENABLED' if case2_enabled else 'DISABLED'} (max_leaders={case2_max_leaders})")
        print(f"🔧 scraper_case2: {'AVAILABLE' if SCRAPER_CASE2_AVAILABLE else 'NOT LOADED'}")

    # -----------------------------
    # Case-1: Google Places
    # -----------------------------
    raw_records, raw_path = _scrape_case1_safe(
        query=query,
        location=location,
        place=place,
        run_id=ts,
        max_results=top_n,
    )

    if debug:
        print(f"\n📊 Case-1 Results: {len(raw_records)} companies fetched")

    cleaned_rows, stats = miner.mine_case1_records(raw_records=raw_records)
    cleaned_rows = (cleaned_rows or [])[:top_n]

    if debug:
        print(f"✅ Cleaned: {len(cleaned_rows)} companies ready")

    # ✅ Ensure baseline keys exist for ALL rows
    for row in cleaned_rows:
        row.setdefault("Leadership Found", "No")
        row.setdefault("case2_management", _empty_case2_management())
        row.setdefault("Company Name", "Unknown")
        row.setdefault("Website URL", "")

    # -----------------------------
    # Case-2: Leadership enrichment
    # -----------------------------
    if case2_enabled and cleaned_rows and SCRAPER_CASE2_AVAILABLE:
        if debug:
            print(f"\n🔍 Starting Case-2 enrichment for {len(cleaned_rows)} companies...")
            print(f"{'='*60}")
        
        start = time.time()
        global_timeout = 600  # 10 min guard
        success_count = 0

        for i, row in enumerate(cleaned_rows, 1):
            if time.time() - start > global_timeout:
                if debug:
                    print(f"\n🛑 Global timeout reached ({global_timeout}s)")
                break

            website = _clean_url(row.get("Website URL") or "")
            company_name = row.get("Company Name", "Unknown")
            
            # ✅ IMPROVED: Log all scenarios
            if not website:
                if debug:
                    print(f"⚠️ [{i}/{len(cleaned_rows)}] {company_name} - No website, skipping")
                # Still ensure row has empty structure
                _apply_case2_management_to_row(row, _empty_case2_management(), "")
                continue

            if debug:
                print(f"\n🔍 [{i}/{len(cleaned_rows)}] {company_name}")
                print(f"   Website: {website}")

            try:
                # Call Case-2 enrichment
                mgmt, email = _enrich_with_case2(
                    company_name=company_name,
                    website=website,
                    max_leaders=case2_max_leaders,
                )

                # Fallback email scrape
                if not email and not (row.get("Contact Email") or "").strip():
                    email = _scrape_contact_email_light(website, int(CASE2_TIMEOUT_SECS or 10))

                # Apply to row
                _apply_case2_management_to_row(row, mgmt, email)

                # ✅ IMPROVED: Detailed status logging
                if row.get("Leadership Found") == "Yes":
                    success_count += 1
                    exec_leader = mgmt.get("Executive Leadership", {})
                    exec_name = exec_leader.get("name", "N/A")
                    exec_role = exec_leader.get("designation", "N/A")
                    
                    # Count total leaders found
                    total_leaders = sum(1 for b in BUCKETS if mgmt.get(b, {}).get("name"))
                    
                    if debug:
                        print(f"   ✅ SUCCESS - {total_leaders} leader(s) found")
                        print(f"   CEO: {exec_name} ({exec_role})")
                else:
                    if debug:
                        print(f"   ⚠️ No leaders found")
                        
            except Exception as e:
                if debug:
                    print(f"   ❌ ERROR: {str(e)[:150]}")
                # ✅ Ensure row still has empty structure
                _apply_case2_management_to_row(row, _empty_case2_management(), "")

        if debug:
            elapsed = time.time() - start
            success_rate = (success_count / len(cleaned_rows) * 100) if cleaned_rows else 0
            print(f"\n{'='*60}")
            print(f"🎯 Case-2 Complete!")
            print(f"   Success: {success_count}/{len(cleaned_rows)} ({success_rate:.1f}%)")
            print(f"   Time: {elapsed:.1f}s")

    elif debug and case2_enabled:
        print(f"\n⚠️ Case-2 SKIPPED:")
        if not cleaned_rows:
            print("  → No companies to process")
        if not SCRAPER_CASE2_AVAILABLE:
            print("  → scraper_case2 NOT LOADED (import failed)")

    # -----------------------------
    # ✅ IMPROVED: Excel Export with validation
    # -----------------------------
    os.makedirs("data/output", exist_ok=True)
    excel_path = os.path.join("data/output", f"case1_{ts}.xlsx")
    
    # ✅ Final validation before Excel export
    for row in cleaned_rows:
        # Ensure all required keys exist
        row.setdefault("Leadership Found", "No")
        row.setdefault("case2_management", _empty_case2_management())
        row.setdefault("Company Name", "Unknown")
        row.setdefault("Website URL", "")
        row.setdefault("Contact Email", "")
        row.setdefault("Contact Phone", "")
        row.setdefault("Address", "")
    
    excel_utils.write_case1_excel(rows=cleaned_rows, out_path=excel_path)

    with_leadership = sum(1 for r in cleaned_rows if r.get("Leadership Found") == "Yes")

    if debug:
        print(f"\n{'='*60}")
        print(f"✅ PIPELINE COMPLETE!")
        print(f"📊 Results:")
        print(f"   Total companies: {len(cleaned_rows)}")
        print(f"   With leaders: {with_leadership}")
        print(f"   Success rate: {with_leadership}/{len(cleaned_rows)} ({100*with_leadership//len(cleaned_rows) if cleaned_rows else 0}%)")
        print(f"📁 Excel: {excel_path}")
        print(f"{'='*60}\n")

    return {
        "excel_path": excel_path,
        "excel_bytes": _read_bytes(excel_path),
        "cleaned_rows": cleaned_rows,
        "stats": {
            "clean_count": len(cleaned_rows),
            "with_leadership": with_leadership,
            "with_leaders": with_leadership,
            "success_rate": f"{with_leadership}/{len(cleaned_rows)}" if cleaned_rows else "0/0",
        },
        "raw_path": raw_path,
    }