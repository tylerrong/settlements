import sqlite3
import json
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    defendant TEXT,
    case_name TEXT,
    case_number TEXT,
    category TEXT,
    eligibility_summary TEXT,
    state_scope TEXT,
    proof_required TEXT,
    claim_required TEXT,
    claim_deadline TEXT,
    exclusion_deadline TEXT,
    objection_deadline TEXT,
    fairness_hearing_date TEXT,
    estimated_payout TEXT,
    max_payout TEXT,
    settlement_fund TEXT,
    claim_form_url TEXT,
    official_website_url TEXT,
    documents_url TEXT,
    administrator TEXT,
    source_url TEXT NOT NULL,
    date_discovered TEXT NOT NULL,
    last_checked TEXT NOT NULL,
    status TEXT DEFAULT 'new',
    confidence_score REAL DEFAULT 0.0,
    raw_text TEXT,
    UNIQUE(title, source_url)
);

CREATE TABLE IF NOT EXISTS crawl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    crawled_at TEXT NOT NULL,
    settlements_found INTEGER DEFAULT 0,
    error TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
