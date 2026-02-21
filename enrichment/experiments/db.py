"""Enrichment database — separate SQLite DB for DH contact discovery data."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "enrichment.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status TEXT DEFAULT 'running',
    scope TEXT,
    facilities_targeted INTEGER,
    facilities_completed INTEGER DEFAULT 0,
    facilities_failed INTEGER DEFAULT 0,
    contacts_found INTEGER DEFAULT 0,
    config_json TEXT
);

CREATE TABLE IF NOT EXISTS api_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    definitive_id INTEGER,
    params_json TEXT,
    http_status INTEGER,
    records_returned INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS executives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    definitive_id INTEGER NOT NULL,
    person_id INTEGER,
    executive_id INTEGER,
    first_name TEXT,
    last_name TEXT,
    prefix TEXT,
    suffix TEXT,
    credentials TEXT,
    gender TEXT,
    department TEXT,
    position_level TEXT,
    standardized_title TEXT,
    title TEXT,
    primary_email TEXT,
    direct_email TEXT,
    direct_phone TEXT,
    location_phone TEXT,
    mobile_phone TEXT,
    linkedin_url TEXT,
    physician_flag BOOLEAN,
    physician_leader BOOLEAN,
    executive_npi INTEGER,
    last_updated_date TEXT,
    icp_matched BOOLEAN DEFAULT 0,
    icp_title TEXT,
    icp_department TEXT,
    icp_category TEXT,
    icp_intent_score INTEGER,
    icp_function_type TEXT,
    icp_job_level TEXT,
    facility_name TEXT,
    parent_system TEXT,
    hospital_type TEXT,
    ehr_vendor TEXT,
    segment TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(executive_id, definitive_id)
);

CREATE TABLE IF NOT EXISTS physicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    definitive_id INTEGER NOT NULL,
    person_id INTEGER,
    npi INTEGER,
    first_name TEXT,
    last_name TEXT,
    credentials TEXT,
    role TEXT,
    gender TEXT,
    primary_specialty TEXT,
    primary_practice_city TEXT,
    primary_practice_state TEXT,
    primary_practice_phone TEXT,
    primary_hospital_affiliation TEXT,
    primary_hospital_def_id TEXT,
    secondary_hospital_affiliation TEXT,
    secondary_hospital_def_id TEXT,
    medicare_payments REAL,
    medicare_unique_patients INTEGER,
    num_procedures INTEGER,
    facility_name TEXT,
    parent_system TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(npi, definitive_id)
);

CREATE TABLE IF NOT EXISTS rfp_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    definitive_id INTEGER NOT NULL,
    rfp_id INTEGER,
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    contact_title TEXT,
    rfp_type TEXT,
    rfp_category TEXT,
    rfp_classification TEXT,
    date_posted TEXT,
    date_due TEXT,
    posting_link TEXT,
    description TEXT,
    facility_name TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    definitive_id INTEGER NOT NULL,
    intelligence_type TEXT,
    publication_date TEXT,
    news_title TEXT,
    body_excerpt TEXT,
    person_mentioned TEXT,
    new_title TEXT,
    facility_name TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trigger_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    definitive_id INTEGER NOT NULL,
    signal_type TEXT,
    signal_source TEXT,
    signal_date TEXT,
    summary TEXT,
    raw_json TEXT,
    facility_name TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS account_enrichment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id),
    definitive_id INTEGER NOT NULL,
    data_type TEXT,
    metric_name TEXT,
    metric_value TEXT,
    numeric_value REAL,
    year INTEGER,
    description TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facility_status (
    definitive_id INTEGER PRIMARY KEY,
    hospital_name TEXT,
    parent_system TEXT,
    segment TEXT,
    last_processed_at TIMESTAMP,
    executives_found INTEGER DEFAULT 0,
    physicians_found INTEGER DEFAULT 0,
    rfp_contacts_found INTEGER DEFAULT 0,
    news_signals_found INTEGER DEFAULT 0,
    quality_metrics_found INTEGER DEFAULT 0,
    financial_metrics_found INTEGER DEFAULT 0,
    processing_status TEXT DEFAULT 'pending',
    error_message TEXT
);
"""


def init_db():
    """Create all tables (idempotent)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"[enrichment.db] Database initialized at {DB_PATH}")


def get_conn() -> sqlite3.Connection:
    """Return a connection with WAL mode and busy timeout for concurrent access."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn


def _retry_db_op(func, max_retries=10, delay=2):
    """Retry a DB operation with exponential backoff."""
    import time
    for attempt in range(max_retries):
        try:
            return func()
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise


def start_run(recipe: str, scope: str, facilities_targeted: int,
              config: dict = None) -> int:
    """Create a new run record and return its ID."""
    import json

    def _do():
        conn = get_conn()
        cur = conn.execute(
            """INSERT INTO runs (recipe, scope, facilities_targeted, config_json)
               VALUES (?, ?, ?, ?)""",
            (recipe, scope, facilities_targeted,
             json.dumps(config) if config else None),
        )
        run_id = cur.lastrowid
        conn.commit()
        conn.close()
        return run_id

    return _retry_db_op(_do)


def finish_run(run_id: int, status: str, facilities_completed: int,
               facilities_failed: int, contacts_found: int):
    """Mark a run as finished."""

    def _do():
        conn = get_conn()
        conn.execute(
            """UPDATE runs SET finished_at = CURRENT_TIMESTAMP,
               status = ?, facilities_completed = ?, facilities_failed = ?,
               contacts_found = ? WHERE id = ?""",
            (status, facilities_completed, facilities_failed, contacts_found, run_id),
        )
        conn.commit()
        conn.close()

    _retry_db_op(_do)


if __name__ == "__main__":
    init_db()
