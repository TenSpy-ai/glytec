"""Mailbox health — check connectivity and log status.

Usage:
    python -m salesforge.ops.mailbox_health
"""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def check_mailbox_health():
    """Sync mailbox data and report health status."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        data = client.list_mailboxes(limit=100)
        mailboxes = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(mailboxes, list):
            print("[mailboxes] Failed to fetch mailbox data")
            return

        today = datetime.date.today().isoformat()
        healthy = []
        disconnected = []

        for mb in mailboxes:
            sf_id = mb.get("id")
            address = mb.get("address", "?")
            status = mb.get("status", "unknown")
            reason = mb.get("disconnectReason")
            limit_val = mb.get("dailyEmailLimit", 0)
            provider = mb.get("mailboxProvider", "?")

            # Upsert into mailboxes table
            existing = conn.execute(
                "SELECT id FROM mailboxes WHERE salesforge_id = ?", (sf_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE mailboxes
                       SET address = ?, status = ?, disconnect_reason = ?,
                           daily_email_limit = ?, provider = ?,
                           tracking_domain = ?, last_synced_at = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE salesforge_id = ?""",
                    (address, status, reason, limit_val, provider,
                     mb.get("trackingDomain"), today, sf_id),
                )
            else:
                conn.execute(
                    """INSERT INTO mailboxes
                       (salesforge_id, address, first_name, last_name,
                        daily_email_limit, provider, status, disconnect_reason,
                        tracking_domain, last_synced_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sf_id, address, mb.get("firstName"), mb.get("lastName"),
                     limit_val, provider, status, reason,
                     mb.get("trackingDomain"), today),
                )

            # Log health snapshot
            local_mb = conn.execute(
                "SELECT id FROM mailboxes WHERE salesforge_id = ?", (sf_id,)
            ).fetchone()
            if local_mb:
                conn.execute(
                    """INSERT OR REPLACE INTO mailbox_health_log
                       (mailbox_id, snapshot_date, status, disconnect_reason)
                       VALUES (?, ?, ?, ?)""",
                    (local_mb["id"], today, status, reason),
                )

            if status == "active" or status == "connected":
                healthy.append((address, limit_val, provider))
            else:
                disconnected.append((address, status, reason))

        conn.commit()

        # Display
        print(f"\n{'='*80}")
        print(f"  MAILBOX HEALTH — {len(mailboxes)} mailboxes")
        print(f"{'='*80}\n")

        print(f"  Healthy: {len(healthy)}")
        for addr, limit_val, provider in healthy:
            print(f"    [+] {addr} — {limit_val}/day ({provider})")

        if disconnected:
            print(f"\n  Disconnected: {len(disconnected)}")
            for addr, status, reason in disconnected:
                print(f"    [!] {addr} — {status}: {reason or 'unknown reason'}")

            # Create UI tasks for disconnected mailboxes
            for addr, status, reason in disconnected:
                existing_task = conn.execute(
                    "SELECT id FROM ui_tasks WHERE task LIKE ? AND status = 'pending'",
                    (f"%{addr}%",),
                ).fetchone()
                if not existing_task:
                    conn.execute(
                        """INSERT INTO ui_tasks (task, category, priority, context)
                           VALUES (?, 'mailbox', 'high', ?)""",
                        (f"Reconnect mailbox: {addr}",
                         f"Status: {status}, Reason: {reason}. Must be done in Salesforge UI."),
                    )
            conn.commit()
            print(f"\n  UI tasks created for {len(disconnected)} disconnected mailbox(es)")
        else:
            print(f"\n  All mailboxes healthy!")

        # Update sync state
        conn.execute(
            """INSERT OR REPLACE INTO sync_state (entity, last_synced_at, total_records, updated_at)
               VALUES ('mailboxes', ?, ?, CURRENT_TIMESTAMP)""",
            (today, len(mailboxes)),
        )
        conn.commit()

    finally:
        conn.close()


if __name__ == "__main__":
    check_mailbox_health()
