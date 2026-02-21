"""Check replies — pull threads and show unhandled.

Usage:
    python -m salesforge.ops.check_replies              # unhandled only
    python -m salesforge.ops.check_replies all           # all threads
    python -m salesforge.ops.check_replies 10            # last 10
"""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def pull_and_show_replies(show_all=False, limit=None):
    """Pull threads from Salesforge, sync locally, show unhandled."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        # Pull all threads
        all_threads = []
        offset = 0
        while True:
            data = client.list_threads(limit=50, offset=offset)
            batch = data.get("data", [])
            all_threads.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        print(f"[replies] Synced {len(all_threads)} threads from Salesforge")

        # Upsert into reply_threads
        new_count = 0
        for t in all_threads:
            thread_id = t.get("id")
            existing = conn.execute(
                "SELECT id FROM reply_threads WHERE salesforge_thread_id = ?",
                (thread_id,),
            ).fetchone()
            if not existing:
                conn.execute(
                    """INSERT INTO reply_threads
                       (salesforge_thread_id, contact_email, contact_first_name,
                        contact_last_name, subject, content, reply_type,
                        mailbox_id, event_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (thread_id, t.get("contactEmail"), t.get("contactFirstName"),
                     t.get("contactLastName"), t.get("subject"),
                     t.get("content"), t.get("replyType"),
                     t.get("mailboxId"), t.get("date")),
                )
                new_count += 1
        conn.commit()
        if new_count:
            print(f"[replies] {new_count} new threads saved locally")

        # Display
        if show_all:
            threads = conn.execute(
                "SELECT * FROM reply_threads ORDER BY event_date DESC"
            ).fetchall()
        else:
            threads = conn.execute(
                "SELECT * FROM reply_threads WHERE status IN ('new', 'needs_follow_up') ORDER BY event_date DESC"
            ).fetchall()

        if limit:
            threads = threads[:limit]

        if not threads:
            print("\n[replies] No unhandled replies.")
            return

        print(f"\n{'='*80}")
        print(f"  {'ALL' if show_all else 'UNHANDLED'} REPLIES — {len(threads)} threads")
        print(f"{'='*80}\n")

        for t in threads:
            status_icon = {"new": "!", "needs_follow_up": "?", "reviewed": "~",
                           "handled": "+", "archived": "-"}.get(t["status"], "?")
            print(f"  [{status_icon}] {t['contact_first_name']} {t['contact_last_name']} <{t['contact_email']}>")
            print(f"      Type: {t['reply_type']} | Status: {t['status']} | Date: {t['event_date']}")
            print(f"      Subject: {t['subject']}")
            content = (t["content"] or "")[:150]
            if content:
                print(f"      Content: {content}...")
            print()

    finally:
        conn.close()


def mark_reply(thread_id, new_status, handler=None, notes=None):
    """Mark a reply thread as handled/needs_follow_up/archived."""
    conn = get_conn()
    try:
        conn.execute(
            """UPDATE reply_threads
               SET status = ?, handled_by = ?, handled_at = ?, follow_up_notes = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ? OR salesforge_thread_id = ?""",
            (new_status, handler, datetime.datetime.now().isoformat() if new_status == "handled" else None,
             notes, thread_id, thread_id),
        )
        conn.commit()
        print(f"[replies] Thread {thread_id} marked as {new_status}")
    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    show_all = "all" in args
    limit = None
    for arg in args:
        if arg.isdigit():
            limit = int(arg)
    pull_and_show_replies(show_all=show_all, limit=limit)
