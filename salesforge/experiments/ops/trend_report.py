"""Trend report — 30/60/90 day trends with rolling averages.

Usage:
    python -m salesforge.ops.trend_report
    python -m salesforge.ops.trend_report --days 90
"""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def trend_report(days=90):
    """Show metric trends over 30/60/90 day windows."""
    conn = get_conn()
    today = datetime.date.today()

    try:
        windows = [30, 60, 90] if days >= 90 else [30, 60] if days >= 60 else [30]

        print(f"\n{'='*80}")
        print(f"  TREND REPORT — Rolling windows")
        print(f"{'='*80}\n")

        print(f"  {'Window':<12} {'Contacted':>10} {'Opened':>8} {'Replied':>8} {'Bounced':>8} {'Open%':>7} {'Reply%':>8}")
        print(f"  {'─'*65}")

        for w in windows:
            from_date = (today - datetime.timedelta(days=w)).isoformat()
            result = conn.execute(
                """SELECT SUM(contacted) as contacted,
                          SUM(opened) as opened,
                          SUM(replied) as replied,
                          SUM(bounced) as bounced,
                          AVG(open_rate) as avg_open,
                          AVG(reply_rate) as avg_reply
                   FROM metric_snapshots
                   WHERE snapshot_date >= ?""",
                (from_date,),
            ).fetchone()

            if result and result["contacted"]:
                print(f"  {w}d{'':8} {result['contacted'] or 0:>10,} {result['opened'] or 0:>8,} {result['replied'] or 0:>8,} {result['bounced'] or 0:>8,} {result['avg_open'] or 0:>6.1f}% {result['avg_reply'] or 0:>7.1f}%")
            else:
                print(f"  {w}d{'':8} {'No data':<50}")

        # Daily trend for last 14 days
        print(f"\n  Daily trend (last 14 days):")
        print(f"  {'Date':<12} {'Contacted':>10} {'Opened':>8} {'Open%':>7}")
        print(f"  {'─'*40}")

        daily = conn.execute(
            """SELECT snapshot_date, SUM(contacted) as contacted,
                      SUM(opened) as opened, AVG(open_rate) as open_rate
               FROM metric_snapshots
               WHERE snapshot_date >= ?
               GROUP BY snapshot_date
               ORDER BY snapshot_date DESC
               LIMIT 14""",
            ((today - datetime.timedelta(days=14)).isoformat(),),
        ).fetchall()

        for d in reversed(daily):
            print(f"  {d['snapshot_date']:<12} {d['contacted'] or 0:>10,} {d['opened'] or 0:>8,} {d['open_rate'] or 0:>6.1f}%")

    finally:
        conn.close()


if __name__ == "__main__":
    days = 90
    for i, a in enumerate(sys.argv):
        if a == "--days" and i + 1 < len(sys.argv):
            days = int(sys.argv[i + 1])
    trend_report(days)
