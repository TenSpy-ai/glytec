"""
GTM Hello World — Campaign Status
Lists all campaigns from Instantly with status, lead counts, and performance.

Usage:
    python -m ops.campaign_status                  # List all
    python -m ops.campaign_status active            # Filter by status
    python -m ops.campaign_status detail <name>     # Detailed view
"""

import sys

from config import DB_PATH
from db import get_conn
from mcp import InstantlyMCP, MCPError

# Instantly status codes → display
STATUS_MAP = {
    0: ("Draft", "~"),
    1: ("Active", "+"),
    2: ("Paused", "||"),
    3: ("Completed", "*"),
    4: ("Running Subsequences", ">>"),
    -99: ("Suspended", "X"),
    -1: ("Unhealthy", "!"),
    -2: ("Bounce Protect", "!!"),
}


def list_campaigns_from_instantly(mcp: InstantlyMCP) -> list:
    """Fetch all campaigns from Instantly via MCP, paginating as needed."""
    all_campaigns = []
    starting_after = None

    while True:
        result = mcp.list_campaigns(limit=100, starting_after=starting_after)

        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = result.get("data", result.get("items", []))
            if not items and not result.get("next_starting_after"):
                # Might be the list itself
                if all(isinstance(v, dict) for v in result.values()):
                    break
                items = [result] if result.get("id") else []

        all_campaigns.extend(items)

        # Pagination
        next_cursor = None
        if isinstance(result, dict):
            next_cursor = result.get("next_starting_after")
        if not next_cursor or not items:
            break
        starting_after = next_cursor

    return all_campaigns


def list_campaigns_from_db(conn) -> list:
    """Fetch campaigns from local DB."""
    rows = conn.execute(
        "SELECT id, name, instantly_campaign_id, instantly_status, "
        "recipe, status, target_persona, step_count, daily_limit "
        "FROM campaigns ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def print_campaign_table(campaigns: list, source: str) -> None:
    """Print campaigns in a formatted table."""
    if not campaigns:
        print(f"  (no campaigns found in {source})")
        return

    print(f"  {'St':>3s} {'Name':<35s} {'Status':<12s} {'Leads':>6s} {'Recipe':<6s}")
    print(f"  {'---':>3s} {'---':<35s} {'---':<12s} {'---':>6s} {'---':<6s}")

    for c in campaigns:
        # Handle both Instantly API and local DB formats
        if "status" in c and isinstance(c["status"], int):
            status_code = c["status"]
            status_label, icon = STATUS_MAP.get(status_code, (str(status_code), "?"))
        elif "instantly_status" in c:
            status_code = c.get("instantly_status")
            status_label, icon = STATUS_MAP.get(status_code, (str(status_code), "?"))
        else:
            status_label = c.get("status", "—")
            icon = "?"

        name = c.get("name", "—")[:35]
        leads = c.get("leads_count", c.get("lead_count", "—"))
        recipe = c.get("recipe", "—") or "—"

        print(f"  [{icon:>1s}] {name:<35s} {status_label:<12s} {str(leads):>6s} {recipe:<6s}")


def print_campaign_detail(campaign: dict) -> None:
    """Print detailed view of a single campaign."""
    print(f"\n  Campaign: {campaign.get('name', '—')}")
    print(f"  ID: {campaign.get('id', '—')}")

    status_code = campaign.get("status")
    status_label, _ = STATUS_MAP.get(status_code, (str(status_code), "?"))
    print(f"  Status: {status_label} ({status_code})")
    print(f"  Leads: {campaign.get('leads_count', '—')}")

    # Sequences/steps
    sequences = campaign.get("sequences", [])
    if sequences:
        steps = sequences[0].get("steps", []) if sequences else []
        print(f"  Steps: {len(steps)}")
        for i, step in enumerate(steps):
            subject = step.get("subject", step.get("variants", [{}])[0].get("subject", "—"))
            print(f"    Step {i+1}: {subject[:60]}")

    # Sender accounts
    email_list = campaign.get("email_list", [])
    if email_list:
        print(f"  Senders: {', '.join(email_list[:5])}")

    # Settings
    print(f"  Daily limit: {campaign.get('daily_limit', '—')}")
    print(f"  Stop on reply: {campaign.get('stop_on_reply', '—')}")
    print(f"  Open tracking: {campaign.get('open_tracking', '—')}")


def main() -> None:
    args = sys.argv[1:]
    mcp = InstantlyMCP()
    conn = get_conn() if DB_PATH.exists() else None

    print("\nGTM Hello World — Campaign Status\n")

    # Detail mode
    if args and args[0] == "detail" and len(args) > 1:
        search_name = " ".join(args[1:])
        print(f"--- Detail: {search_name} ---")
        try:
            campaigns = list_campaigns_from_instantly(mcp)
            match = next((c for c in campaigns
                          if search_name.lower() in c.get("name", "").lower()), None)
            if match and match.get("id"):
                detail = mcp.get_campaign(match["id"])
                print_campaign_detail(detail)
            else:
                print(f"  Campaign '{search_name}' not found in Instantly")
        except MCPError as e:
            print(f"  MCP error: {e.message}")
        return

    # List mode
    print("--- Instantly Campaigns ---")
    try:
        campaigns = list_campaigns_from_instantly(mcp)

        # Filter by status if arg provided
        if args and args[0] in ("active", "paused", "draft", "completed"):
            status_filter = {"active": 1, "paused": 2, "draft": 0, "completed": 3}
            code = status_filter[args[0]]
            campaigns = [c for c in campaigns if c.get("status") == code]

        print_campaign_table(campaigns, "Instantly")
        print(f"\n  Total: {len(campaigns)} campaigns")
    except MCPError as e:
        print(f"  MCP error: {e.message}")
        print("  (Falling back to local DB)")

    # Also show local DB campaigns
    if conn:
        print("\n--- Local DB Campaigns ---")
        db_campaigns = list_campaigns_from_db(conn)
        print_campaign_table(db_campaigns, "local DB")
        print(f"\n  Total: {len(db_campaigns)} campaigns")
        conn.close()


if __name__ == "__main__":
    main()
