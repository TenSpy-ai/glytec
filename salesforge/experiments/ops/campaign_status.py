"""Campaign overview — lists all sequences with inline stats.

Usage:
    python -m salesforge.ops.campaign_status                  # all campaigns
    python -m salesforge.ops.campaign_status active            # active only
    python -m salesforge.ops.campaign_status detail <name>     # detailed view
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def list_campaigns(status_filter=None):
    """Pull sequences from Salesforge and display with local campaign data."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        # Pull all sequences from API
        all_seqs = []
        offset = 0
        while True:
            data = client.list_sequences(limit=50, offset=offset)
            batch = data.get("data", [])
            all_seqs.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        if status_filter:
            all_seqs = [s for s in all_seqs if s.get("status", "").lower() == status_filter.lower()]

        if not all_seqs:
            print(f"No {'matching ' if status_filter else ''}sequences found.")
            return

        print(f"\n{'='*80}")
        print(f"  CAMPAIGN OVERVIEW — {len(all_seqs)} sequences")
        print(f"{'='*80}\n")

        for seq in all_seqs:
            sid = seq.get("id", "?")
            name = seq.get("name", "Unnamed")
            status = seq.get("status", "?")
            leads = seq.get("leadCount", 0)
            contacted = seq.get("contactedCount", 0)
            opened_pct = seq.get("openedPercent", 0)
            replied_pct = seq.get("repliedPercent", 0)
            bounced_pct = seq.get("bouncedPercent", 0)

            status_icon = {"active": "+", "paused": "~", "draft": "-", "completed": "*"}.get(status, "?")

            print(f"  [{status_icon}] {name}")
            print(f"      Status: {status} | Leads: {leads} | Contacted: {contacted}")
            print(f"      Open: {opened_pct:.1f}% | Reply: {replied_pct:.1f}% | Bounce: {bounced_pct:.1f}%")

            # Check local campaign record
            local = conn.execute(
                "SELECT * FROM campaigns WHERE salesforge_seq_id = ?", (sid,)
            ).fetchone()
            if local:
                print(f"      Local: {local['status']} | Target: {local['target_segment'] or '-'} / {local['target_ehr'] or '-'}")
            print()

    finally:
        conn.close()


def detail_campaign(name_query):
    """Show detailed view of a single campaign."""
    client = SalesforgeClient(dry_run=False)
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
            print(f"No sequence matching '{name_query}' found.")
            return

        seq = matches[0]
        detail = client.get_sequence(seq["id"])
        if not detail:
            print(f"Failed to fetch detail for {seq['id']}")
            return

        print(f"\n{'='*80}")
        print(f"  CAMPAIGN DETAIL: {detail.get('name', '?')}")
        print(f"{'='*80}\n")

        print(f"  ID:         {detail.get('id')}")
        print(f"  Status:     {detail.get('status')}")
        print(f"  Leads:      {detail.get('leadCount', 0)}")
        print(f"  Contacted:  {detail.get('contactedCount', 0)}")
        print(f"  Opened:     {detail.get('openedCount', 0)} ({detail.get('openedPercent', 0):.1f}%)")
        print(f"  Replied:    {detail.get('repliedCount', 0)} ({detail.get('repliedPercent', 0):.1f}%)")
        print(f"  Bounced:    {detail.get('bouncedCount', 0)} ({detail.get('bouncedPercent', 0):.1f}%)")
        print(f"  Clicked:    {detail.get('clickedCount', 0)} ({detail.get('clickedPercent', 0):.1f}%)")
        print(f"  Completed:  {detail.get('completedCount', 0)}")

        steps = detail.get("steps", [])
        print(f"\n  Steps ({len(steps)}):")
        for step in steps:
            print(f"    Step {step.get('order', '?')}: {step.get('name', '?')} (wait {step.get('waitDays', 0)}d)")
            for v in step.get("variants", []):
                print(f"      [{v.get('status', '?')}] {v.get('label', '?')} — \"{v.get('emailSubject', '?')[:50]}\"")

        mailboxes = detail.get("mailboxes", [])
        print(f"\n  Mailboxes ({len(mailboxes)}):")
        for mb in mailboxes[:5]:
            print(f"    {mb.get('address', '?')} ({mb.get('status', '?')})")
        if len(mailboxes) > 5:
            print(f"    ... and {len(mailboxes) - 5} more")

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "detail" and len(args) > 1:
        detail_campaign(" ".join(args[1:]))
    elif args and args[0] in ("active", "paused", "draft", "completed"):
        list_campaigns(args[0])
    else:
        list_campaigns()
