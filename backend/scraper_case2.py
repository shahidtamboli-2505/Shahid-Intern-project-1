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

MAX_RETRIES = 2

# pages we want to prioritize
TEAM_KEYWORDS = [
    "leadership", "leader", "management", "about", "about-us", "our-team", "team",
    "board", "governance", "people", "who-we-are", "who we are",
    "administration", "faculty", "staff",
    "principal", "director", "dean", "chancellor", "vice chancellor", "registrar",
]

# IMPORTANT: role words. If designation doesn't contain any of these, reject.
ROLE_WORDS_RE = re.compile(
    r"\b("
    r"founder|co[- ]?founder|chairman|chairperson|ceo|chief executive|"
    r"managing director|md|director|president|principal|dean|registrar|"
    r"vice[- ]?chancellor|chancellor|controller of examinations|"
    r"cto|cfo|coo|cmo|cio|chief|head\b"
    r")\b",
    re.I,
)

# Bad texts that frequently appear in nav/cta/services and get incorrectly picked as names
BAD_NAME_WORDS_RE = re.compile(
    r"\b("
    r"explore|platform|contact|careers|testimonial|testimonials|solutions|services|"
    r"product|products|pricing|blog|news|resources|support|case studies|"
    r"download|demo|get started|learn more|overview|integration|apps|"
    r"workflow|orchestration|how we can help|privacy|terms"
    r")\b",
    re.I,
)

# A stricter name pattern: 2-5 tokens, mostly Capitalized or initials, allows Dr./Mr./Ms./Prof./Shri
TITLE_PREFIXES = {"dr", "mr", "mrs", "ms", "miss", "prof", "shri", "smt", "sir"}
TOKEN_OK_RE = re.compile(r"^[A-Za-z][A-Za-z.\-']*$")

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
            return r.text or ""
        except Exception as e:
            last_err = e
            time.sleep(0.6 * attempt)
    return ""

def _clean_designation(s: str) -> str:
    s = _norm(s)
    if not s:
        return ""
    # kill contacts
    if "@" in s:
        return ""
    if re.search(r"\+?\d[\d\-\s]{7,}", s):
        return ""
    if len(s) > 140:
        s = s[:140].strip()
    return s

def _looks_like_human_name(s: str) -> bool:
    s = _norm(s)
    if not s:
        return False

    sl = s.lower()

    # hard rejects
    if "http" in sl or "www." in sl:
        return False
    if "@" in s:
        return False
    if re.search(r"\d", s):
        return False
    if "|" in s or "/" in s:
        return False
    if BAD_NAME_WORDS_RE.search(s):
        return False

    parts = [p for p in s.replace(",", " ").split() if p]
    if len(parts) < 2 or len(parts) > 5:
        return False

    # validate tokens: allow prefix titles + initials + Capitalized words
    ok_tokens = 0
    for i, tok in enumerate(parts):
        t = tok.strip(".").lower()
        if i == 0 and t in TITLE_PREFIXES:
            ok_tokens += 1
            continue

        if not TOKEN_OK_RE.match(tok):
            return False

        # initial like "A." / "A"
        if len(tok.strip(".")) == 1:
            ok_tokens += 1
            continue

        # Capitalized word like Abhishek / Patil
        if tok[0].isupper():
            ok_tokens += 1
            continue

        return False

    return ok_tokens >= 2

def _strip_noise_dom(soup: BeautifulSoup) -> None:
    # remove nav/footer/header/script/style/forms to avoid menu items
    for tag in soup(["script", "style", "noscript", "svg", "form"]):
        tag.decompose()
    for tag in soup.find_all(["nav", "footer", "header"]):
        tag.decompose()

def discover_team_pages(homepage: str) -> List[str]:
    homepage = (homepage or "").strip()
    if not homepage:
        return []

    if not (homepage.startswith("http://") or homepage.startswith("https://")):
        homepage = "https://" + homepage

    html = _safe_get(homepage)
    if not html:
        return [homepage]

    soup = BeautifulSoup(html, "lxml")
    _strip_noise_dom(soup)

    links: List[str] = []
    seen: Set[str] = set()

    def _add(u: str):
        u = u.split("#", 1)[0].strip()
        if not u:
            return
        if u not in seen:
            seen.add(u)
            links.append(u)

    _add(homepage)

    for a in soup.select("a[href]"):
        href_raw = (a.get("href") or "").strip()
        if not href_raw:
            continue

        anchor_text = _norm(a.get_text(" ", strip=True)).lower()
        href_l = href_raw.lower()
        hay = f"{href_l} {anchor_text}"

        if any(k in hay for k in TEAM_KEYWORDS):
            full = urljoin(homepage, href_raw)
            if _same_domain(full, homepage):
                _add(full)
        if len(links) >= CASE2_MAX_PAGES:
            break

    # add common paths (same domain)
    common_paths = [
        "/about", "/about-us", "/leadership", "/management", "/our-team", "/team",
        "/board", "/governance", "/administration", "/faculty", "/staff",
    ]
    for p in common_paths:
        if len(links) >= CASE2_MAX_PAGES:
            break
        _add(urljoin(homepage, p))

    return links[:CASE2_MAX_PAGES]

