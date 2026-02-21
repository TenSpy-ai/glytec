"""
GTM Hello World — Pull Metrics
Pulls Instantly campaign analytics into metric_snapshots.

Usage:
    python pull_metrics.py          # Dry run — inserts placeholder zeros
    python pull_metrics.py --live   # Live — calls Instantly API
"""

import json
import sqlite3
import sys
from datetime import date, datetime

from config import DB_PATH, DRY_RUN, BOUNCE_RATE_LIMIT, SPAM_RATE_LIMIT, INSTANTLY_API_KEY
from db import get_conn, log_api_call


def pull_campaign_analytics(conn: sqlite3.Connection, live: bool) -> list[dict]:
    """Pull aggregate analytics for all campaigns.

    In dry-run mode, returns placeholder data for any existing campaigns.
    In live mode, would call Instantly MCP get_campaign_analytics.
    """
    campaigns = conn.execute(
        "SELECT id, name, instantly_campaign_id FROM campaigns WHERE status != 'archived'"
    ).fetchall()

    results = []
    today = date.today().isoformat()

    mcp = None
    if live:
        from mcp import InstantlyMCP, MCPError
        mcp = InstantlyMCP(dry_run=False)

    for c in campaigns:
        if live and c["instantly_campaign_id"] and mcp:
            print(f"  [LIVE] Pulling analytics for {c['name']}...")
            try:
                result = mcp.get_campaign_analytics(
                    campaign_id=c["instantly_campaign_id"])
                # Extract metrics from MCP response
                if isinstance(result, dict):
                    data = {
                        "sent": result.get("sent", result.get("total_sent", 0)),
                        "opened": result.get("opened", result.get("total_opened", 0)),
                        "replied": result.get("replied", result.get("total_replied", 0)),
                        "bounced": result.get("bounced", result.get("total_bounced", 0)),
                    }
                else:
                    data = {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}
                print(f"    sent={data['sent']} opened={data['opened']} "
                      f"replied={data['replied']} bounced={data['bounced']}")
            except Exception as e:
                print(f"    MCP error: {e} — using zeros")
                data = {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}
        else:
            print(f"  [DRY RUN] Inserting placeholder metrics for {c['name']}")
            data = {"sent": 0, "opened": 0, "replied": 0, "bounced": 0}

        # Insert/update metric snapshot
        conn.execute(
            """INSERT OR REPLACE INTO metric_snapshots
               (campaign_id, instantly_campaign_id, snapshot_date, sent, opened, replied, bounced,
                open_rate, reply_rate, bounce_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (c["id"], c["instantly_campaign_id"], today,
             data["sent"], data["opened"], data["replied"], data["bounced"],
             data["opened"] / data["sent"] if data["sent"] > 0 else 0,
             data["replied"] / data["sent"] if data["sent"] > 0 else 0,
             data["bounced"] / data["sent"] if data["sent"] > 0 else 0),
        )
        results.append({"campaign": c["name"], **data})

    conn.commit()
    return results


def pull_daily_analytics(conn: sqlite3.Connection, live: bool) -> None:
    """Pull day-by-day analytics breakdown.

    In live mode, would call Instantly MCP get_daily_campaign_analytics.
    """
    if live:
        from mcp import InstantlyMCP, MCPError
        mcp = InstantlyMCP(dry_run=False)
        print("  [LIVE] Pulling daily campaign analytics...")
        try:
            result = mcp.get_daily_campaign_analytics(status=1)
            if isinstance(result, dict):
                daily_data = result.get("data", result.get("items", []))
            elif isinstance(result, list):
                daily_data = result
            else:
                daily_data = []
            print(f"    Got {len(daily_data)} daily records")
            for entry in daily_data[:5]:
                print(f"    {entry}")
        except Exception as e:
            print(f"    MCP error: {e}")
    else:
        print("  [DRY RUN] Skipping daily analytics (no campaigns active)")


def check_kill_switches(conn: sqlite3.Connection) -> list[str]:
    """Check all campaigns for kill-switch conditions.

    Returns list of WARNING strings for any threshold violations.
    """
    warnings = []
    rows = conn.execute(
        "SELECT m.*, c.name AS campaign_name "
        "FROM metric_snapshots m "
        "JOIN campaigns c ON m.campaign_id = c.id "
        "WHERE m.snapshot_date = date('now') AND m.sent > 0"
    ).fetchall()

    for r in rows:
        if r["bounce_rate"] and r["bounce_rate"] > BOUNCE_RATE_LIMIT:
            msg = (f"WARNING: {r['campaign_name']} bounce rate {r['bounce_rate']*100:.1f}% "
                   f"exceeds {BOUNCE_RATE_LIMIT*100:.0f}% threshold — PAUSE CAMPAIGN")
            warnings.append(msg)
            print(f"  {msg}")

    if not warnings:
        print("  All campaigns within thresholds.")

    return warnings


def main() -> None:
    live = "--live" in sys.argv and not DRY_RUN if "--live" not in sys.argv else "--live" in sys.argv

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python seed_db.py")
        return

    conn = get_conn()
    try:
        mode = "LIVE" if live else "DRY RUN"
        print(f"\nGTM Hello World — Pull Metrics ({mode})")
        print(f"Date: {date.today().isoformat()}\n")

        print("--- Campaign Analytics ---")
        results = pull_campaign_analytics(conn, live)
        if not results:
            print("  No campaigns found. Create one first (see PROCESS.md).")

        print("\n--- Daily Analytics ---")
        pull_daily_analytics(conn, live)

        print("\n--- Kill Switch Check ---")
        check_kill_switches(conn)

        log_api_call(conn, "local", "pull_metrics.py", "RUN",
                     {"mode": mode}, None, f"Completed with {len(results)} campaigns")

        print(f"\nDone. Metrics stored in {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
