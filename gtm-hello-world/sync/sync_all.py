"""
GTM Hello World — Full Sync from Instantly
Syncs campaigns, leads, emails, accounts, and metrics into local DB.

Usage:
    python -m sync.sync_all             # Dry run
    python -m sync.sync_all --live      # Live sync from Instantly MCP
"""

import json
import sqlite3
import sys
from datetime import date

from config import DB_PATH, DRY_RUN
from db import get_conn, log_api_call
from mcp import InstantlyMCP, MCPError


def paginate_all(fetch_fn, **kwargs) -> list:
    """Generic cursor-based pagination helper.

    fetch_fn should accept starting_after kwarg and return a dict with
    items + next_starting_after, or a list.
    """
    all_items = []
    starting_after = None

    while True:
        result = fetch_fn(starting_after=starting_after, **kwargs)

        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = result.get("data", result.get("items", []))

        all_items.extend(items)

        next_cursor = None
        if isinstance(result, dict):
            next_cursor = result.get("next_starting_after")
        if not next_cursor or not items:
            break
        starting_after = next_cursor

    return all_items


def sync_campaigns(conn: sqlite3.Connection, mcp: InstantlyMCP) -> int:
    """Sync campaigns from Instantly → local campaigns table."""
    print("  Fetching campaigns from Instantly...")
    campaigns = paginate_all(mcp.list_campaigns, limit=100)
    print(f"  Found {len(campaigns)} campaigns")

    synced = 0
    for c in campaigns:
        camp_id = c.get("id")
        name = c.get("name", "")
        status = c.get("status", 0)

        # Upsert by instantly_campaign_id
        existing = conn.execute(
            "SELECT id FROM campaigns WHERE instantly_campaign_id = ?",
            (camp_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE campaigns SET name = ?, instantly_status = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE instantly_campaign_id = ?""",
                (name, status, camp_id),
            )
        else:
            conn.execute(
                """INSERT INTO campaigns (name, instantly_campaign_id, instantly_status, status)
                   VALUES (?, ?, ?, ?)""",
                (name, camp_id, status,
                 {0: "draft", 1: "active", 2: "paused", 3: "completed"}.get(status, "draft")),
            )
        synced += 1

    conn.commit()
    print(f"  Synced {synced} campaigns")
    return synced


def sync_leads(conn: sqlite3.Connection, mcp: InstantlyMCP) -> int:
    """Sync leads from Instantly → match to local contacts by email."""
    print("  Fetching leads from Instantly...")
    leads = paginate_all(mcp.list_leads, limit=100)
    print(f"  Found {len(leads)} leads")

    matched = 0
    for lead in leads:
        email = lead.get("email", "").lower()
        lead_id = lead.get("id", lead.get("lead_id"))
        if not email:
            continue

        # Match by email to local contacts
        updated = conn.execute(
            """UPDATE contacts SET instantly_lead_id = ?, updated_at = CURRENT_TIMESTAMP
               WHERE LOWER(email) = ?""",
            (lead_id, email),
        ).rowcount
        if updated:
            matched += 1

    conn.commit()
    print(f"  Matched {matched} leads to local contacts")
    return matched


def sync_emails(conn: sqlite3.Connection, mcp: InstantlyMCP) -> int:
    """Sync emails from Instantly → local email_threads table."""
    print("  Fetching emails from Instantly...")
    emails = paginate_all(mcp.list_emails, limit=100)
    print(f"  Found {len(emails)} emails")

    synced = 0
    for email in emails:
        email_id = email.get("id")
        thread_id = email.get("thread_id")
        if not email_id:
            continue

        # Check if already exists
        existing = conn.execute(
            "SELECT id FROM email_threads WHERE instantly_email_id = ?",
            (email_id,),
        ).fetchone()

        if not existing:
            # Find matching contact
            contact_email = email.get("lead_email", email.get("to", ""))
            contact = conn.execute(
                "SELECT id FROM contacts WHERE email = ?",
                (contact_email,),
            ).fetchone()

            # Find matching campaign
            campaign_id_str = email.get("campaign_id", "")
            campaign = conn.execute(
                "SELECT id FROM campaigns WHERE instantly_campaign_id = ?",
                (campaign_id_str,),
            ).fetchone() if campaign_id_str else None

            conn.execute(
                """INSERT INTO email_threads
                   (instantly_thread_id, instantly_email_id, campaign_id,
                    contact_id, contact_email, subject, body_text,
                    sender_account, ue_type, ai_interest_value)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (thread_id, email_id,
                 campaign["id"] if campaign else None,
                 contact["id"] if contact else None,
                 contact_email,
                 email.get("subject", ""),
                 email.get("body", email.get("body_text", "")),
                 email.get("from", email.get("eaccount", "")),
                 email.get("ue_type", 1),
                 email.get("ai_interest_value")),
            )
            synced += 1

    conn.commit()
    print(f"  Synced {synced} new emails")
    return synced


def sync_accounts(conn: sqlite3.Connection, mcp: InstantlyMCP) -> int:
    """Sync sending accounts from Instantly → local mailboxes table."""
    print("  Fetching sending accounts from Instantly...")
    accounts = paginate_all(mcp.list_accounts, limit=100)
    print(f"  Found {len(accounts)} accounts")

    synced = 0
    for a in accounts:
        email = a.get("email", "")
        if not email:
            continue

        # Upsert by email
        existing = conn.execute(
            "SELECT id FROM mailboxes WHERE email = ?", (email,),
        ).fetchone()

        status = a.get("status", 0)
        warmup_status = a.get("warmup_status", a.get("warmup", {}).get("status", 0))
        daily_limit = a.get("daily_limit", a.get("sending_limit", 30))
        first_name = a.get("first_name", "")
        last_name = a.get("last_name", "")

        if existing:
            conn.execute(
                """UPDATE mailboxes SET status = ?, warmup_status = ?,
                   daily_limit = ?, first_name = ?, last_name = ?,
                   last_synced_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                   WHERE email = ?""",
                (status, warmup_status, daily_limit, first_name, last_name, email),
            )
        else:
            conn.execute(
                """INSERT INTO mailboxes
                   (email, first_name, last_name, daily_limit, status,
                    warmup_status, last_synced_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (email, first_name, last_name, daily_limit, status, warmup_status),
            )
        synced += 1

    conn.commit()
    print(f"  Synced {synced} accounts")
    return synced


def sync_metrics(conn: sqlite3.Connection, mcp: InstantlyMCP) -> int:
    """Sync campaign analytics from Instantly → local metric_snapshots."""
    print("  Pulling workspace analytics...")
    try:
        result = mcp.get_campaign_analytics()
        if isinstance(result, dict):
            data = {
                "sent": result.get("sent", result.get("total_sent", 0)),
                "opened": result.get("opened", result.get("total_opened", 0)),
                "replied": result.get("replied", result.get("total_replied", 0)),
                "bounced": result.get("bounced", result.get("total_bounced", 0)),
            }
            print(f"  Workspace: sent={data['sent']} opened={data['opened']} "
                  f"replied={data['replied']} bounced={data['bounced']}")
        return 1
    except MCPError as e:
        print(f"  Analytics error: {e.message}")
        return 0


def main() -> None:
    live = "--live" in sys.argv

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python seed_db.py")
        return

    conn = get_conn()
    mcp = InstantlyMCP(dry_run=not live)

    try:
        mode = "LIVE" if live else "DRY RUN"
        print(f"\nGTM Hello World — Full Sync ({mode})\n")

        if not live:
            print("  [DRY RUN] Sync requires --live to pull from Instantly MCP.")
            print("  Re-run with: python -m sync.sync_all --live")
            return

        results = {}

        print("--- 1/5: Campaigns ---")
        results["campaigns"] = sync_campaigns(conn, mcp)

        print("\n--- 2/5: Leads ---")
        results["leads"] = sync_leads(conn, mcp)

        print("\n--- 3/5: Emails ---")
        results["emails"] = sync_emails(conn, mcp)

        print("\n--- 4/5: Accounts (Mailboxes) ---")
        results["accounts"] = sync_accounts(conn, mcp)

        print("\n--- 5/5: Metrics ---")
        results["metrics"] = sync_metrics(conn, mcp)

        # Log
        log_api_call(conn, "local", "sync_all.py", "RUN",
                     {"mode": mode}, None,
                     f"Synced: {json.dumps(results)}")

        print(f"\n--- Sync Summary ---")
        for job, count in results.items():
            print(f"  {job:<15s} {count:>5d} records")
        print(f"\nDone. Database updated: {DB_PATH}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
