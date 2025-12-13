# backend/excel_utils.py
# GOOGLE PLACES ONLY Excel export

from typing import List, Dict, Any
import pandas as pd


def write_case1_excel(rows: List[Dict[str, Any]], out_path: str) -> None:
    df = pd.DataFrame(rows)

    # Columns expected from GOOGLE-only miner
    cols = [
        "Name",
        "Primary Category",
        "Address",
        "City",
        "State",
        "Phone",
        "Email",
        "Website",
        "Has Website",
        "Source Name",
        "Source URL",
    ]

    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df = df[cols]

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
