"""Compare campaigns — side-by-side metrics for 2+ campaigns.

Usage:
    python -m salesforge.ops.compare_campaigns "Campaign A" "Campaign B"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn
from api import SalesforgeClient


def compare_campaigns(names):
    """Show side-by-side metrics for multiple campaigns."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        # Get all sequences
        all_seqs = []
        offset = 0
        while True:
            data = client.list_sequences(limit=50, offset=offset)
            batch = data.get("data", [])
            all_seqs.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        matched = []
        for name in names:
            found = [s for s in all_seqs if name.lower() in s.get("name", "").lower()]
            if found:
                matched.append(found[0])
            else:
                print(f"  No sequence matching '{name}'")

        if len(matched) < 2:
            print("Need at least 2 campaigns to compare.")
            return

        # Header
        print(f"\n{'='*80}")
        print(f"  CAMPAIGN COMPARISON")
        print(f"{'='*80}\n")

        # Build comparison table
        metrics = ["name", "status", "leadCount", "contactedCount",
                    "openedPercent", "repliedPercent", "bouncedPercent",
                    "clickedPercent", "completedCount"]
        labels = ["Campaign", "Status", "Leads", "Contacted",
                  "Open %", "Reply %", "Bounce %", "Click %", "Completed"]

        col_width = max(len(m.get("name", "?")) for m in matched) + 2
        col_width = max(col_width, 15)

        # Print header
        print(f"  {'Metric':<20}", end="")
        for m in matched:
            print(f"  {m.get('name', '?')[:col_width]:<{col_width}}", end="")
        print()
        print(f"  {'─'*20}", end="")
        for _ in matched:
            print(f"  {'─'*col_width}", end="")
        print()

        for metric, label in zip(metrics, labels):
            print(f"  {label:<20}", end="")
            for m in matched:
                val = m.get(metric, "-")
                if isinstance(val, float):
                    print(f"  {val:<{col_width}.1f}", end="")
                else:
                    print(f"  {str(val)[:col_width]:<{col_width}}", end="")
            print()

        # Winner summary
        if all(m.get("openedPercent", 0) for m in matched):
            best_open = max(matched, key=lambda m: m.get("openedPercent", 0))
            print(f"\n  Best open rate: {best_open['name']} ({best_open['openedPercent']:.1f}%)")
        if all(m.get("repliedPercent", 0) for m in matched):
            best_reply = max(matched, key=lambda m: m.get("repliedPercent", 0))
            print(f"  Best reply rate: {best_reply['name']} ({best_reply['repliedPercent']:.1f}%)")

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: compare_campaigns.py <name1> <name2> [name3...]")
        sys.exit(1)
    compare_campaigns(args)
