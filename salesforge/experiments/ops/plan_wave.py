"""Plan wave — find untouched Priority/Active accounts for next outreach.

Usage:
    python -m salesforge.ops.plan_wave
    python -m salesforge.ops.plan_wave --tier Priority
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def plan_wave(tier_filter=None, limit=30):
    """Find Priority/Active accounts that have no contacts in any campaign."""
    conn = get_conn()
    try:
        tiers = [tier_filter] if tier_filter else ["Priority", "Active"]
        placeholders = ",".join("?" * len(tiers))

        untouched = conn.execute(
            f"""SELECT a.*, COUNT(c.id) as contact_count
               FROM accounts a
               LEFT JOIN contacts c ON c.account_name = a.system_name
                   AND c.suppressed = 0 AND c.icp_matched = 1
               WHERE a.tier IN ({placeholders})
               AND NOT EXISTS (
                   SELECT 1 FROM campaign_contacts cc
                   JOIN contacts c2 ON cc.contact_id = c2.id
                   WHERE c2.account_name = a.system_name
               )
               GROUP BY a.id
               ORDER BY a.score DESC
               LIMIT ?""",
            (*tiers, limit),
        ).fetchall()

        print(f"\n{'='*80}")
        print(f"  WAVE PLANNER — Untouched {'/'.join(tiers)} accounts")
        print(f"{'='*80}\n")

        if not untouched:
            print("  All accounts in target tiers have been reached!")
            return

        print(f"  {len(untouched)} untouched accounts:\n")
        print(f"  {'Account':<45} {'Score':>6} {'Tier':<10} {'Contacts':>9} {'Beds':>6}")
        print(f"  {'─'*80}")

        for a in untouched:
            name = (a["system_name"] or "?")[:44]
            print(f"  {name:<45} {a['score'] or 0:>6.1f} {a['tier']:<10} {a['contact_count']:>9} {a['total_beds'] or 0:>6}")

        total_contacts = sum(a["contact_count"] for a in untouched)
        print(f"\n  Total contacts available: {total_contacts}")
        print(f"  Recommendation: Create a campaign targeting these accounts")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    plan_wave(tier_filter=args.tier, limit=args.limit)
