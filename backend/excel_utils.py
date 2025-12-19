# backend/excel_utils.py
# GOOGLE PLACES ONLY Excel export
# ✅ Case-1 + Case-2 (Top Management Names + Designation)
# ✅ One row per company
# ✅ Efficient + startup-grade formatting
# ✅ Works with BOTH schemas:
#    - Old miner output (Name/Website/Google Rating...)
#    - New miner output (Company Name/Website URL/Rating Count...) etc.

from __future__ import annotations

from typing import List, Dict, Any
import re

import pandas as pd
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


# -----------------------------
# Helpers
# -----------------------------
def _norm(s: Any) -> str:
    return re.sub(r"\s+", " ", ("" if s is None else str(s)).strip())


def _pick(row: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in row and row.get(k) not in (None, ""):
            return row.get(k)
    return default


def _yes_no(v: Any) -> str:
    if isinstance(v, bool):
        return "Yes" if v else "No"
    s = _norm(v).lower()
    if s in {"yes", "true", "1"}:
        return "Yes"
    if s in {"no", "false", "0"}:
        return "No"
    return ""


def _to_number_or_blank(x: Any) -> Any:
    """
    Keep rating/count numeric if possible; else blank.
    """
    if x in (None, ""):
        return ""
    try:
        s = str(x).strip()
        if not s:
            return ""
        # allow float/int
        if "." in s:
            return float(s)
        return int(float(s))
    except Exception:
        return ""


def _leaders_list(row: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Accepts:
      - row["case2_leaders"] as list of {"name","designation"}
      - row["leaders"] wrapper
    Returns max 5.
    """
    val = row.get("case2_leaders") or row.get("leaders") or []
    if isinstance(val, dict) and "leaders" in val:
        val = val.get("leaders") or []
    if not isinstance(val, list):
        return []

    out: List[Dict[str, str]] = []
    for item in val:
        if not isinstance(item, dict):
            continue
        nm = _norm(item.get("name"))
        ds = _norm(item.get("designation"))
        if not nm:
            continue
        out.append({"name": nm, "designation": ds})
        if len(out) >= 5:
            break
    return out


def _build_excel_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize any incoming row into the final Excel schema.
    """
    company_name = _norm(_pick(row, "Company Name", "Name", "company_name", default="Unknown"))
    industry = _norm(_pick(row, "Industry", "Primary Category", "industry", "raw_category", default="Business / Services"))

    rating = _to_number_or_blank(_pick(row, "Google Rating", "google_rating", default=""))
    rating_count = _to_number_or_blank(_pick(row, "Rating Count", "Google Rating Count", "google_rating_count", default=""))

    has_web = _pick(row, "Has Website", "has_website", default="")
    has_web = _yes_no(has_web)

    website_url = _norm(_pick(row, "Website URL", "Website", "website_url", "website", default=""))
    if not has_web:
        has_web = "Yes" if website_url else "No"

    source_name = _norm(_pick(row, "Source Name", "source_name", default="google_places"))
    source_url = _norm(_pick(row, "Source URL", "source_url", default=""))

    # Leaders (Top 5) - prefer list if present
    leaders = _leaders_list(row)

    out: Dict[str, Any] = {
        "Company Name": company_name,
        "Industry": industry,
        "Google Rating": rating,
        "Rating Count": rating_count,
        "Has Website": has_web,
        "Website URL": website_url,
    }

    # ✅ If leaders list not present, fallback to already-flattened columns (Leader 1..5)
    if not leaders:
        for i in range(1, 6):
            out[f"Leader {i} Name"] = _norm(_pick(row, f"Leader {i} Name", default=""))
            out[f"Leader {i} Designation"] = _norm(_pick(row, f"Leader {i} Designation", default=""))
    else:
        for i in range(5):
            nm = leaders[i]["name"] if i < len(leaders) else ""
            ds = leaders[i]["designation"] if i < len(leaders) else ""
            out[f"Leader {i+1} Name"] = nm
            out[f"Leader {i+1} Designation"] = ds

    out["Source Name"] = source_name
    out["Source URL"] = source_url

    return out


# -----------------------------
# Final column order (LOCKED)
# -----------------------------
FINAL_COLS: List[str] = [
    "Company Name",
    "Industry",
    "Google Rating",
    "Rating Count",
    "Has Website",
    "Website URL",
    "Leader 1 Name",
    "Leader 1 Designation",
    "Leader 2 Name",
    "Leader 2 Designation",
    "Leader 3 Name",
    "Leader 3 Designation",
    "Leader 4 Name",
    "Leader 4 Designation",
    "Leader 5 Name",
    "Leader 5 Designation",
    "Source Name",
    "Source URL",
]


def write_case1_excel(rows: List[Dict[str, Any]], out_path: str) -> None:
    """
    Writes Case-1 + Case-2 output to a single clean Excel sheet: "Results"

    Output:
      - One row per company
      - Top 5 leaders (Name + Designation)
      - No personal contacts
      - Clean formatting + reasonable column widths
    """
    # Normalize
    normalized: List[Dict[str, Any]] = []
    for r in (rows or []):
        rr = dict(r) if isinstance(r, dict) else {}
        normalized.append(_build_excel_row(rr))

    df = pd.DataFrame(normalized)
    if df.empty:
        df = pd.DataFrame(columns=FINAL_COLS)

    # Ensure all expected columns exist + enforce order
    for c in FINAL_COLS:
        if c not in df.columns:
            df[c] = ""
    df = df[FINAL_COLS]

    # Write Excel
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        sheet_name = "Results"
        df.to_excel(writer, index=False, sheet_name=sheet_name)

        ws = writer.book[sheet_name]

        # ---- Styling ----
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        header_font = Font(bold=True)
        header_align = Alignment(vertical="center", wrap_text=True)
        body_align = Alignment(vertical="top", wrap_text=False)

        # Header
        for cell in ws[1]:
            cell.font = header_font
            cell.alignment = header_align

        # Body alignment default
        for r in range(2, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                ws.cell(row=r, column=c).alignment = body_align

        # Wrap columns
        wrap_cols = {
            "Website URL",
            "Leader 1 Name", "Leader 1 Designation",
            "Leader 2 Name", "Leader 2 Designation",
            "Leader 3 Name", "Leader 3 Designation",
            "Leader 4 Name", "Leader 4 Designation",
            "Leader 5 Name", "Leader 5 Designation",
            "Source URL",
        }
        col_index = {name: i + 1 for i, name in enumerate(FINAL_COLS)}
        for col_name in wrap_cols:
            idx = col_index.get(col_name)
            if not idx:
                continue
            for r in range(2, ws.max_row + 1):
                ws.cell(row=r, column=idx).alignment = Alignment(wrap_text=True, vertical="top")

        # Slightly bigger header row
        ws.row_dimensions[1].height = 22

        # Efficient column widths (fast)
        # clamp to keep professional
        for i, col in enumerate(FINAL_COLS, start=1):
            if df.empty:
                max_len = len(col)
            else:
                # only first 400 rows for speed
                vals = df[col].astype(str).head(400).tolist()
                max_len = max([len(col)] + [len(v) for v in vals])

            if col in {"Website URL", "Source URL"}:
                width = min(max(18, max_len + 2), 55)
            elif "Designation" in col:
                width = min(max(16, max_len + 2), 42)
            elif "Leader" in col:
                width = min(max(14, max_len + 2), 30)
            else:
                width = min(max(14, max_len + 2), 32)

            ws.column_dimensions[get_column_letter(i)].width = width
