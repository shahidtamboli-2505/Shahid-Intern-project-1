# backend/excel_utils.py

# GOOGLE PLACES ONLY Excel export
# Case-1 + Case-2 (Top Level Management READY)

from __future__ import annotations

from typing import List, Dict, Any
import pandas as pd

from openpyxl.styles import Font


# -----------------------------
# Column mapping for Case-2 mgmt
# -----------------------------
MGMT_BUCKET_TO_PREFIX = {
    "Executive Leadership": "Executive",
    "Technology / Operations": "Tech/Ops",
    "Finance / Administration": "Finance/Admin",
    "Business Development / Growth": "Business/Growth",
    "Marketing / Branding": "Marketing/Brand",
}

MGMT_FIELDS = ["name", "designation", "email", "phone", "linkedin"]
MGMT_SUFFIX_MAP = {
    "name": "Name",
    "designation": "Designation",
    "email": "Email",
    "phone": "Phone",
    "linkedin": "LinkedIn",
}


def _apply_case2_management_to_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    If row has: row["case2_management"] = {bucket: {name/designation/email/phone/linkedin}}
    then fill the Excel columns:
      Executive Name, Executive Designation, ...
      Tech/Ops Name, ...
      etc.
    """
    mgmt = row.get("case2_management")

    if not isinstance(mgmt, dict) or not mgmt:
        return row

    for bucket, prefix in MGMT_BUCKET_TO_PREFIX.items():
        pdata = mgmt.get(bucket, {})
        if not isinstance(pdata, dict):
            pdata = {}

        for f in MGMT_FIELDS:
            col = f"{prefix} {MGMT_SUFFIX_MAP[f]}"
            val = pdata.get(f, "")
            # only fill if not already filled
            if not row.get(col):
                row[col] = val if val is not None else ""

    return row


def write_case1_excel(rows: List[Dict[str, Any]], out_path: str) -> None:
    """
    Writes Case-1 + Case-2 results to an Excel file.

    Case-1:
      - Nearby organizations (Google Places)

    Case-2 (DESIGN READY):
      - Google rating & website intelligence
      - Top-level management (same row)

    NOTE:
    - Management data will be populated in Case-2 scraping phase
    - Current structure is FINAL & exam-safe
    """

    # ✅ FINAL COLUMN ORDER (LOCKED)
    cols = [
        # -----------------------------
        # Identity
        # -----------------------------
        "Name",
        "Primary Category",

        # -----------------------------
        # Location
        # -----------------------------
        "Address",
        "City",
        "State",

        # -----------------------------
        # Organization Contact
        # -----------------------------
        "Phone",
        "Email",
        "Website",

        # -----------------------------
        # Case-2 Base Intelligence
        # -----------------------------
        "Has Website",
        "Google Rating",
        "Google Rating Count",

        # -----------------------------
        # Top-Level Management (Case-2)
        # -----------------------------
        # Executive
        "Executive Name",
        "Executive Designation",
        "Executive Email",
        "Executive Phone",
        "Executive LinkedIn",

        # Tech / Operations
        "Tech/Ops Name",
        "Tech/Ops Designation",
        "Tech/Ops Email",
        "Tech/Ops Phone",
        "Tech/Ops LinkedIn",

        # Finance / Admin
        "Finance/Admin Name",
        "Finance/Admin Designation",
        "Finance/Admin Email",
        "Finance/Admin Phone",
        "Finance/Admin LinkedIn",

        # Business / Growth
        "Business/Growth Name",
        "Business/Growth Designation",
        "Business/Growth Email",
        "Business/Growth Phone",
        "Business/Growth LinkedIn",

        # Marketing / Brand
        "Marketing/Brand Name",
        "Marketing/Brand Designation",
        "Marketing/Brand Email",
        "Marketing/Brand Phone",
        "Marketing/Brand LinkedIn",

        # -----------------------------
        # Source
        # -----------------------------
        "Source Name",
        "Source URL",
    ]

    # Handle empty safely
    if not rows:
        df = pd.DataFrame(columns=cols)
    else:
        # Ensure each row is a dict (safe)
        normalized_rows: List[Dict[str, Any]] = []
        for r in rows:
            rr = dict(r) if isinstance(r, dict) else {}
            rr = _apply_case2_management_to_row(rr)
            normalized_rows.append(rr)

        df = pd.DataFrame(normalized_rows)

<<<<<<< HEAD
        # Ensure all expected columns exist
        for c in cols:
            if c not in df.columns:
                df[c] = ""

        # Enforce column order
        df = df[cols]

    # Write Excel
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        sheet_name = "Results"
        df.to_excel(writer, index=False, sheet_name=sheet_name)

        ws = writer.book[sheet_name]

        # -------- Formatting (clean & professional) --------
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        # Header styling
        header_font = Font(bold=True)
        for cell in ws[1]:
            cell.font = header_font

        # Auto column widths (readable but controlled)
        for col_cells in ws.columns:
            col_letter = col_cells[0].column_letter
            max_len = 0
            for cell in col_cells:
                val = "" if cell.value is None else str(cell.value)
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = min(max(14, max_len + 2), 42)
=======
import pandas as pd

def generate_excel_from_business_list(business_list, out_path="case1_output.xlsx"):
    """
    business_list: list of dicts with keys name,address,phone,website,primary_category
    Produces an .xlsx file with 3 sheets.
    """
    df = pd.DataFrame(business_list)
    # Ensure expected columns
    for col in ["name","address","phone","website","primary_category","has_website"]:
        if col not in df.columns:
            df[col] = ""
main

    # Write sheets
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:

        df.to_excel(writer, index=False, sheet_name="Results")

        df.to_excel(writer, sheet_name="All Results", index=False)
        df[df["has_website"]==True].to_excel(writer, sheet_name="With Website", index=False)
        df[df["has_website"]==False].to_excel(writer, sheet_name="No Website", index=False)
    return out_path

 main
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
