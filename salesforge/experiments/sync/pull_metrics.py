"""Daily metric snapshots from Salesforge analytics."""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def pull_metrics():
    """Pull analytics for all campaigns and save daily snapshots."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    today = datetime.date.today().isoformat()
    from_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()

    try:
        campaigns = conn.execute(
            "SELECT id, salesforge_seq_id, name FROM campaigns WHERE salesforge_seq_id IS NOT NULL"
        ).fetchall()

        if not campaigns:
            # Pull from API directly
            all_seqs = []
            offset = 0
            while True:
                data = client.list_sequences(limit=50, offset=offset)
                batch = data.get("data", [])
                all_seqs.extend(batch)
                if len(batch) < 50:
                    break
                offset += 50
            campaigns = [{"id": None, "salesforge_seq_id": s["id"], "name": s.get("name", "?")} for s in all_seqs]

        synced = 0
        for c in campaigns:
            sid = c["salesforge_seq_id"]
            analytics = client.get_analytics(sid, from_date, today)
            if not analytics:
                continue

            stats = analytics.get("stats", {})
            conn.execute(
                """INSERT OR REPLACE INTO metric_snapshots
                   (campaign_id, salesforge_seq_id, snapshot_date,
                    contacted, opened, unique_opened, clicked, unique_clicked,
                    replied, bounced,
                    open_rate, reply_rate, bounce_rate, click_rate)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (c["id"], sid, today,
                 stats.get("contacted", 0),
                 stats.get("opened", 0), 0,
                 stats.get("clicked", 0), 0,
                 0, 0,
                 stats.get("openedPercent", 0), 0, 0,
                 stats.get("clickedPercent", 0)),
            )
            synced += 1

        conn.commit()

        conn.execute(
            """INSERT OR REPLACE INTO sync_state (entity, last_synced_at, total_records, updated_at)
               VALUES ('metrics', ?, ?, CURRENT_TIMESTAMP)""",
            (datetime.datetime.now().isoformat(), synced),
        )
        conn.commit()
        print(f"[sync:metrics] Saved snapshots for {synced} campaigns")

    finally:
        conn.close()


if __name__ == "__main__":
    pull_metrics()
