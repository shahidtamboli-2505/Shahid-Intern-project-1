# backend/scraper_case2.py
from __future__ import annotations

import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from backend.config import (
    CASE2_TIMEOUT_SECS,
    CASE2_USER_AGENT,
    CASE2_MAX_PAGES,
    CASE2_MAX_BYTES,
)

HEADERS = {"User-Agent": CASE2_USER_AGENT}

TEAM_KEYWORDS = [
    "team", "leadership", "leaders", "management", "about", "our team", "our-team",
    "board", "people", "who we are", "who-we-are", "governance", "executive",
    "director", "faculty", "administration", "staff", "principal", "dean",
]

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
LINKEDIN_RE = re.compile(r"^https?://(www\.)?linkedin\.com/", re.I)

# Light retry for transient network issues
MAX_RETRIES = 2


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _same_domain(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()
    except Exception:
        return False


def _safe_get(url: str) -> str:
    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=CASE2_TIMEOUT_SECS)
            r.raise_for_status()
            if len(r.content) > CASE2_MAX_BYTES:
                return ""
            # best effort decode via requests
            return r.text or ""
        except Exception as e:
            last_err = e
            time.sleep(0.6 * attempt)
    return ""


def _looks_like_name(s: str) -> bool:
    s = _norm(s)
    if not s:
        return False
    if len(s) < 4 or len(s) > 70:
        return False
    if "http" in s.lower() or "www." in s.lower():
        return False
    # 2+ words is a decent heuristic for names
    parts = [p for p in re.split(r"\s+", s) if p]
    if len(parts) < 2:
        return False
    # avoid pure role headings
    bad = {"team", "leadership", "management", "board", "directors", "faculty", "administration"}
    if s.lower() in bad:
        return False
    return True


def _extract_linkedin_from_node(node) -> str:
    try:
        for a in node.select("a[href]"):
            href = (a.get("href") or "").strip()
            if href and LINKEDIN_RE.search(href):
                return href
    except Exception:
        pass
    return ""


def _extract_contact_from_text(text: str) -> Tuple[str, str]:
    text = text or ""
    email = ""
    phone = ""

    m1 = EMAIL_RE.search(text)
    if m1:
        email = m1.group(0)

    m2 = PHONE_RE.search(text)
    if m2:
        phone = _norm(m2.group(1))

    return email, phone


def _candidate_sections(soup: BeautifulSoup):
    """
    Return likely 'cards' / repeated blocks where people are listed.
    We try common patterns first, else fallback to body.
    """
    selectors = [
        "[class*='team']",
        "[class*='leader']",
        "[class*='management']",
        "[class*='board']",
        "[class*='people']",
        "section",
        "article",
        "div",
    ]
    for sel in selectors:
        nodes = soup.select(sel)
        if nodes and len(nodes) >= 3:
            return nodes
    return [soup.body] if soup.body else []


def discover_team_pages(homepage: str) -> List[str]:
    homepage = (homepage or "").strip()
    if not homepage:
        return []

    if not (homepage.startswith("http://") or homepage.startswith("https://")):
        homepage = "https://" + homepage

    html = _safe_get(homepage)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    links: Set[str] = set()

    # Always include homepage as fallback
    links.add(homepage)

    for a in soup.select("a[href]"):
        href_raw = (a.get("href") or "").strip()
        anchor_text = _norm(a.get_text(" ", strip=True)).lower()
        href_l = href_raw.lower()

        hay = f"{href_l} {anchor_text}"
        if any(k in hay for k in TEAM_KEYWORDS):
            full = urljoin(homepage, href_raw)
            if _same_domain(full, homepage):
                # remove fragments
                full = full.split("#", 1)[0]
                links.add(full)

        if len(links) >= max(2, CASE2_MAX_PAGES):
            # keep going a bit but no need to explode
            continue

    # Keep deterministic order
    out = list(links)
    out.sort()
    return out[:CASE2_MAX_PAGES]


def extract_management(page_url: str) -> List[Dict[str, str]]:
    html = _safe_get(page_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")

    people: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str]] = set()

    # Find repeated blocks and try to parse names + nearby designation
    for node in _candidate_sections(soup):
        # Prefer headings inside node as name candidates
        headings = node.find_all(["h1", "h2", "h3", "h4", "strong"])
        for h in headings:
            name = _norm(h.get_text(" ", strip=True))
            if not _looks_like_name(name):
                continue

            # Try designation near the name
            designation = ""
            # 1) next sibling short text
            sib = h.find_next(string=True)
            if sib:
                d = _norm(str(sib))
                if d and len(d) <= 80 and d.lower() != name.lower():
                    designation = d

            # 2) parent container text (first short line after name)
            if not designation:
                parent = h.parent
                if parent:
                    txt = _norm(parent.get_text(" ", strip=True))
                    # Remove name from text
                    txt2 = _norm(txt.replace(name, ""))
                    # pick first 3-8 words as designation candidate
                    if txt2 and len(txt2) <= 140:
                        designation = txt2

            # Extract email/phone within same container to stay "public"
            container = h.parent if h.parent else node
            ctext = _norm(container.get_text(" ", strip=True)) if container else ""
            email, phone = _extract_contact_from_text(ctext)

            linkedin = _extract_linkedin_from_node(container) if container else ""

            key = (name.lower(), designation.lower())
            if key in seen:
                continue
            seen.add(key)

            people.append(
                {
                    "name": name,
                    "designation": designation,
                    "email": email,
                    "phone": phone,
                    "linkedin": linkedin,
                    "source": page_url,
                }
            )

    # If nothing found, fallback: scan page headings only
    if not people:
        for tag in soup.find_all(["h2", "h3", "h4"]):
            name = _norm(tag.get_text(" ", strip=True))
            if not _looks_like_name(name):
                continue
            people.append(
                {
                    "name": name,
                    "designation": "",
                    "email": "",
                    "phone": "",
                    "linkedin": "",
                    "source": page_url,
                }
            )

    return people


def scrape_management_from_website(website: str) -> List[Dict[str, str]]:
    pages = discover_team_pages(website)
    all_people: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str]] = set()

    for page in pages:
        for p in extract_management(page):
            name = _norm(p.get("name", "")).lower()
            des = _norm(p.get("designation", "")).lower()
            key = (name, des)
            if not name:
                continue
            if key in seen:
                continue
            seen.add(key)
            all_people.append(p)

    return all_people
