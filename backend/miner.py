# backend/miner.py

# GOOGLE PLACES ONLY miner (simple clean + dedupe)

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


def _has_website(w: str) -> bool:
    w = (w or "").strip()
    return bool(w) and (w.startswith("http://") or w.startswith("https://") or "." in w)


def _infer_city_state_from_address(addr: str) -> Tuple[str, str]:
    a = (addr or "").strip()
    if not a:
        return "", ""
    parts = [p.strip() for p in a.split(",") if p.strip()]
    if len(parts) >= 2:
        state = parts[-1]
        city = parts[-2]
        city = re.sub(r"\b\d{6}\b", "", city).strip()
        state = re.sub(r"\b\d{6}\b", "", state).strip()
        return city, state
    return "", ""


def mine_case1_records(
    raw_records: List[Dict[str, Any]],
    gpt_client=None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    GOOGLE ONLY:
    raw_records expected keys (from scraper.py):
      name, raw_category, address, phone, email, website, source_name, source_url
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
        source_name = _norm_text(r.get("source_name", "google_places")) or "google_places"
        source_url = _norm_url(r.get("source_url", ""))

        if not name and not source_url:
            continue

        # ✅ Simple dedupe: name + address + phone
        key = (name.lower(), addr.lower(), phone)
        if key in seen:
            continue
        seen.add(key)

        city, state = _infer_city_state_from_address(addr)

        cleaned.append({
            "Name": name or "Unknown",
            "Primary Category": raw_cat,
            "Address": addr,
            "City": city,
            "State": state,
            "Phone": phone,
            "Email": email,
            "Website": website,
            "Has Website": "Yes" if _has_website(website) else "No",
            "Source Name": source_name,
            "Source URL": source_url,
        })

    stats = {
        "raw_count": len(raw_records),
        "clean_count": len(cleaned),
        "with_website": sum(1 for x in cleaned if x["Has Website"] == "Yes"),
        "no_website": sum(1 for x in cleaned if x["Has Website"] == "No"),
    }

    return cleaned, stats
=======
import pandas as pd
import re

def to_dataframe(raw_list):
    df = pd.DataFrame(raw_list)
    # ensure cols
    for c in ["name","address","phone","website"]:
        if c not in df.columns:
            df[c] = ""
    return df

def clean_phone(x):
    if not isinstance(x, str):
        return ""
    # keep digits and + sign
    s = re.sub(r"[^\d\+]", "", x)
    return s

def clean_and_process(raw_list):
    df = to_dataframe(raw_list)

    # Basic cleaning
    df["name"] = df["name"].astype(str).str.strip()
    df["address"] = df["address"].astype(str).str.strip()
    df["phone"] = df["phone"].astype(str).apply(clean_phone)
    df["website"] = df["website"].astype(str).str.strip()

    # Remove empty names
    df = df[df["name"] != ""]

    # Deduplicate by name or phone if present
    df.drop_duplicates(subset=["name"], inplace=True)

    # Assign primary_category (Case 1: Manufacturing)
    def primary_cat(row):
        # you can add better heuristics
        txt = f"{row['name']} {row['address']}".lower()
        if "manufactur" in txt or "factory" in txt or "industry" in txt or "engineer" in txt:
            return "Manufacturing"
        return "Other"

    df["primary_category"] = df.apply(primary_cat, axis=1)

    # Website flag
    df["has_website"] = df["website"].apply(lambda u: bool(u and u.strip()))

    # Convert to list of dicts (cleaned)
    clean_list = df.to_dict(orient="records")
    return clean_list
main
