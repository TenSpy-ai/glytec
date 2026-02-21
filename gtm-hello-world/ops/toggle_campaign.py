"""
GTM Hello World — Toggle Campaign
Pause or activate an Instantly campaign.

Usage:
    python -m ops.toggle_campaign "GHW_New_In_Role" pause
    python -m ops.toggle_campaign "GHW_New_In_Role" activate
    python -m ops.toggle_campaign "GHW_New_In_Role" activate --live
"""

import sys

from config import DB_PATH
from db import get_conn
from mcp import InstantlyMCP, MCPError


def find_campaign(mcp: InstantlyMCP, conn, name: str) -> tuple[str | None, str | None]:
    """Find campaign by name. Returns (instantly_id, local_db_id)."""
    # Search Instantly
    try:
        result = mcp.list_campaigns(search=name)
        items = result.get("data", result.get("items", [])) if isinstance(result, dict) else result
        for c in (items if isinstance(items, list) else []):
            if name.lower() in c.get("name", "").lower():
                return c.get("id"), None
    except MCPError:
        pass

    # Search local DB
    if conn:
        row = conn.execute(
            "SELECT id, instantly_campaign_id FROM campaigns WHERE name LIKE ?",
            (f"%{name}%",),
        ).fetchone()
        if row:
            return row["instantly_campaign_id"], row["id"]

    return None, None


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: python -m ops.toggle_campaign <name> <pause|activate> [--live]")
        return

    name = args[0]
    action = args[1].lower()
    live = "--live" in args

    if action not in ("pause", "activate"):
        print(f"Invalid action: {action} — must be 'pause' or 'activate'")
        return

    mcp = InstantlyMCP(dry_run=not live)
    conn = get_conn() if DB_PATH.exists() else None

    print(f"\nGTM Hello World — Toggle Campaign")
    print(f"Action: {action} | Campaign: {name} | Mode: {'LIVE' if live else 'DRY RUN'}\n")

    # Find campaign
    instantly_id, local_id = find_campaign(mcp, conn, name)
    if not instantly_id:
        print(f"  Campaign '{name}' not found")
        return

    print(f"  Found campaign: {instantly_id}")

    # Execute toggle
    try:
        if action == "pause":
            result = mcp.pause_campaign(instantly_id)
            print(f"  Paused campaign: {instantly_id}")
        else:
            result = mcp.activate_campaign(instantly_id)
            print(f"  Activated campaign: {instantly_id}")

        # Update local DB
        if conn and local_id:
            new_status = "paused" if action == "pause" else "active"
            new_instantly_status = 2 if action == "pause" else 1
            timestamp_col = "paused_at" if action == "pause" else "launched_at"
            conn.execute(
                f"""UPDATE campaigns SET status = ?, instantly_status = ?,
                    {timestamp_col} = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                (new_status, new_instantly_status, local_id),
            )
            conn.commit()
            print(f"  Local DB updated: status={new_status}")

    except MCPError as e:
        print(f"  MCP error: {e.message}")
        if action == "activate":
            print("  (Activation requires: senders, leads, sequences, schedule all configured)")

    if conn:
        conn.close()


if __name__ == "__main__":
    main()
