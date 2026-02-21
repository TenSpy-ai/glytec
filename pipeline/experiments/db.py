"""SQLite database setup — creates tables for the V1 pipeline."""

import sqlite3
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name TEXT NOT NULL,
    definitive_id TEXT,
    sfdc_account_id TEXT,
    city TEXT,
    state TEXT,
    segment TEXT,
    facility_count INTEGER,
    total_beds INTEGER,
    avg_beds_per_facility REAL,
    glytec_client TEXT,
    glytec_arr REAL,
    gc_opp REAL,
    cc_opp REAL,
    total_opp REAL,
    adj_total_opp REAL,
    rank INTEGER,
    score REAL,
    tier TEXT,
    UNIQUE(system_name)
);

CREATE TABLE IF NOT EXISTS facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name TEXT NOT NULL,
    definitive_id TEXT,
    highest_level_parent TEXT,
    firm_type TEXT,
    hospital_type TEXT,
    city TEXT,
    state TEXT,
    ehr_inpatient TEXT,
    staffed_beds INTEGER,
    net_operating_profit_margin REAL,
    cms_overall_rating REAL,
    readmission_rate REAL,
    avg_length_of_stay REAL,
    icu_beds INTEGER,
    net_patient_revenue REAL,
    assigned_rep TEXT,
    hospital_ownership TEXT,
    geographic_classification TEXT,
    UNIQUE(definitive_id)
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    title TEXT,
    company TEXT,
    icp_category TEXT,
    icp_intent_score INTEGER,
    icp_function_type TEXT,
    icp_job_level TEXT,
    facility_definitive_id TEXT,
    account_name TEXT,
    linkedin_url TEXT,
    source TEXT,
    validated INTEGER DEFAULT 0,
    suppressed INTEGER DEFAULT 0,
    suppression_reason TEXT,
    icp_matched INTEGER DEFAULT 0,
    golden_record INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    salesforge_id TEXT,
    status TEXT DEFAULT 'draft',
    account_segment TEXT,
    contact_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER REFERENCES contacts(id),
    subject TEXT,
    body TEXT,
    layer1_persona TEXT,
    layer2_ehr TEXT,
    layer3_financial TEXT,
    signal_hook TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint TEXT,
    method TEXT,
    params TEXT,
    response_code INTEGER,
    response_summary TEXT
);
"""


def init_db():
    """Create all tables (idempotent)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"[db] Database initialized at {DB_PATH}")


def get_conn() -> sqlite3.Connection:
    """Return a connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    init_db()
