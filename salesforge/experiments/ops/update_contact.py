"""Update contact — local field updates (Salesforge contacts are read-only).

Usage:
    python -m salesforge.ops.update_contact --email user@example.com --title "VP of Quality"
    python -m salesforge.ops.update_contact --email user@example.com --account "New Health System"
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn
from icp import load_icp_titles, match_title


def update_contact(email, **fields):
    """Update a contact's local fields. Salesforge has no update API."""
    conn = get_conn()

    try:
        contact = conn.execute(
            "SELECT * FROM contacts WHERE LOWER(email) = ?", (email.lower(),)
        ).fetchone()

        if not contact:
            print(f"No contact found with email: {email}")
            return

        print(f"\n  Contact: {contact['first_name']} {contact['last_name']} <{contact['email']}>")

        updates = []
        params = []
        for field, value in fields.items():
            if value is not None and field in (
                "first_name", "last_name", "title", "phone", "company",
                "linkedin_url", "account_name", "facility_definitive_id", "source"
            ):
                old_val = contact[field]
                updates.append(f"{field} = ?")
                params.append(value)
                print(f"  {field}: {old_val} → {value}")

        if not updates:
            print("  No valid fields to update")
            return

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(contact["id"])

        conn.execute(
            f"UPDATE contacts SET {', '.join(updates)} WHERE id = ?",
            params,
        )

        # Re-run ICP matching if title changed
        if "title" in fields and fields["title"]:
            icp = match_title(fields["title"])
            if icp:
                conn.execute(
                    """UPDATE contacts SET icp_matched = 1, icp_category = ?,
                       icp_intent_score = ?, icp_function_type = ?, icp_job_level = ?,
                       icp_department = ? WHERE id = ?""",
                    (icp["Category"], icp["Intent Score"], icp["Function Type"],
                     icp["Job Level"], icp["Department"], contact["id"]),
                )
                print(f"  ICP re-matched: {icp['Category']} ({icp['Intent Score']})")

        conn.commit()
        print(f"\n  Note: Salesforge contact is NOT updated (no update API exists)")
        print(f"  These changes are local only")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--first-name")
    parser.add_argument("--last-name")
    parser.add_argument("--title")
    parser.add_argument("--phone")
    parser.add_argument("--company")
    parser.add_argument("--linkedin")
    parser.add_argument("--account")
    args = parser.parse_args()

    update_contact(
        args.email,
        first_name=args.first_name,
        last_name=args.last_name,
        title=args.title,
        phone=args.phone,
        company=args.company,
        linkedin_url=args.linkedin,
        account_name=args.account,
    )
