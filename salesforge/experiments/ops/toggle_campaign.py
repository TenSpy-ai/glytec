"""Toggle campaign — activate or pause a sequence.

Usage:
    python -m salesforge.ops.toggle_campaign "Campaign Name" pause
    python -m salesforge.ops.toggle_campaign "Campaign Name" activate --live
"""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn
from config import DRY_RUN


def toggle_campaign(name_query, action, dry_run=True):
    """Activate or pause a campaign by name."""
    if action not in ("activate", "pause"):
        print(f"[toggle] Invalid action '{action}' — must be 'activate' or 'pause'")
        return

    target_status = "active" if action == "activate" else "paused"
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
            print(f"[toggle] No sequence matching '{name_query}'")
            return

        if len(matches) > 1:
            print(f"[toggle] Multiple matches — please be more specific:")
            for m in matches:
                print(f"  - {m['name']} ({m.get('status', '?')})")
            return

        seq = matches[0]
        sid = seq["id"]
        current_status = seq.get("status", "?")

        print(f"\n  Campaign: {seq['name']}")
        print(f"  Current: {current_status} → Target: {target_status}")
        print(f"  Leads: {seq.get('leadCount', 0)}")
        print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")

        if current_status == target_status:
            print(f"\n  Already {target_status} — no change needed.")
            return

        if action == "activate":
            print(f"\n  WARNING: Activating will START SENDING emails to {seq.get('leadCount', 0)} contacts!")

        success = client.set_status(sid, target_status)

        if success or dry_run:
            conn.execute(
                """UPDATE campaigns SET status = ?, salesforge_status = ?,
                   updated_at = CURRENT_TIMESTAMP WHERE salesforge_seq_id = ?""",
                (target_status, target_status, sid),
            )
            if action == "activate":
                conn.execute(
                    "UPDATE campaigns SET launched_at = ? WHERE salesforge_seq_id = ?",
                    (datetime.datetime.now().isoformat(), sid),
                )
            elif action == "pause":
                conn.execute(
                    "UPDATE campaigns SET paused_at = ? WHERE salesforge_seq_id = ?",
                    (datetime.datetime.now().isoformat(), sid),
                )
            conn.commit()

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--live" not in args
    args = [a for a in args if a != "--live"]

    if len(args) < 2:
        print("Usage: toggle_campaign.py <name> <activate|pause> [--live]")
        sys.exit(1)

    name_query = args[0]
    action = args[1]
    toggle_campaign(name_query, action, dry_run=dry_run)
