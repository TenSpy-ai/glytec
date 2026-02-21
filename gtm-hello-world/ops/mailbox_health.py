"""
GTM Hello World — Mailbox Health
Lists sending accounts with status, warmup, and connectivity from Instantly.

Usage:
    python -m ops.mailbox_health                    # List all accounts
    python -m ops.mailbox_health test                # Test vitals on all accounts
    python -m ops.mailbox_health detail <email>      # Detailed view of one account
"""

import sys

from config import DB_PATH
from db import get_conn
from mcp import InstantlyMCP, MCPError

# Instantly account status codes
ACCOUNT_STATUS = {
    1: ("Active", "+"),
    2: ("Paused", "||"),
    3: ("Unknown", "?"),
    -1: ("Conn Error", "X"),
    -2: ("Soft Bounce", "!"),
    -3: ("Send Error", "!!"),
}

WARMUP_STATUS = {
    0: "Paused",
    1: "Active",
    -1: "Banned",
    -2: "Spam Unknown",
    -3: "Perm Suspended",
}


def list_accounts_from_instantly(mcp: InstantlyMCP) -> list:
    """Fetch all sending accounts via MCP, paginating."""
    all_accounts = []
    starting_after = None

    while True:
        result = mcp.list_accounts(limit=100, starting_after=starting_after)

        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = result.get("data", result.get("items", []))

        all_accounts.extend(items)

        next_cursor = None
        if isinstance(result, dict):
            next_cursor = result.get("next_starting_after")
        if not next_cursor or not items:
            break
        starting_after = next_cursor

    return all_accounts


def print_health_table(accounts: list) -> None:
    """Print account health in a formatted table."""
    if not accounts:
        print("  (no sending accounts found)")
        return

    print(f"  {'St':>3s} {'Email':<40s} {'Status':<12s} {'Warmup':<14s} {'Daily':>5s}")
    print(f"  {'---':>3s} {'-'*40} {'-'*12} {'-'*14} {'---':>5s}")

    warnings = []
    for a in accounts:
        email = a.get("email", "—")[:40]
        status_code = a.get("status", 0)
        status_label, icon = ACCOUNT_STATUS.get(status_code, (str(status_code), "?"))

        warmup_code = a.get("warmup_status", a.get("warmup", {}).get("status", 0))
        warmup_label = WARMUP_STATUS.get(warmup_code, str(warmup_code))

        daily = a.get("daily_limit", a.get("sending_limit", "—"))

        print(f"  [{icon:>1s}] {email:<40s} {status_label:<12s} {warmup_label:<14s} {str(daily):>5s}")

        # Flag problems
        if status_code < 0:
            warnings.append(f"  WARNING: {email} — {status_label}")
        if isinstance(warmup_code, int) and warmup_code < 0:
            warnings.append(f"  WARNING: {email} warmup — {warmup_label}")

    if warnings:
        print(f"\n--- Warnings ---")
        for w in warnings:
            print(w)


def test_all_vitals(mcp: InstantlyMCP, accounts: list) -> None:
    """Run test_vitals on all active accounts."""
    print("\n--- Testing Vitals ---")
    for a in accounts:
        email = a.get("email", "")
        if not email:
            continue
        print(f"  Testing {email}...", end=" ")
        try:
            result = mcp.manage_account_state(email, "test_vitals")
            print(f"OK — {result}")
        except MCPError as e:
            print(f"FAILED — {e.message[:80]}")


def main() -> None:
    args = sys.argv[1:]
    mcp = InstantlyMCP()

    print("\nGTM Hello World — Mailbox Health\n")

    # Detail mode
    if args and args[0] == "detail" and len(args) > 1:
        email = args[1]
        print(f"--- Account Detail: {email} ---")
        try:
            detail = mcp.get_account(email)
            for key, val in detail.items():
                if isinstance(val, dict):
                    print(f"  {key}:")
                    for k2, v2 in val.items():
                        print(f"    {k2}: {v2}")
                else:
                    print(f"  {key}: {val}")
        except MCPError as e:
            print(f"  MCP error: {e.message}")
        return

    # List + warmup analytics
    print("--- Sending Accounts ---")
    try:
        accounts = list_accounts_from_instantly(mcp)
        print_health_table(accounts)
        print(f"\n  Total: {len(accounts)} accounts")

        # Get warmup analytics if accounts exist
        if accounts:
            emails = [a.get("email") for a in accounts if a.get("email")]
            if emails:
                print("\n--- Warmup Analytics ---")
                try:
                    warmup = mcp.get_warmup_analytics(emails)
                    if isinstance(warmup, dict):
                        for email, stats in warmup.items():
                            if isinstance(stats, dict):
                                sent = stats.get("sent", "—")
                                received = stats.get("received", "—")
                                inbox = stats.get("inbox_placement", "—")
                                print(f"  {email}: sent={sent} recv={received} inbox={inbox}")
                    elif isinstance(warmup, list):
                        for w in warmup:
                            print(f"  {w}")
                except MCPError:
                    print("  (warmup analytics not available)")

        # Test vitals if requested
        if args and args[0] == "test":
            test_all_vitals(mcp, accounts)

    except MCPError as e:
        print(f"  MCP error: {e.message}")

    # Compare with local DB
    if DB_PATH.exists():
        conn = get_conn()
        rows = conn.execute(
            "SELECT email, status, warmup_status, warmup_score, daily_limit "
            "FROM mailboxes ORDER BY email"
        ).fetchall()
        if rows:
            print(f"\n--- Local DB Mailboxes ({len(rows)}) ---")
            for r in rows:
                st = "Active" if r["status"] == 1 else "Inactive"
                wu = "Warmed" if r["warmup_status"] == 1 else "Not warmed"
                print(f"  {r['email']:<40s} {st} | {wu} | Score: {r['warmup_score']}")
        conn.close()


if __name__ == "__main__":
    main()
