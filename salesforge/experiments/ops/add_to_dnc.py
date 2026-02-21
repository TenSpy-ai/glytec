"""Add to DNC — local + Salesforge Do Not Contact list.

Usage:
    python -m salesforge.ops.add_to_dnc user@example.com --reason opt_out
    python -m salesforge.ops.add_to_dnc user@example.com another@example.com --reason bounce --live

IRREVERSIBLE: Salesforge DNC entries cannot be removed via API.
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn
from config import DRY_RUN
import datetime


def add_to_dnc(emails, reason="manual", source="manual", dry_run=True):
    """Add emails to DNC list (local + Salesforge)."""
    client = SalesforgeClient(dry_run=dry_run)
    conn = get_conn()

    try:
        print(f"\n  WARNING: Adding to DNC is IRREVERSIBLE in Salesforge!")
        print(f"  Cannot list or remove DNC entries via API.")
        print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}\n")

        added_local = 0
        for email in emails:
            email = email.strip().lower()

            # Show context
            contact = conn.execute(
                "SELECT * FROM contacts WHERE LOWER(email) = ?", (email,)
            ).fetchone()
            if contact:
                print(f"  {email}")
                print(f"    Name: {contact['first_name']} {contact['last_name']}")
                print(f"    Title: {contact['title']} @ {contact['company']}")
                print(f"    Account: {contact['account_name']}")
            else:
                print(f"  {email} (not in local database)")

            # Add to local DNC
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO dnc_list (email, reason, source)
                       VALUES (?, ?, ?)""",
                    (email, reason, source),
                )
                added_local += 1
            except Exception:
                pass

            # Suppress the contact locally
            conn.execute(
                "UPDATE contacts SET suppressed = 1, suppression_reason = ? WHERE LOWER(email) = ?",
                (f"dnc_{reason}", email),
            )

        conn.commit()

        # Push to Salesforge
        if not dry_run:
            result = client.add_to_dnc(emails)
            created = result.get("created", 0) if result else 0
            print(f"\n  Salesforge DNC: {created} added")

            # Mark as pushed
            for email in emails:
                conn.execute(
                    "UPDATE dnc_list SET pushed_to_salesforge = 1, pushed_at = ? WHERE email = ?",
                    (datetime.datetime.now().isoformat(), email.strip().lower()),
                )
            conn.commit()

        print(f"\n  Local DNC: {added_local} added")
        print(f"  Contacts suppressed locally")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("emails", nargs="+", help="Email addresses to add to DNC")
    parser.add_argument("--reason", default="manual", help="Reason: opt_out, bounce, suppression, manual")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    add_to_dnc(args.emails, reason=args.reason, source=args.source,
               dry_run=not args.live)
