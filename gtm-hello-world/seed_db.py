"""
GTM Hello World — Seed Database
Creates schema + inserts seed data into gtm_hello_world.db.

Usage:
    python seed_db.py
"""

import sqlite3
from config import DB_PATH


def get_schema() -> str:
    """Return the full DDL for the hello-world subset schema (12 tables)."""
    return """
    -- ===========================================
    -- CORE ENTITIES
    -- ===========================================

    CREATE TABLE IF NOT EXISTS accounts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        system_name     TEXT NOT NULL UNIQUE,
        segment         TEXT,
        total_beds      INTEGER,
        primary_ehr     TEXT,
        score           REAL,
        tier            TEXT,       -- Priority / Active / Nurture / Monitor
        total_opp       REAL,
        assigned_rep    TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS contacts (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name          TEXT,
        last_name           TEXT,
        email               TEXT UNIQUE,
        title               TEXT,
        company_name        TEXT,
        account_name        TEXT,       -- FK -> accounts.system_name
        icp_category        TEXT,       -- Decision Maker / Influencer
        icp_intent_score    INTEGER,
        icp_department      TEXT,
        icp_job_level       TEXT,
        instantly_lead_id   TEXT,
        email_verified      TEXT,       -- valid / invalid / risky / unknown / NULL
        email_verified_at   TIMESTAMP,
        last_pushed_at      TIMESTAMP,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ===========================================
    -- CAMPAIGN MANAGEMENT
    -- ===========================================

    CREATE TABLE IF NOT EXISTS campaigns (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        name                    TEXT NOT NULL,
        instantly_campaign_id   TEXT,
        instantly_status        INTEGER, -- 0=Draft, 1=Active, 2=Paused, 3=Completed, 4=Running Subsequences, -99=Suspended, -1=Unhealthy, -2=Bounce Protect
        recipe                  TEXT,       -- R3, R4, R5, etc.
        target_segment          TEXT,
        target_ehr              TEXT,
        target_persona          TEXT,
        step_count              INTEGER DEFAULT 3,
        daily_limit             INTEGER DEFAULT 30,
        email_gap               INTEGER DEFAULT 10,
        stop_on_reply           INTEGER DEFAULT 1,
        open_tracking           INTEGER DEFAULT 0,
        link_tracking           INTEGER DEFAULT 0,
        status                  TEXT DEFAULT 'draft',
        launched_at             TIMESTAMP,
        paused_at               TIMESTAMP,
        created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS campaign_contacts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id     INTEGER NOT NULL REFERENCES campaigns(id),
        contact_id      INTEGER NOT NULL REFERENCES contacts(id),
        enrolled_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status          TEXT DEFAULT 'enrolled',
        emails_sent     INTEGER DEFAULT 0,
        emails_opened   INTEGER DEFAULT 0,
        replied         INTEGER DEFAULT 0,
        reply_type      TEXT,
        bounced         INTEGER DEFAULT 0,
        ai_interest     REAL,
        UNIQUE(campaign_id, contact_id)
    );

    -- ===========================================
    -- ENGAGEMENT TRACKING
    -- ===========================================

    CREATE TABLE IF NOT EXISTS metric_snapshots (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id             INTEGER REFERENCES campaigns(id),
        instantly_campaign_id   TEXT,
        snapshot_date           DATE NOT NULL,
        sent            INTEGER DEFAULT 0,
        opened          INTEGER DEFAULT 0,
        replied         INTEGER DEFAULT 0,
        bounced         INTEGER DEFAULT 0,
        open_rate       REAL,
        reply_rate      REAL,
        bounce_rate     REAL,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(campaign_id, snapshot_date)
    );

    CREATE TABLE IF NOT EXISTS reply_sentiment (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        instantly_email_id      TEXT,
        campaign_id             INTEGER REFERENCES campaigns(id),
        contact_id              INTEGER REFERENCES contacts(id),
        contact_email           TEXT,
        sentiment               TEXT NOT NULL,   -- positive, negative, neutral, ooo, bounce
        sentiment_confidence    REAL,
        classified_by           TEXT,            -- ai, manual, keyword
        pushed_to_clay          INTEGER DEFAULT 0,
        pushed_at               TIMESTAMP,
        clay_webhook_response   TEXT,
        salesforce_lead_id      TEXT,
        created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS clay_push_log (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        reply_sentiment_id      INTEGER REFERENCES reply_sentiment(id),
        contact_email           TEXT,
        contact_first_name      TEXT,
        contact_last_name       TEXT,
        account_name            TEXT,
        campaign_name           TEXT,
        sentiment               TEXT,
        webhook_url             TEXT,
        payload_json            TEXT,
        response_code           INTEGER,
        response_body           TEXT,
        pushed_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        salesforce_sync_status  TEXT DEFAULT 'pending',
        salesforce_synced_at    TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS email_threads (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        instantly_thread_id     TEXT UNIQUE,
        instantly_email_id      TEXT,
        campaign_id             INTEGER REFERENCES campaigns(id),
        contact_id              INTEGER REFERENCES contacts(id),
        contact_email           TEXT,
        subject                 TEXT,
        body_text               TEXT,
        sender_account          TEXT,
        ue_type                 INTEGER,
        is_unread               INTEGER DEFAULT 1,
        ai_interest_value       REAL,
        status                  TEXT DEFAULT 'new',
        sentiment               TEXT,
        created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

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

    -- ===========================================
    -- MAILBOXES
    -- ===========================================

    CREATE TABLE IF NOT EXISTS mailboxes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        email           TEXT NOT NULL UNIQUE,
        first_name      TEXT,
        last_name       TEXT,
        daily_limit     INTEGER,
        status          INTEGER,        -- 1=Active
        warmup_status   INTEGER,        -- 1=Active
        warmup_score    REAL,
        last_synced_at  TIMESTAMP,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ===========================================
    -- OPERATIONS
    -- ===========================================

    CREATE TABLE IF NOT EXISTS api_log (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        interface       TEXT DEFAULT 'mcp',
        tool_or_endpoint TEXT,
        method          TEXT,
        params          TEXT,
        response_code   INTEGER,
        response_summary TEXT,
        duration_ms     INTEGER
    );

    -- ===========================================
    -- BLOCK LIST
    -- ===========================================

    CREATE TABLE IF NOT EXISTS block_list (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        value           TEXT NOT NULL UNIQUE,  -- email or domain
        is_domain       INTEGER DEFAULT 0,
        reason          TEXT,                  -- opt_out, bounce, manual, etc.
        instantly_id    TEXT,                  -- block list entry ID in Instantly
        added_by        TEXT DEFAULT 'manual',
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ===========================================
    -- AUTOPILOT
    -- ===========================================

    CREATE TABLE IF NOT EXISTS autopilot_runs (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        template                TEXT NOT NULL,
        campaign_name           TEXT,
        campaign_id             INTEGER REFERENCES campaigns(id),
        instantly_campaign_id   TEXT,
        query_desc              TEXT,
        contact_count           INTEGER,
        sender_count            INTEGER,
        schedule_type           TEXT,
        mode                    TEXT,          -- 'dry_run' or 'live'
        config_json             TEXT,          -- full AutopilotConfig serialized
        status                  TEXT DEFAULT 'pending',  -- pending/running/completed/failed
        error_message           TEXT,
        steps_completed         TEXT,          -- JSON array of completed step names
        duration_ms             INTEGER,
        created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at            TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS autopilot_steps (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id          INTEGER NOT NULL REFERENCES autopilot_runs(id),
        step_number     INTEGER NOT NULL,
        step_name       TEXT NOT NULL,       -- resolve_template, select_contacts, preflight, create, enroll, activate, record
        status          TEXT DEFAULT 'pending',  -- pending/running/completed/failed/skipped
        detail          TEXT,               -- human-readable output or error
        data_json       TEXT,               -- structured output (contact list, campaign id, etc.)
        duration_ms     INTEGER,
        started_at      TIMESTAMP,
        completed_at    TIMESTAMP
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_autopilot_status ON autopilot_runs(status);
    CREATE INDEX IF NOT EXISTS idx_autopilot_steps_run ON autopilot_steps(run_id);
    CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
    CREATE INDEX IF NOT EXISTS idx_contacts_account ON contacts(account_name);
    CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
    CREATE INDEX IF NOT EXISTS idx_cc_campaign ON campaign_contacts(campaign_id);
    CREATE INDEX IF NOT EXISTS idx_cc_contact ON campaign_contacts(contact_id);
    CREATE INDEX IF NOT EXISTS idx_metrics_campaign ON metric_snapshots(campaign_id, snapshot_date);
    CREATE INDEX IF NOT EXISTS idx_sentiment_campaign ON reply_sentiment(campaign_id);
    CREATE INDEX IF NOT EXISTS idx_sentiment_pushed ON reply_sentiment(pushed_to_clay);
    CREATE INDEX IF NOT EXISTS idx_threads_status ON email_threads(status);
    CREATE INDEX IF NOT EXISTS idx_engagement_type ON engagement_events(event_type);
    CREATE INDEX IF NOT EXISTS idx_api_log_ts ON api_log(timestamp);
    CREATE INDEX IF NOT EXISTS idx_block_list_value ON block_list(value);
    """


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes."""
    conn.executescript(get_schema())
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.commit()


def seed_accounts(conn: sqlite3.Connection) -> None:
    """Insert 10 test health systems."""
    accounts = [
        ("HCA Healthcare",       "Enterprise/Strategic", 47000, "MEDITECH", 72, "Active",  45000000),
        ("Allina Health",        "Enterprise/Strategic",  3200, "Epic",     68, "Active",   8500000),
        ("UC Health",            "Enterprise/Strategic",  2100, "Epic",     75, "Active",   6200000),
        ("NYC Health + Hospitals","Enterprise/Strategic",  7500, "Epic",     65, "Active",  22000000),
        ("MedStar Health",       "Enterprise/Strategic",  4800, "Cerner",   70, "Active",  12000000),
        ("Baylor Scott & White", "Enterprise/Strategic",  5600, "Epic",     78, "Active",  15000000),
        ("NYU Langone",          "Enterprise/Strategic",  1800, "Epic",     73, "Active",   5500000),
        ("LifePoint Health",     "Commercial",            9200, "MEDITECH", 62, "Active",  28000000),
        ("Kaiser Permanente",    "Enterprise/Strategic", 12000, "Epic",     58, "Nurture", 35000000),
        ("Providence",           "Enterprise/Strategic",  8500, "Epic",     71, "Active",  25000000),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO accounts
           (system_name, segment, total_beds, primary_ehr, score, tier, total_opp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        accounts,
    )
    conn.commit()


def seed_contacts(conn: sqlite3.Connection) -> None:
    """Insert 10 ICP-matched test contacts."""
    contacts = [
        ("Charles", "Mallon",   "charles.mallon@alaskaregional.com",  "CFO",                    "HCA Healthcare",        "Decision Maker", 90, "Finance",  "Executive"),
        ("Filip",   "Roos",     "filip.roos@alaskaregional.com",      "CMO",                    "HCA Healthcare",        "Decision Maker", 90, "Medical",  "Executive"),
        ("Sabrina", "Braun",    "sabrina.braun@alaskaregional.com",   "CNO",                    "HCA Healthcare",        "Decision Maker", 95, "Nursing",  "Executive"),
        ("Steven",  "Dickson",  "steven.dickson@allinahealth.org",    "CNO",                    "Allina Health",         "Decision Maker", 95, "Nursing",  "Executive"),
        ("Ghada",   "Ashkar",   "gashkar@mednet.ucla.edu",            "Chief Pharmacy Officer",  "UC Health",            "Decision Maker", 85, "Pharmacy", "Executive"),
        ("Benjamin","Njoku",    "benjamin.njoku@nychhc.org",          "Dir. Inpatient Nursing",  "NYC Health + Hospitals","Decision Maker", 85, "Nursing",  "Director"),
        ("Kellee",  "McArdle",  "kellee.mcardle@medstar.net",         "Dir. Inpatient Nursing",  "MedStar Health",       "Decision Maker", 85, "Nursing",  "Director"),
        ("Brett",   "Stauffer", "Brett.Stauffer@baylorhealth.edu",    "CQO",                    "Baylor Scott & White",  "Decision Maker", 90, "Quality",  "Executive"),
        ("Elaine",  "Soto",     "esoto@nyp.org",                      "Dir. Inpatient Nursing",  "NYU Langone",          "Decision Maker", 85, "Nursing",  "Director"),
        ("Lindsey", "Metelko",  "lindsey.metelko@lpnt.net",           "CNO",                    "LifePoint Health",      "Decision Maker", 95, "Nursing",  "Executive"),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO contacts
           (first_name, last_name, email, title, account_name, icp_category, icp_intent_score, icp_department, icp_job_level)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        contacts,
    )
    conn.commit()


def seed_mailboxes(conn: sqlite3.Connection) -> None:
    """Insert 3 placeholder mailboxes (Clayton Maike, all Active/warmed)."""
    mailboxes = [
        ("clayton@glytec-outreach.com",    "Clayton", "Maike", 30, 1, 1, 92.5),
        ("clayton@glucommander-mail.com",  "Clayton", "Maike", 30, 1, 1, 89.3),
        ("c.maike@glytec-health.com",      "Clayton", "Maike", 30, 1, 1, 91.0),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO mailboxes
           (email, first_name, last_name, daily_limit, status, warmup_status, warmup_score)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        mailboxes,
    )
    conn.commit()


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    try:
        print(f"Creating database at {DB_PATH} ...")
        init_db(conn)

        print("Seeding accounts ...")
        seed_accounts(conn)

        print("Seeding contacts ...")
        seed_contacts(conn)

        print("Seeding mailboxes ...")
        seed_mailboxes(conn)

        # Summary
        counts = {}
        for table in ["accounts", "contacts", "mailboxes", "campaigns",
                       "campaign_contacts", "metric_snapshots", "reply_sentiment",
                       "clay_push_log", "email_threads", "engagement_events",
                       "api_log", "block_list", "autopilot_runs",
                       "autopilot_steps"]:
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0]

        print("\n--- Seed Summary ---")
        for table, count in counts.items():
            print(f"  {table:25s} {count:>5d} rows")
        print(f"\nDatabase ready: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