def _extract_from_schema_person(soup: BeautifulSoup, page_url: str) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    # schema.org Person
    nodes = soup.select('[itemtype*="schema.org/Person"]')
    for node in nodes:
        name = ""
        desig = ""

        nm = node.select_one('[itemprop="name"]')
        if nm:
            name = _norm(nm.get_text(" ", strip=True))

        jt = node.select_one('[itemprop="jobTitle"]')
        if jt:
            desig = _clean_designation(jt.get_text(" ", strip=True))

        if _looks_like_human_name(name) and desig and ROLE_WORDS_RE.search(desig):
            out.append({"name": name, "designation": desig, "source": page_url})
    return out

def _extract_from_tables(soup: BeautifulSoup, page_url: str) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # try to detect header mapping
        header = [ _norm(th.get_text(" ", strip=True)).lower() for th in rows[0].find_all(["th","td"]) ]
        name_idx = None
        role_idx = None
        for i, h in enumerate(header):
            if any(x in h for x in ["name", "faculty", "person"]):
                name_idx = i
            if any(x in h for x in ["designation", "position", "role", "title"]):
                role_idx = i

        for tr in rows[1:]:
            cols = [ _norm(td.get_text(" ", strip=True)) for td in tr.find_all(["td","th"]) ]
            cols = [c for c in cols if c]
            if len(cols) < 2:
                continue

            # fallback: first two columns
            ni = name_idx if name_idx is not None and name_idx < len(cols) else 0
            di = role_idx if role_idx is not None and role_idx < len(cols) else 1

            name = cols[ni]
            desig = _clean_designation(cols[di])

            if _looks_like_human_name(name) and desig and ROLE_WORDS_RE.search(desig):
                out.append({"name": name, "designation": desig, "source": page_url})
    return out

def _extract_from_cards(soup: BeautifulSoup, page_url: str) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []

    # containers likely containing people cards
    selectors = [
        "[class*='team'] [class*='member']",
        "[class*='team'] [class*='card']",
        "[class*='leader']",
        "[class*='leadership']",
        "[class*='management']",
        "[class*='board']",
        "[class*='profile']",
        "[class*='faculty']",
        "[class*='staff']",
        "article",
        "section",
        "li",
    ]

    # pick first selector that gives repeated blocks
    nodes = []
    for sel in selectors:
        nodes = soup.select(sel)
        if nodes and len(nodes) >= 3:
            break

    for node in nodes[:250]:
        text = _norm(node.get_text(" ", strip=True))
        if not text or len(text) < 10:
            continue

        # try name candidates in headings/bold
        name_candidates = []
        for tag in node.find_all(["h1","h2","h3","h4","strong","b"]):
            nm = _norm(tag.get_text(" ", strip=True))
            if _looks_like_human_name(nm):
                name_candidates.append(nm)

        name_candidates = name_candidates[:2]
        for name in name_candidates:
            # remove name from text, look for designation around role words
            rest = _norm(text.replace(name, " "))
            # keep it shorter
            rest_short = " ".join(rest.split()[:24])
            desig = _clean_designation(rest_short)

            # must include role word
            if desig and ROLE_WORDS_RE.search(desig):
                out.append({"name": name, "designation": desig, "source": page_url})
                break

    return out

def _rank_role(desig: str) -> int:
    d = (desig or "").lower()
    # higher is better
    rank = 0
    if "founder" in d: rank += 120
    if "chair" in d or "chairman" in d: rank += 110
    if "chief executive" in d or re.search(r"\bceo\b", d): rank += 105
    if "managing director" in d or re.search(r"\bmd\b", d): rank += 100
    if re.search(r"\bdirector\b", d): rank += 90
    if "principal" in d: rank += 85
    if "dean" in d: rank += 80
    if "registrar" in d: rank += 70
    if "vice chancellor" in d or "chancellor" in d: rank += 95
    if re.search(r"\bcto\b|\bcfo\b|\bcoo\b|\bcmo\b|\bcio\b", d): rank += 75
    if "head" in d: rank += 55
    if "chief" in d: rank += 60
    return rank

def extract_management(page_url: str) -> List[Dict[str, str]]:
    html = _safe_get(page_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    _strip_noise_dom(soup)

    candidates: List[Dict[str, str]] = []

    candidates += _extract_from_schema_person(soup, page_url)
    candidates += _extract_from_tables(soup, page_url)
    candidates += _extract_from_cards(soup, page_url)

    # dedupe by name
    seen: Set[str] = set()
    uniq: List[Dict[str, str]] = []
    for c in candidates:
        name = _norm(c.get("name", ""))
        desig = _clean_designation(c.get("designation", ""))
        if not _looks_like_human_name(name):
            continue
        if not desig or not ROLE_WORDS_RE.search(desig):
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append({"name": name, "designation": desig, "source": page_url})

    # rank by seniority
    uniq.sort(key=lambda x: _rank_role(x.get("designation", "")), reverse=True)
    return uniq

def scrape_management_from_website(website: str, max_leaders: int = 5) -> List[Dict[str, str]]:
    max_leaders = int(max_leaders or 5)
    max_leaders = max(1, min(max_leaders, 5))

    pages = discover_team_pages(website)
    all_people: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for page in pages:
        people = extract_management(page)
        for p in people:
            key = (p.get("name", "").strip().lower())
            if not key or key in seen:
                continue
            seen.add(key)
            all_people.append({"name": p["name"], "designation": p["designation"]})
            if len(all_people) >= max_leaders:
                return all_people

    return all_people[:max_leaders]
