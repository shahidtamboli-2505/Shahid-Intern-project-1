# backend/db.py
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent.parent / "data" / "db.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cached_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS business (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        address TEXT,
        phone TEXT,
        website TEXT,
        primary_category TEXT,
        query_tag TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

def cache_raw_results(query, results):
    """Store raw scraped list (as JSON) for a query"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO cached_results (query, result_json, created_at) VALUES (?, ?, ?)",
        (query, json.dumps(results, ensure_ascii=False), datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

def get_cached_results(query):
    """Return last cached raw results for this query or None"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT result_json, created_at FROM cached_results WHERE query = ? ORDER BY id DESC LIMIT 1", (query,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    try:
        return json.loads(row["result_json"])
    except Exception:
        return None

def insert_business_list(business_list, query_tag):
    """Insert cleaned businesses into business table (query_tag helps grouping)"""
    conn = get_conn()
    cur = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    for b in business_list:
        cur.execute("""
            INSERT INTO business (name, address, phone, website, primary_category, query_tag, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            b.get("name",""),
            b.get("address",""),
            b.get("phone",""),
            b.get("website",""),
            b.get("primary_category",""),
            query_tag,
            ts
        ))
    conn.commit()
    conn.close()

def fetch_businesses_by_query(query_tag):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, address, phone, website, primary_category, timestamp FROM business WHERE query_tag = ?", (query_tag,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_search_history(query):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO search_history (query, created_at) VALUES (?, ?)", (query, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()
