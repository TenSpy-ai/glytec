"""Step 6 — Push to Salesforge: create sequences, populate steps, enroll contacts.

Verified API patterns (from testing 2026-02-19):
  - POST /sequences                     → create sequence (draft, one empty step)
      Requires: name, productId, language ("american_english", NOT "en"), timezone
  - PUT  /sequences/{id}/steps          → populate email subject + content
      Requires: distributionStrategy, label, status on each variant. Replaces ALL steps.
  - PUT  /sequences/{id}/mailboxes      → assign mailboxes: {"mailboxIds": ["mbox_..."]}
      Must be PUT (POST → 404). Empty array clears all. Invalid ID → 500.
  - PUT  /sequences/{id}/import-lead    → create + enroll in one call
      Required: firstName, lastName, email, company
      Optional: linkedinUrl (omit or null OK; empty string "" → 400), tags, customVars
      jobTitle accepted but does NOT persist — use customVars instead
  - PUT  /sequences/{id}/contacts       → enroll existing contacts: {"contactIds": ["lead_..."]}
  - PUT  /sequences/{id}/status         → activate/pause: {"status": "active"|"paused"}
  - POST /contacts                      → create single contact (returns lead_id)
  - POST /contacts/bulk                 → create multiple (requires tags on each)

Contact model has only 8 fields: id, firstName, lastName, email, company, linkedinUrl, tags, customVars.
List endpoint filters (status, tags) are broken — always filter client-side.
"""

import json
import datetime
import requests
from db import get_conn
from config import (
    DRY_RUN,
    salesforge_headers,
    workspace_url,
    API_LOG_PATH,
    PRODUCT_ID,
)


def _log_api_call(conn, endpoint, method, params, response_code, response_summary):
    """Log API call to both SQLite and markdown file."""
    conn.execute(
        """INSERT INTO api_log (endpoint, method, params, response_code, response_summary)
           VALUES (?, ?, ?, ?, ?)""",
        (endpoint, method, json.dumps(params) if params else None, response_code, response_summary),
    )
    conn.commit()
    with open(API_LOG_PATH, "a") as f:
        ts = datetime.datetime.now().isoformat()
        f.write(f"\n### {ts}\n")
        f.write(f"- **{method}** `{endpoint}`\n")
        if params:
            f.write(f"- Params: `{json.dumps(params)[:200]}`\n")
        f.write(f"- Response: {response_code} — {response_summary}\n")


# ---------------------------------------------------------------------------
# Sequence lifecycle
# ---------------------------------------------------------------------------

def _create_sequence(conn, name, dry_run=True):
    """Create a Salesforge sequence (draft status with one empty step)."""
    endpoint = workspace_url("sequences")
    payload = {"name": name, "productId": PRODUCT_ID, "language": "american_english", "timezone": "America/New_York"}

    if dry_run:
        _log_api_call(conn, endpoint, "POST", payload, 0, f"DRY RUN — would create sequence '{name}'")
        print(f"  [dry-run] Would create sequence: {name}")
        return None

    resp = requests.post(endpoint, headers=salesforge_headers(), json=payload)
    data = resp.json() if resp.status_code in (200, 201) else {}
    seq_id = data.get("id")
    step_id = None
    variant_id = None
    steps = data.get("steps", [])
    if steps:
        step_id = steps[0].get("id")
        variants = steps[0].get("variants", [])
        if variants:
            variant_id = variants[0].get("id")

    _log_api_call(conn, endpoint, "POST", payload, resp.status_code,
                  f"Created sequence {seq_id}" if seq_id else resp.text[:150])
    print(f"  [live] Created sequence: {name} → {seq_id} (HTTP {resp.status_code})")
    return {"seq_id": seq_id, "step_id": step_id, "variant_id": variant_id}


