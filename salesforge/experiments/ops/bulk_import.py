"""Bulk import — CSV → ICP match → dedup → insert contacts.

Usage:
    python -m salesforge.ops.bulk_import contacts.csv
"""

import sys
import csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn
from icp import load_icp_titles, match_title


def bulk_import(csv_path):
    """Import contacts from CSV with ICP matching and dedup."""
    conn = get_conn()
    icp_titles = load_icp_titles()

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print("[import] Empty CSV file")
            return

        print(f"[import] Processing {len(rows)} rows from {csv_path}...")

        imported = 0
        dupes = 0
        matched = 0

        for row in rows:
            email = (row.get("email") or row.get("Email") or "").strip()
            if not email:
                continue

            # Check for duplicates
            existing = conn.execute(
                "SELECT id FROM contacts WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                dupes += 1
                continue

            first_name = row.get("first_name") or row.get("FirstName") or row.get("First Name") or ""
            last_name = row.get("last_name") or row.get("LastName") or row.get("Last Name") or ""
            title = row.get("title") or row.get("Title") or row.get("Job Title") or ""
            company = row.get("company") or row.get("Company") or row.get("Organization") or ""
            linkedin = row.get("linkedin_url") or row.get("LinkedIn") or row.get("LinkedIn URL") or ""
            account = row.get("account_name") or row.get("Account") or row.get("Parent Company") or company

            # ICP match
            icp = match_title(title, icp_titles)
            icp_category = icp["Category"] if icp else None
            icp_score = icp["Intent Score"] if icp else None
            icp_function = icp["Function Type"] if icp else None
            icp_level = icp["Job Level"] if icp else None
            icp_dept = icp["Department"] if icp else None
            icp_matched_flag = 1 if icp else 0

            conn.execute(
                """INSERT INTO contacts
                   (first_name, last_name, email, title, company, linkedin_url,
                    account_name, source, validated, golden_record,
                    icp_category, icp_intent_score, icp_function_type, icp_job_level,
                    icp_department, icp_matched)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'csv_import', 1, 1, ?, ?, ?, ?, ?, ?)""",
                (first_name.strip(), last_name.strip(), email, title.strip(),
                 company.strip(), linkedin.strip() or None, account.strip(),
                 icp_category, icp_score, icp_function, icp_level, icp_dept,
                 icp_matched_flag),
            )
            imported += 1
            if icp:
                matched += 1

        conn.commit()

        print(f"\n[import] Results:")
        print(f"  Imported: {imported}")
        print(f"  Duplicates skipped: {dupes}")
        print(f"  ICP matched: {matched}")

    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: bulk_import.py <csv_file>")
        sys.exit(1)
    bulk_import(sys.argv[1])
