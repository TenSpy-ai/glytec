"""
GTM Hello World — Launch Campaign
Full campaign lifecycle: create → configure sequences → assign senders → enroll leads → activate.

Usage:
    python -m ops.launch_campaign --name "GHW_New_In_Role" --account "HCA" --live
    python -m ops.launch_campaign --name "GHW_New_In_Role" --tier Active --live
    python -m ops.launch_campaign --name "GHW_New_In_Role" --all --live
    python -m ops.launch_campaign --name "GHW_New_In_Role" --account "HCA"  # dry run

Options:
    --name <name>       Campaign name (required)
    --account <name>    Filter contacts by account name
    --tier <tier>       Filter contacts by tier (Priority/Active/Nurture)
    --all               Include all eligible contacts
    --activate          Auto-activate after setup (default: leave as draft)
    --live              Execute real API calls (default: dry run)
"""

import json
import sys

from config import DB_PATH
from db import get_conn, log_api_call
from mcp import InstantlyMCP, MCPError


# Default campaign schedule: Mon-Fri 8AM-5PM ET
DEFAULT_SCHEDULE = {
    "schedules": [{
        "name": "Weekdays",
        "timing": {"from": "08:00", "to": "17:00"},
        "days": {"1": True, "2": True, "3": True, "4": True, "5": True},
        "timezone": "America/New_York",
    }]
}

# Default sequence template — 3 steps over 7 days
DEFAULT_SEQUENCES = [{
    "steps": [
        {
            "type": "email",
            "delay": 0,
            "variants": [{
                "subject": "{{subject_line}}",
                "body": "{{email_body}}",
            }],
        },
        {
            "type": "email",
            "delay": 3,
            "variants": [{
                "subject": "Re: {{subject_line}}",
                "body": "{{follow_up_1}}",
            }],
        },
        {
            "type": "email",
            "delay": 4,
            "variants": [{
                "subject": "Re: {{subject_line}}",
                "body": "{{follow_up_2}}",
            }],
        },
    ]
}]


def get_eligible_contacts(conn, account=None, tier=None) -> list:
    """Get contacts eligible for a new campaign (have email, not blocked)."""
    conditions = ["c.email IS NOT NULL"]
    params = []

    if account:
        conditions.append("c.account_name LIKE ?")
        params.append(f"%{account}%")

    if tier:
        conditions.append("a.tier = ?")
        params.append(tier)

    where = " AND ".join(conditions)

    query = f"""
        SELECT c.id, c.first_name, c.last_name, c.email, c.title,
               c.account_name, c.icp_category, c.icp_intent_score,
               c.icp_department, c.icp_job_level
        FROM contacts c
        LEFT JOIN accounts a ON c.account_name = a.system_name
        WHERE {where}
          AND c.email NOT IN (SELECT value FROM block_list)
        ORDER BY c.icp_intent_score DESC
    """

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_sender_accounts(conn) -> list[str]:
    """Get active sender account emails from local DB."""
    rows = conn.execute(
        "SELECT email FROM mailboxes WHERE status = 1 ORDER BY email"
    ).fetchall()
    return [r["email"] for r in rows]


def build_lead_payload(contact: dict) -> dict:
    """Build Instantly lead payload from local contact."""
    payload = {
        "email": contact["email"],
        "first_name": contact.get("first_name", ""),
        "last_name": contact.get("last_name", ""),
        "company_name": contact.get("account_name", ""),
    }

    custom_vars = {}
    if contact.get("title"):
        custom_vars["title"] = contact["title"]
    if contact.get("icp_category"):
        custom_vars["icp_category"] = contact["icp_category"]
    if contact.get("icp_department"):
        custom_vars["icp_department"] = contact["icp_department"]
    if contact.get("icp_intent_score"):
        custom_vars["icp_intent_score"] = str(contact["icp_intent_score"])
    if custom_vars:
        payload["custom_variables"] = custom_vars

    return payload


