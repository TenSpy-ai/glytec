"""Launch campaign — full lifecycle: create seq → steps → mailboxes → enroll → activate.

Usage:
    python -m salesforge.ops.launch_campaign --campaign-name "Q1 CNO Outreach" --dry-run
    python -m salesforge.ops.launch_campaign --campaign-name "Q1 CNO Outreach" --live

DRY-RUN by default. Shows full preview before any API calls.
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn
from config import DRY_RUN


def launch_campaign(campaign_name, dry_run=True, target_tier=None, target_ehr=None,
                    target_persona=None, activate=False):
    """Create and configure a full Salesforge campaign.

    Steps:
    1. POST /sequences → draft + 1 empty step
    2. PUT /steps → email content (with distributionStrategy, label, status on variants)
    3. PUT /mailboxes → assign all workspace mailboxes (PUT not POST!)
    4. PUT /import-lead → enroll contacts (linkedinUrl omitted if None)
    5. PUT /status → activate (only if --activate flag, requires mailboxes)
    """
    client = SalesforgeClient(dry_run=dry_run)
    conn = get_conn()

    try:
        # Find eligible contacts
        query = """
            SELECT c.*, a.system_name as acct_name, a.total_beds, a.tier
            FROM contacts c
            JOIN accounts a ON c.account_name = a.system_name
            WHERE c.golden_record = 1
            AND c.suppressed = 0
            AND c.icp_matched = 1
        """
        params = []
        if target_tier:
            query += " AND a.tier = ?"
            params.append(target_tier)
        else:
            query += " AND a.tier IN ('Priority', 'Active')"
        if target_ehr:
            query += " AND EXISTS (SELECT 1 FROM facilities f WHERE f.highest_level_parent = a.system_name AND UPPER(f.ehr_inpatient) LIKE ?)"
            params.append(f"%{target_ehr.upper()}%")
        if target_persona:
            query += " AND UPPER(c.icp_category) = ?"
            params.append(target_persona.upper())
        query += " ORDER BY a.score DESC"

        contacts = conn.execute(query, params).fetchall()

        if not contacts:
            print("[launch] No eligible contacts found with current filters.")
            return

        # Check for suppressed/DNC
        dnc_emails = set(row["email"] for row in conn.execute("SELECT email FROM dnc_list").fetchall())
        contacts = [c for c in contacts if c["email"] not in dnc_emails]

        # Preview
        print(f"\n{'='*80}")
        print(f"  LAUNCH CAMPAIGN: {campaign_name}")
        print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"{'='*80}\n")
        print(f"  Contacts: {len(contacts)}")
        if target_tier:
            print(f"  Tier: {target_tier}")
        if target_ehr:
            print(f"  EHR: {target_ehr}")
        if target_persona:
            print(f"  Persona: {target_persona}")

        # Show sample contacts
        print(f"\n  Sample contacts:")
        for c in contacts[:5]:
            print(f"    {c['first_name']} {c['last_name']} <{c['email']}> — {c['title']} @ {c['company']}")
        if len(contacts) > 5:
            print(f"    ... and {len(contacts) - 5} more")

        # Get campaign step content from campaign_steps or compose on the fly
        step_content = conn.execute(
            """SELECT * FROM campaign_steps WHERE campaign_id IN
               (SELECT id FROM campaigns WHERE name = ?)
               ORDER BY step_order""",
            (campaign_name,),
        ).fetchall()

        if not step_content:
            # Use a default initial email step
            print(f"\n  [info] No pre-built steps found — using default email template")
            subject = f"Transforming glycemic management at your organization"
            body_html = "<p>I'm reaching out because your organization may benefit from FDA-cleared insulin management technology.</p><p>Would it make sense to schedule 15 minutes to discuss?</p>"
        else:
            subject = step_content[0]["email_subject"]
            body_html = step_content[0]["email_body_html"]

        print(f"\n  Email subject: \"{subject[:60]}\"")

        # --- Step 1: Create sequence ---
        print(f"\n  Step 1: Creating sequence...")
        seq_data = client.create_sequence(campaign_name)
        if not seq_data:
            print("  [error] Failed to create sequence")
            return

        seq_id = seq_data.get("id") or f"dry_run_{campaign_name}"
        steps = seq_data.get("steps", [{}])
        step_id = steps[0].get("id") if steps else None
        variants = steps[0].get("variants", [{}]) if steps else [{}]
        variant_id = variants[0].get("id") if variants else None

        # --- Step 2: Populate email step ---
        print(f"  Step 2: Setting email content...")
        step_payload = [{
            "id": step_id,
            "order": 0,
            "name": "Initial email",
            "waitDays": 0,
            "distributionStrategy": "equal",
            "variants": [{
                "id": variant_id,
                "order": 0,
                "label": "Initial email",
                "status": "active",
                "emailSubject": subject,
                "emailContent": body_html,
                "distributionWeight": 100,
            }],
        }]
        client.update_steps(seq_id, step_payload)

        # --- Step 3: Assign mailboxes ---
        print(f"  Step 3: Assigning mailboxes...")
        mailbox_ids = client.get_all_mailbox_ids()
        if mailbox_ids or dry_run:
            client.assign_mailboxes(seq_id, mailbox_ids if not dry_run else ["dry_run_mbox"])

        # --- Step 4: Enroll contacts ---
        print(f"  Step 4: Enrolling {len(contacts)} contacts...")
        enrolled = 0
        for c in contacts:
            custom_vars = {}
            if c["title"]:
                custom_vars["job_title"] = c["title"]
            if c["icp_category"]:
                custom_vars["icp_category"] = c["icp_category"]
            if c["icp_function_type"]:
                custom_vars["function_type"] = c["icp_function_type"]

            success = client.import_lead(
                seq_id,
                first_name=c["first_name"],
                last_name=c["last_name"],
                email=c["email"],
                company=c["company"] or c["acct_name"],
                linkedin_url=c["linkedin_url"] if c["linkedin_url"] else None,
                custom_vars=custom_vars if custom_vars else None,
            )
            if success:
                enrolled += 1

        print(f"  Enrolled: {enrolled}/{len(contacts)}")

        # --- Step 5: Activate (if requested) ---
        if activate and not dry_run:
            print(f"  Step 5: Activating sequence...")
            client.set_status(seq_id, "active")

        # Save to local campaigns table
        conn.execute(
            """INSERT INTO campaigns
               (name, salesforge_seq_id, salesforge_status, status,
                target_segment, target_ehr, target_tier, target_persona,
                contact_count, mailbox_count, step_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (campaign_name, seq_id if not dry_run else None,
             "active" if activate and not dry_run else "draft",
             "active" if activate and not dry_run else "draft",
             target_tier, target_ehr, target_tier, target_persona,
             enrolled, len(mailbox_ids) if not dry_run else 0, 1),
        )

        # Save campaign_contacts records
        campaign_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for c in contacts:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO campaign_contacts (campaign_id, contact_id) VALUES (?, ?)",
                    (campaign_id, c["id"]),
                )
            except Exception:
                pass

        conn.commit()

        print(f"\n  {'[DRY RUN] Preview complete — no API calls made.' if dry_run else '[LIVE] Campaign launched!'}")
        if not dry_run and not activate:
            print(f"  Sequence is in DRAFT status. Run sf-toggle to activate.")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch a Salesforge campaign")
    parser.add_argument("--campaign-name", required=True, help="Campaign name")
    parser.add_argument("--live", action="store_true", help="Execute real API calls")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview only (default)")
    parser.add_argument("--tier", help="Target tier (Priority, Active, Nurture)")
    parser.add_argument("--ehr", help="Target EHR (Epic, Cerner, Meditech)")
    parser.add_argument("--persona", help="Target persona (Decision Maker, Influencer)")
    parser.add_argument("--activate", action="store_true", help="Auto-activate after creation")
    args = parser.parse_args()

    dry_run = not args.live
    launch_campaign(
        campaign_name=args.campaign_name,
        dry_run=dry_run,
        target_tier=args.tier,
        target_ehr=args.ehr,
        target_persona=args.persona,
        activate=args.activate,
    )