def _update_steps(conn, seq_id, step_id, variant_id, messages, dry_run=True):
    """Populate email step content via PUT /sequences/{id}/steps.

    Requires: distributionStrategy, label, status on each variant.
    """
    endpoint = workspace_url(f"sequences/{seq_id}/steps")

    # Use the first message for the initial email step
    msg = messages[0] if messages else None
    subject = msg["subject"] if msg else ""
    # Convert plain text body to HTML paragraphs
    body_html = ""
    if msg:
        paragraphs = msg["body"].split("\n\n")
        body_html = "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

    payload = {
        "steps": [{
            "id": step_id,
            "order": 0,
            "name": "Initial email",
            "waitDays": 0,
            "distributionStrategy": "equal",
            "variants": [{
                "id": variant_id,
                "order": 0,
                "label": "Initial email",
                "status": "active",
                "emailSubject": subject,
                "emailContent": body_html,
                "distributionWeight": 100,
            }],
        }],
    }

    if dry_run:
        _log_api_call(conn, endpoint, "PUT", {"subject": subject[:60], "content_len": len(body_html)},
                      0, f"DRY RUN — would set email subject/content")
        print(f"  [dry-run] Would set email: \"{subject[:50]}...\"")
        return

    resp = requests.put(endpoint, headers=salesforge_headers(), json=payload)
    _log_api_call(conn, endpoint, "PUT", {"subject": subject[:60]},
                  resp.status_code, f"Updated steps: {resp.text[:100]}")
    print(f"  [live] Updated email content (HTTP {resp.status_code})")


def _assign_mailboxes(conn, seq_id, dry_run=True):
    """Assign all workspace mailboxes via PUT /sequences/{id}/mailboxes.

    Body: {"mailboxIds": ["mbox_...", ...]}
    """
    endpoint = workspace_url(f"sequences/{seq_id}/mailboxes")

    if dry_run:
        _log_api_call(conn, endpoint, "PUT", {"action": "assign all workspace mailboxes"},
                      0, "DRY RUN — would assign mailboxes")
        print(f"  [dry-run] Would assign mailboxes")
        return

    # Fetch all mailbox IDs
    mb_resp = requests.get(workspace_url("mailboxes"), headers=salesforge_headers(),
                           params={"limit": 100})
    if mb_resp.status_code != 200:
        print(f"  [live] Failed to fetch mailboxes: HTTP {mb_resp.status_code}")
        return

    mb_data = mb_resp.json()
    mailboxes = mb_data.get("data", mb_data) if isinstance(mb_data, dict) else mb_data
    mailbox_ids = [m["id"] for m in mailboxes if m.get("id")]

    resp = requests.put(endpoint, headers=salesforge_headers(),
                        json={"mailboxIds": mailbox_ids})
    _log_api_call(conn, endpoint, "PUT", {"mailboxIds_count": len(mailbox_ids)},
                  resp.status_code, f"Assigned {len(mailbox_ids)} mailboxes")
    print(f"  [live] Assigned {len(mailbox_ids)} mailboxes (HTTP {resp.status_code})")


