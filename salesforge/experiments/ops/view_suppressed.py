"""View suppressed contacts grouped by reason.

Usage:
    python -m salesforge.ops.view_suppressed
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def view_suppressed():
    """Show all suppressed contacts grouped by suppression reason."""
    conn = get_conn()

    try:
        # Summary by reason
        reasons = conn.execute(
            """SELECT suppression_reason, COUNT(*) as cnt
               FROM contacts WHERE suppressed = 1
               GROUP BY suppression_reason ORDER BY cnt DESC"""
        ).fetchall()

        total = sum(r["cnt"] for r in reasons)

        if not reasons:
            print("No suppressed contacts.")
            return

        print(f"\n{'='*80}")
        print(f"  SUPPRESSED CONTACTS — {total} total")
        print(f"{'='*80}\n")

        for r in reasons:
            reason = r["suppression_reason"] or "unknown"
            count = r["cnt"]
            print(f"  {reason}: {count}")

            # Show sample contacts per reason
            samples = conn.execute(
                """SELECT first_name, last_name, email, title, account_name
                   FROM contacts WHERE suppressed = 1 AND suppression_reason = ?
                   LIMIT 5""",
                (r["suppression_reason"],),
            ).fetchall()
            for s in samples:
                print(f"    {s['first_name']} {s['last_name']} <{s['email']}> — {s['title'] or '-'} @ {s['account_name'] or '-'}")
            if count > 5:
                print(f"    ... and {count - 5} more")
            print()

        # DNC list summary
        dnc_count = conn.execute("SELECT COUNT(*) FROM dnc_list").fetchone()[0]
        if dnc_count:
            print(f"  DNC List: {dnc_count} emails")
            pushed = conn.execute("SELECT COUNT(*) FROM dnc_list WHERE pushed_to_salesforge = 1").fetchone()[0]
            print(f"    Pushed to Salesforge: {pushed}")
            print(f"    Local only: {dnc_count - pushed}")

    finally:
        conn.close()


if __name__ == "__main__":
    view_suppressed()
