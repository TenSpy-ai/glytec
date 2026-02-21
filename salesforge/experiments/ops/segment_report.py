"""Segment report — EHR + persona breakdowns.

Usage:
    python -m salesforge.ops.segment_report ehr
    python -m salesforge.ops.segment_report persona
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def ehr_report():
    """Aggregate metrics by campaign target EHR."""
    conn = get_conn()
    try:
        results = conn.execute(
            """SELECT camp.target_ehr,
                      COUNT(DISTINCT camp.id) as campaigns,
                      SUM(camp.contact_count) as total_contacts,
                      AVG(ms.open_rate) as avg_open,
                      AVG(ms.reply_rate) as avg_reply,
                      AVG(ms.bounce_rate) as avg_bounce
               FROM campaigns camp
               LEFT JOIN metric_snapshots ms ON ms.campaign_id = camp.id
               WHERE camp.target_ehr IS NOT NULL
               GROUP BY camp.target_ehr
               ORDER BY total_contacts DESC"""
        ).fetchall()

        print(f"\n{'='*80}")
        print(f"  EHR SEGMENT REPORT")
        print(f"{'='*80}\n")

        if not results:
            print("  No campaign data by EHR segment. Assign target_ehr to campaigns.")
            return

        for r in results:
            print(f"  {r['target_ehr'] or 'Unset'}:")
            print(f"    Campaigns: {r['campaigns']} | Contacts: {r['total_contacts'] or 0}")
            print(f"    Open: {r['avg_open'] or 0:.1f}% | Reply: {r['avg_reply'] or 0:.1f}% | Bounce: {r['avg_bounce'] or 0:.1f}%")
            print()

    finally:
        conn.close()


def persona_report():
    """Aggregate metrics by ICP category/persona."""
    conn = get_conn()
    try:
        results = conn.execute(
            """SELECT c.icp_category, c.icp_function_type, c.icp_job_level,
                      COUNT(*) as total,
                      SUM(CASE WHEN cc.replied > 0 THEN 1 ELSE 0 END) as replied,
                      SUM(CASE WHEN cc.emails_opened > 0 THEN 1 ELSE 0 END) as opened,
                      SUM(CASE WHEN cc.bounced > 0 THEN 1 ELSE 0 END) as bounced
               FROM contacts c
               LEFT JOIN campaign_contacts cc ON cc.contact_id = c.id
               WHERE c.icp_matched = 1 AND c.suppressed = 0
               GROUP BY c.icp_category, c.icp_function_type, c.icp_job_level
               ORDER BY total DESC"""
        ).fetchall()

        print(f"\n{'='*80}")
        print(f"  PERSONA SEGMENT REPORT")
        print(f"{'='*80}\n")

        for r in results:
            enrolled = r["opened"] or 0
            print(f"  {r['icp_category']} | {r['icp_function_type']} | {r['icp_job_level']}")
            print(f"    Total: {r['total']} | Opened: {enrolled} | Replied: {r['replied'] or 0} | Bounced: {r['bounced'] or 0}")
            print()

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "ehr":
        ehr_report()
    elif args and args[0] == "persona":
        persona_report()
    else:
        ehr_report()
        persona_report()
