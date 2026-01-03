"""
scraper_case2.py - NUCLEAR MODE + BOT DETECTION BYPASS
Strict validation + Advanced anti-detection techniques
"""
from __future__ import annotations

import json
import re
import time
import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

# 🆕 Selenium imports for bot bypass
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available - bot bypass limited")

try:
    from backend.config import (
        HEADERS, REQUEST_TIMEOUT, USER_AGENTS_POOL,
        AGENT_RETRY_DELAY_MIN, AGENT_RETRY_DELAY_MAX
    )
except ImportError:
    try:
        from config import HEADERS, REQUEST_TIMEOUT
        USER_AGENTS_POOL = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        AGENT_RETRY_DELAY_MIN = 2
        AGENT_RETRY_DELAY_MAX = 5
    except ImportError:
        HEADERS = {}
        REQUEST_TIMEOUT = 25
        USER_AGENTS_POOL = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
        AGENT_RETRY_DELAY_MIN = 2
        AGENT_RETRY_DELAY_MAX = 5

try:
    from db import get_conn, save_leaders_to_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    def get_conn():
        return None
    def save_leaders_to_db(conn, url, leaders):
        pass

# =============================================================================
# NUCLEAR Configuration
# =============================================================================
MAX_PAGES = 15
MAX_DEPTH = 2
REQUEST_TIMEOUT = 20
RATE_SLEEP_SEC = 0.5
MAX_LEADERS = 5
CONF_THRESHOLD = 0.40  # Relaxed threshold

# 🆕 Bot detection bypass settings
USE_SELENIUM_FALLBACK = True
SELENIUM_TIMEOUT = 20
CAPTCHA_DETECT_KEYWORDS = ["captcha", "recaptcha", "hcaptcha", "cloudflare", "verify you are human"]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

LEADERSHIP_LINK_KEYWORDS = [
    "leader", "team", "management", "executive", "about", "people",
    "board", "founder", "director", "who-we-are", "our-team"
]

EXEC_RE = re.compile(
    r"\b(ceo|coo|cto|cfo|cmo|cro|chief\s+\w+\s+officer|managing\s+director|"
    r"founder|co-?founder|chairman|president|director|vice\s+president|"
    r"vp|head\s+of|executive|partner|owner|principal)\b",
    re.I
)

BAD_KEYWORDS = {
    "tally", "prime", "software", "solution", "service", "product", "platform",
    "system", "application", "app", "tool", "suite",
    "dealer", "partner", "reseller", "distributor", "vendor", "supplier",
    "client", "customer", "pvt", "ltd", "inc", "llc", "corporation", "corp",
    "team", "leadership", "management", "excellence", "innovation", "expert",
    "digitally", "elevated", "endless", "possibilities", "speaking",
    "learn", "read", "click", "contact", "get", "started", "more",
    "our", "the", "and", "or", "with", "for",
    "|", "©", "®", "™", "→", "➔", "…",
    ".com", ".in", ".org", ".net", "www", "http"
}

NEGATIVE_CONTEXT = [
    "testimonial", "client", "customer", "review", "award", "recognition",
    "press", "product", "service", "solution", "dealer", "partner"
]


# =============================================================================
# Data Structures
# =============================================================================
@dataclass
class LeaderCandidate:
    name: str
    role: str
    confidence: float
    source_url: str
    evidence: str
    method: str
    category: str = "Executive Leadership"


# =============================================================================
# NUCLEAR Validation
# =============================================================================
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

try:
    from db import _ensure_url as db_ensure_url
    def _ensure_url(u: str) -> str:
        return db_ensure_url(u)
except ImportError:
    def _ensure_url(u: str) -> str:
        u = (u or "").strip()
        if not u:
            return ""
        if not u.startswith(("http://", "https://")):
            u = "https://" + u
        return u.rstrip("/")

def _host(u: str) -> str:
    try:
        return urlparse(u).netloc.lower()
    except:
        return ""

def _canonicalize(url: str) -> str:
    try:
        p = urlparse(url)
        scheme = (p.scheme or "https").lower()
        netloc = (p.netloc or "").lower()
        path = p.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return urlunparse((scheme, netloc, path, "", p.query or "", ""))
    except:
        return (url or "").split("#")[0].rstrip("/")


