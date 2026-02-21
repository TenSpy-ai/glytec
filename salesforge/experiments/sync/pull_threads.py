"""Reply thread sync from Salesforge."""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def pull_threads():
    """Sync all reply threads from Salesforge."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        all_threads = []
        offset = 0
        while True:
            data = client.list_threads(limit=50, offset=offset)
            batch = data.get("data", [])
            all_threads.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

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

        conn.execute(
            """INSERT OR REPLACE INTO sync_state (entity, last_synced_at, total_records, updated_at)
               VALUES ('threads', ?, ?, CURRENT_TIMESTAMP)""",
            (datetime.datetime.now().isoformat(), len(all_threads)),
        )
        conn.commit()

        print(f"[sync:threads] {len(all_threads)} total, {new_count} new")

    finally:
        conn.close()


if __name__ == "__main__":
    pull_threads()
