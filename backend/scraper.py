# --- Case 1 Agent API ---
# backend/scraper.py
import os
import json
from typing import Tuple, List, Dict
from datetime import datetime

def scrape_case1_to_raw(query: str, location: str, run_id: str) -> Tuple[List[Dict], str]:
    """
    Case 1 ONLY: Returns (raw_records, raw_json_path)
    Existing scraping logic reuse karo. Abhi placeholder minimal.
    """
    os.makedirs("data/raw", exist_ok=True)

    # TODO: Replace with your real scraping logic
    # For now: basic stub record so pipeline works
    raw_records = [{
        "name": f"{query} sample business",
        "raw_category": "Manufacturing",
        "address": f"{location}",
        "phone": "",
        "website": "",
        "source": "stub",
    }]

    path = os.path.join("data/raw", f"case1_raw_{run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw_records, f, ensure_ascii=False, indent=2)

    return raw_records, path
