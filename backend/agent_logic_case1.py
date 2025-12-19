# backend/agent_logic_case1.py
# Case 1 — GOOGLE PLACES ONLY pipeline
# ✅ Case-2 integration (Top 5 leaders from website)
# ✅ No-hang guards (org limit + total time cap)
# ✅ Excel-ready flatten: Leader 1..5 Name/Designation
# ✅ No GPT required

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import os
import time

from backend.config import (
    DEFAULT_LOCATION,
    DEFAULT_TOP_N,
    TOP_N_CAP,
    CASE2_ENABLED,
    CASE2_MAX_LEADERS,
    CASE2_MAX_SECONDARY_ORGS,
    CASE2_TOTAL_TIMEOUT_SECS,
)
from backend import scraper, miner, excel_utils

from backend.agent_logic_case2 import enrich_company_record_with_case2


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
    n = min(n, cap)
    return max(1, n)


def _read_bytes(path: str) -> bytes | None:
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    except Exception:
        return None
    return None


def _env_true(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() == "true"


def _env_int(key: str, default: int) -> int:
    try:
        return int(str(os.getenv(key, str(default))).strip())
    except Exception:
        return default


def _is_yes(v: Any) -> bool:
    return str(v or "").strip().lower() == "yes"


def _norm_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    if u.startswith("www."):
        return "https://" + u
    return u


# -----------------------------
# Pipeline
# -----------------------------
def run_case1_pipeline(
    query: str,
    location: Optional[str] = None,
    place: str = "",
    top_n: int = DEFAULT_TOP_N,
    use_gpt: bool = False,   # kept for compatibility (unused)
    debug: bool = True,
) -> Dict[str, Any]:
    location = (location or DEFAULT_LOCATION).strip()
    place = (place or "").strip()
    query = (query or "").strip()

    if not query:
        raise ValueError("Query is empty. Please enter what you want to find.")

    top_n = _safe_top_n(top_n, default=DEFAULT_TOP_N, cap=TOP_N_CAP)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1) SCRAPE (Google Places)
    raw_records, raw_path = scraper.scrape_case1_to_raw(
        query=query,
        location=location,
        place=place,
        run_id=ts,
        max_results=top_n,
        debug=debug,
    )

    # 2) MINE (clean + dedupe)
    cleaned_rows, stats = miner.mine_case1_records(raw_records=raw_records, gpt_client=None)
    cleaned_rows = (cleaned_rows or [])[:top_n]

    # Ensure leader columns always exist (even if Case-2 is OFF / fails)
    for row in cleaned_rows:
        for i in range(1, 6):
            row.setdefault(f"Leader {i} Name", "")
            row.setdefault(f"Leader {i} Designation", "")

    # 3) OPTIONAL CASE-2 (Top leaders from website) - SAFE + FAST
    # runtime overrides (UI sets env vars, so this matters)
    case2_enabled_runtime = _env_true("CASE2_ENABLED", "true" if CASE2_ENABLED else "false")

    # how many orgs to process in case2
    case2_org_limit = _env_int("CASE2_MAX_SECONDARY_ORGS", int(CASE2_MAX_SECONDARY_ORGS))
    case2_org_limit = max(1, min(case2_org_limit, 100))

    # overall time cap (prevents hang)
    case2_total_cap = _env_int("CASE2_TOTAL_TIMEOUT_SECS", int(CASE2_TOTAL_TIMEOUT_SECS))
    case2_total_cap = max(20, min(case2_total_cap, 600))

    # leaders cap
    case2_max_leaders = _env_int("CASE2_MAX_LEADERS", int(CASE2_MAX_LEADERS))
    case2_max_leaders = max(1, min(case2_max_leaders, 5))

    case2_ran = 0
    case2_skipped_no_website = 0
    case2_errors = 0
    case2_stopped_by_timeout = 0

    if case2_enabled_runtime and cleaned_rows:
        start = time.time()
        limit = min(case2_org_limit, len(cleaned_rows))

        for i in range(limit):
            # ✅ overall guard
            if time.time() - start > case2_total_cap:
                case2_stopped_by_timeout = 1
                break

            row = cleaned_rows[i]

            has_web = _is_yes(row.get("Has Website"))
            website = _norm_url(str(row.get("Website URL") or row.get("Website") or row.get("website") or ""))

            if (not has_web) or (not website):
                case2_skipped_no_website += 1
                continue

            try:
                # ✅ This will add:
                # - row["case2_leaders"]
                # - row["case2_meta"]
                # - Leader 1..5 columns
                # (max leaders = CASE2_MAX_LEADERS from config/env)
                os.environ["CASE2_MAX_LEADERS"] = str(case2_max_leaders)
                enrich_company_record_with_case2(row)
                case2_ran += 1
            except Exception as e:
                # keep pipeline safe (no crash)
                row["case2_leaders"] = []
                row["case2_meta"] = {"website": website, "error": str(e)}
                for k in range(1, 6):
                    row.setdefault(f"Leader {k} Name", "")
                    row.setdefault(f"Leader {k} Designation", "")
                case2_errors += 1

    # 4) STATS
    stats = stats or {}
    stats["top_n"] = top_n
    stats["returned_rows"] = len(cleaned_rows) if cleaned_rows else 0
    stats["raw_count"] = int(stats.get("raw_count") or (len(raw_records) if raw_records else 0))
    stats["clean_count"] = int(stats.get("clean_count") or len(cleaned_rows))

    # case2 stats
    stats["case2_enabled"] = bool(case2_enabled_runtime)
    stats["case2_max_leaders"] = int(case2_max_leaders)
    stats["case2_org_limit"] = int(case2_org_limit)
    stats["case2_total_timeout_secs"] = int(case2_total_cap)
    stats["case2_ran"] = int(case2_ran)
    stats["case2_skipped_no_website"] = int(case2_skipped_no_website)
    stats["case2_errors"] = int(case2_errors)
    stats["case2_stopped_by_timeout"] = int(case2_stopped_by_timeout)

    # 5) EXCEL
    os.makedirs("data/output", exist_ok=True)
    excel_path = os.path.join("data/output", f"case1_{ts}.xlsx")
    excel_utils.write_case1_excel(rows=cleaned_rows, out_path=excel_path)

    excel_bytes = _read_bytes(excel_path)
    if not excel_bytes:
        raise RuntimeError("Excel generation failed: output file not found or unreadable.")

    return {
        "raw_path": raw_path,
        "excel_path": excel_path,
        "excel_bytes": excel_bytes,
        "cleaned_rows": cleaned_rows or [],
        "stats": stats,
    }
