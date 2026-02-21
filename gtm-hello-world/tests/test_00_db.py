"""
Test 00 — Database Schema & Seed Data
Verifies all 12 tables, 11 indexes, seed data, WAL mode, and log_api_call.
"""

import sqlite3
from tests.helpers import TestResult, ensure_db_seeded


EXPECTED_TABLES = [
    "accounts", "contacts", "campaigns", "campaign_contacts",
    "metric_snapshots", "reply_sentiment", "clay_push_log",
    "email_threads", "engagement_events", "mailboxes", "api_log", "block_list",
]

EXPECTED_INDEXES = [
    "idx_contacts_email", "idx_contacts_account", "idx_campaigns_status",
    "idx_cc_campaign", "idx_cc_contact", "idx_metrics_campaign",
    "idx_sentiment_campaign", "idx_sentiment_pushed", "idx_threads_status",
    "idx_engagement_type", "idx_api_log_ts",
]


def run() -> TestResult:
    r = TestResult("test_00_db — Database Schema & Seed Data")
    ensure_db_seeded()

    from db import get_conn, log_api_call
    from config import DB_PATH

    conn = get_conn()
    try:
        # --- 12 tables exist ---
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        for t in EXPECTED_TABLES:
            if t in tables:
                r.ok(f"table_exists:{t}")
            else:
                r.fail(f"table_exists:{t}", f"Table '{t}' not found. Got: {tables}")

        # --- 11 indexes exist ---
        indexes = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()]
        missing_idx = [i for i in EXPECTED_INDEXES if i not in indexes]
        if not missing_idx:
            r.ok("all_indexes_exist")
        else:
            r.fail("all_indexes_exist", f"Missing indexes: {missing_idx}")

        # --- Seed data counts ---
        acct_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if acct_count >= 10:
            r.ok(f"seed_accounts:{acct_count}")
        else:
            r.fail(f"seed_accounts:{acct_count}", f"Expected >=10, got {acct_count}")

        contact_count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        if contact_count >= 10:
            r.ok(f"seed_contacts:{contact_count}")
        else:
            r.fail(f"seed_contacts:{contact_count}", f"Expected >=10, got {contact_count}")

        mb_count = conn.execute("SELECT COUNT(*) FROM mailboxes").fetchone()[0]
        if mb_count >= 3:
            r.ok(f"seed_mailboxes:{mb_count}")
        else:
            r.fail(f"seed_mailboxes:{mb_count}", f"Expected >=3, got {mb_count}")

        # --- FK integrity: every contact has a valid account ---
        orphans = conn.execute("""
            SELECT c.email FROM contacts c
            LEFT JOIN accounts a ON c.account_name = a.system_name
            WHERE a.id IS NULL AND c.account_name IS NOT NULL
        """).fetchall()
        if not orphans:
            r.ok("fk_contacts_accounts")
        else:
            r.fail("fk_contacts_accounts",
                    f"{len(orphans)} orphaned contacts: {[o[0] for o in orphans[:3]]}")

        # --- All contacts have email + ICP fields ---
        missing = conn.execute("""
            SELECT email FROM contacts
            WHERE email IS NULL OR icp_category IS NULL OR icp_intent_score IS NULL
        """).fetchall()
        if not missing:
            r.ok("contacts_have_icp_fields")
        else:
            r.fail("contacts_have_icp_fields",
                    f"{len(missing)} contacts missing ICP fields")

        # --- get_conn returns Row factory ---
        row = conn.execute("SELECT 1 AS test_col").fetchone()
        try:
            val = row["test_col"]
            r.ok("row_factory")
        except (TypeError, IndexError):
            r.fail("row_factory", "get_conn() does not set Row factory")

        # --- log_api_call works ---
        log_conn = get_conn()
        try:
            before = log_conn.execute("SELECT COUNT(*) FROM api_log").fetchone()[0]
            log_api_call(log_conn, "test", "test_endpoint", "TEST",
                         {"key": "val"}, 200, "test summary", 42)
            after = log_conn.execute("SELECT COUNT(*) FROM api_log").fetchone()[0]
            if after == before + 1:
                r.ok("log_api_call")
            else:
                r.fail("log_api_call", f"Count didn't increase: {before} -> {after}")
            # Clean up test log entry
            log_conn.execute(
                "DELETE FROM api_log WHERE interface='test' AND tool_or_endpoint='test_endpoint'"
            )
            log_conn.commit()
        finally:
            log_conn.close()

        # --- WAL mode active ---
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        if mode.lower() == "wal":
            r.ok("wal_mode")
        else:
            r.fail("wal_mode", f"Expected 'wal', got '{mode}'")

        # --- Idempotent seed (re-run doesn't crash or duplicate) ---
        try:
            from seed_db import init_db, seed_accounts, seed_contacts, seed_mailboxes
            conn2 = sqlite3.connect(str(DB_PATH))
            init_db(conn2)
            seed_accounts(conn2)
            seed_contacts(conn2)
            seed_mailboxes(conn2)
            acct2 = conn2.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
            conn2.close()
            if acct2 == acct_count:
                r.ok("idempotent_seed")
            else:
                r.fail("idempotent_seed",
                        f"Count changed: {acct_count} -> {acct2}")
        except Exception as e:
            r.fail("idempotent_seed", e)

    finally:
        conn.close()

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
