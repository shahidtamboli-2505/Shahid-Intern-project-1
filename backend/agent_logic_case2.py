# backend/agent_logic_case2.py
# Case 2 — AGENTIC SCRAPING (Top Management + Contact Email)
# -------------------------------------------------------
# 🤖 UPDATED: Now uses AI-powered scraper for better results
#
# Primary path:
#   Agent -> AI Scraper -> Decision Making -> Retry/Alternate/Skip
#
# Output formats:
# 1) output["case2_leaders"] = [{"name": "...", "role": "..."}]
# 2) output["case2_management"] = {5 buckets}

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
import re
import json
import time
import random
import logging

try:
    from backend.config import (
        CASE2_ENABLED,
        CASE2_MAX_LEADERS,
        AGENT_MAX_RETRIES,
        AGENT_RETRY_DELAY_MIN,
        AGENT_RETRY_DELAY_MAX,
        AGENT_ALTERNATE_PATHS,
    )
except ImportError:
    from config import (
        CASE2_ENABLED,
        CASE2_MAX_LEADERS,
        AGENT_MAX_RETRIES,
        AGENT_RETRY_DELAY_MIN,
        AGENT_RETRY_DELAY_MAX,
        AGENT_ALTERNATE_PATHS,
    )

# 🆕 SCRAPING-FIRST module - AI-POWERED
try:
    from backend.scraper_ai_powered import run_discovery_sync
except ImportError:
    try:
        from scraper_ai_powered import run_discovery_sync
    except ImportError:
        # Fallback to old scraper
        try:
            from backend.scraper_case2 import run_discovery_sync
        except ImportError:
            from scraper_case2 import run_discovery_sync

# LLM Client for decision making
try:
    from backend.gpt_client import GeminiClient
except ImportError:
    from gpt_client import GeminiClient

# Optional DB cache
try:
    from backend import db
except Exception:
    db = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -----------------------------
# Helpers
# -----------------------------
def _max_leaders() -> int:
    try:
        return max(1, min(int(CASE2_MAX_LEADERS or 5), 5))
    except Exception:
        return 5


def _norm(s: Any) -> str:
    return re.sub(r"\s+", " ", ("" if s is None else str(s)).strip())


