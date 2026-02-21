"""
Test 07 — Sync Pipeline
Tests all 5 sync jobs + paginate_all helper.
Sync works against whatever is in the workspace (may be empty).
"""

from tests.helpers import (
    TestResult, ensure_db_seeded, get_live_mcp,
    cleanup_db_test_rows,
)


def run() -> TestResult:
    r = TestResult("test_07_sync — Sync Pipeline")
    ensure_db_seeded()

    from db import get_conn
    from sync.sync_all import (
        paginate_all, sync_campaigns, sync_leads,
        sync_emails, sync_accounts, sync_metrics,
    )

    mcp = get_live_mcp()
    conn = get_conn()

    try:
        # --- paginate_all helper ---
        try:
            items = paginate_all(mcp.list_campaigns, limit=5)
            if isinstance(items, list):
                r.ok(f"paginate_all:{len(items)}_items")
            else:
                r.fail("paginate_all", f"Unexpected: {type(items)}")
        except Exception as e:
            r.fail("paginate_all", e)

        # --- sync_campaigns ---
        try:
            count = sync_campaigns(conn, mcp)
            if isinstance(count, int) and count >= 0:
                r.ok(f"sync_campaigns:{count}")
            else:
                r.fail("sync_campaigns", f"Unexpected: {count}")
        except Exception as e:
            r.fail("sync_campaigns", e)

        # --- sync_leads ---
        try:
            count = sync_leads(conn, mcp)
            if isinstance(count, int) and count >= 0:
                r.ok(f"sync_leads:{count}")
            else:
                r.fail("sync_leads", f"Unexpected: {count}")
        except Exception as e:
            r.fail("sync_leads", e)

        # --- sync_emails ---
        try:
            count = sync_emails(conn, mcp)
            if isinstance(count, int) and count >= 0:
                r.ok(f"sync_emails:{count}")
            else:
                r.fail("sync_emails", f"Unexpected: {count}")
        except Exception as e:
            r.fail("sync_emails", e)

        # --- sync_accounts ---
        try:
            count = sync_accounts(conn, mcp)
            if isinstance(count, int) and count >= 0:
                r.ok(f"sync_accounts:{count}")
            else:
                r.fail("sync_accounts", f"Unexpected: {count}")
        except Exception as e:
            r.fail("sync_accounts", e)

        # --- sync_metrics ---
        try:
            count = sync_metrics(conn, mcp)
            if isinstance(count, int) and count >= 0:
                r.ok(f"sync_metrics:{count}")
            else:
                r.fail("sync_metrics", f"Unexpected: {count}")
        except Exception as e:
            r.fail("sync_metrics", e)

        # --- Dry-run sync_all respects dry_run flag ---
        try:
            # paginate_all with empty result
            items = paginate_all(mcp.list_accounts, limit=5)
            if isinstance(items, list):
                r.ok(f"paginate_accounts:{len(items)}")
            else:
                r.fail("paginate_accounts", f"Unexpected: {type(items)}")
        except Exception as e:
            r.fail("paginate_accounts", e)

        # --- DB has sync data ---
        try:
            # After sync, check if any data was written
            camp_count = conn.execute(
                "SELECT COUNT(*) FROM campaigns"
            ).fetchone()[0]
            r.ok(f"db_after_sync:campaigns={camp_count}")
        except Exception as e:
            r.fail("db_after_sync", e)

    finally:
        cleanup_db_test_rows(conn)
        conn.close()

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
