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
