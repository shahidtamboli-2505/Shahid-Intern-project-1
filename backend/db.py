# backend/db.py
# ✅ DB schema aligned with NEW startup output:
#    Company Name, Industry, Rating, Rating Count, Has Website, Website URL
#    + Case-2 leaders (Top 5) stored as JSON (case2_leaders_json)
# ✅ Backward compatible + safe migration
# ✅ No crashes if DB was created earlier

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "db.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _col_exists(conn: sqlite3.Connection, table: str, col: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    return col in cols


def _ensure_columns(conn: sqlite3.Connection, table: str, cols: Dict[str, str]) -> None:
    """
    cols = {"col_name": "SQL_TYPE", ...}
    Adds missing columns safely.
    """
    cur = conn.cursor()
    for c, sql_type in cols.items():
        if not _col_exists(conn, table, c):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {c} {sql_type}")


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # Search history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Cached results
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cached_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cache_key TEXT NOT NULL,
        result_type TEXT NOT NULL,
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Business table (base create)
    # NOTE: If business table already exists with old schema, this does nothing.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS business (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        industry TEXT,
        website_url TEXT,
        has_website INTEGER,
        google_rating REAL,
        rating_count INTEGER,
        case2_leaders_json TEXT,
        query_tag TEXT,
        timestamp TEXT
    )
    """)

    # Indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cached_cachekey ON cached_results(cache_key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_business_querytag ON business(query_tag)")

    # Soft migration: add missing columns if DB was old
    _ensure_columns(conn, "business", {
        "company_name": "TEXT",
        "industry": "TEXT",
        "website_url": "TEXT",
        "has_website": "INTEGER",
        "google_rating": "REAL",
        "rating_count": "INTEGER",
        "case2_leaders_json": "TEXT",
        "query_tag": "TEXT",
        "timestamp": "TEXT",
    })

    conn.commit()
    conn.close()


# -----------------------------
# Cache helpers
# -----------------------------
def make_cache_key(
    query: str,
    location: str = "",
    place: str = "",
    top_n: int = 0,
    case2_enabled: bool = False,
) -> str:
    payload = {
        "query": (query or "").strip().lower(),
        "location": (location or "").strip().lower(),
        "place": (place or "").strip().lower(),
        "top_n": int(top_n or 0),
        "case2_enabled": bool(case2_enabled),
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def cache_results(cache_key: str, result_type: str, results: Any) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cached_results (cache_key, result_type, result_json, created_at) VALUES (?, ?, ?, ?)",
        (cache_key, result_type, json.dumps(results, ensure_ascii=False), _now_iso()),
    )
    conn.commit()
    conn.close()


def get_cached_results(cache_key: str, result_type: str) -> Optional[Any]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT result_json FROM cached_results WHERE cache_key = ? AND result_type = ? ORDER BY id DESC LIMIT 1",
        (cache_key, result_type),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    try:
        return json.loads(row["result_json"])
    except Exception:
        return None


# -----------------------------
# Business storage
# -----------------------------
def _to_int_or_none(x: Any) -> Optional[int]:
    if x in (None, ""):
        return None
    try:
        s = str(x).strip().replace(",", "")
        if not s:
            return None
        return int(float(s))
    except Exception:
        return None


def _to_float_or_none(x: Any) -> Optional[float]:
    if x in (None, ""):
        return None
    try:
        s = str(x).strip().replace(",", "")
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def insert_business_list(business_list: List[Dict[str, Any]], query_tag: str) -> None:
    """
    Insert cleaned businesses into business table.
    Stores Case-2 leaders JSON if present:
      b["case2_leaders"] (list of {name,designation})
    """
    if not business_list:
        return

    conn = get_conn()
    cur = conn.cursor()
    ts = _now_iso()

    for b in business_list:
        company_name = b.get("Company Name") or b.get("company_name") or b.get("Name") or b.get("name") or ""
        industry = b.get("Industry") or b.get("industry") or b.get("Primary Category") or b.get("primary_category") or ""

        website_url = b.get("Website URL") or b.get("website_url") or b.get("Website") or b.get("website") or ""
        has_website_val = b.get("Has Website") if "Has Website" in b else b.get("has_website")

        if isinstance(has_website_val, bool):
            has_website_int = 1 if has_website_val else 0
        else:
            s = str(has_website_val).strip().lower()
            if s in {"yes", "true", "1"}:
                has_website_int = 1
            elif s in {"no", "false", "0"}:
                has_website_int = 0
            else:
                has_website_int = 1 if str(website_url).strip() else 0

        google_rating = b.get("Google Rating") if "Google Rating" in b else b.get("google_rating")
        rating_count = b.get("Rating Count") if "Rating Count" in b else (
            b.get("Google Rating Count") if "Google Rating Count" in b else b.get("google_rating_count")
        )

        leaders = b.get("case2_leaders") or b.get("leaders") or []
        if isinstance(leaders, dict) and "leaders" in leaders:
            leaders = leaders.get("leaders") or []
        if not isinstance(leaders, list):
            leaders = []
        case2_leaders_json = json.dumps(leaders, ensure_ascii=False) if leaders else ""

        cur.execute("""
            INSERT INTO business (
                company_name, industry,
                website_url, has_website,
                google_rating, rating_count,
                case2_leaders_json,
                query_tag, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(company_name),
            str(industry),
            str(website_url),
            int(has_website_int),
            _to_float_or_none(google_rating),
            _to_int_or_none(rating_count),
            str(case2_leaders_json),
            str(query_tag),
            ts,
        ))

    conn.commit()
    conn.close()


def fetch_businesses_by_query(query_tag: str) -> List[Dict[str, Any]]:
    """
    Fetch rows for a query_tag.
    Assumes init_db() has been called (recommended at app startup).
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            company_name, industry,
            website_url, has_website,
            google_rating, rating_count,
            case2_leaders_json,
            query_tag, timestamp
        FROM business
        WHERE query_tag = ?
        ORDER BY id ASC
    """, (query_tag,))
    rows = cur.fetchall()
    conn.close()

    out: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        try:
            d["case2_leaders"] = json.loads(d["case2_leaders_json"]) if d.get("case2_leaders_json") else []
        except Exception:
            d["case2_leaders"] = []
        out.append(d)
    return out


# -----------------------------
# Search history
# -----------------------------
def add_search_history(query: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO search_history (query, created_at) VALUES (?, ?)",
        (query, _now_iso()),
    )
    conn.commit()
    conn.close()
