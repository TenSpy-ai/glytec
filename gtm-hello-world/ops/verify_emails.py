"""
GTM Hello World — Verify Emails
Verify email addresses via Instantly MCP before enrollment.

Usage:
    python -m ops.verify_emails user@example.com           # Verify single email
    python -m ops.verify_emails --from-db --unverified      # Verify all unverified in DB
    python -m ops.verify_emails --from-db --account "HCA"   # Verify contacts at account
"""

import sys
import time

from config import DB_PATH
from db import get_conn
from mcp import InstantlyMCP, MCPError


def verify_single(mcp: InstantlyMCP, email: str) -> dict:
    """Verify a single email address. Returns verification result."""
    print(f"  Verifying {email}...", end=" ", flush=True)
    try:
        result = mcp.verify_email(email)
        status = result.get("verification_status", result.get("status", "unknown"))
        print(f"{status}")
        return {"email": email, "status": status, "result": result}
    except MCPError as e:
        print(f"ERROR: {e.message[:60]}")
        return {"email": email, "status": "error", "error": str(e)}


def verify_batch(mcp: InstantlyMCP, emails: list, conn=None,
                 delay: float = 1.0) -> dict:
    """Verify a batch of emails with rate limiting.

    Returns summary: {valid: N, invalid: N, risky: N, unknown: N, error: N}
    """
    summary = {"valid": 0, "invalid": 0, "risky": 0, "unknown": 0, "error": 0}
    results = []

    for i, email in enumerate(emails):
        result = verify_single(mcp, email)
        status = result.get("status", "unknown").lower()

        # Map to standard categories
        if status in ("valid", "deliverable"):
            summary["valid"] += 1
            db_status = "valid"
        elif status in ("invalid", "undeliverable", "bounce"):
            summary["invalid"] += 1
            db_status = "invalid"
        elif status in ("risky", "accept_all", "catch_all"):
            summary["risky"] += 1
            db_status = "risky"
        elif status == "error":
            summary["error"] += 1
            db_status = None
        else:
            summary["unknown"] += 1
            db_status = "unknown"

        results.append(result)

        # Update DB if connected
        if conn and db_status:
            conn.execute(
                """UPDATE contacts SET email_verified = ?,
                   email_verified_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE email = ?""",
                (db_status, email),
            )
            conn.commit()

        # Rate limit (verify_email takes 5-45s per call, but add safety delay)
        if i < len(emails) - 1:
            time.sleep(delay)

    return summary


def get_unverified_emails(conn, account: str | None = None) -> list:
    """Get emails from DB that haven't been verified yet."""
    if account:
        rows = conn.execute(
            """SELECT email FROM contacts
               WHERE email IS NOT NULL AND email_verified IS NULL
                 AND account_name LIKE ?
               ORDER BY icp_intent_score DESC""",
            (f"%{account}%",),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT email FROM contacts
               WHERE email IS NOT NULL AND email_verified IS NULL
               ORDER BY icp_intent_score DESC""",
        ).fetchall()
    return [r["email"] for r in rows]


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python -m ops.verify_emails <email>")
        print("  python -m ops.verify_emails --from-db --unverified")
        print("  python -m ops.verify_emails --from-db --account <name>")
        return

    mcp = InstantlyMCP()
    conn = get_conn() if DB_PATH.exists() else None

    print(f"\nGTM Hello World — Verify Emails\n")

    if "--from-db" in args:
        if not conn:
            print("  Database not found. Run: python seed_db.py")
            return

        account = None
        if "--account" in args:
            idx = args.index("--account")
            if idx + 1 < len(args):
                account = args[idx + 1]

        emails = get_unverified_emails(conn, account=account)
        if not emails:
            print("  No unverified emails found")
            return

        print(f"  Found {len(emails)} unverified emails")
        if account:
            print(f"  Filtered to account: {account}")
        print()

        summary = verify_batch(mcp, emails, conn=conn)

        print(f"\n--- Summary ---")
        print(f"  Valid:   {summary['valid']}")
        print(f"  Invalid: {summary['invalid']}")
        print(f"  Risky:   {summary['risky']}")
        print(f"  Unknown: {summary['unknown']}")
        print(f"  Error:   {summary['error']}")

        if summary["invalid"] > 0:
            print(f"\n  {summary['invalid']} invalid emails found — consider adding to block list")

    else:
        # Single email verification
        email = args[0]
        result = verify_single(mcp, email)

        if conn:
            status = result.get("status", "unknown").lower()
            if status in ("valid", "deliverable"):
                db_status = "valid"
            elif status in ("invalid", "undeliverable"):
                db_status = "invalid"
            elif status in ("risky", "accept_all"):
                db_status = "risky"
            else:
                db_status = "unknown"
            conn.execute(
                """UPDATE contacts SET email_verified = ?,
                   email_verified_at = CURRENT_TIMESTAMP
                   WHERE email = ?""",
                (db_status, email),
            )
            conn.commit()

    if conn:
        conn.close()


if __name__ == "__main__":
    main()
