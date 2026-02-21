"""
GTM Hello World — Block List (DNC)
Add, list, or remove entries from the Instantly block list.
Uses REST API (no MCP for block list).

Usage:
    python -m ops.block_list --list                           # List entries
    python -m ops.block_list add user@example.com --reason opt_out   # Block email
    python -m ops.block_list add example.com --reason domain         # Block domain
    python -m ops.block_list remove <entry_id>                # Unblock (reversible!)
    python -m ops.block_list add user@example.com --live      # Live mode
"""

import sys

from config import DB_PATH
from db import get_conn
from api import InstantlyAPI


def list_entries(api: InstantlyAPI, conn) -> None:
    """List all block list entries from Instantly + local DB."""
    print("--- Instantly Block List ---")
    all_entries = []
    starting_after = None

    while True:
        result = api.list_block_list_entries(limit=100, starting_after=starting_after)
        items = result.get("items", result.get("data", []))
        if isinstance(items, list):
            all_entries.extend(items)
        next_cursor = result.get("next_starting_after")
        if not next_cursor or not items:
            break
        starting_after = next_cursor

    if all_entries:
        print(f"  {'ID':<25s} {'Value':<40s} {'Domain?':>7s}")
        print(f"  {'-'*25} {'-'*40} {'-'*7}")
        for entry in all_entries:
            eid = str(entry.get("id", "—"))[:25]
            value = entry.get("bl_value", entry.get("value", "—"))[:40]
            is_domain = "Yes" if entry.get("is_domain") else "No"
            print(f"  {eid:<25s} {value:<40s} {is_domain:>7s}")
        print(f"\n  Total: {len(all_entries)} entries")
    else:
        print("  (no entries)")

    # Local DB block list
    if conn:
        rows = conn.execute(
            "SELECT value, is_domain, reason, added_by, created_at "
            "FROM block_list ORDER BY created_at DESC"
        ).fetchall()
        if rows:
            print(f"\n--- Local Block List ({len(rows)} entries) ---")
            for r in rows:
                domain = "domain" if r["is_domain"] else "email"
                print(f"  {r['value']:<40s} {domain:>6s} | {r['reason'] or '—'} "
                      f"| {r['added_by']} | {r['created_at']}")


def add_entry(api: InstantlyAPI, conn, value: str, reason: str, live: bool) -> None:
    """Add an email or domain to the block list."""
    is_domain = "@" not in value and "." in value

    print(f"  Blocking: {value} ({'domain' if is_domain else 'email'})")
    print(f"  Reason: {reason}")

    # Add to Instantly
    result = api.create_block_list_entry(value)
    instantly_id = result.get("id")

    # Add to local DB
    if conn:
        conn.execute(
            """INSERT OR IGNORE INTO block_list
               (value, is_domain, reason, instantly_id, added_by)
               VALUES (?, ?, ?, ?, ?)""",
            (value, 1 if is_domain else 0, reason, instantly_id, "command"),
        )
        conn.commit()
        print(f"  Added to local block_list table")


def remove_entry(api: InstantlyAPI, conn, entry_id: str) -> None:
    """Remove an entry from the block list (reversible!)."""
    print(f"  Removing block entry: {entry_id}")

    success = api.delete_block_list_entry(entry_id)
    if success:
        print(f"  Removed from Instantly")

    # Remove from local DB by instantly_id
    if conn:
        conn.execute(
            "DELETE FROM block_list WHERE instantly_id = ?", (entry_id,),
        )
        conn.commit()


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python -m ops.block_list --list")
        print("  python -m ops.block_list add <email_or_domain> --reason <reason> [--live]")
        print("  python -m ops.block_list remove <entry_id> [--live]")
        return

    live = "--live" in args
    args = [a for a in args if a != "--live"]

    api = InstantlyAPI(dry_run=not live)
    conn = get_conn() if DB_PATH.exists() else None

    mode = "LIVE" if live else "DRY RUN"
    print(f"\nGTM Hello World — Block List ({mode})\n")

    if args[0] == "--list":
        list_entries(api, conn)

    elif args[0] == "add" and len(args) >= 2:
        value = args[1]
        reason = "manual"
        if "--reason" in args:
            idx = args.index("--reason")
            if idx + 1 < len(args):
                reason = args[idx + 1]
        add_entry(api, conn, value, reason, live)

    elif args[0] == "remove" and len(args) >= 2:
        entry_id = args[1]
        remove_entry(api, conn, entry_id)

    else:
        print("Unknown command. Use --list, add, or remove.")

    if conn:
        conn.close()


if __name__ == "__main__":
    main()
