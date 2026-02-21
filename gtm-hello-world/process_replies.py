"""
GTM Hello World — Process Replies
Scans for new replies, classifies sentiment, stores results.

Usage:
    python process_replies.py          # Dry run — processes any existing email_threads
    python process_replies.py --live   # Live — pulls from Instantly first
"""

import json
import sqlite3
import sys
from datetime import datetime

from config import (DB_PATH, DRY_RUN, POSITIVE_THRESHOLD, NEGATIVE_THRESHOLD,
                    INSTANTLY_API_KEY)
from db import get_conn


POSITIVE_KEYWORDS = ["interested", "tell me more", "schedule", "meeting", "demo",
                     "learn more", "send info", "sounds good", "worth exploring"]
NEGATIVE_KEYWORDS = ["not interested", "remove me", "unsubscribe", "stop emailing",
                     "do not contact", "opt out", "no thank you", "wrong person"]
OOO_KEYWORDS = ["out of office", "on vacation", "away from", "auto-reply",
                "automatic reply", "i am currently out", "limited access"]


def pull_new_emails(conn: sqlite3.Connection, mcp) -> int:
    """Pull new received emails from Instantly MCP into email_threads."""
    from sync.sync_all import paginate_all

    print("  Pulling emails from Instantly MCP...")
    emails = paginate_all(mcp.list_emails, limit=100)
    print(f"  Found {len(emails)} emails in Instantly")

    inserted = 0
    for email in emails:
        email_id = email.get("id")
        if not email_id:
            continue

        # Skip if already in DB
        existing = conn.execute(
            "SELECT id FROM email_threads WHERE instantly_email_id = ?",
            (email_id,),
        ).fetchone()
        if existing:
            continue

        # Only process received emails (ue_type=2)
        ue_type = email.get("ue_type", 1)

        contact_email = email.get("lead_email", email.get("to", ""))
        contact = conn.execute(
            "SELECT id FROM contacts WHERE email = ?",
            (contact_email,),
        ).fetchone()

        campaign_id_str = email.get("campaign_id", "")
        campaign = conn.execute(
            "SELECT id FROM campaigns WHERE instantly_campaign_id = ?",
            (campaign_id_str,),
        ).fetchone() if campaign_id_str else None

        conn.execute(
            """INSERT INTO email_threads
               (instantly_thread_id, instantly_email_id, campaign_id,
                contact_id, contact_email, subject, body_text,
                sender_account, ue_type, ai_interest_value, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (email.get("thread_id"), email_id,
             campaign["id"] if campaign else None,
             contact["id"] if contact else None,
             contact_email,
             email.get("subject", ""),
             email.get("body", email.get("body_text", "")),
             email.get("from", email.get("eaccount", "")),
             ue_type,
             email.get("ai_interest_value"),
             "new"),
        )
        inserted += 1

    conn.commit()
    print(f"  Inserted {inserted} new emails into email_threads")
    return inserted


def scan_for_new_replies(conn: sqlite3.Connection, live: bool) -> list[dict]:
    """Get unprocessed replies from email_threads.

    In live mode, pulls new emails from Instantly via MCP first.
    """
    if live:
        from mcp import InstantlyMCP
        mcp_client = InstantlyMCP(dry_run=False)
        pull_new_emails(conn, mcp_client)

    rows = conn.execute(
        "SELECT id, instantly_email_id, campaign_id, contact_id, contact_email, "
        "subject, body_text, ai_interest_value, status "
        "FROM email_threads WHERE status = 'new' AND ue_type = 2"
    ).fetchall()

    return [dict(r) for r in rows]


def classify_sentiment(reply: dict) -> tuple[str, float, str]:
    """Classify reply sentiment using AI interest value + keyword overrides.

    Returns: (sentiment, confidence, classified_by)
    """
    body = (reply.get("body_text") or "").lower()
    ai_score = reply.get("ai_interest_value")

    # Keyword overrides take priority
    for kw in OOO_KEYWORDS:
        if kw in body:
            return "ooo", 0.95, "keyword"

    for kw in NEGATIVE_KEYWORDS:
        if kw in body:
            return "negative", 0.90, "keyword"

    for kw in POSITIVE_KEYWORDS:
        if kw in body:
            return "positive", 0.85, "keyword"

    # Fall back to AI interest score
    if ai_score is not None:
        if ai_score > POSITIVE_THRESHOLD:
            return "positive", ai_score, "ai"
        elif ai_score < NEGATIVE_THRESHOLD:
            return "negative", 1.0 - ai_score, "ai"
        else:
            return "neutral", 0.5, "ai"

    return "neutral", 0.5, "ai"


def store_reply(conn: sqlite3.Connection, reply: dict,
                sentiment: str, confidence: float, classified_by: str) -> int:
    """Store classified reply in reply_sentiment table. Returns row ID."""
    cursor = conn.execute(
        """INSERT INTO reply_sentiment
           (instantly_email_id, campaign_id, contact_id, contact_email,
            sentiment, sentiment_confidence, classified_by)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (reply.get("instantly_email_id"), reply.get("campaign_id"),
         reply.get("contact_id"), reply.get("contact_email"),
         sentiment, confidence, classified_by),
    )

    # Update email_thread status
    conn.execute(
        "UPDATE email_threads SET status = ?, sentiment = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        ("reviewed" if sentiment in ("neutral", "ooo") else "needs_follow_up"
         if sentiment == "positive" else "handled",
         sentiment, reply["id"]),
    )

    conn.commit()
    return cursor.lastrowid


def triage_reply(sentiment: str, contact_email: str) -> str:
    """Determine next action based on sentiment."""
    actions = {
        "positive": f"  -> POSITIVE: {contact_email} — needs follow-up, queue for Clay push",
        "negative": f"  -> NEGATIVE: {contact_email} — mark handled, consider block list",
        "neutral":  f"  -> NEUTRAL: {contact_email} — mark reviewed, no action",
        "ooo":      f"  -> OOO: {contact_email} — mark reviewed, auto-archived",
        "bounce":   f"  -> BOUNCE: {contact_email} — add to block list",
    }
    return actions.get(sentiment, f"  -> UNKNOWN: {contact_email}")


def main() -> None:
    live = "--live" in sys.argv

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python seed_db.py")
        return

    conn = get_conn()
    try:
        mode = "LIVE" if live else "DRY RUN"
        print(f"\nGTM Hello World — Process Replies ({mode})\n")

        print("--- Scanning for new replies ---")
        replies = scan_for_new_replies(conn, live)

        if not replies:
            print("  No new replies to process.")
            print("  (Replies appear in email_threads when pulled from Instantly)")
            return

        print(f"  Found {len(replies)} new replies\n")

        print("--- Classifying sentiment ---")
        positive_count = 0
        for reply in replies:
            sentiment, confidence, classified_by = classify_sentiment(reply)
            row_id = store_reply(conn, reply, sentiment, confidence, classified_by)
            print(f"  [{sentiment}] ({confidence:.2f}, {classified_by}) "
                  f"{reply['contact_email']} — reply_sentiment #{row_id}")
            print(triage_reply(sentiment, reply["contact_email"]))
            if sentiment == "positive":
                positive_count += 1

        print(f"\n--- Summary ---")
        print(f"  Processed: {len(replies)} replies")
        print(f"  Positive:  {positive_count} (queued for Clay push)")
        print(f"  Run push_to_clay.py to push positive replies downstream")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