def launch(mcp: InstantlyMCP, conn, name: str, contacts: list,
           senders: list[str], activate: bool = False,
           schedule: dict | None = None,
           sequences: list | None = None) -> dict:
    """Full campaign launch lifecycle.

    Returns dict with campaign details and counts.
    """
    result = {"name": name, "steps_completed": []}

    # Step 1: Create campaign with schedule + sequences
    print("  Step 1: Creating campaign...")
    schedule = schedule or DEFAULT_SCHEDULE
    sequences = sequences or DEFAULT_SEQUENCES

    campaign = mcp.create_campaign(
        name=name,
        campaign_schedule=schedule,
        sequences=sequences,
        email_list=senders if senders else None,
    )
    campaign_id = campaign.get("id", "")
    result["campaign_id"] = campaign_id
    result["steps_completed"].append("create")
    print(f"    Campaign ID: {campaign_id}")

    # Step 2: Assign sender accounts (if not included in create)
    if senders and not campaign.get("email_list"):
        print(f"  Step 2: Assigning {len(senders)} sender accounts...")
        mcp.update_campaign(campaign_id, email_list=senders)
        result["steps_completed"].append("assign_senders")
        print(f"    Assigned: {', '.join(senders[:3])}{'...' if len(senders) > 3 else ''}")
    else:
        print(f"  Step 2: Senders assigned in create ({len(senders)} accounts)")
        result["steps_completed"].append("assign_senders")

    # Step 3: Enroll contacts in batches
    print(f"  Step 3: Enrolling {len(contacts)} contacts...")
    batch_size = 1000
    total_enrolled = 0

    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        leads = [build_lead_payload(c) for c in batch]
        batch_num = i // batch_size + 1

        print(f"    Batch {batch_num}: {len(leads)} leads...")
        mcp.add_leads_bulk(
            campaign_id=campaign_id,
            leads=leads,
            skip_if_in_workspace=True,
        )
        total_enrolled += len(leads)

    result["enrolled"] = total_enrolled
    result["steps_completed"].append("enroll_leads")
    print(f"    Enrolled: {total_enrolled} contacts")

    # Step 4: Activate (optional)
    if activate:
        print("  Step 4: Activating campaign...")
        try:
            mcp.activate_campaign(campaign_id)
            result["status"] = "active"
            result["steps_completed"].append("activate")
            print("    Campaign is ACTIVE")
        except MCPError as e:
            result["status"] = "draft"
            result["activation_error"] = e.message
            print(f"    Activation failed: {e.message}")
            print("    (Requires: senders, leads, sequences, schedule all configured)")
    else:
        result["status"] = "draft"
        print("  Step 4: Skipping activation (use --activate to auto-activate)")

    # Save to local DB
    instantly_status = 1 if result["status"] == "active" else 0
    conn.execute(
        """INSERT INTO campaigns
           (name, instantly_campaign_id, instantly_status, status)
           VALUES (?, ?, ?, ?)""",
        (name, campaign_id, instantly_status, result["status"]),
    )
    camp_row = conn.execute(
        "SELECT id FROM campaigns WHERE instantly_campaign_id = ?",
        (campaign_id,),
    ).fetchone()

    if camp_row:
        for contact in contacts:
            conn.execute(
                """INSERT OR IGNORE INTO campaign_contacts (campaign_id, contact_id)
                   VALUES (?, ?)""",
                (camp_row["id"], contact["id"]),
            )
    conn.commit()
    result["steps_completed"].append("save_local_db")

    return result


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m ops.launch_campaign --name <name> [filters] [options]")
        print("  --name <name>       Campaign name (required)")
        print("  --account <name>    Filter by account name")
        print("  --tier <tier>       Filter by account tier (Priority/Active/Nurture)")
        print("  --all               Include all eligible contacts")
        print("  --activate          Auto-activate after setup")
        print("  --live              Execute real API calls")
        return

    # Parse args
    name = None
    account = None
    tier = None
    all_contacts = False
    activate = "--activate" in args
    live = "--live" in args

    i = 0
    while i < len(args):
        if args[i] == "--name" and i + 1 < len(args):
            name = args[i + 1]; i += 2
        elif args[i] == "--account" and i + 1 < len(args):
            account = args[i + 1]; i += 2
        elif args[i] == "--tier" and i + 1 < len(args):
            tier = args[i + 1]; i += 2
        elif args[i] == "--all":
            all_contacts = True; i += 1
        else:
            i += 1

    if not name:
        print("Error: --name is required")
        return

    if not account and not tier and not all_contacts:
        print("Error: specify --account, --tier, or --all to select contacts")
        return

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = get_conn()
    mcp = InstantlyMCP(dry_run=not live)

    mode = "LIVE" if live else "DRY RUN"
    print(f"\nGTM Hello World — Launch Campaign ({mode})")
    print(f"Campaign: {name}\n")

    # Get eligible contacts
    print("--- Preparing ---")
    contacts = get_eligible_contacts(conn, account=account, tier=tier)
    if not contacts:
        print("  No eligible contacts found")
        conn.close()
        return

    print(f"  Eligible contacts: {len(contacts)}")
    for c in contacts[:5]:
        print(f"    {c['first_name']} {c['last_name']} ({c['title']}) @ {c['account_name']}")
    if len(contacts) > 5:
        print(f"    ... and {len(contacts) - 5} more")

    # Get sender accounts
    senders = get_sender_accounts(conn)
    print(f"  Sender accounts: {len(senders)}")
    if not senders:
        print("  WARNING: No active sender accounts found in local DB")
        print("  Run /instantly-sync --live to pull accounts from Instantly")

    # Launch
    print(f"\n--- Launching ---")
    try:
        result = launch(mcp, conn, name, contacts, senders, activate=activate)

        print(f"\n--- Summary ---")
        print(f"  Campaign:  {result['name']}")
        print(f"  ID:        {result.get('campaign_id', '—')}")
        print(f"  Status:    {result['status']}")
        print(f"  Enrolled:  {result.get('enrolled', 0)} contacts")
        print(f"  Senders:   {len(senders)} accounts")
        print(f"  Steps:     {', '.join(result['steps_completed'])}")

        if result.get("activation_error"):
            print(f"  Error:     {result['activation_error']}")

        log_api_call(conn, "local", "launch_campaign.py", "RUN",
                     {"name": name, "mode": mode, "enrolled": result.get("enrolled", 0)},
                     None, f"Launched {name}: {result['status']}")

    except MCPError as e:
        print(f"\n  MCP Error: {e.message}")
        log_api_call(conn, "local", "launch_campaign.py", "ERROR",
                     {"name": name, "mode": mode}, e.code, e.message)

    conn.close()


if __name__ == "__main__":
    main()
