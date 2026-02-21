"""GTM Operations database — 16-table schema + indexes + ICP seeding."""

import json
import sqlite3
from pathlib import Path

# Import config carefully — support both direct run and module import
try:
    from salesforge.config import DB_PATH, ICP_JSON
except ImportError:
    from config import DB_PATH, ICP_JSON

SCHEMA = """
-- ═══════════════════════════════════════════
-- CORE ENTITIES
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS accounts (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name           TEXT NOT NULL UNIQUE,
    definitive_id         TEXT,
    sfdc_account_id       TEXT,
    city                  TEXT,
    state                 TEXT,
    segment               TEXT,
    facility_count        INTEGER,
    total_beds            INTEGER,
    avg_beds_per_facility REAL,
    primary_ehr           TEXT,
    operating_margin_avg  REAL,
    cms_rating_avg        REAL,
    readmission_rate_avg  REAL,
    glytec_client         TEXT,
    glytec_arr            REAL,
    gc_opp                REAL,
    cc_opp                REAL,
    total_opp             REAL,
    adj_total_opp         REAL,
    rank                  INTEGER,
    score                 REAL,
    tier                  TEXT,
    trigger_signal        TEXT,
    trigger_date          TEXT,
    assigned_rep          TEXT,
    notes                 TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facilities (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name             TEXT NOT NULL,
    definitive_id             TEXT UNIQUE,
    highest_level_parent      TEXT,
    city                      TEXT,
    state                     TEXT,
    firm_type                 TEXT,
    hospital_type             TEXT,
    hospital_ownership        TEXT,
    ehr_inpatient             TEXT,
    staffed_beds              INTEGER,
    icu_beds                  INTEGER,
    net_operating_profit_margin REAL,
    cms_overall_rating        REAL,
    readmission_rate          REAL,
    avg_length_of_stay        REAL,
    net_patient_revenue       REAL,
    assigned_rep              TEXT,
    created_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contacts (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name              TEXT,
    last_name               TEXT,
    email                   TEXT,
    title                   TEXT,
    phone                   TEXT,
    company                 TEXT,
    linkedin_url            TEXT,
    account_name            TEXT,
    facility_definitive_id  TEXT,
    icp_category            TEXT,
    icp_intent_score        INTEGER,
    icp_function_type       TEXT,
    icp_job_level           TEXT,
    icp_department          TEXT,
    icp_matched             INTEGER DEFAULT 0,
    source                  TEXT,
    validated               INTEGER DEFAULT 0,
    golden_record           INTEGER DEFAULT 0,
    suppressed              INTEGER DEFAULT 0,
    suppression_reason      TEXT,
    salesforge_lead_id      TEXT,
    last_pushed_at          TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email)
);

CREATE TABLE IF NOT EXISTS icp_titles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    department      TEXT,
    title           TEXT,
    category        TEXT,
    intent_score    INTEGER,
    function_type   TEXT,
    job_level       TEXT
);

-- ═══════════════════════════════════════════
-- CAMPAIGN MANAGEMENT
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS campaign_ideas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    description     TEXT,
    target_segment  TEXT,
    target_ehr      TEXT,
    target_geo      TEXT,
    target_tier     TEXT,
    target_persona  TEXT,
    priority        TEXT DEFAULT 'medium',
    status          TEXT DEFAULT 'idea',
    estimated_contacts INTEGER,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    idea_id         INTEGER REFERENCES campaign_ideas(id),
    salesforge_seq_id TEXT,
    salesforge_status TEXT,
    target_segment  TEXT,
    target_ehr      TEXT,
    target_geo      TEXT,
    target_tier     TEXT,
    target_persona  TEXT,
    step_count      INTEGER DEFAULT 1,
    mailbox_count   INTEGER DEFAULT 0,
    contact_count   INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'draft',
    launched_at     TIMESTAMP,
    paused_at       TIMESTAMP,
    completed_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaign_contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL REFERENCES campaigns(id),
    contact_id      INTEGER NOT NULL REFERENCES contacts(id),
    enrolled_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          TEXT DEFAULT 'enrolled',
    emails_sent     INTEGER DEFAULT 0,
    emails_opened   INTEGER DEFAULT 0,
    emails_clicked  INTEGER DEFAULT 0,
    replied         INTEGER DEFAULT 0,
    reply_type      TEXT,
    bounced         INTEGER DEFAULT 0,
    UNIQUE(campaign_id, contact_id)
);

CREATE TABLE IF NOT EXISTS campaign_steps (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id         INTEGER NOT NULL REFERENCES campaigns(id),
    step_order          INTEGER NOT NULL,
    step_name           TEXT,
    wait_days           INTEGER DEFAULT 0,
    email_subject       TEXT,
    email_body_html     TEXT,
    email_body_plain    TEXT,
    layer1_persona      TEXT,
    layer2_ehr          TEXT,
    layer3_financial    TEXT,
    signal_hook         TEXT,
    variant_label       TEXT DEFAULT 'A',
    distribution_weight INTEGER DEFAULT 100,
    salesforge_step_id    TEXT,
    salesforge_variant_id TEXT,
    synced_at             TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category        TEXT,
    persona         TEXT,
    ehr_segment     TEXT,
    subject         TEXT,
    body_html       TEXT,
    body_plain      TEXT,
    tags            TEXT,
    times_used      INTEGER DEFAULT 0,
    avg_open_rate   REAL,
    avg_reply_rate  REAL,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════
-- ENGAGEMENT TRACKING
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS engagement_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    contact_id      INTEGER REFERENCES contacts(id),
    contact_email   TEXT,
    event_type      TEXT NOT NULL,
    event_date      TIMESTAMP,
    metadata        TEXT,
    source          TEXT DEFAULT 'api_pull',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reply_threads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    salesforge_thread_id TEXT,
    campaign_id         INTEGER REFERENCES campaigns(id),
    contact_id          INTEGER REFERENCES contacts(id),
    contact_email       TEXT,
    contact_first_name  TEXT,
    contact_last_name   TEXT,
    subject             TEXT,
    content             TEXT,
    reply_type          TEXT,
    sentiment           TEXT,
    mailbox_id          TEXT,
    event_date          TIMESTAMP,
    status              TEXT DEFAULT 'new',
    handled_by          TEXT,
    handled_at          TIMESTAMP,
    follow_up_notes     TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(salesforge_thread_id)
);

-- ═══════════════════════════════════════════
-- DELIVERABILITY & MAILBOX HEALTH
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS mailboxes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    salesforge_id       TEXT UNIQUE,
    address             TEXT NOT NULL,
    first_name          TEXT,
    last_name           TEXT,
    daily_email_limit   INTEGER,
    provider            TEXT,
    status              TEXT,
    disconnect_reason   TEXT,
    tracking_domain     TEXT,
    last_synced_at      TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mailbox_health_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mailbox_id      INTEGER REFERENCES mailboxes(id),
    snapshot_date   DATE NOT NULL,
    status          TEXT,
    disconnect_reason TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mailbox_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS dnc_list (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    reason          TEXT,
    source          TEXT,
    added_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pushed_to_salesforge INTEGER DEFAULT 0,
    pushed_at       TIMESTAMP
);

-- ═══════════════════════════════════════════
-- REPORTING & METRICS
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS metric_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    salesforge_seq_id TEXT,
    snapshot_date   DATE NOT NULL,
    contacted       INTEGER DEFAULT 0,
    sent            INTEGER DEFAULT 0,
    opened          INTEGER DEFAULT 0,
    unique_opened   INTEGER DEFAULT 0,
    clicked         INTEGER DEFAULT 0,
    unique_clicked  INTEGER DEFAULT 0,
    replied         INTEGER DEFAULT 0,
    bounced         INTEGER DEFAULT 0,
    unsubscribed    INTEGER DEFAULT 0,
    open_rate       REAL,
    reply_rate      REAL,
    bounce_rate     REAL,
    click_rate      REAL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS account_engagement (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name    TEXT NOT NULL,
    total_contacts  INTEGER DEFAULT 0,
    contacts_enrolled INTEGER DEFAULT 0,
    contacts_opened INTEGER DEFAULT 0,
    contacts_replied INTEGER DEFAULT 0,
    contacts_bounced INTEGER DEFAULT 0,
    latest_campaign TEXT,
    latest_activity_date TIMESTAMP,
    engagement_tier TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_name)
);

-- ═══════════════════════════════════════════
-- OPERATIONS
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS api_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint        TEXT,
    method          TEXT,
    params          TEXT,
    response_code   INTEGER,
    response_summary TEXT
);

CREATE TABLE IF NOT EXISTS sync_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity          TEXT NOT NULL UNIQUE,
    last_synced_at  TIMESTAMP,
    last_offset     INTEGER DEFAULT 0,
    total_records   INTEGER,
    notes           TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ui_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task            TEXT NOT NULL,
    category        TEXT,
    priority        TEXT DEFAULT 'medium',
    status          TEXT DEFAULT 'pending',
    context         TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meetings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id      INTEGER REFERENCES contacts(id),
    account_name    TEXT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    meeting_date    DATE,
    meeting_type    TEXT,
    outcome         TEXT,
    notes           TEXT,
    attributed_to   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_account ON contacts(account_name);
CREATE INDEX IF NOT EXISTS idx_contacts_icp ON contacts(icp_category, icp_function_type);
CREATE INDEX IF NOT EXISTS idx_contacts_suppressed ON contacts(suppressed);
CREATE INDEX IF NOT EXISTS idx_contacts_salesforge ON contacts(salesforge_lead_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_sf ON campaigns(salesforge_seq_id);
CREATE INDEX IF NOT EXISTS idx_campaign_contacts_cid ON campaign_contacts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_contacts_contact ON campaign_contacts(contact_id);
CREATE INDEX IF NOT EXISTS idx_engagement_campaign ON engagement_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_engagement_contact ON engagement_events(contact_id);
CREATE INDEX IF NOT EXISTS idx_engagement_type ON engagement_events(event_type);
CREATE INDEX IF NOT EXISTS idx_metrics_campaign ON metric_snapshots(campaign_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_dnc_email ON dnc_list(email);
CREATE INDEX IF NOT EXISTS idx_reply_threads_status ON reply_threads(status);
CREATE INDEX IF NOT EXISTS idx_account_engagement ON account_engagement(engagement_tier);
"""


def init_db():
    """Create all tables, indexes, and seed ICP titles (idempotent)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    conn.executescript(INDEXES)

    # Seed icp_titles from ICP.json if empty
    count = conn.execute("SELECT COUNT(*) FROM icp_titles").fetchone()[0]
    if count == 0 and ICP_JSON.exists():
        with open(ICP_JSON, "r") as f:
            titles = json.load(f)
        for t in titles:
            conn.execute(
                """INSERT INTO icp_titles (department, title, category, intent_score, function_type, job_level)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (t["Department"], t["Title"], t["Category"], t["Intent Score"],
                 t["Function Type"], t["Job Level"]),
            )
        conn.commit()
        print(f"[db] Seeded {len(titles)} ICP titles from {ICP_JSON.name}")

    conn.commit()
    conn.close()
    print(f"[db] Database initialized at {DB_PATH}")
    print(f"[db] 20 tables + 15 indexes created")


def get_conn() -> sqlite3.Connection:
    """Return a connection with row factory + WAL mode enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


if __name__ == "__main__":
    init_db()
