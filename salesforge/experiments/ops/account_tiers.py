"""Account tiers — scored list + rescore option.

Usage:
    python -m salesforge.ops.account_tiers
    python -m salesforge.ops.account_tiers --rescore
    python -m salesforge.ops.account_tiers --tier Priority
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn
from scoring import compute_score, assign_tier


def show_tiers(tier_filter=None, limit=50):
    """Display accounts sorted by score with tier information."""
    conn = get_conn()
    try:
        if tier_filter:
            accounts = conn.execute(
                "SELECT * FROM accounts WHERE tier = ? ORDER BY score DESC LIMIT ?",
                (tier_filter, limit),
            ).fetchall()
        else:
            accounts = conn.execute(
                "SELECT * FROM accounts ORDER BY score DESC LIMIT ?", (limit,)
            ).fetchall()

        # Tier distribution
        dist = conn.execute(
            "SELECT tier, COUNT(*) as cnt FROM accounts GROUP BY tier ORDER BY cnt DESC"
        ).fetchall()

        print(f"\n{'='*80}")
        print(f"  ACCOUNT TIERS")
        print(f"{'='*80}\n")

        print("  Distribution:")
        for d in dist:
            print(f"    {d['tier'] or 'Unscored'}: {d['cnt']}")

        print(f"\n  {'Rank':<6} {'Account':<45} {'Score':>6} {'Tier':<10} {'Beds':>6}")
        print(f"  {'─'*75}")

        for i, a in enumerate(accounts, 1):
            name = (a["system_name"] or "?")[:44]
            print(f"  {i:<6} {name:<45} {a['score'] or 0:>6.1f} {a['tier'] or '-':<10} {a['total_beds'] or 0:>6}")

    finally:
        conn.close()


def rescore_all():
    """Re-run the 6-factor scoring model on all accounts."""
    conn = get_conn()
    try:
        accounts = conn.execute(
            "SELECT id, system_name, total_beds FROM accounts"
        ).fetchall()

        print(f"[rescore] Scoring {len(accounts)} accounts...")
        tier_counts = {"Priority": 0, "Active": 0, "Nurture": 0, "Monitor": 0}

        for acct in accounts:
            score = compute_score(conn, acct["system_name"], acct["total_beds"])
            tier = assign_tier(score)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            conn.execute(
                "UPDATE accounts SET score = ?, tier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (score, tier, acct["id"]),
            )

        conn.commit()
        print(f"[rescore] Done:")
        for tier, count in tier_counts.items():
            print(f"  {tier}: {count}")

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rescore", action="store_true")
    parser.add_argument("--tier")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    if args.rescore:
        rescore_all()
    show_tiers(tier_filter=args.tier, limit=args.limit)