def _looks_like_person_name(name: str) -> bool:
    """RELAXED MODE: Less strict name validation for better extraction"""
    name = _norm(name)
    
    # Basic length check (more lenient)
    if not (5 <= len(name) <= 60):
        return False
    
    # Remove titles
    name = re.sub(r"^(mr|mrs|ms|dr|prof|sir)\.?\s+", "", name, flags=re.I)
    low = name.lower()
    
    # Only reject obvious non-names (reduced list)
    bad_keywords_strict = [
        "tally", "software", "solution", "dealer", "pvt", "ltd", "inc", 
        "www", "http", "privacy", "terms", "cookie", "login", "signup"
    ]
    for bad in bad_keywords_strict:
        if bad in low:
            return False
    
    # Must have 2-5 words (relaxed)
    words = [w for w in name.split() if len(w) > 1]
    if not (2 <= len(words) <= 5):
        return False
    
    # At least first word should start with capital
    if not words[0][0].isupper():
        return False
    
    # Should have vowels (real names have vowels)
    if not re.search(r"[aeiouAEIOU]", name):
        return False
    
    # No excessive numbers (allow some)
    digit_count = sum(1 for c in name if c.isdigit())
    if digit_count > 2:
        return False
    
    # Reject if too many special characters
    special_count = sum(1 for c in name if not c.isalnum() and c not in [' ', '-', '.', "'"])
    if special_count > 2:
        return False
    
    return True


def _looks_like_role(role: str) -> bool:
    """RELAXED MODE: Less strict role validation"""
    role = _norm(role)
    
    # Length check (more lenient)
    if not (5 <= len(role) <= 100):
        return False
    
    low = role.lower()
    
    # Must match executive pattern
    if not EXEC_RE.search(role):
        return False
    
    # Reject obvious bad keywords (reduced)
    bad_keywords_roles = ["tally", "prime", "dealer", "solution"]
    for bad in bad_keywords_roles:
        if bad in low:
            return False
    
    # Allow more punctuation
    if "…" in role or role.count("...") > 1:
        return False
    
    # More lenient word count
    word_count = len(role.split())
    if word_count > 15:
        return False
    
    return True


def _categorize_role(role: str) -> str:
    r = role.lower()
    if re.search(r"\b(ceo|chief executive|founder|managing director|chairman|president)\b", r):
        return "Executive Leadership"
    if re.search(r"\b(coo|cto|chief operating|chief technology)\b", r):
        return "Technology / Operations"
    if re.search(r"\b(cfo|chief financial)\b", r):
        return "Finance / Administration"
    if re.search(r"\b(cro|chief revenue|business development|sales)\b", r):
        return "Business Development / Growth"
    if re.search(r"\b(cmo|chief marketing)\b", r):
        return "Marketing / Branding"
    return "Executive Leadership"


def _score_candidate(name: str, role: str, bonus: float = 0.0) -> float:
    """Scoring with strict validation"""
    s = 0.0
    
    if not _looks_like_person_name(name):
        return 0.0
    
    s += 0.50
    
    if not _looks_like_role(role):
        return 0.0
    
    s += 0.40
    
    role_low = role.lower()
    if any(word in role_low for word in ["ceo", "founder", "chairman", "president"]):
        s += 0.10
    elif any(word in role_low for word in ["cto", "cfo", "coo", "cro", "cmo"]):
        s += 0.06
    
    return max(0.0, min(1.0, s + bonus))


def is_blocked(html: str) -> bool:
    """Detect if page is blocked/CAPTCHA"""
    if not html or len(html) < 300:
        return True
    h = html.lower()
    
    for keyword in CAPTCHA_DETECT_KEYWORDS:
        if keyword in h:
            if len(html) < 5000:
                return True
    
    if any(sig in h for sig in ["access denied", "verify you are human"]) and len(html) < 2000:
        return True
    
    return False


