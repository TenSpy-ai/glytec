"""Enroll contacts — add contacts to an existing campaign.

Usage:
    python -m salesforge.ops.enroll_contacts --campaign "Q1 CNO" --tier Active
    python -m salesforge.ops.enroll_contacts --campaign "Q1 CNO" --account "HCA" --live
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn
from config import DRY_RUN


def enroll_contacts(campaign_name, dry_run=True, tier=None, ehr=None,
                    account=None, persona=None):
    """Enroll additional contacts into an existing campaign."""
    client = SalesforgeClient(dry_run=dry_run)
    conn = get_conn()

    try:
        # Find the campaign
        campaign = conn.execute(
            "SELECT * FROM campaigns WHERE name LIKE ?",
            (f"%{campaign_name}%",),
        ).fetchone()

        if not campaign:
            # Try Salesforge directly
            all_seqs = []
            offset = 0
            while True:
                data = client.list_sequences(limit=50, offset=offset)
                batch = data.get("data", [])
                all_seqs.extend(batch)
                if len(batch) < 50:
                    break
                offset += 50
            matches = [s for s in all_seqs if campaign_name.lower() in s.get("name", "").lower()]
            if not matches:
                print(f"[enroll] No campaign matching '{campaign_name}'")
                return
            seq_id = matches[0]["id"]
            campaign_id = None
        else:
            seq_id = campaign["salesforge_seq_id"]
            campaign_id = campaign["id"]

        if not seq_id:
            print("[enroll] Campaign has no Salesforge sequence ID (still in draft?)")
            return

        # Find contacts to enroll
        query = """
            SELECT c.* FROM contacts c
            JOIN accounts a ON c.account_name = a.system_name
            WHERE c.golden_record = 1 AND c.suppressed = 0 AND c.icp_matched = 1
        """
        params = []
        if tier:
            query += " AND a.tier = ?"
            params.append(tier)
        if ehr:
            query += " AND EXISTS (SELECT 1 FROM facilities f WHERE f.highest_level_parent = a.system_name AND UPPER(f.ehr_inpatient) LIKE ?)"
            params.append(f"%{ehr.upper()}%")
        if account:
            query += " AND a.system_name LIKE ?"
            params.append(f"%{account}%")
        if persona:
            query += " AND UPPER(c.icp_category) = ?"
            params.append(persona.upper())

        contacts = conn.execute(query, params).fetchall()

        # Dedup against already enrolled
        if campaign_id:
            already_enrolled = set(
                row["contact_id"] for row in conn.execute(
                    "SELECT contact_id FROM campaign_contacts WHERE campaign_id = ?",
                    (campaign_id,),
                ).fetchall()
            )
            contacts = [c for c in contacts if c["id"] not in already_enrolled]

        # Check DNC
        dnc_emails = set(row["email"] for row in conn.execute("SELECT email FROM dnc_list").fetchall())
        contacts = [c for c in contacts if c["email"] not in dnc_emails]

        if not contacts:
            print("[enroll] No new contacts to enroll (all already enrolled or filtered out)")
            return

        print(f"\n  Campaign: {campaign_name}")
        print(f"  New contacts to enroll: {len(contacts)}")
        print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")

        # Enroll
        enrolled = 0
        for c in contacts:
            custom_vars = {}
            if c["title"]:
                custom_vars["job_title"] = c["title"]
            if c["icp_category"]:
                custom_vars["icp_category"] = c["icp_category"]

            success = client.import_lead(
                seq_id,
                first_name=c["first_name"],
                last_name=c["last_name"],
                email=c["email"],
                company=c["company"] or c["account_name"],
                linkedin_url=c["linkedin_url"] if c["linkedin_url"] else None,
                custom_vars=custom_vars if custom_vars else None,
            )
            if success:
                enrolled += 1
                if campaign_id:
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO campaign_contacts (campaign_id, contact_id) VALUES (?, ?)",
                            (campaign_id, c["id"]),
                        )
                    except Exception:
                        pass

        conn.commit()
        print(f"  Enrolled: {enrolled}/{len(contacts)}")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--tier")
    parser.add_argument("--ehr")
    parser.add_argument("--account")
    parser.add_argument("--persona")
    args = parser.parse_args()

    enroll_contacts(args.campaign, dry_run=not args.live,
                    tier=args.tier, ehr=args.ehr,
                    account=args.account, persona=args.persona)
