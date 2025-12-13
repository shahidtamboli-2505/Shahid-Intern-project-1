# backend/agent_logic_case1.py
# Case 1 — GOOGLE PLACES ONLY pipeline

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import os

from backend.config import DEFAULT_LOCATION
from backend import scraper, miner, excel_utils


def run_case1_pipeline(
    query: str,
    location: Optional[str] = None,
    place: str = "",
    use_gpt: bool = False,   # ❌ GPT disabled by default
) -> Dict[str, Any]:
    """
    GOOGLE PLACES ONLY pipeline:
      scraper (google maps) -> miner -> excel
    """

    location = (location or DEFAULT_LOCATION).strip()
    place = (place or "").strip()
    query = (query or "").strip()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # -----------------------------
    # 1️⃣ SCRAPE (Google Places only)
    # -----------------------------
    raw_records, raw_path = scraper.scrape_case1_to_raw(
        query=query,
        location=location,
        place=place,
        run_id=ts,
        debug=True,   # 🔥 IMPORTANT: see GOOGLE logs in terminal
    )

    # -----------------------------
    # 2️⃣ MINE / CLEAN
    # -----------------------------
    cleaned_rows, stats = miner.mine_case1_records(
        raw_records=raw_records,
        gpt_client=None,   # ❌ GPT not used
    )

    # -----------------------------
    # 3️⃣ EXCEL EXPORT
    # -----------------------------
    os.makedirs("data/output", exist_ok=True)
    excel_path = os.path.join("data/output", f"case1_{ts}.xlsx")

    excel_utils.write_case1_excel(
        rows=cleaned_rows,
        out_path=excel_path,
    )

    return {
        "raw_path": raw_path,
        "excel_path": excel_path,
        "stats": stats,
    }
