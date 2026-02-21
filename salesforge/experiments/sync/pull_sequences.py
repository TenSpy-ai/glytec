"""Sync sequence list + detail from Salesforge."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn
import datetime


def pull_sequences():
    """Sync all sequences from Salesforge into local campaigns table."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        all_seqs = []
        offset = 0
        while True:
            data = client.list_sequences(limit=50, offset=offset)
            batch = data.get("data", [])
            all_seqs.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        synced = 0
        for seq in all_seqs:
            sid = seq["id"]
            existing = conn.execute(
                "SELECT id FROM campaigns WHERE salesforge_seq_id = ?", (sid,)
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE campaigns SET
                       salesforge_status = ?, contact_count = ?, step_count = ?,
                       mailbox_count = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE salesforge_seq_id = ?""",
                    (seq.get("status"), seq.get("leadCount", 0),
                     len(seq.get("steps", [])), len(seq.get("mailboxes", [])), sid),
                )
            else:
                conn.execute(
                    """INSERT INTO campaigns
                       (name, salesforge_seq_id, salesforge_status, status,
                        contact_count, step_count, mailbox_count)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (seq.get("name", "Unnamed"), sid, seq.get("status"),
                     seq.get("status", "draft"),
                     seq.get("leadCount", 0), len(seq.get("steps", [])),
                     len(seq.get("mailboxes", []))),
                )
            synced += 1

        conn.commit()

        conn.execute(
            """INSERT OR REPLACE INTO sync_state (entity, last_synced_at, total_records, updated_at)
               VALUES ('sequences', ?, ?, CURRENT_TIMESTAMP)""",
            (datetime.datetime.now().isoformat(), len(all_seqs)),
        )
        conn.commit()

        print(f"[sync:sequences] Synced {synced} sequences")

    finally:
        conn.close()


if __name__ == "__main__":
    pull_sequences()
