"""Weekly metrics — week-over-week with deltas.

Usage:
    python -m salesforge.ops.weekly_metrics
    python -m salesforge.ops.weekly_metrics --weeks 4
"""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def weekly_metrics(weeks=4):
    """Show week-over-week metrics with deltas."""
    conn = get_conn()
    try:
        # Get metric snapshots grouped by ISO week
        results = conn.execute(
            """SELECT strftime('%Y-W%W', snapshot_date) as week,
                      SUM(contacted) as contacted,
                      SUM(opened) as opened,
                      SUM(replied) as replied,
                      SUM(bounced) as bounced,
                      SUM(clicked) as clicked,
                      AVG(open_rate) as avg_open_rate,
                      AVG(reply_rate) as avg_reply_rate,
                      AVG(bounce_rate) as avg_bounce_rate,
                      COUNT(DISTINCT campaign_id) as campaigns
               FROM metric_snapshots
               GROUP BY week
               ORDER BY week DESC
               LIMIT ?""",
            (weeks,),
        ).fetchall()

        if not results:
            print("No metric snapshots available. Run sf-sync first.")
            return

        print(f"\n{'='*80}")
        print(f"  WEEKLY METRICS — Last {weeks} weeks")
        print(f"{'='*80}\n")

        print(f"  {'Week':<12} {'Contacted':>10} {'Opened':>8} {'Replied':>8} {'Bounced':>8} {'Open%':>7} {'Reply%':>8}")
        print(f"  {'─'*65}")

        prev = None
        for r in reversed(results):
            contacted = r["contacted"] or 0
            opened = r["opened"] or 0
            replied = r["replied"] or 0
            bounced = r["bounced"] or 0
            open_rate = r["avg_open_rate"] or 0
            reply_rate = r["avg_reply_rate"] or 0

            delta_str = ""
            if prev:
                d_contacted = contacted - (prev["contacted"] or 0)
                d_open = open_rate - (prev["avg_open_rate"] or 0)
                delta_str = f"  Δ contacted: {d_contacted:+d}, Δ open%: {d_open:+.1f}"

            print(f"  {r['week']:<12} {contacted:>10,} {opened:>8,} {replied:>8,} {bounced:>8,} {open_rate:>6.1f}% {reply_rate:>7.1f}%")
            if delta_str:
                print(f"  {delta_str}")
            prev = r

    finally:
        conn.close()


if __name__ == "__main__":
    weeks = 4
    for i, a in enumerate(sys.argv):
        if a == "--weeks" and i + 1 < len(sys.argv):
            weeks = int(sys.argv[i + 1])
    weekly_metrics(weeks)
