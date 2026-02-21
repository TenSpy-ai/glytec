"""Delete campaign — permanently removes a sequence from Salesforge.

Usage:
    python -m salesforge.ops.delete_campaign "Campaign Name"
    python -m salesforge.ops.delete_campaign "Campaign Name" --live
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn
from config import DRY_RUN


def delete_campaign(name_query, dry_run=True):
    """Delete a Salesforge sequence by name. Irreversible!"""
    client = SalesforgeClient(dry_run=dry_run)
    conn = get_conn()

    try:
        # Find matching sequence
        all_seqs = []
        offset = 0
        while True:
            data = client.list_sequences(limit=50, offset=offset)
            batch = data.get("data", [])
            all_seqs.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        matches = [s for s in all_seqs if name_query.lower() in s.get("name", "").lower()]
        if not matches:
            print(f"[delete] No sequence matching '{name_query}'")
            return

        if len(matches) > 1:
            print(f"[delete] Multiple matches:")
            for m in matches:
                print(f"  - {m['name']} ({m.get('status', '?')}, {m.get('leadCount', 0)} leads)")
            return

        seq = matches[0]
        sid = seq["id"]
        print(f"\n  Campaign: {seq['name']}")
        print(f"  Status: {seq.get('status', '?')}")
        print(f"  Leads: {seq.get('leadCount', 0)}")
        print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"\n  WARNING: This permanently deletes the sequence. Cannot be undone.")

        success = client.delete_sequence(sid)

        if success or dry_run:
            conn.execute(
                """UPDATE campaigns SET status = 'deleted', salesforge_status = 'deleted',
                   updated_at = CURRENT_TIMESTAMP WHERE salesforge_seq_id = ?""",
                (sid,),
            )
            conn.commit()

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--live" not in args
    args = [a for a in args if a != "--live"]
    if not args:
        print("Usage: delete_campaign.py <name> [--live]")
        sys.exit(1)
    delete_campaign(" ".join(args), dry_run=dry_run)
