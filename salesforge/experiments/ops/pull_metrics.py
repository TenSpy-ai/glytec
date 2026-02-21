"""Pull metrics — dashboard with per-campaign + aggregate metrics.

Usage:
    python -m salesforge.ops.pull_metrics              # all campaigns, last 30 days
    python -m salesforge.ops.pull_metrics 90d           # last 90 days
    python -m salesforge.ops.pull_metrics <name>        # specific campaign
"""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def pull_metrics(campaign_name=None, days=30):
    """Pull and display metrics from Salesforge."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    to_date = datetime.date.today().isoformat()
    from_date = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

    try:
        # Get all sequences
        all_seqs = []
        offset = 0
        while True:
            data = client.list_sequences(limit=50, offset=offset)
            batch = data.get("data", [])
            all_seqs.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        if campaign_name:
            all_seqs = [s for s in all_seqs if campaign_name.lower() in s.get("name", "").lower()]

        if not all_seqs:
            print("No sequences found.")
            return

        print(f"\n{'='*80}")
        print(f"  METRICS DASHBOARD — {from_date} to {to_date}")
        print(f"{'='*80}\n")

        totals = {"contacted": 0, "opened": 0, "replied": 0, "bounced": 0, "clicked": 0}

        for seq in all_seqs:
            sid = seq["id"]
            name = seq.get("name", "?")

            analytics = client.get_analytics(sid, from_date, to_date)
            if not analytics:
                print(f"  {name}: No analytics available")
                continue

            stats = analytics.get("stats", {})
            contacted = stats.get("contacted", 0)
            opened = stats.get("opened", 0)
            opened_pct = stats.get("openedPercent", 0)
            clicked = stats.get("clicked", 0)
            clicked_pct = stats.get("clickedPercent", 0)
            replied = seq.get("repliedCount", 0)
            bounced = seq.get("bouncedCount", 0)

            totals["contacted"] += contacted
            totals["opened"] += opened
            totals["replied"] += replied
            totals["bounced"] += bounced
            totals["clicked"] += clicked

            print(f"  {name}")
            print(f"    Contacted: {contacted} | Opened: {opened} ({opened_pct:.1f}%)")
            print(f"    Clicked: {clicked} ({clicked_pct:.1f}%) | Replied: {replied} | Bounced: {bounced}")

            # Save snapshot
            local_campaign = conn.execute(
                "SELECT id FROM campaigns WHERE salesforge_seq_id = ?", (sid,)
            ).fetchone()
            campaign_id = local_campaign["id"] if local_campaign else None

            conn.execute(
                """INSERT OR REPLACE INTO metric_snapshots
                   (campaign_id, salesforge_seq_id, snapshot_date, contacted, opened,
                    replied, bounced, clicked,
                    open_rate, reply_rate, bounce_rate, click_rate)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (campaign_id, sid, to_date, contacted, opened, replied, bounced, clicked,
                 opened_pct, 0, 0, clicked_pct),
            )
            print()

        conn.commit()

        # Aggregates
        if len(all_seqs) > 1:
            t = totals
            print(f"  {'─'*60}")
            print(f"  TOTALS")
            print(f"    Contacted: {t['contacted']} | Opened: {t['opened']} | Replied: {t['replied']}")
            print(f"    Bounced: {t['bounced']} | Clicked: {t['clicked']}")
            if t["contacted"] > 0:
                print(f"    Open rate: {t['opened']/t['contacted']*100:.1f}% | Reply rate: {t['replied']/t['contacted']*100:.1f}% | Bounce rate: {t['bounced']/t['contacted']*100:.1f}%")

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    days = 30
    name = None
    for arg in args:
        if arg.endswith("d") and arg[:-1].isdigit():
            days = int(arg[:-1])
        else:
            name = arg
    pull_metrics(campaign_name=name, days=days)