def _enroll_contacts(conn, seq_id, contacts, dry_run=True):
    """Enroll contacts into a sequence via import-lead.

    import-lead creates + enrolls in one call. linkedinUrl is optional (omit or null OK;
    empty string "" → 400). All contacts go through import-lead — no need to split by
    LinkedIn presence. Supports customVars and tags for passing dynamic data.
    """
    endpoint_import = workspace_url(f"sequences/{seq_id}/import-lead")

    if dry_run:
        _log_api_call(conn, endpoint_import, "PUT", {"count": len(contacts)},
                      0, f"DRY RUN — would enroll {len(contacts)} contacts")
        print(f"  [dry-run] Would enroll {len(contacts)} contacts")
        return

    enrolled = 0
    for c in contacts:
        payload = {
            "firstName": c["first_name"],
            "lastName": c["last_name"],
            "email": c["email"],
            "company": c["company"] or c["account_name"],
            "customVars": {},
        }

        # linkedinUrl: include only if we have one (omit field entirely if not)
        if c["linkedin_url"]:
            payload["linkedinUrl"] = c["linkedin_url"]

        # Pass title and ICP data via customVars (jobTitle doesn't persist on the model)
        if c["title"]:
            payload["customVars"]["job_title"] = c["title"]
        if c.get("icp_category"):
            payload["customVars"]["icp_category"] = c["icp_category"]
        if c.get("icp_function_type"):
            payload["customVars"]["function_type"] = c["icp_function_type"]

        resp = requests.put(endpoint_import, headers=salesforge_headers(), json=payload)
        _log_api_call(conn, endpoint_import, "PUT", {"email": c["email"]},
                      resp.status_code, f"Imported {c['email']}")
        if resp.status_code == 204:
            enrolled += 1

    print(f"  [live] Enrolled {enrolled}/{len(contacts)} contacts via import-lead")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    """Execute step 6."""
    print("\n=== Step 6: Push to Salesforge ===")
    dry_run = DRY_RUN
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"[step6] Mode: {mode}")

    with open(API_LOG_PATH, "a") as f:
        f.write(f"\n\n## Step 6 — Push to Salesforge ({mode})\n")
        f.write(f"Run at: {datetime.datetime.now().isoformat()}\n")

    conn = get_conn()
    try:
        # Get contacts with their composed messages, grouped by tier+segment
        contacts = conn.execute(
            """SELECT c.*, a.system_name as acct_name, a.tier, a.segment
               FROM contacts c
               JOIN accounts a ON c.account_name = a.system_name
               WHERE c.golden_record = 1
               AND c.suppressed = 0
               AND c.icp_matched = 1
               AND a.tier IN ('Priority', 'Active')
               ORDER BY a.tier, a.segment"""
        ).fetchall()

        if not contacts:
            print("[step6] No eligible contacts to push")
            return

        # Group contacts by tier+segment → one sequence per group
        groups = {}
        for c in contacts:
            key = f"{c['tier']}_{(c['segment'] or 'General').replace('/', '_')}"
            groups.setdefault(key, []).append(c)

        print(f"[step6] Creating {len(groups)} sequences for {len(contacts)} contacts...")
        sequences_created = 0

        for group_key, group_contacts in groups.items():
            seq_name = f"Glucommander_Q1_2026_{group_key}"
            print(f"\n  Sequence: {seq_name} ({len(group_contacts)} contacts)")

            # Get composed messages for these contacts
            contact_ids = [c["id"] for c in group_contacts]
            placeholders = ",".join("?" * len(contact_ids))
            messages = conn.execute(
                f"SELECT * FROM messages WHERE contact_id IN ({placeholders})",
                contact_ids,
            ).fetchall()

            # 1. Create sequence
            result = _create_sequence(conn, seq_name, dry_run=dry_run)

            if not dry_run and result and result["seq_id"]:
                seq_id = result["seq_id"]
                # 2. Populate email step content
                _update_steps(conn, seq_id, result["step_id"], result["variant_id"],
                              messages, dry_run=dry_run)
                # 3. Assign mailboxes
                _assign_mailboxes(conn, seq_id, dry_run=dry_run)
                # 4. Enroll contacts
                _enroll_contacts(conn, seq_id, group_contacts, dry_run=dry_run)
            elif dry_run:
                _update_steps(conn, "dry_run", "dry_run", "dry_run", messages, dry_run=True)
                _assign_mailboxes(conn, "dry_run", dry_run=True)
                _enroll_contacts(conn, "dry_run", group_contacts, dry_run=True)

            # Track in sequences table
            sf_id = result["seq_id"] if (result and not dry_run) else f"dry_run_{seq_name}"
            conn.execute(
                """INSERT INTO sequences (name, salesforge_id, status, account_segment, contact_count)
                   VALUES (?, ?, ?, ?, ?)""",
                (seq_name, str(sf_id), "draft" if dry_run else "created", group_key, len(group_contacts)),
            )
            sequences_created += 1

        conn.commit()
        print(f"\n[step6] Done — {sequences_created} sequences {'planned' if dry_run else 'created'}, "
              f"{len(contacts)} contacts {'queued' if dry_run else 'enrolled'}")
        if not dry_run:
            print(f"  Note: Sequences created in DRAFT status. Use PUT /status to activate.")

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    if "--live" in sys.argv:
        from config import enable_live_mode
        enable_live_mode()
    run()