def _safe_json_load(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return x
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        try:
            return json.loads(s)
        except Exception:
            return None
    return None


def _make_cache_key(company_name: str, website_url: str, cache_key: str = "") -> str:
    if cache_key:
        return _norm(cache_key)

    website_url = _norm(website_url)
    company_name = _norm(company_name)

    try:
        host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", website_url)).split("/")[0].strip().lower()
    except Exception:
        host = website_url.strip().lower()

    return f"case2::{host}::{company_name.lower()[:80]}"


# -----------------------------
# Buckets
# -----------------------------
BUCKETS = [
    "Executive Leadership",
    "Technology / Operations",
    "Finance / Administration",
    "Business Development / Growth",
    "Marketing / Branding",
]


def _empty_management() -> Dict[str, Dict[str, str]]:
    base = {"name": "", "designation": "", "email": "", "phone": "", "linkedin": ""}
    return {b: dict(base) for b in BUCKETS}


def _leadership_found_strict(mgmt: Dict[str, Dict[str, str]]) -> bool:
    if not isinstance(mgmt, dict):
        return False
    for b in BUCKETS:
        d = mgmt.get(b) or {}
        if _norm(d.get("name", "")):
            return True
    return False


# -----------------------------
# Role normalization
# -----------------------------
_BUCKET_RULES: List[Tuple[str, List[str]]] = [
    (
        "Executive Leadership",
        [
            "founder", "co-founder", "cofounder", "ceo", "chief executive",
            "managing director", "md", "director", "executive director",
            "chairman", "chairperson", "president",
            "principal", "dean", "medical director", "clinical director",
            "owner", "proprietor",
        ],
    ),
    (
        "Technology / Operations",
        [
            "cto", "chief technology", "cio", "chief information",
            "coo", "chief operating",
            "operations", "it head", "technical", "plant head",
            "head of operations", "administrator",
        ],
    ),
    (
        "Finance / Administration",
        [
            "cfo", "chief financial", "finance", "accounts", "controller",
            "treasurer", "admin", "administration", "hr head",
            "human resources", "compliance",
        ],
    ),
    (
        "Business Development / Growth",
        [
            "cro", "chief revenue officer", "chief revenue",
            "business development", "bd", "growth", "strategy",
            "partnership", "sales head",
            "admissions", "placement",
            "revenue", "commercial",
        ],
    ),
    (
        "Marketing / Branding",
        [
            "cmo", "chief marketing", "marketing", "brand",
            "communications", "pr", "digital marketing",
            "outreach", "social media",
        ],
    ),
]


def _map_role_to_bucket(role: str) -> str:
    r = _norm(role).lower()
    if not r:
        return ""
    for bucket, keys in _BUCKET_RULES:
        for k in keys:
            if k in r:
                return bucket
    return ""


def _clean_leaders_list(value: Any, max_leaders: int = 5) -> List[Dict[str, str]]:
    if max_leaders <= 0:
        max_leaders = 5

    parsed = _safe_json_load(value)
    if parsed is not None:
        value = parsed

    if isinstance(value, dict):
        value = value.get("leaders_raw") or value.get("leaders") or value.get("all_leaders") or []

    if not isinstance(value, list):
        return []

    out: List[Dict[str, str]] = []
    seen = set()
    for it in value:
        if not isinstance(it, dict):
            continue
        nm = _norm(it.get("name", ""))
        rl = _norm(it.get("role", "")) or _norm(it.get("designation", ""))
        if not nm or not rl:
            continue
        key = nm.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": nm, "role": rl})
        if len(out) >= max_leaders:
            break
    return out


def _leaders_to_management(leaders: List[Dict[str, str]], email: str = "") -> Dict[str, Dict[str, str]]:
    mgmt = _empty_management()
    seen_buckets = set()

    for it in leaders or []:
        name = _norm(it.get("name", ""))
        role = _norm(it.get("role", "")) or _norm(it.get("designation", ""))
        if not name or not role:
            continue

        bucket = _map_role_to_bucket(role)
        if not bucket:
            continue
        if bucket in seen_buckets:
            continue

        mgmt[bucket]["name"] = name
        mgmt[bucket]["designation"] = role

        if bucket == "Executive Leadership" and email:
            mgmt[bucket]["email"] = _norm(email)

        seen_buckets.add(bucket)
        if len(seen_buckets) >= 5:
            break

    return mgmt


def _normalize_management_from_payload(payload: Any, email: str = "") -> Dict[str, Dict[str, str]]:
    base = _empty_management()

    if not isinstance(payload, dict):
        return base

    mgmt = payload.get("case2_management") or payload.get("leaders_by_category")
    if isinstance(mgmt, str):
        mgmt = _safe_json_load(mgmt)

    if isinstance(mgmt, dict):
        for b in BUCKETS:
            v = mgmt.get(b)
            if isinstance(v, dict):
                nm = _norm(v.get("name", ""))
                dg = _norm(v.get("designation", "")) or _norm(v.get("role", ""))

                if nm:
                    base[b]["name"] = nm
                    base[b]["designation"] = dg
                    base[b]["email"] = _norm(v.get("email", "")) or base[b]["email"]
                    base[b]["phone"] = _norm(v.get("phone", "")) or base[b]["phone"]
                    base[b]["linkedin"] = _norm(v.get("linkedin", "")) or base[b]["linkedin"]
            elif isinstance(v, list) and v:
                # Handle list format from AI scraper
                first = v[0] if isinstance(v[0], dict) else {}
                nm = _norm(first.get("name", ""))
                dg = _norm(first.get("role", ""))
                
                if nm:
                    base[b]["name"] = nm
                    base[b]["designation"] = dg

        if email and not base["Executive Leadership"]["email"]:
            base["Executive Leadership"]["email"] = _norm(email)

        return base

    leaders = _clean_leaders_list(payload, max_leaders=_max_leaders())
    return _leaders_to_management(leaders, email=email)


# ------------------------------------------------------------
# Cache helpers
# ------------------------------------------------------------
def _cache_get(cache_key: str) -> Optional[Dict[str, Any]]:
    if not db:
        return None
    fn = getattr(db, "get_case2_cache", None)
    if callable(fn):
        try:
            return fn(cache_key)
        except Exception:
            return None
    return None


def _cache_set(cache_key: str, payload: Dict[str, Any]) -> None:
    if not db:
        return
    fn = getattr(db, "save_case2_cache", None)
    if callable(fn):
        try:
            fn(cache_key, payload)
        except Exception:
            pass


# ------------------------------------------------------------
# 🤖 AGENTIC LOGIC
# ------------------------------------------------------------
class Case2Agent:
    """Autonomous agent for Case 2 with retry and decision logic"""
    
    def __init__(self):
        try:
            self.llm_client = GeminiClient()
            self.use_llm_decisions = self.llm_client.is_enabled()
        except:
            self.use_llm_decisions = False
        
        if self.use_llm_decisions:
            logger.info("🤖 Agent initialized with LLM decision making")
        else:
            logger.info("🤖 Agent initialized with rule-based decision making")
    
    def _get_base_url(self, url: str) -> str:
        url = _norm(url)
        try:
            url_clean = re.sub(r'^https?://', '', url)
            base = url_clean.split('?')[0].rstrip('/')
            return f"https://{base}"
        except:
            return url
    
    def _try_alternate_urls(self, base_url: str, company_name: str) -> Tuple[Optional[Dict], str]:
        base = self._get_base_url(base_url)
        
        for path in AGENT_ALTERNATE_PATHS:
            url = f"{base}{path}"
            logger.info(f"🔍 Trying alternate URL: {url}")
            
            try:
                payload, email = run_discovery_sync(website=url, company_name=company_name)
                
                leaders = _clean_leaders_list(payload.get("leaders_raw") if isinstance(payload, dict) else payload)
                if leaders:
                    logger.info(f"✅ Found {len(leaders)} leaders at {url}")
                    return (payload, email)
                    
            except Exception as e:
                logger.debug(f"Failed alternate URL {url}: {e}")
                continue
        
        return (None, "")
    
    def _decide_next_action(self, context: Dict[str, Any]) -> str:
        attempt = context.get("attempt", 0)
        max_retries = context.get("max_retries", AGENT_MAX_RETRIES)
        has_leaders = context.get("has_leaders", False)
        error_type = context.get("error_type", "")
        
        if has_leaders:
            return "SUCCESS"
        
        if attempt >= max_retries:
            return "SKIP"
        
        if "timeout" in error_type.lower() or "network" in error_type.lower():
            if attempt < max_retries - 1:
                return "RETRY"
            else:
                return "TRY_ALTERNATE"
        
        if "captcha" in error_type.lower() or "blocked" in error_type.lower():
            return "TRY_ALTERNATE"
        
        if attempt == 0:
            return "TRY_ALTERNATE"
        else:
            return "RETRY" if attempt < max_retries - 1 else "SKIP"
    
    def scrape_with_agent(self, company_name: str, website_url: str) -> Dict[str, Any]:
        logger.info(f"\n{'='*60}")
        logger.info(f"🏢 Processing: {company_name}")
        logger.info(f"🌐 Website: {website_url}")
        
        for attempt in range(1, AGENT_MAX_RETRIES + 1):
            logger.info(f"🔄 Attempt {attempt}/{AGENT_MAX_RETRIES}")
            
            try:
                payload, email = run_discovery_sync(website=website_url, company_name=company_name)
                
                leaders = _clean_leaders_list(
                    payload.get("leaders_raw") or payload.get("all_leaders") if isinstance(payload, dict) else payload
                )
                
                if leaders:
                    logger.info(f"✅ Success! Found {len(leaders)} leaders")
                    return self._build_output(payload, email, leaders)
                
                context = {
                    "attempt": attempt,
                    "max_retries": AGENT_MAX_RETRIES,
                    "has_leaders": False,
                    "error_type": "no_data"
                }
                
                action = self._decide_next_action(context)
                logger.info(f"🤖 Decision: {action}")
                
                if action == "TRY_ALTERNATE":
                    logger.info("🔍 Trying alternate URLs...")
                    alt_payload, alt_email = self._try_alternate_urls(website_url, company_name)
                    
                    if alt_payload:
                        alt_leaders = _clean_leaders_list(
                            alt_payload.get("leaders_raw") or alt_payload.get("all_leaders") if isinstance(alt_payload, dict) else alt_payload
                        )
                        if alt_leaders:
                            logger.info(f"✅ Success via alternate URL! Found {len(alt_leaders)} leaders")
                            return self._build_output(alt_payload, alt_email, alt_leaders)
                
                elif action == "SKIP":
                    logger.warning(f"⏭️ Skipping after {attempt} attempts")
                    break
                
                if attempt < AGENT_MAX_RETRIES:
                    delay = random.uniform(AGENT_RETRY_DELAY_MIN, AGENT_RETRY_DELAY_MAX)
                    logger.info(f"⏳ Waiting {delay:.1f}s before next attempt...")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Error on attempt {attempt}: {e}")
                
                context = {
                    "attempt": attempt,
                    "max_retries": AGENT_MAX_RETRIES,
                    "has_leaders": False,
                    "error_type": str(e)
                }
                
                action = self._decide_next_action(context)
                
                if action == "SKIP" or attempt >= AGENT_MAX_RETRIES:
                    break
                
                if attempt < AGENT_MAX_RETRIES:
                    delay = random.uniform(AGENT_RETRY_DELAY_MIN, AGENT_RETRY_DELAY_MAX)
                    time.sleep(delay)
        
        logger.error(f"❌ Failed after {AGENT_MAX_RETRIES} attempts")
        return self._build_output({}, "", [])
    
    def _build_output(self, payload: Dict, email: str, leaders: List[Dict]) -> Dict[str, Any]:
        mgmt = _normalize_management_from_payload(payload, email=email)
        
        return {
            "case2_leaders": leaders,
            "case2_email": _norm(email),
            "case2_management": mgmt,
            "Leadership Found": "Yes" if _leadership_found_strict(mgmt) else "No",
        }


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------
def run_case2_enrichment(
    company_name: str,
    website_url: str,
    cache_key: str = "",
    use_agent: bool = True,
) -> Dict[str, Any]:
    """
    Main Case-2 entry with AGENTIC mode using AI scraper.
    
    Args:
        company_name: Company name
        website_url: Website URL
        cache_key: Optional cache key
        use_agent: Use agentic retry logic
    
    Returns:
        Dict with case2_leaders, case2_email, case2_management, Leadership Found
    """
    out: Dict[str, Any] = {
        "case2_leaders": [],
        "case2_email": "",
        "case2_management": _empty_management(),
        "Leadership Found": "No",
    }

    if not CASE2_ENABLED:
        return out

    website_url = _norm(website_url)
    company_name = _norm(company_name)

    if not website_url:
        return out

    cache_key = _make_cache_key(company_name, website_url, cache_key)

    # Check cache
    if cache_key:
        cached = _cache_get(cache_key)
        if isinstance(cached, dict):
            cached.setdefault("case2_leaders", [])
            cached.setdefault("case2_email", "")
            cached.setdefault("case2_management", _empty_management())
            cached.setdefault("Leadership Found", "No")
            logger.info(f"✅ Cache hit for {company_name}")
            return cached

    # Scrape with agent or direct
    if use_agent:
        agent = Case2Agent()
        result = agent.scrape_with_agent(company_name, website_url)
    else:
        try:
            payload, email = run_discovery_sync(website=website_url, company_name=company_name)
            email = _norm(email)
            leaders = _clean_leaders_list(
                payload.get("leaders_raw") or payload.get("all_leaders") if isinstance(payload, dict) else payload,
                max_leaders=_max_leaders(),
            )
            mgmt = _normalize_management_from_payload(payload, email=email)
            
            result = {
                "case2_leaders": leaders,
                "case2_email": email,
                "case2_management": mgmt,
                "Leadership Found": "Yes" if _leadership_found_strict(mgmt) else "No",
            }
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            result = out

    # Save to cache
    if cache_key:
        _cache_set(cache_key, result)

    return result


# Backward compatibility
def run_case2_top_management(company_name: str, website_url: str) -> Dict[str, Any]:
    """Legacy wrapper"""
    output: Dict[str, Any] = {}
    max_leaders = _max_leaders()

    for i in range(1, 6):
        output[f"Leader {i} Name"] = ""
        output[f"Leader {i} Role"] = ""

    if not CASE2_ENABLED:
        output["case2_leaders"] = []
        return output

    data = run_case2_enrichment(
        company_name=company_name or "",
        website_url=website_url or "",
        cache_key="",
        use_agent=True,
    )

    leaders = (data.get("case2_leaders") or [])[:max_leaders]
    output["case2_leaders"] = leaders

    for idx, leader in enumerate(leaders[:5]):
        col = idx + 1
        output[f"Leader {col} Name"] = _norm(leader.get("name", "")) or ""
        output[f"Leader {col} Role"] = _norm(leader.get("role", "")) or ""

    return output