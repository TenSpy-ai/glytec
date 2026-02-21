"""Pipeline report — meeting attribution from campaigns.

Usage:
    python -m salesforge.ops.pipeline_report
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def pipeline_report():
    """Show meetings attributed to campaigns."""
    conn = get_conn()

    try:
        meetings = conn.execute(
            """SELECT m.*, c.first_name, c.last_name, c.email, c.title,
                      camp.name as campaign_name
               FROM meetings m
               LEFT JOIN contacts c ON m.contact_id = c.id
               LEFT JOIN campaigns camp ON m.campaign_id = camp.id
               ORDER BY m.meeting_date DESC"""
        ).fetchall()

        print(f"\n{'='*80}")
        print(f"  PIPELINE REPORT — {len(meetings)} meetings")
        print(f"{'='*80}\n")

        if not meetings:
            print("  No meetings recorded. Add meetings via the meetings table.")
            return

        # Summary by attribution
        by_attribution = {}
        for m in meetings:
            attr = m["attributed_to"] or "unattributed"
            by_attribution.setdefault(attr, []).append(m)

        print("  Attribution Summary:")
        for attr, mlist in by_attribution.items():
            print(f"    {attr}: {len(mlist)} meetings")

        # Detail
        print(f"\n  Meeting Details:")
        for m in meetings:
            name = f"{m['first_name'] or '?'} {m['last_name'] or '?'}" if m["contact_id"] else m["account_name"] or "?"
            print(f"    {m['meeting_date'] or '?'} | {name} | {m['meeting_type'] or '-'} | {m['outcome'] or '-'}")
            if m["campaign_name"]:
                print(f"      Campaign: {m['campaign_name']} | Attributed: {m['attributed_to'] or '-'}")

        # Campaign → meeting conversion
        campaign_meetings = conn.execute(
            """SELECT camp.name, COUNT(m.id) as meetings,
                      camp.contact_count
               FROM campaigns camp
               LEFT JOIN meetings m ON m.campaign_id = camp.id
               GROUP BY camp.id
               HAVING meetings > 0
               ORDER BY meetings DESC"""
        ).fetchall()

        if campaign_meetings:
            print(f"\n  Campaign → Meeting Conversion:")
            for cm in campaign_meetings:
                rate = (cm["meetings"] / cm["contact_count"] * 100) if cm["contact_count"] > 0 else 0
                print(f"    {cm['name']}: {cm['meetings']} meetings / {cm['contact_count']} contacts ({rate:.1f}%)")

    finally:
        conn.close()


if __name__ == "__main__":
    pipeline_report()
