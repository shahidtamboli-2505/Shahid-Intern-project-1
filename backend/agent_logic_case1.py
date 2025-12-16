# backend/agent_logic_case1.py
# Case 1 — GOOGLE PLACES ONLY pipeline (Case-2 integration supported)

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import os

from backend.config import (
    DEFAULT_LOCATION,
    DEFAULT_TOP_N,
    TOP_N_CAP,
    CASE2_MAX_SECONDARY_ORGS,
)
from backend import scraper, miner, excel_utils

from backend.agent_logic_case2 import run_case2_management_from_website


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


def _is_yes(v: Any) -> bool:
    return str(v or "").strip().lower() == "yes"


def _env_true(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() == "true"


def run_case1_pipeline(
    query: str,
    location: Optional[str] = None,
    place: str = "",
    top_n: int = DEFAULT_TOP_N,
    use_gpt: bool = False,
    debug: bool = True,
) -> Dict[str, Any]:

    location = (location or DEFAULT_LOCATION).strip()
    place = (place or "").strip()
    query = (query or "").strip()

    if not query:
        raise ValueError("Query is empty. Please enter what you want to find.")

    top_n = _safe_top_n(top_n, default=DEFAULT_TOP_N, cap=TOP_N_CAP)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1) SCRAPE
    raw_records, raw_path = scraper.scrape_case1_to_raw(
        query=query,
        location=location,
        place=place,
        run_id=ts,
        max_results=top_n,
        debug=debug,
    )

    # 2) MINE
    cleaned_rows, stats = miner.mine_case1_records(raw_records=raw_records, gpt_client=None)
    if cleaned_rows:
        cleaned_rows = cleaned_rows[:top_n]

    # ✅ IMPORTANT: Read Case-2 flags at RUNTIME (not import time)
    case2_enabled = _env_true("CASE2_ENABLED", "false")
    case2_secondary = _env_true("CASE2_ENABLE_SECONDARY_SEARCH", "false")

    # 3) OPTIONAL CASE-2
    case2_ran = 0
    case2_skipped_no_website = 0
    case2_errors = 0

    if case2_enabled and case2_secondary and cleaned_rows:
        limit = min(int(CASE2_MAX_SECONDARY_ORGS), len(cleaned_rows))
        for i in range(limit):
            row = cleaned_rows[i]
            has_website = _is_yes(row.get("Has Website"))
            website = str(row.get("Website") or "").strip()

            if (not has_website) or (not website):
                case2_skipped_no_website += 1
                continue

            try:
                mgmt, meta = run_case2_management_from_website(website)
                row["case2_management"] = mgmt or {}
                row["case2_meta"] = meta or {}
                case2_ran += 1
            except Exception as e:
                row["case2_management"] = {}
                row["case2_meta"] = {"website": website, "error": str(e)}
                case2_errors += 1

    # 4) STATS
    stats = stats or {}
    stats["top_n"] = top_n
    stats["returned_rows"] = len(cleaned_rows) if cleaned_rows else 0
    stats["raw_count"] = int(stats.get("raw_count") or (len(raw_records) if raw_records else 0))
    stats["clean_count"] = int(stats.get("clean_count") or (len(cleaned_rows) if cleaned_rows else 0))

    if "with_website" not in stats:
        stats["with_website"] = sum(1 for x in cleaned_rows if str(x.get("Has Website", "")).strip() == "Yes")
    if "no_website" not in stats:
        stats["no_website"] = sum(1 for x in cleaned_rows if str(x.get("Has Website", "")).strip() == "No")
    if "with_rating" not in stats:
        stats["with_rating"] = sum(1 for x in cleaned_rows if str(x.get("Google Rating", "")).strip() != "")

    stats["case2_enabled"] = bool(case2_enabled)
    stats["case2_secondary_search_enabled"] = bool(case2_secondary)
    stats["case2_attempted_orgs_limit"] = int(min(int(CASE2_MAX_SECONDARY_ORGS), len(cleaned_rows) if cleaned_rows else 0))
    stats["case2_ran"] = int(case2_ran)
    stats["case2_skipped_no_website"] = int(case2_skipped_no_website)
    stats["case2_errors"] = int(case2_errors)

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