# =============================================================================
# 🆕 BOT DETECTION BYPASS - Selenium Driver
# =============================================================================
class SeleniumFetcher:
    """Advanced Selenium fetcher with bot detection bypass"""
    
    def __init__(self):
        self.driver = None
    
    def _setup_driver(self) -> Optional[webdriver.Chrome]:
        """Setup Chrome with anti-detection"""
        if not SELENIUM_AVAILABLE:
            return None
        
        try:
            options = Options()
            
            ua = random.choice(USER_AGENTS_POOL)
            options.add_argument(f'user-agent={ua}')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
            
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": ua})
            
            return driver
            
        except Exception as e:
            print(f"❌ Selenium setup failed: {e}")
            return None
    
    def get(self, url: str) -> Tuple[Optional[str], str, int]:
        """Fetch with Selenium (bot bypass)"""
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            
            if not self.driver:
                return None, "selenium_unavailable", 0
            
            time.sleep(random.uniform(1.0, 2.5))
            self.driver.get(url)
            
            try:
                WebDriverWait(self.driver, SELENIUM_TIMEOUT).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except TimeoutException:
                pass
            
            time.sleep(random.uniform(1.5, 3.0))
            html = self.driver.page_source
            
            if is_blocked(html):
                return None, "blocked", 0
            
            return html, "ok", 200
            
        except WebDriverException as e:
            return None, "driver_error", 0
        except Exception as e:
            return None, "error", 0
    
    def close(self):
        """Close driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


# =============================================================================
# Requests Fetcher
# =============================================================================
class RequestsFetcher:
    """HTTP fetcher with basic bot bypass"""
    
    def __init__(self):
        self.session = requests.Session()
        self._update_headers()

    def _update_headers(self):
        """Rotate User-Agent"""
        ua = random.choice(USER_AGENTS_POOL)
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def get(self, url: str) -> Tuple[Optional[str], str, int]:
        try:
            self._update_headers()
            time.sleep(random.uniform(0.5, 1.5))
            
            r = self.session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            
            if r.status_code >= 400:
                return None, "error", r.status_code
            
            html = r.text or ""
            
            if is_blocked(html):
                return None, "blocked", r.status_code
            
            return html, "ok", r.status_code
            
        except requests.Timeout:
            return None, "timeout", 0
        except requests.ConnectionError:
            return None, "connection_error", 0
        except Exception as e:
            return None, "error", 0


# =============================================================================
# SMART FETCHER
# =============================================================================
class SmartFetcher:
    """Intelligent fetcher: requests first, Selenium fallback"""
    
    def __init__(self):
        self.requests_fetcher = RequestsFetcher()
        self.selenium_fetcher = None
        self.selenium_active = False
    
    def get(self, url: str, force_selenium: bool = False) -> Tuple[Optional[str], str, int]:
        """Smart fetch with automatic fallback"""
        if force_selenium or self.selenium_active:
            return self._get_selenium(url)
        
        html, status, code = self.requests_fetcher.get(url)
        
        if html:
            return html, status, code
        
        if status == "blocked" and USE_SELENIUM_FALLBACK and SELENIUM_AVAILABLE:
            print(f"🤖 Blocked detected, switching to Selenium for: {url}")
            self.selenium_active = True
            return self._get_selenium(url)
        
        return None, status, code
    
    def _get_selenium(self, url: str) -> Tuple[Optional[str], str, int]:
        """Fetch with Selenium"""
        if not self.selenium_fetcher:
            self.selenium_fetcher = SeleniumFetcher()
        
        return self.selenium_fetcher.get(url)
    
    def close(self):
        """Cleanup"""
        if self.selenium_fetcher:
            self.selenium_fetcher.close()


# =============================================================================
# URL Discovery
# =============================================================================
def discover_urls_smart(home_url: str, fetcher: SmartFetcher) -> List[str]:
    home_url = _ensure_url(home_url)
    if not home_url:
        return []
    
    host = _host(home_url)
    visited = set()
    found_urls = [home_url]
    visited.add(home_url)
    
    priority_paths = [
        "/about-us", "/about", "/team", "/our-team", "/leadership",
        "/management", "/executives", "/board", "/people",
        "/company", "/about-us/leadership", "/company/team"
    ]
    
    for path in priority_paths:
        if len(found_urls) >= MAX_PAGES:
            break
        test_url = _canonicalize(urljoin(home_url, path))
        if test_url not in visited:
            visited.add(test_url)
            found_urls.append(test_url)
    
    if len(found_urls) < MAX_PAGES:
        to_visit = [(home_url, 0, 100)]
        
        while to_visit and len(found_urls) < MAX_PAGES:
            to_visit.sort(key=lambda x: x[2], reverse=True)
            current_url, depth, priority = to_visit.pop(0)
            
            if depth > MAX_DEPTH:
                continue
            
            time.sleep(random.uniform(RATE_SLEEP_SEC, RATE_SLEEP_SEC * 2))
            html, st, sc = fetcher.get(current_url)
            
            if not html:
                continue
            
            soup = BeautifulSoup(html, "lxml")
            
            for a in soup.find_all("a", href=True, limit=100):
                href = a.get("href", "").strip()
                if not href:
                    continue
                
                abs_url = urljoin(current_url, href)
                abs_url = _canonicalize(abs_url)
                
                if _host(abs_url) != host or abs_url in visited:
                    continue
                
                if re.search(r"\.(jpg|png|pdf|zip|mp4|css|js)$", abs_url, re.I):
                    continue
                
                if len(found_urls) >= MAX_PAGES:
                    break
                
                visited.add(abs_url)
                found_urls.append(abs_url)
    
    return found_urls[:MAX_PAGES]


# =============================================================================
# Extraction Functions
# =============================================================================
def extract_jsonld(soup, leaders: list, seen: set, url: str):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
            if isinstance(data, list):
                for item in data:
                    _process_jsonld(item, leaders, seen, url)
            else:
                _process_jsonld(data, leaders, seen, url)
        except:
            pass

def _process_jsonld(data: dict, leaders: list, seen: set, url: str):
    if not isinstance(data, dict):
        return
    
    dtype = str(data.get("@type", "")).lower()
    if "person" in dtype:
        name = _norm(str(data.get("name", "")))
        role = _norm(str(data.get("jobTitle", "")))
        
        if _looks_like_person_name(name) and _looks_like_role(role):
            key = (name.lower(), role.lower())
            if key not in seen:
                seen.add(key)
                conf = _score_candidate(name, role, 0.15)
                if conf >= CONF_THRESHOLD:
                    leaders.append(LeaderCandidate(
                        name, role, conf, url, "jsonld", "jsonld", _categorize_role(role)
                    ))


def extract_cards(soup, leaders: list, seen: set, url: str):
    containers = soup.find_all(["section", "div", "main", "article"], limit=40)
    
    for container in containers:
        txt = container.get_text(" ", strip=True).lower()
        
        if not any(kw in txt for kw in ["ceo", "founder", "director", "executive", "officer"]):
            continue
        
        cards = container.find_all(["div", "li", "article"], limit=100)
        
        for card in cards:
            block_text = _norm(card.get_text(" ", strip=True))
            
            if len(block_text) < 20 or len(block_text) > 1000:
                continue
            
            if any(neg in block_text.lower() for neg in NEGATIVE_CONTEXT):
                continue
            
            name = ""
            for h in card.find_all(["h2", "h3", "h4", "h5", "strong", "b"]):
                cand = _norm(h.get_text())
                if _looks_like_person_name(cand):
                    name = cand
                    break
            
            if not name:
                continue
            
            role = ""
            for el in card.find_all(["p", "span", "div", "em", "i"]):
                cand = _norm(el.get_text())
                if cand != name and _looks_like_role(cand):
                    role = cand
                    break
            
            if not role:
                continue
            
            key = (name.lower(), role.lower())
            if key not in seen:
                seen.add(key)
                conf = _score_candidate(name, role, 0.08)
                if conf >= CONF_THRESHOLD:
                    leaders.append(LeaderCandidate(
                        name, role, conf, url, block_text[:150], "card", _categorize_role(role)
                    ))


def extract_tables(soup, leaders: list, seen: set, url: str):
    for table in soup.find_all("table"):
        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                name = _norm(cells[0].get_text())
                role = _norm(cells[1].get_text())
                
                if _looks_like_person_name(name) and _looks_like_role(role):
                    key = (name.lower(), role.lower())
                    if key not in seen:
                        seen.add(key)
                        conf = _score_candidate(name, role, 0.06)
                        if conf >= CONF_THRESHOLD:
                            leaders.append(LeaderCandidate(
                                name, role, conf, url, f"{name}|{role}", "table", _categorize_role(role)
                            ))


def extract_lists(soup, leaders: list, seen: set, url: str):
    for lst in soup.find_all(["ul", "ol"]):
        for item in lst.find_all("li", limit=40):
            text = _norm(item.get_text())
            
            if len(text) < 15:
                continue
            
            if "-" in text or ":" in text:
                parts = re.split(r"[-:]", text, maxsplit=1)
                if len(parts) == 2:
                    name = _norm(parts[0])
                    role = _norm(parts[1])
                    
                    if _looks_like_person_name(name) and _looks_like_role(role):
                        key = (name.lower(), role.lower())
                        if key not in seen:
                            seen.add(key)
                            conf = _score_candidate(name, role, 0.05)
                            if conf >= CONF_THRESHOLD:
                                leaders.append(LeaderCandidate(
                                    name, role, conf, url, text, "list", _categorize_role(role)
                                ))


def extract_text_pairs(soup, leaders: list, seen: set, url: str):
    text = soup.get_text("\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    for i in range(len(lines) - 1):
        line1 = _norm(lines[i])
        line2 = _norm(lines[i + 1])
        
        if not line1 or not line2:
            continue
        
        if _looks_like_person_name(line1) and _looks_like_role(line2):
            key = (line1.lower(), line2.lower())
            if key not in seen:
                seen.add(key)
                conf = _score_candidate(line1, line2, 0.02)
                if conf >= CONF_THRESHOLD:
                    leaders.append(LeaderCandidate(
                        line1, line2, conf, url, f"{line1} {line2}", 
                        "text_pair", _categorize_role(line2)
                    ))


def extract_leaders_improved(html: str, source_url: str) -> List[LeaderCandidate]:
    soup = BeautifulSoup(html, "lxml")
    
    for tag in soup(["script", "style", "noscript", "iframe", "footer", "nav", "header"]):
        tag.decompose()
    
    leaders = []
    seen = set()
    
    extract_jsonld(soup, leaders, seen, source_url)
    extract_cards(soup, leaders, seen, source_url)
    extract_tables(soup, leaders, seen, source_url)
    extract_lists(soup, leaders, seen, source_url)
    
    if len(leaders) < 2:
        extract_text_pairs(soup, leaders, seen, source_url)
    
    leaders.sort(key=lambda x: x.confidence, reverse=True)
    return leaders[:MAX_LEADERS]


# =============================================================================
# MAIN SCRAPER
# =============================================================================
def scrape_company_leadership(company_url: str, respect_robots: bool = True, 
                              save_to_db: bool = False) -> Dict[str, Any]:
    """NUCLEAR MODE Leadership Scraper + BOT DETECTION BYPASS"""
    
    company_url = _ensure_url(company_url)
    
    if not company_url:
        return {"error": "Invalid URL", "success": False, "all_leaders": []}
    
    fetcher = SmartFetcher()
    
    try:
        urls = discover_urls_smart(company_url, fetcher)
        
        if not urls:
            return {"error": "No URLs found", "success": False, "all_leaders": []}
        
        all_leaders = []
        stats = {"success": 0, "failed": 0, "blocked": 0, "selenium_used": 0}
        
        for url in urls:
            time.sleep(random.uniform(RATE_SLEEP_SEC, RATE_SLEEP_SEC * 2))
            html, st, sc = fetcher.get(url)
            
            if fetcher.selenium_active:
                stats["selenium_used"] += 1
            
            if html:
                stats["success"] += 1
                leaders = extract_leaders_improved(html, url)
                if leaders:
                    all_leaders.extend(leaders)
            elif st == "blocked":
                stats["blocked"] += 1
            else:
                stats["failed"] += 1
        
        seen = set()
        final = []
        for l in all_leaders:
            key = (l.name.lower(), l.role.lower())
            if key not in seen:
                seen.add(key)
                final.append(l)
        
        final.sort(key=lambda x: x.confidence, reverse=True)
        final = final[:MAX_LEADERS]
        
        by_category = {}
        for l in final:
            cat = l.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "name": l.name,
                "role": l.role,
                "confidence": round(l.confidence, 3)
            })
        
        result = {
            "success": len(final) > 0,
            "company_url": company_url,
            "total_leaders": len(final),
            "stats": stats,
            "leaders_by_category": by_category,
            "all_leaders": [asdict(l) for l in final]
        }
        
        if save_to_db and final and DB_AVAILABLE:
            try:
                conn = get_conn()
                if conn:
                    db_leaders = [{'name': l.name, 'role': l.role, 'confidence': l.confidence,
                                  'source_url': l.source_url, 'method': l.method, 'category': l.category}
                                 for l in final]
                    save_leaders_to_db(conn, company_url, db_leaders)
                    conn.close()
            except:
                pass
        
        return result
        
    finally:
        fetcher.close()


# =============================================================================
# Wrapper for agent
# =============================================================================
def run_discovery_sync(website: str, company_name: str = "") -> Tuple[Dict[str, Any], str]:
    """Wrapper for agent_logic_case2.py"""
    result = scrape_company_leadership(website, respect_robots=True, save_to_db=False)
    
    payload = {
        "leaders_raw": result.get("all_leaders", []),
        "case2_management": result.get("leaders_by_category", {}),
        "success": result.get("success", False),
        "stats": result.get("stats", {})
    }
    
    email = ""
    
    return payload, email


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python scraper_case2.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print(f"\n🔍 Scraping: {url}")
    print(f"🤖 Selenium available: {SELENIUM_AVAILABLE}")
    result = scrape_company_leadership(url, True, False)
    
    print(f"\n✅ Found {result.get('total_leaders', 0)} leaders")
    print(f"📊 Stats: {result.get('stats', {})}")
    
    if result.get("all_leaders"):
        print("\n📋 Leaders:")
        for i, l in enumerate(result["all_leaders"], 1):
            print(f"  {i}. {l['name']} - {l['role']} (confidence: {l['confidence']})")
    else:
        print("⚠️ No valid leaders found (strict filtering active)")
    
    output_file = "data/output/leadership_case2.json"
    try:
        os.makedirs("data/output", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved to: {output_file}")
    except:
        pass