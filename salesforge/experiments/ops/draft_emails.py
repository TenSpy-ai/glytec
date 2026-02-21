"""Draft emails — create/list/preview drafts and manage templates.

Usage:
    python -m salesforge.ops.draft_emails list
    python -m salesforge.ops.draft_emails templates
    python -m salesforge.ops.draft_emails preview --campaign "Q1 CNO"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def list_drafts(campaign_name=None):
    """List draft email steps."""
    conn = get_conn()
    try:
        if campaign_name:
            steps = conn.execute(
                """SELECT cs.*, c.name as campaign_name FROM campaign_steps cs
                   JOIN campaigns c ON cs.campaign_id = c.id
                   WHERE c.name LIKE ?
                   ORDER BY cs.step_order""",
                (f"%{campaign_name}%",),
            ).fetchall()
        else:
            steps = conn.execute(
                """SELECT cs.*, c.name as campaign_name FROM campaign_steps cs
                   JOIN campaigns c ON cs.campaign_id = c.id
                   ORDER BY c.name, cs.step_order"""
            ).fetchall()

        if not steps:
            print("No draft email steps found.")
            return

        print(f"\n{'='*80}")
        print(f"  EMAIL DRAFTS — {len(steps)} steps")
        print(f"{'='*80}\n")

        for s in steps:
            print(f"  [{s['campaign_name']}] Step {s['step_order']}: {s['step_name'] or '-'}")
            print(f"    Subject: {s['email_subject'] or '-'}")
            print(f"    Variant: {s['variant_label']} ({s['distribution_weight']}%)")
            print(f"    Layers: {s['layer1_persona'] or '-'} / {s['layer2_ehr'] or '-'} / {s['layer3_financial'] or '-'}")
            if s['salesforge_step_id']:
                print(f"    Synced: {s['salesforge_step_id']}")
            print()

    finally:
        conn.close()


def list_templates():
    """List reusable email templates."""
    conn = get_conn()
    try:
        templates = conn.execute(
            "SELECT * FROM email_templates ORDER BY times_used DESC"
        ).fetchall()

        if not templates:
            print("No email templates found.")
            return

        print(f"\n{'='*80}")
        print(f"  EMAIL TEMPLATES — {len(templates)} templates")
        print(f"{'='*80}\n")

        for t in templates:
            print(f"  {t['name']} ({t['category'] or '-'})")
            print(f"    Persona: {t['persona'] or 'any'} | EHR: {t['ehr_segment'] or 'any'}")
            print(f"    Subject: {t['subject'] or '-'}")
            print(f"    Used: {t['times_used']}x | Open: {t['avg_open_rate'] or '-'}% | Reply: {t['avg_reply_rate'] or '-'}%")
            print()

    finally:
        conn.close()


def preview_draft(campaign_name):
    """Preview a draft email with sample merge fields."""
    conn = get_conn()
    try:
        step = conn.execute(
            """SELECT cs.* FROM campaign_steps cs
               JOIN campaigns c ON cs.campaign_id = c.id
               WHERE c.name LIKE ? ORDER BY cs.step_order LIMIT 1""",
            (f"%{campaign_name}%",),
        ).fetchone()

        if not step:
            print(f"No drafts found for '{campaign_name}'")
            return

        print(f"\n{'='*80}")
        print(f"  EMAIL PREVIEW")
        print(f"{'='*80}\n")

        print(f"  Subject: {step['email_subject']}")
        print(f"\n  --- Body ---")
        body = step["email_body_plain"] or step["email_body_html"] or "(empty)"
        print(f"  {body[:500]}")
        if len(body) > 500:
            print(f"  ... ({len(body)} chars total)")

    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "list":
        campaign = None
        for i, a in enumerate(args):
            if a == "--campaign" and i + 1 < len(args):
                campaign = args[i + 1]
        list_drafts(campaign)
    elif args[0] == "templates":
        list_templates()
    elif args[0] == "preview" and len(args) > 1:
        campaign = None
        for i, a in enumerate(args):
            if a == "--campaign" and i + 1 < len(args):
                campaign = args[i + 1]
        if campaign:
            preview_draft(campaign)
        else:
            preview_draft(" ".join(args[1:]))
    else:
        print("Usage: draft_emails.py [list|templates|preview] [--campaign name]")
