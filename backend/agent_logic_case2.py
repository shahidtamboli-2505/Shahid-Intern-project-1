# backend/agent_logic_case2.py
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from backend.scraper_case2 import scrape_management_from_website

# -----------------------------
# Fixed 5 buckets (as decided)
# -----------------------------
BUCKETS = [
    "Executive Leadership",
    "Technology / Operations",
    "Finance / Administration",
    "Business Development / Growth",
    "Marketing / Branding",
]

FIELDS = ["name", "designation", "email", "phone", "linkedin"]


# -----------------------------
# Keyword signals for buckets
# -----------------------------
EXEC_KW = [
    "ceo", "chief executive", "founder", "co-founder", "cofounder",
    "chairman", "chairperson", "president", "managing director", "md",
    "director", "board", "trustee", "principal", "dean", "vice chancellor",
    "vc", "owner", "partner",
]

TECHOPS_KW = [
    "cto", "chief technology", "chief information", "cio",
    "engineering", "engineer", "tech", "technology",
    "operations", "ops", "plant", "production", "manufacturing",
    "quality", "qa", "delivery", "project", "program", "it manager",
    "head of operations", "operations manager", "service delivery",
]

FINADMIN_KW = [
    "cfo", "finance", "accounts", "accounting", "controller",
    "admin", "administration", "hr", "human resources",
    "legal", "compliance", "procurement", "purchase", "office",
]

BIZGROWTH_KW = [
    "business development", "bd", "growth", "sales", "partnership",
    "partnerships", "alliances", "revenue", "client", "accounts manager",
    "key account", "account manager", "commercial", "strategy",
]

MKTBRAND_KW = [
    "marketing", "brand", "branding", "communications", "comm",
    "public relations", "pr", "digital", "social", "content",
    "community", "campaign", "creative",
]

LINKEDIN_RE = re.compile(r"(linkedin\.com/in/|linkedin\.com/company/)", re.I)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def _looks_like_name(s: str) -> bool:
    """Very light heuristic: 2+ words, not too long, no URL-ish text."""
    t = (s or "").strip()
    if not t:
        return False
    if "http" in t.lower() or "www." in t.lower():
        return False
    parts = [p for p in re.split(r"\s+", t) if p]
    if len(parts) < 2:
        return False
    if len(t) > 60:
        return False
    return True


def _dedupe_people(people: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Deduplicate by (name + designation) mostly."""
    seen = set()
    out: List[Dict[str, str]] = []
    for p in people:
        name = _norm(p.get("name", ""))
        desig = _norm(p.get("designation", ""))
        if not name:
            continue
        key = (name, desig)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _score_for_keywords(text: str, keywords: List[str]) -> int:
    t = _norm(text)
    score = 0
    for kw in keywords:
        if kw in t:
            score += 3
    return score


def _bucket_scores(person: Dict[str, str]) -> Dict[str, int]:
    """
    Score a person for each bucket using name/designation/source text.
    Note: designation may be empty in v1 extraction; we still score based on any hints.
    """
    name = person.get("name", "") or ""
    desig = person.get("designation", "") or ""
    src = person.get("source", "") or ""
    text = f"{name} {desig} {src}"

    scores = {
        "Executive Leadership": _score_for_keywords(text, EXEC_KW),
        "Technology / Operations": _score_for_keywords(text, TECHOPS_KW),
        "Finance / Administration": _score_for_keywords(text, FINADMIN_KW),
        "Business Development / Growth": _score_for_keywords(text, BIZGROWTH_KW),
        "Marketing / Branding": _score_for_keywords(text, MKTBRAND_KW),
    }

    # small boosts
    if person.get("linkedin") and LINKEDIN_RE.search(person["linkedin"]):
        for b in scores:
            scores[b] += 1
    if person.get("email"):
        for b in scores:
            scores[b] += 1

    return scores


def _pick_best_for_bucket(people: List[Dict[str, str]], bucket: str) -> Dict[str, str]:
    """
    Picks one best candidate for a bucket.
    If nothing decent, returns blank fields (allowed).
    """
    best: Optional[Dict[str, str]] = None
    best_score = -1

    for p in people:
        if not _looks_like_name(p.get("name", "")):
            continue
        scores = _bucket_scores(p)
        score = scores.get(bucket, 0)

        # extra: if designation is present and matches bucket strongly
        if bucket == "Executive Leadership":
            score += 2 * _score_for_keywords(p.get("designation", ""), EXEC_KW)
        elif bucket == "Technology / Operations":
            score += 2 * _score_for_keywords(p.get("designation", ""), TECHOPS_KW)
        elif bucket == "Finance / Administration":
            score += 2 * _score_for_keywords(p.get("designation", ""), FINADMIN_KW)
        elif bucket == "Business Development / Growth":
            score += 2 * _score_for_keywords(p.get("designation", ""), BIZGROWTH_KW)
        elif bucket == "Marketing / Branding":
            score += 2 * _score_for_keywords(p.get("designation", ""), MKTBRAND_KW)

        if score > best_score:
            best_score = score
            best = p

    # threshold: if best score is too low, keep blank (avoid hallucinating)
    if best is None or best_score <= 1:
        return {k: "" for k in FIELDS}

    # keep only public fields (already public-only pipeline)
    return {
        "name": best.get("name", "") or "",
        "designation": best.get("designation", "") or "",
        "email": best.get("email", "") or "",
        "phone": best.get("phone", "") or "",
        "linkedin": best.get("linkedin", "") or "",
    }


def run_case2_management_from_website(website: str) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Any]]:
    """
    Main Case-2 function:
      website -> scrape people -> dedupe -> pick best per bucket

    Returns:
      (management_by_bucket, debug_meta)
    """
    meta: Dict[str, Any] = {"website": website, "count_scraped": 0, "count_after_dedupe": 0}

    if not website or not isinstance(website, str):
        return ({b: {k: "" for k in FIELDS} for b in BUCKETS}, meta)

    website = website.strip()
    if not (website.startswith("http://") or website.startswith("https://")):
        website = "https://" + website

    people = scrape_management_from_website(website) or []
    meta["count_scraped"] = len(people)

    people = _dedupe_people(people)
    meta["count_after_dedupe"] = len(people)

    management: Dict[str, Dict[str, str]] = {}
    for bucket in BUCKETS:
        management[bucket] = _pick_best_for_bucket(people, bucket)

    return management, meta


def enrich_company_record_with_case2(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes a single company record (from Case-1 results),
    reads website field, and attaches:
      record["case2_management"] = {bucket: {fields...}}
      record["case2_meta"] = {...}
    """
    # tolerate different key styles
    website = (
        record.get("Website")
        or record.get("website")
        or record.get("Has Website")  # sometimes boolean-like; ignore if not URL
        or ""
    )

    # If Has Website is boolean and Website is empty -> keep blank
    if isinstance(website, bool):
        website = ""

    management, meta = run_case2_management_from_website(str(website) if website else "")
    record["case2_management"] = management
    record["case2_meta"] = meta
    return record


if __name__ == "__main__":
    # Quick manual test (optional)
    mgmt, meta = run_case2_management_from_website("https://www.tcs.com")
    print(meta)
    for b in BUCKETS:
        print(b, "=>", mgmt[b])
