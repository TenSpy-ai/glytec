"""
GTM Hello World — Enroll Contacts
Add contacts from local DB into an existing Instantly campaign via MCP bulk add.

Usage:
    python -m ops.enroll_contacts --campaign "GHW_New_In_Role" --account "HCA"
    python -m ops.enroll_contacts --campaign "GHW_New_In_Role" --tier Active --live
    python -m ops.enroll_contacts --campaign "GHW_New_In_Role" --all --live
"""

import json
import sys

from config import DB_PATH
from db import get_conn, log_api_call
from mcp import InstantlyMCP, MCPError


def find_campaign_id(conn, mcp: InstantlyMCP, name: str) -> str | None:
    """Find Instantly campaign ID by name (local DB first, then MCP)."""
    # Local DB
    row = conn.execute(
        "SELECT instantly_campaign_id FROM campaigns WHERE name LIKE ?",
        (f"%{name}%",),
    ).fetchone()
    if row and row["instantly_campaign_id"]:
        return row["instantly_campaign_id"]

    # MCP search
    try:
        result = mcp.list_campaigns(search=name)
        items = result.get("data", result.get("items", [])) if isinstance(result, dict) else result
        for c in (items if isinstance(items, list) else []):
            if name.lower() in c.get("name", "").lower():
                return c.get("id")
    except MCPError:
        pass

    return None


def get_eligible_contacts(conn, account: str | None = None,
                          tier: str | None = None,
                          campaign_name: str | None = None) -> list:
    """Get contacts eligible for enrollment (deduped against existing enrollments + block list)."""
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
          AND c.email NOT IN (
              SELECT ct.email FROM contacts ct
              JOIN campaign_contacts cc ON ct.id = cc.contact_id
              JOIN campaigns camp ON cc.campaign_id = camp.id
              WHERE camp.name LIKE ?
          )
          AND c.email NOT IN (SELECT value FROM block_list)
        ORDER BY c.icp_intent_score DESC
    """
    params.append(f"%{campaign_name or ''}%")

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def build_lead_payload(contact: dict) -> dict:
    """Build Instantly lead payload from local contact."""
    payload = {
        "email": contact["email"],
        "first_name": contact.get("first_name", ""),
        "last_name": contact.get("last_name", ""),
        "company_name": contact.get("account_name", ""),
    }

    # Custom variables for ICP data
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


def enroll_batch(mcp: InstantlyMCP, campaign_id: str, contacts: list,
                 conn=None, batch_size: int = 1000) -> int:
    """Enroll contacts in batches of up to 1000."""
    total_enrolled = 0

    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        leads = [build_lead_payload(c) for c in batch]

        print(f"  Enrolling batch {i//batch_size + 1} ({len(leads)} leads)...")
        result = mcp.add_leads_bulk(
            campaign_id=campaign_id,
            leads=leads,
            skip_if_in_workspace=True,
        )
        total_enrolled += len(leads)
        print(f"    Result: {result}")

        # Record in campaign_contacts
        if conn:
            # Find local campaign id
            camp = conn.execute(
                "SELECT id FROM campaigns WHERE instantly_campaign_id = ?",
                (campaign_id,),
            ).fetchone()
            if camp:
                for contact in batch:
                    conn.execute(
                        """INSERT OR IGNORE INTO campaign_contacts (campaign_id, contact_id)
                           VALUES (?, ?)""",
                        (camp["id"], contact["id"]),
                    )
                conn.commit()

    return total_enrolled


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m ops.enroll_contacts --campaign <name> [filters] [--live]")
        print("  --campaign <name>   Campaign to enroll into (required)")
        print("  --account <name>    Filter by account name")
        print("  --tier <tier>       Filter by account tier (Priority/Active/Nurture)")
        print("  --all               Enroll all eligible contacts")
        print("  --live              Execute real API calls")
        return

    # Parse args
    campaign_name = None
    account = None
    tier = None
    all_contacts = False
    live = "--live" in args

    i = 0
    while i < len(args):
        if args[i] == "--campaign" and i + 1 < len(args):
            campaign_name = args[i + 1]; i += 2
        elif args[i] == "--account" and i + 1 < len(args):
            account = args[i + 1]; i += 2
        elif args[i] == "--tier" and i + 1 < len(args):
            tier = args[i + 1]; i += 2
        elif args[i] == "--all":
            all_contacts = True; i += 1
        else:
            i += 1

    if not campaign_name:
        print("Error: --campaign is required")
        return

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = get_conn()
    mcp = InstantlyMCP(dry_run=not live)

    mode = "LIVE" if live else "DRY RUN"
    print(f"\nGTM Hello World — Enroll Contacts ({mode})")
    print(f"Campaign: {campaign_name}\n")

    # Find campaign
    campaign_id = find_campaign_id(conn, mcp, campaign_name)
    if not campaign_id:
        print(f"  Campaign '{campaign_name}' not found")
        conn.close()
        return
    print(f"  Campaign ID: {campaign_id}")

    # Get eligible contacts
    contacts = get_eligible_contacts(conn, account=account, tier=tier,
                                     campaign_name=campaign_name)
    if not contacts:
        print("  No eligible contacts found (all may already be enrolled or blocked)")
        conn.close()
        return

    print(f"  Eligible contacts: {len(contacts)}")
    for c in contacts[:5]:
        print(f"    {c['first_name']} {c['last_name']} ({c['title']}) @ {c['account_name']}")
    if len(contacts) > 5:
        print(f"    ... and {len(contacts) - 5} more")

    # Enroll
    print()
    enrolled = enroll_batch(mcp, campaign_id, contacts, conn=conn)

    print(f"\n--- Summary ---")
    print(f"  Enrolled: {enrolled}/{len(contacts)} contacts")

    log_api_call(conn, "local", "enroll_contacts.py", "RUN",
                 {"campaign": campaign_name, "mode": mode, "enrolled": enrolled},
                 None, f"Enrolled {enrolled} contacts")
    conn.close()


if __name__ == "__main__":
    main()
