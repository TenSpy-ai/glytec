"""A/B test — set up multi-variant steps on a campaign.

Usage:
    python -m salesforge.ops.ab_test --campaign "Q1 CNO" --step 0 --split 50/50
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn
from config import DRY_RUN


def setup_ab_test(campaign_name, step_order=0, split="50/50",
                  subject_a=None, subject_b=None,
                  body_a=None, body_b=None, dry_run=True):
    """Set up A/B testing on a campaign step.

    Uses distributionStrategy: "custom" with split weights.
    PUT /steps replaces ALL steps — must include full step array.
    """
    client = SalesforgeClient(dry_run=dry_run)
    conn = get_conn()

    try:
        # Find sequence
        all_seqs = []
        offset = 0
        while True:
            data = client.list_sequences(limit=50, offset=offset)
            batch = data.get("data", [])
            all_seqs.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        matches = [s for s in all_seqs if campaign_name.lower() in s.get("name", "").lower()]
        if not matches:
            print(f"[ab-test] No sequence matching '{campaign_name}'")
            return
        seq = matches[0]
        sid = seq["id"]

        # Get current steps
        detail = client.get_sequence(sid)
        if not detail:
            print("[ab-test] Failed to fetch sequence detail")
            return

        current_steps = detail.get("steps", [])
        if step_order >= len(current_steps):
            print(f"[ab-test] Step {step_order} doesn't exist (only {len(current_steps)} steps)")
            return

        target_step = current_steps[step_order]
        current_variants = target_step.get("variants", [])

        # Parse split
        weights = [int(w) for w in split.split("/")]
        if sum(weights) != 100:
            print(f"[ab-test] Split must sum to 100 (got {sum(weights)})")
            return

        # Build new variants
        variant_a = current_variants[0] if current_variants else {}
        new_variants = [
            {
                "id": variant_a.get("id"),
                "order": 0,
                "label": "Variant A",
                "status": "active",
                "emailSubject": subject_a or variant_a.get("emailSubject", ""),
                "emailContent": body_a or variant_a.get("emailContent", ""),
                "distributionWeight": weights[0],
            },
            {
                "order": 1,
                "label": "Variant B",
                "status": "active",
                "emailSubject": subject_b or variant_a.get("emailSubject", ""),
                "emailContent": body_b or variant_a.get("emailContent", ""),
                "distributionWeight": weights[1],
            },
        ]

        target_step["distributionStrategy"] = "custom"
        target_step["variants"] = new_variants

        # Rebuild full steps array (PUT replaces ALL)
        steps_payload = []
        for s in current_steps:
            step_data = {
                "id": s.get("id"),
                "order": s.get("order"),
                "name": s.get("name"),
                "waitDays": s.get("waitDays", 0),
                "distributionStrategy": s.get("distributionStrategy", "equal"),
                "variants": s.get("variants", []),
            }
            steps_payload.append(step_data)

        print(f"\n  Campaign: {detail.get('name')}")
        print(f"  Step {step_order}: {target_step.get('name')}")
        print(f"  Split: {split}")
        print(f"  Variant A: \"{new_variants[0]['emailSubject'][:50]}\" ({weights[0]}%)")
        print(f"  Variant B: \"{new_variants[1]['emailSubject'][:50]}\" ({weights[1]}%)")
        print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")

        client.update_steps(sid, steps_payload)

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--step", type=int, default=0)
    parser.add_argument("--split", default="50/50")
    parser.add_argument("--subject-a")
    parser.add_argument("--subject-b")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    setup_ab_test(args.campaign, step_order=args.step, split=args.split,
                  subject_a=args.subject_a, subject_b=args.subject_b,
                  dry_run=not args.live)
