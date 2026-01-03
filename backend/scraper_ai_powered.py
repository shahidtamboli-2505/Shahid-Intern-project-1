"""
scraper_ai_powered.py - AI SCRAPER WITH COMPLETE AUDIT SYSTEM
🆕 Now includes diagnostic reporting + better extraction patterns
"""
from __future__ import annotations

import json
import re
import time
import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

from bs4 import BeautifulSoup

# Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# LLM Client
try:
    from backend.gpt_client import GeminiClient
except ImportError:
    try:
        from gpt_client import GeminiClient
    except ImportError:
        GeminiClient = None

# Config
try:
    from backend.config import USER_AGENTS_POOL
except ImportError:
    try:
        from config import USER_AGENTS_POOL
    except ImportError:
        USER_AGENTS_POOL = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ]

# Config
MAX_PAGES_TO_CHECK = 5
SELENIUM_TIMEOUT = 30
WAIT_TIME = 10

LEADERSHIP_KEYWORDS = [
    'leadership', 'team', 'management', 'executive', 'about',
    'people', 'board', 'founder', 'director', 'who-we-are',
    'our-team', 'leaders', 'officers', 'ceo', 'cto', 'cfo',
    'governance', 'corporate', 'company', 'organization',
    'our-people', 'meet', 'key', 'senior'
]

# Data Structures
@dataclass
class LeaderCandidate:
    name: str
    role: str
    confidence: float
    source_url: str
    method: str
    category: str = "Executive Leadership"

# Helpers
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

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

