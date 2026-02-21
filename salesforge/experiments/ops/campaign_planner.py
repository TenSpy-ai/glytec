"""Campaign planner — plan by segment/EHR/tier, manage backlog, coverage report.

Usage:
    python -m salesforge.ops.campaign_planner plan --tier Priority --ehr Epic
    python -m salesforge.ops.campaign_planner backlog
    python -m salesforge.ops.campaign_planner coverage
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def plan_campaign(tier=None, ehr=None, segment=None, persona=None):
    """Plan a campaign by showing eligible contacts grouped by criteria."""
    conn = get_conn()
    try:
        query = """
            SELECT a.tier, a.segment, c.icp_category, c.icp_function_type,
                   COUNT(*) as contact_count,
                   GROUP_CONCAT(DISTINCT UPPER(f.ehr_inpatient)) as ehr_vendors
            FROM contacts c
            JOIN accounts a ON c.account_name = a.system_name
            LEFT JOIN facilities f ON f.highest_level_parent = a.system_name
            WHERE c.golden_record = 1 AND c.suppressed = 0 AND c.icp_matched = 1
        """
        params = []
        if tier:
            query += " AND a.tier = ?"
            params.append(tier)
        if ehr:
            query += " AND UPPER(f.ehr_inpatient) LIKE ?"
            params.append(f"%{ehr.upper()}%")
        if segment:
            query += " AND a.segment LIKE ?"
            params.append(f"%{segment}%")
        if persona:
            query += " AND c.icp_category = ?"
            params.append(persona)

        query += " GROUP BY a.tier, a.segment, c.icp_category ORDER BY contact_count DESC"

        results = conn.execute(query, params).fetchall()

        print(f"\n{'='*80}")
        print(f"  CAMPAIGN PLANNER")
        print(f"{'='*80}\n")

        total = 0
        for r in results:
            count = r["contact_count"]
            total += count
            print(f"  {r['tier']} | {r['segment'] or '-'} | {r['icp_category']} ({r['icp_function_type']})")
            print(f"    Contacts: {count} | EHRs: {r['ehr_vendors'] or '-'}")
        print(f"\n  Total eligible: {total}")

    finally:
        conn.close()


def show_backlog():
    """Show campaign ideas backlog."""
    conn = get_conn()
    try:
        ideas = conn.execute(
            "SELECT * FROM campaign_ideas ORDER BY priority DESC, created_at DESC"
        ).fetchall()

        print(f"\n{'='*80}")
        print(f"  CAMPAIGN BACKLOG — {len(ideas)} ideas")
        print(f"{'='*80}\n")

        if not ideas:
            print("  No campaign ideas in backlog. Use campaign_planner to create some.")
            return

        for i in ideas:
            priority_icon = {"high": "!", "medium": "~", "low": "-"}.get(i["priority"], "?")
            print(f"  [{priority_icon}] {i['name']} ({i['status']})")
            print(f"      Target: {i['target_tier'] or '-'} / {i['target_ehr'] or '-'} / {i['target_persona'] or '-'}")
            if i["estimated_contacts"]:
                print(f"      Est. contacts: {i['estimated_contacts']}")
            if i["notes"]:
                print(f"      Notes: {i['notes'][:100]}")
            print()

    finally:
        conn.close()


def show_coverage():
    """Show campaign coverage — which tiers/segments have been reached."""
    conn = get_conn()
    try:
        # Accounts by tier with campaign coverage
        tiers = conn.execute(
            """SELECT a.tier, COUNT(DISTINCT a.id) as total_accounts,
                      COUNT(DISTINCT cc.contact_id) as contacts_enrolled,
                      COUNT(DISTINCT c.id) as total_contacts
               FROM accounts a
               LEFT JOIN contacts c ON c.account_name = a.system_name AND c.suppressed = 0
               LEFT JOIN campaign_contacts cc ON cc.contact_id = c.id
               GROUP BY a.tier
               ORDER BY CASE a.tier WHEN 'Priority' THEN 1 WHEN 'Active' THEN 2 WHEN 'Nurture' THEN 3 ELSE 4 END"""
        ).fetchall()

        print(f"\n{'='*80}")
        print(f"  COVERAGE REPORT")
        print(f"{'='*80}\n")

        for t in tiers:
            enrolled_pct = (t["contacts_enrolled"] / t["total_contacts"] * 100) if t["total_contacts"] > 0 else 0
            print(f"  {t['tier']}:")
            print(f"    Accounts: {t['total_accounts']} | Contacts: {t['total_contacts']} | Enrolled: {t['contacts_enrolled']} ({enrolled_pct:.1f}%)")

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "plan":
        tier = ehr = segment = persona = None
        for i, a in enumerate(args):
            if a == "--tier" and i + 1 < len(args):
                tier = args[i + 1]
            elif a == "--ehr" and i + 1 < len(args):
                ehr = args[i + 1]
            elif a == "--segment" and i + 1 < len(args):
                segment = args[i + 1]
            elif a == "--persona" and i + 1 < len(args):
                persona = args[i + 1]
        plan_campaign(tier=tier, ehr=ehr, segment=segment, persona=persona)
    elif args[0] == "backlog":
        show_backlog()
    elif args[0] == "coverage":
        show_coverage()
    else:
        print("Usage: campaign_planner.py [plan|backlog|coverage] [--tier X] [--ehr X]")
