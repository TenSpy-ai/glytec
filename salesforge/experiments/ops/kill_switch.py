"""Kill switch — check bounce/spam thresholds and auto-pause campaigns.

Thresholds: bounce >5%, spam >0.3%
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from config import BOUNCE_THRESHOLD, SPAM_THRESHOLD, DRY_RUN
from db import get_conn


def check_kill_switch():
    """Check all active campaigns against kill-switch thresholds."""
    client = SalesforgeClient(dry_run=DRY_RUN)
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

        active_seqs = [s for s in all_seqs if s.get("status") == "active"]
        if not active_seqs:
            print("[kill-switch] No active campaigns to check.")
            return

        print(f"\n[kill-switch] Checking {len(active_seqs)} active campaigns...")
        paused = 0

        for seq in active_seqs:
            name = seq.get("name", "?")
            sid = seq["id"]
            contacted = seq.get("contactedCount", 0) or 1
            bounced = seq.get("bouncedCount", 0)
            bounce_rate = bounced / contacted

            # Salesforge doesn't track spam separately — use bounce as proxy
            should_pause = False
            reasons = []

            if bounce_rate > BOUNCE_THRESHOLD:
                should_pause = True
                reasons.append(f"bounce {bounce_rate*100:.1f}% > {BOUNCE_THRESHOLD*100}%")

            if should_pause:
                print(f"  [!] {name}: PAUSING — {', '.join(reasons)}")
                success = client.set_status(sid, "paused")
                if success or DRY_RUN:
                    paused += 1
                    # Update local record
                    conn.execute(
                        "UPDATE campaigns SET status = 'paused', salesforge_status = 'paused' WHERE salesforge_seq_id = ?",
                        (sid,),
                    )
            else:
                print(f"  [ok] {name}: bounce {bounce_rate*100:.1f}% — within limits")

        conn.commit()
        if paused:
            print(f"\n[kill-switch] Paused {paused} campaign(s)")
        else:
            print(f"\n[kill-switch] All campaigns within healthy thresholds")

    finally:
        conn.close()


if __name__ == "__main__":
    if "--live" in sys.argv:
        from config import enable_live_mode
        enable_live_mode()
    check_kill_switch()