# AI Selenium Fetcher
class AISeleniumFetcher:
    def __init__(self):
        self.driver = None
        self.llm = None
        self.audit_data = {
            "names_detected": 0,
            "roles_detected": 0,
            "exec_keywords": [],
            "content_quality": "Unknown"
        }
        if GeminiClient:
            try:
                self.llm = GeminiClient()
                if not self.llm.is_enabled():
                    self.llm = None
            except:
                self.llm = None
    
    def _setup_driver(self):
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
            
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            print(f"❌ Selenium setup failed: {e}")
            return None
    
    def get_page(self, url: str):
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            if not self.driver:
                return None
            
            time.sleep(random.uniform(2.0, 3.0))
            print(f"🌐 Loading: {url}")
            self.driver.get(url)
            
            try:
                WebDriverWait(self.driver, SELENIUM_TIMEOUT).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except TimeoutException:
                pass
            
            print(f"⏳ Waiting {WAIT_TIME}s for JavaScript...")
            time.sleep(WAIT_TIME)
            
            # Scroll
            try:
                for i in range(3):
                    self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/3});")
                    time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            except:
                pass
            
            html = self.driver.page_source
            print(f"✅ Captured {len(html)} bytes")
            return html
        except WebDriverException as e:
            error = str(e)
            if "ERR_NAME_NOT_RESOLVED" in error:
                print(f"❌ Domain not found")
            else:
                print(f"❌ Error: {error[:100]}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def discover_leadership_links(self, homepage_url: str):
        print(f"\n🔍 Discovering leadership links...")
        html = self.get_page(homepage_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        leadership_links = []
        seen_urls = set()
        
        for a in soup.find_all('a', href=True):
            href = a.get('href', '').strip()
            text = _norm(a.get_text()).lower()
            
            if not href:
                continue
            
            abs_url = urljoin(homepage_url, href)
            
            if _host(abs_url) != _host(homepage_url):
                continue
            
            combined = f"{text} {href}".lower()
            
            if any(keyword in combined for keyword in LEADERSHIP_KEYWORDS):
                if abs_url not in seen_urls:
                    seen_urls.add(abs_url)
                    leadership_links.append({
                        'url': abs_url,
                        'text': _norm(a.get_text()),
                        'score': sum(1 for kw in LEADERSHIP_KEYWORDS if kw in combined)
                    })
        
        leadership_links.sort(key=lambda x: x['score'], reverse=True)
        top_links = leadership_links[:MAX_PAGES_TO_CHECK]
        
        print(f"✅ Found {len(top_links)} leadership-related links")
        for link in top_links:
            print(f"   - {link['text'][:50]} → {link['url']}")
        
        return [link['url'] for link in top_links]
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

# Content Analysis
def analyze_content(html: str) -> Dict[str, Any]:
    """Analyze for audit"""
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    text = soup.get_text()
    
    # Names
    name_pattern = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b')
    names = list(set(name_pattern.findall(text)))
    
    # Keywords
    exec_keywords = ['ceo', 'founder', 'director', 'president', 'chief']
    found = [kw for kw in exec_keywords if kw in text.lower()]
    
    # Roles
    role_pattern = re.compile(r'\b(ceo|coo|cto|cfo|founder|director|president)\b', re.I)
    roles = len(role_pattern.findall(text))
    
    return {
        "names": len(names),
        "keywords": found,
        "roles": roles,
        "quality": "High" if len(names) > 5 and roles > 3 else "Medium" if len(names) > 2 else "Low"
    }

# ENHANCED Pattern Extraction
def extract_leaders_enhanced(html: str, url: str) -> List[LeaderCandidate]:
    """Enhanced extraction for structures like XDE Studios"""
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    leaders = []
    seen = set()
    
    exec_pattern = re.compile(
        r"\b(ceo|coo|cto|cfo|cmo|chief|president|director|founder|executive|vp|vice president)\b",
        re.I
    )
    
    # Strategy 1: Team member cards (XDE Studios style)
    # Look for div/section containing name + role together
    for container in soup.find_all(['div', 'section', 'article'], limit=100):
        text = _norm(container.get_text())
        
        # Skip if too large (whole page) or too small
        if len(text) < 10 or len(text) > 300:
            continue
        
        # Must contain executive keyword
        if not exec_pattern.search(text):
            continue
        
        # Find name (first bold/heading)
        name = None
        for tag in container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'], limit=3):
            cand = _norm(tag.get_text())
            if 8 <= len(cand) <= 50:
                words = cand.split()
                if 2 <= len(words) <= 4 and not exec_pattern.search(cand):
                    name = cand
                    break
        
        if not name:
            continue
        
        # Find role (any text with exec keyword in same container)
        role = None
        for line in text.split('\n'):
            line = _norm(line)
            if exec_pattern.search(line) and name not in line and len(line) < 100:
                role = line
                break
        
        if role:
            key = (name.lower(), role.lower())
            if key not in seen:
                seen.add(key)
                leaders.append(LeaderCandidate(
                    name=name,
                    role=role[:80],
                    confidence=0.75,
                    source_url=url,
                    method="card_extraction",
                    category=_categorize_role(role)
                ))
    
    # Strategy 2: Consecutive headings
    all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
    for i in range(len(all_headings) - 1):
        h1 = _norm(all_headings[i].get_text())
        h2 = _norm(all_headings[i + 1].get_text())
        
        if exec_pattern.search(h1) and not exec_pattern.search(h2):
            name, role = h2, h1
        elif not exec_pattern.search(h1) and exec_pattern.search(h2):
            name, role = h1, h2
        else:
            continue
        
        words = name.split()
        if 2 <= len(words) <= 5 and 8 <= len(name) <= 50:
            key = (name.lower(), role.lower())
            if key not in seen:
                seen.add(key)
                leaders.append(LeaderCandidate(
                    name=name,
                    role=role[:80],
                    confidence=0.7,
                    source_url=url,
                    method="consecutive_headings",
                    category=_categorize_role(role)
                ))
    
    return leaders[:5]

# Main Scraper with Audit
def scrape_with_ai(company_url: str) -> Dict[str, Any]:
    company_url = _ensure_url(company_url)
    
    print(f"\n{'='*80}")
    print(f"🤖 AI-POWERED SCRAPING WITH AUDIT")
    print(f"🏢 Company: {company_url}")
    print(f"{'='*80}\n")
    
    # Audit data
    audit = {
        "accessible": False,
        "links_found": 0,
        "pages_checked": 0,
        "names_detected": 0,
        "roles_detected": 0,
        "keywords_found": [],
        "quality": "Unknown",
        "reason": "",
        "recommendation": "",
        "confidence": 0
    }
    
    fetcher = AISeleniumFetcher()
    
    try:
        # Discover
        urls = fetcher.discover_leadership_links(company_url)
        audit["links_found"] = len(urls)
        
        if not urls:
            urls = [company_url]
            audit["reason"] = "No leadership links found, trying homepage"
        else:
            audit["accessible"] = True
        
        # Extract
        all_leaders = []
        total_analysis = {"names": 0, "keywords": set(), "roles": 0}
        
        for url in urls:
            print(f"\n📄 Extracting from: {url}")
            html = fetcher.get_page(url)
            audit["pages_checked"] += 1
            
            if not html:
                continue
            
            # Analyze
            analysis = analyze_content(html)
            total_analysis["names"] += analysis["names"]
            total_analysis["keywords"].update(analysis["keywords"])
            total_analysis["roles"] += analysis["roles"]
            
            # Extract
            leaders = extract_leaders_enhanced(html, url)
            
            if leaders:
                print(f"   ✅ Found {len(leaders)} leaders")
                all_leaders.extend(leaders)
            else:
                print(f"   ⚠️ No leaders extracted")
            
            time.sleep(2)
        
        # Update audit
        audit["names_detected"] = total_analysis["names"]
        audit["roles_detected"] = total_analysis["roles"]
        audit["keywords_found"] = list(total_analysis["keywords"])
        
        if total_analysis["names"] == 0:
            audit["quality"] = "None"
        elif total_analysis["names"] < 3:
            audit["quality"] = "Low"
        elif total_analysis["names"] < 10:
            audit["quality"] = "Medium"
        else:
            audit["quality"] = "High"
        
        # Deduplicate
        seen = set()
        final = []
        for l in all_leaders:
            key = (l.name.lower(), l.role.lower())
            if key not in seen:
                seen.add(key)
                final.append(l)
        
        final.sort(key=lambda x: x.confidence, reverse=True)
        final = final[:5]
        
        # Generate audit report
        if len(final) > 0:
            audit["confidence"] = 90 if len(final) >= 3 else 70
            audit["reason"] = "Successful extraction"
            audit["recommendation"] = "Results look good"
        else:
            if audit["quality"] == "None":
                audit["confidence"] = 0
                audit["reason"] = "No leadership content on website"
                audit["recommendation"] = "Website may not have public team info"
            elif audit["quality"] in ["Low", "Medium"]:
                audit["confidence"] = 40
                audit["reason"] = f"Content exists ({audit['names_detected']} names, {audit['roles_detected']} roles) but extraction failed"
                audit["recommendation"] = "⚠️ MANUAL CHECK RECOMMENDED - Data detected but structure complex"
            else:
                audit["confidence"] = 60
                audit["reason"] = f"HIGH-QUALITY content ({audit['names_detected']} names, {audit['roles_detected']} roles) but pairing failed"
                audit["recommendation"] = "🔴 DEFINITELY MANUAL CHECK - Names and roles exist but not extracted properly"
        
        # Print Audit
        print(f"\n{'='*80}")
        print(f"📊 AUDIT REPORT")
        print(f"{'='*80}")
        print(f"Status: {'✅ SUCCESS' if len(final) > 0 else '⚠️ NEEDS REVIEW'}")
        print(f"Leaders Extracted: {len(final)}")
        print(f"Confidence: {audit['confidence']}%")
        print(f"\n🔍 Diagnostics:")
        print(f"   Pages Checked: {audit['pages_checked']}")
        print(f"   Content Quality: {audit['quality']}")
        print(f"   Names Detected: {audit['names_detected']}")
        print(f"   Roles Detected: {audit['roles_detected']}")
        if audit['keywords_found']:
            print(f"   Keywords: {', '.join(audit['keywords_found'][:5])}")
        print(f"\n💡 Analysis:")
        print(f"   {audit['reason']}")
        print(f"   {audit['recommendation']}")
        print(f"{'='*80}\n")
        
        # Build result
        by_category = {}
        for l in final:
            if l.category not in by_category:
                by_category[l.category] = []
            by_category[l.category].append({
                "name": l.name,
                "role": l.role,
                "confidence": round(l.confidence, 2)
            })
        
        result = {
            "success": len(final) > 0,
            "company_url": company_url,
            "total_leaders": len(final),
            "leaders_by_category": by_category,
            "all_leaders": [asdict(l) for l in final],
            "audit": audit
        }
        
        if final:
            print("📋 Leaders Found:")
            for i, l in enumerate(final, 1):
                print(f"   {i}. {l.name}")
                print(f"      Role: {l.role}")
                print(f"      Category: {l.category}")
                print(f"      Method: {l.method}")
                print()
        
        return result
        
    finally:
        fetcher.close()

# Wrapper
def run_discovery_sync(website: str, company_name: str = ""):
    result = scrape_with_ai(website)
    payload = {
        "leaders_raw": result.get("all_leaders", []),
        "case2_management": result.get("leaders_by_category", {}),
        "success": result.get("success", False),
        "audit": result.get("audit", {})
    }
    return payload, ""

# CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scraper_ai_powered.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    result = scrape_with_ai(url)
    
    # Save
    try:
        with open("ai_scraper_results.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to: ai_scraper_results.json")
    except:
        pass
