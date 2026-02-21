"""
GTM Hello World — Push to Clay
Sends positive replies to Clay webhook for Salesforce integration.

Usage:
    python push_to_clay.py          # Dry run — shows what would be pushed
    python push_to_clay.py --live   # Live — fires HTTP POST to Clay webhook
"""

import json
import sqlite3
import sys
from datetime import datetime

from config import DB_PATH, DRY_RUN, CLAY_WEBHOOK_URL
from db import get_conn


def get_unpushed_positive_replies(conn: sqlite3.Connection) -> list[dict]:
    """Get all positive replies not yet pushed to Clay."""
    rows = conn.execute(
        """SELECT rs.id, rs.instantly_email_id, rs.campaign_id, rs.contact_id,
                  rs.contact_email, rs.sentiment, rs.sentiment_confidence,
                  c.first_name, c.last_name, c.title, c.account_name,
                  c.icp_department, c.icp_intent_score,
                  camp.name AS campaign_name, camp.recipe
           FROM reply_sentiment rs
           JOIN contacts c ON rs.contact_id = c.id
           LEFT JOIN campaigns camp ON rs.campaign_id = camp.id
           WHERE rs.sentiment = 'positive' AND rs.pushed_to_clay = 0"""
    ).fetchall()
    return [dict(r) for r in rows]


def build_clay_payload(reply: dict) -> dict:
    """Build webhook payload matching the design doc spec."""
    return {
        "contact": {
            "email": reply["contact_email"],
            "first_name": reply["first_name"],
            "last_name": reply["last_name"],
            "title": reply["title"],
            "company": reply["account_name"],
            "account_name": reply["account_name"],
        },
        "campaign": {
            "name": reply.get("campaign_name", ""),
            "recipe": reply.get("recipe", ""),
            "campaign_id": reply.get("campaign_id"),
        },
        "engagement": {
            "sentiment": reply["sentiment"],
            "sentiment_confidence": reply["sentiment_confidence"],
            "icp_department": reply.get("icp_department", ""),
            "icp_intent_score": reply.get("icp_intent_score"),
            "reply_date": datetime.now().isoformat(),
        },
    }


def push_to_clay(payload: dict, live: bool) -> tuple[int, str]:
    """Fire HTTP POST to Clay webhook.

    Returns: (response_code, response_body)
    """
    if not live:
        return 200, '{"status": "dry_run"}'

    if not CLAY_WEBHOOK_URL:
        print("  WARNING: CLAY_WEBHOOK_URL not set in .env — skipping push")
        return 0, "no_webhook_url"

    import urllib.request
    import urllib.error

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CLAY_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def log_push(conn: sqlite3.Connection, reply: dict, payload: dict,
             response_code: int, response_body: str) -> None:
    """Log push to clay_push_log and update reply_sentiment."""
    conn.execute(
        """INSERT INTO clay_push_log
           (reply_sentiment_id, contact_email, contact_first_name, contact_last_name,
            account_name, campaign_name, sentiment, webhook_url, payload_json,
            response_code, response_body)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (reply["id"], reply["contact_email"], reply["first_name"], reply["last_name"],
         reply["account_name"], reply.get("campaign_name", ""),
         reply["sentiment"], CLAY_WEBHOOK_URL or "(dry_run)",
         json.dumps(payload), response_code, response_body),
    )

    conn.execute(
        "UPDATE reply_sentiment SET pushed_to_clay = 1, pushed_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (reply["id"],),
    )
    conn.commit()


def main() -> None:
    live = "--live" in sys.argv

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python seed_db.py")
        return

    conn = get_conn()
    try:
        mode = "LIVE" if live else "DRY RUN"
        print(f"\nGTM Hello World — Push to Clay ({mode})\n")

        replies = get_unpushed_positive_replies(conn)

        if not replies:
            print("  No unpushed positive replies found.")
            print("  (Run process_replies.py first to classify replies)")
            return

        print(f"  Found {len(replies)} positive replies to push\n")

        success_count = 0
        for reply in replies:
            payload = build_clay_payload(reply)
            print(f"  Pushing: {reply['first_name']} {reply['last_name']} "
                  f"({reply['title']}) @ {reply['account_name']}")

            if not live:
                print(f"    [DRY RUN] Payload: {json.dumps(payload, indent=2)[:200]}...")

            code, body = push_to_clay(payload, live)
            log_push(conn, reply, payload, code, body)

            if code == 200:
                success_count += 1
                print(f"    -> OK ({code})")
            else:
                print(f"    -> FAILED ({code}): {body[:100]}")

        print(f"\n--- Summary ---")
        print(f"  Pushed: {success_count}/{len(replies)} replies")
        print(f"  Logged in clay_push_log table")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
