"""Account view — contacts + engagement at an account.

Usage:
    python -m salesforge.ops.account_view "HCA Healthcare"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def view_account(name_query):
    """Show account detail with all contacts and engagement rollup."""
    conn = get_conn()

    try:
        # Find account
        account = conn.execute(
            "SELECT * FROM accounts WHERE system_name LIKE ?",
            (f"%{name_query}%",),
        ).fetchone()

        if not account:
            print(f"No account matching '{name_query}'")
            return

        print(f"\n{'='*80}")
        print(f"  ACCOUNT: {account['system_name']}")
        print(f"{'='*80}\n")

        print(f"  Tier: {account['tier'] or '-'} | Score: {account['score'] or '-'}")
        print(f"  Segment: {account['segment'] or '-'}")
        print(f"  Beds: {account['total_beds'] or '-'} | Facilities: {account['facility_count'] or '-'}")
        print(f"  State: {account['state'] or '-'}")
        if account['glytec_client']:
            print(f"  Glytec Client: {account['glytec_client']} (ARR: ${account['glytec_arr'] or 0:,.0f})")
        if account['total_opp']:
            print(f"  Total Opportunity: ${account['total_opp']:,.0f}")
        if account['trigger_signal']:
            print(f"  Trigger Signal: {account['trigger_signal']}")

        # Contacts
        contacts = conn.execute(
            """SELECT * FROM contacts WHERE account_name = ?
               ORDER BY icp_intent_score DESC NULLS LAST""",
            (account['system_name'],),
        ).fetchall()

        print(f"\n  Contacts ({len(contacts)}):")
        for c in contacts:
            suppressed = " [SUPPRESSED]" if c["suppressed"] else ""
            icp = f" | {c['icp_category']}" if c["icp_category"] else ""
            print(f"    {c['first_name']} {c['last_name']} <{c['email']}>{suppressed}")
            print(f"      {c['title'] or '-'}{icp}")

        # Engagement (from campaign_contacts)
        engagement = conn.execute(
            """SELECT cc.*, camp.name as campaign_name
               FROM campaign_contacts cc
               JOIN campaigns camp ON cc.campaign_id = camp.id
               JOIN contacts c ON cc.contact_id = c.id
               WHERE c.account_name = ?""",
            (account['system_name'],),
        ).fetchall()

        if engagement:
            print(f"\n  Campaign Engagement ({len(engagement)}):")
            for e in engagement:
                status = e["status"]
                print(f"    [{status}] Campaign: {e['campaign_name']} | Sent: {e['emails_sent']} | Opened: {e['emails_opened']} | Replied: {e['replied']}")

        # Account engagement rollup
        ae = conn.execute(
            "SELECT * FROM account_engagement WHERE account_name = ?",
            (account['system_name'],),
        ).fetchone()
        if ae:
            print(f"\n  Engagement Tier: {ae['engagement_tier']}")
            print(f"    Enrolled: {ae['contacts_enrolled']} | Opened: {ae['contacts_opened']} | Replied: {ae['contacts_replied']}")

        # Facilities
        facilities = conn.execute(
            "SELECT * FROM facilities WHERE highest_level_parent = ? ORDER BY staffed_beds DESC LIMIT 10",
            (account['system_name'],),
        ).fetchall()

        if facilities:
            print(f"\n  Top Facilities ({len(facilities)} shown):")
            for f in facilities:
                print(f"    {f['hospital_name']} — {f['staffed_beds'] or '?'} beds, {f['ehr_inpatient'] or '?'} EHR, {f['state']}")

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: account_view.py <account name>")
        sys.exit(1)
    view_account(" ".join(args))
