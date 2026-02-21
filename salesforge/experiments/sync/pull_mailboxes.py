"""Mailbox health sync from Salesforge."""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def pull_mailboxes():
    """Sync mailbox data from Salesforge."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        data = client.list_mailboxes(limit=100)
        mailboxes = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(mailboxes, list):
            print("[sync:mailboxes] Failed to fetch mailbox data")
            return

        today = datetime.date.today().isoformat()
        for mb in mailboxes:
            sf_id = mb.get("id")
            existing = conn.execute(
                "SELECT id FROM mailboxes WHERE salesforge_id = ?", (sf_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE mailboxes SET
                       address = ?, status = ?, disconnect_reason = ?,
                       daily_email_limit = ?, provider = ?,
                       tracking_domain = ?, last_synced_at = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE salesforge_id = ?""",
                    (mb.get("address"), mb.get("status"), mb.get("disconnectReason"),
                     mb.get("dailyEmailLimit", 0), mb.get("mailboxProvider"),
                     mb.get("trackingDomain"), today, sf_id),
                )
            else:
                conn.execute(
                    """INSERT INTO mailboxes
                       (salesforge_id, address, first_name, last_name,
                        daily_email_limit, provider, status, disconnect_reason,
                        tracking_domain, last_synced_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sf_id, mb.get("address"), mb.get("firstName"), mb.get("lastName"),
                     mb.get("dailyEmailLimit", 0), mb.get("mailboxProvider"),
                     mb.get("status"), mb.get("disconnectReason"),
                     mb.get("trackingDomain"), today),
                )

        conn.commit()

        conn.execute(
            """INSERT OR REPLACE INTO sync_state (entity, last_synced_at, total_records, updated_at)
               VALUES ('mailboxes', ?, ?, CURRENT_TIMESTAMP)""",
            (datetime.datetime.now().isoformat(), len(mailboxes)),
        )
        conn.commit()

        print(f"[sync:mailboxes] Synced {len(mailboxes)} mailboxes")

    finally:
        conn.close()


if __name__ == "__main__":
    pull_mailboxes()
