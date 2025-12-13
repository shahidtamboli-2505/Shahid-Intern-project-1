# backend/miner.py
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

# Case 1 ONLY: record cleaning + (optional) GPT categorization

from typing import List, Dict, Any, Tuple
import re


def _norm_phone(p: str) -> str:
    p = (p or "").strip()
    p = re.sub(r"[^\d+]", "", p)
    return p


def _has_website(w: str) -> bool:
    w = (w or "").strip()
    return bool(w) and ("http" in w or "." in w)


def _is_drop_url(source: str) -> bool:
    """
    Drop only obvious non-business / internal pages
    """
    s = (source or "").lower()

    drop_words = [
        "privacy",
        "terms",
        "policy",
        "grievance",
        "complaint",
        "testimonial",
        "review",
        "reviews",
        "reviewratings",
        "about",
        "contact-us",
        "link-to-us",
        "sitemap",
    ]

    return any(w in s for w in drop_words)


def mine_case1_records(
    raw_records: List[Dict[str, Any]],
    gpt_client=None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Case 1 ONLY: returns (cleaned_rows, stats)
    """
    cleaned: List[Dict[str, Any]] = []
    seen = set()

    dropped_url = 0
    dropped_dupe = 0

    for r in raw_records:
        name = (r.get("name") or "").strip()
        addr = (r.get("address") or "").strip()
        phone = _norm_phone(r.get("phone") or "")
        website = (r.get("website") or "").strip()
        source = (r.get("source") or "").strip()
        raw_cat = (r.get("raw_category") or r.get("category") or "").strip()

        if not name and not source:
            continue

        # 🔥 DROP ONLY CLEAR JUNK URLs
        if _is_drop_url(source):
            dropped_url += 1
            continue

        # 🔁 DEDUPE (safe)
        key = (
            name.lower(),
            addr.lower(),
            phone,
            website.lower(),
            source.lower(),
        )
        if key in seen:
            dropped_dupe += 1
            continue
        seen.add(key)

        primary_cat = ""
        if gpt_client is not None and getattr(gpt_client, "is_enabled", lambda: False)():
            primary_cat = gpt_client.classify_primary_category_case1(
                name=name,
                raw_category=raw_cat,
                address=addr,
            )

        cleaned.append({
            "Name": name or "Unknown",
            "Primary Category": primary_cat or raw_cat or "Manufacturing / Industrial",
            "Address": addr,
            "Phone": phone,
            "Email": (r.get("email") or "").strip(),
            "Website": website,
            "Has Website": "Yes" if _has_website(website) else "No",
            "Source": source,
        })

    stats = {
        "raw_count": len(raw_records),
        "clean_count": len(cleaned),
        "dropped_url": dropped_url,
        "dropped_dupe": dropped_dupe,
        "with_website": sum(1 for x in cleaned if x["Has Website"] == "Yes"),
        "no_website": sum(1 for x in cleaned if x["Has Website"] == "No"),
    }

    return cleaned, stats
