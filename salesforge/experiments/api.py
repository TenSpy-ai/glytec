"""SalesforgeClient — wraps all verified API endpoints with rules baked in.

Rules source: docs/salesforge/salesforge-api-rules.md (tested 2026-02-19)
Key constraints:
  - Auth: raw key in Authorization header, NO Bearer prefix
  - PATCH never works on any endpoint
  - Filters are broken on all list endpoints — filter client-side
  - jobTitle/phone don't persist — use customVars
  - PUT on steps/mailboxes replaces ALL — send full arrays
  - import-lead: linkedinUrl must be omitted or null (empty string → 400)
  - DELETE only works on sequences
  - language must be "american_english" not "en"
"""

import json
import datetime
import requests

try:
    from salesforge.config import (
        DRY_RUN, salesforge_headers, workspace_url, API_LOG_PATH, PRODUCT_ID,
        SALESFORGE_BASE_URL,
    )
    from salesforge.db import get_conn
except ImportError:
    from config import (
        DRY_RUN, salesforge_headers, workspace_url, API_LOG_PATH, PRODUCT_ID,
        SALESFORGE_BASE_URL,
    )
    from db import get_conn


class SalesforgeClient:
    """Centralized Salesforge API client with all verified rules encoded."""

    def __init__(self, dry_run=None):
        self.dry_run = dry_run if dry_run is not None else DRY_RUN
        self.headers = salesforge_headers()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(self, method, path, json_body=None, params=None, expect_204=False):
        """Make an API request with logging.

        Returns (response_data, status_code) or (None, status_code) for 204s.
        """
        url = workspace_url(path)
        resp = requests.request(method, url, headers=self.headers,
                                json=json_body, params=params)
        # Log the call
        self._log(path, method, json_body or params, resp.status_code,
                  resp.text[:200] if resp.text else "")

        if expect_204:
            return None, resp.status_code

        if resp.status_code in (200, 201):
            try:
                return resp.json(), resp.status_code
            except ValueError:
                return resp.text, resp.status_code
        return None, resp.status_code

    def _log(self, endpoint, method, params, status_code, summary):
        """Log API call to SQLite and markdown file."""
        try:
            conn = get_conn()
            conn.execute(
                """INSERT INTO api_log (endpoint, method, params, response_code, response_summary)
                   VALUES (?, ?, ?, ?, ?)""",
                (endpoint, method, json.dumps(params)[:500] if params else None,
                 status_code, summary[:500]),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass  # Don't let logging failures break API calls

        try:
            API_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(API_LOG_PATH, "a") as f:
                ts = datetime.datetime.now().isoformat()
                f.write(f"\n### {ts}\n")
                f.write(f"- **{method}** `{endpoint}`\n")
                if params:
                    f.write(f"- Params: `{json.dumps(params)[:200]}`\n")
                f.write(f"- Response: {status_code} — {summary[:150]}\n")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------------

    def list_sequences(self, limit=50, offset=0):
        """GET /sequences — list all sequences (filters broken, filter client-side)."""
        data, status = self._request("GET", "sequences",
                                     params={"limit": limit, "offset": offset})
        return data if data else {"data": [], "total": 0}

    def get_sequence(self, seq_id):
        """GET /sequences/{id} — full detail including steps and mailboxes."""
        data, status = self._request("GET", f"sequences/{seq_id}")
        return data

    def create_sequence(self, name):
        """POST /sequences — creates draft with one empty step.

        Auto-fills productId, language="american_english", timezone.
        Returns full sequence object with id, steps[0].id, steps[0].variants[0].id.
        """
        if self.dry_run:
            print(f"  [dry-run] Would create sequence: {name}")
            return {"id": f"dry_run_{name}", "steps": [{"id": "dry_step", "variants": [{"id": "dry_variant"}]}]}

        payload = {
            "name": name,
            "productId": PRODUCT_ID,
            "language": "american_english",
            "timezone": "America/New_York",
        }
        data, status = self._request("POST", "sequences", json_body=payload)
        if data and data.get("id"):
            print(f"  [live] Created sequence: {name} → {data['id']} (HTTP {status})")
        else:
            print(f"  [live] Failed to create sequence: HTTP {status}")
        return data

    def update_sequence(self, seq_id, **kwargs):
        """PUT /sequences/{id} — update name, tracking settings.

        WARNING: language, timezone, productId changes are ignored/crash.
        Steps and mailboxes are silently ignored — use dedicated endpoints.
        """
        safe_fields = {"name", "openTrackingEnabled", "clickTrackingEnabled"}
        payload = {k: v for k, v in kwargs.items() if k in safe_fields}
        if not payload:
            print("  [warn] No updatable fields provided")
            return None
        if self.dry_run:
            print(f"  [dry-run] Would update sequence {seq_id}: {payload}")
            return payload
        data, status = self._request("PUT", f"sequences/{seq_id}", json_body=payload)
        return data

    def delete_sequence(self, seq_id):
        """DELETE /sequences/{id} — permanently deletes (204). Only DELETE that works."""
        if self.dry_run:
            print(f"  [dry-run] Would delete sequence {seq_id}")
            return True
        _, status = self._request("DELETE", f"sequences/{seq_id}", expect_204=True)
        success = status == 204
        if success:
            print(f"  [live] Deleted sequence {seq_id}")
        else:
            print(f"  [live] Failed to delete sequence {seq_id}: HTTP {status}")
        return success

    def set_status(self, seq_id, status):
        """PUT /sequences/{id}/status — activate or pause.

        Only "active" and "paused" are valid. Cannot go back to draft.
        Activating requires mailboxes assigned.
        """
        if status not in ("active", "paused"):
            print(f"  [error] Invalid status '{status}' — must be 'active' or 'paused'")
            return False
        if self.dry_run:
            print(f"  [dry-run] Would set sequence {seq_id} to {status}")
            return True
        _, code = self._request("PUT", f"sequences/{seq_id}/status",
                                json_body={"status": status}, expect_204=True)
        success = code == 204
        if success:
            print(f"  [live] Set sequence {seq_id} to {status}")
        else:
            print(f"  [live] Failed to set status: HTTP {code}")
        return success

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def update_steps(self, seq_id, steps):
        """PUT /sequences/{id}/steps — replaces ALL steps. Min 1 step required.

        Each step needs: order, name, waitDays, distributionStrategy, variants[].
        Each variant needs: label, status, distributionWeight, emailSubject, emailContent.
        """
        if not steps:
            print("  [error] At least 1 step required")
            return False
        if self.dry_run:
            print(f"  [dry-run] Would update {len(steps)} steps on {seq_id}")
            return True
        _, code = self._request("PUT", f"sequences/{seq_id}/steps",
                                json_body={"steps": steps}, expect_204=True)
        success = code in (200, 204)
        if success:
            print(f"  [live] Updated {len(steps)} steps on {seq_id}")
        else:
            print(f"  [live] Failed to update steps: HTTP {code}")
        return success

    # ------------------------------------------------------------------
    # Mailboxes
    # ------------------------------------------------------------------

    def list_mailboxes(self, limit=100, offset=0):
        """GET /mailboxes — read-only list. No create/update/delete via API."""
        data, status = self._request("GET", "mailboxes",
                                     params={"limit": limit, "offset": offset})
        return data if data else {"data": [], "total": 0}

    def get_mailbox(self, mailbox_id):
        """GET /mailboxes/{id} — single mailbox detail."""
        data, status = self._request("GET", f"mailboxes/{mailbox_id}")
        return data

    def assign_mailboxes(self, seq_id, mailbox_ids):
        """PUT /sequences/{id}/mailboxes — full replacement (PUT not POST!).

        Empty array clears all. Invalid ID → 500.
        """
        if self.dry_run:
            print(f"  [dry-run] Would assign {len(mailbox_ids)} mailboxes to {seq_id}")
            return True
        _, code = self._request("PUT", f"sequences/{seq_id}/mailboxes",
                                json_body={"mailboxIds": mailbox_ids}, expect_204=True)
        success = code == 204
        if success:
            print(f"  [live] Assigned {len(mailbox_ids)} mailboxes to {seq_id}")
        else:
            print(f"  [live] Failed to assign mailboxes: HTTP {code}")
        return success

    def get_all_mailbox_ids(self):
        """Fetch all mailbox IDs from the workspace."""
        data = self.list_mailboxes(limit=100)
        mailboxes = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(mailboxes, list):
            return [m["id"] for m in mailboxes if m.get("id")]
        return []

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    def list_contacts(self, limit=50, offset=0):
        """GET /contacts — list all (filters broken, filter client-side)."""
        data, status = self._request("GET", "contacts",
                                     params={"limit": limit, "offset": offset})
        return data if data else {"data": [], "total": 0}

    def get_contact(self, contact_id):
        """GET /contacts/{id} — same 8 fields as list."""
        data, status = self._request("GET", f"contacts/{contact_id}")
        return data

    def create_contact(self, first_name, last_name, email, company="",
                       linkedin_url=None, tags=None, custom_vars=None):
        """POST /contacts — create single contact.

        Duplicate email returns same lead ID (upsert on name/company).
        jobTitle/phone don't persist — pass via custom_vars.
        """
        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "company": company,
        }
        if linkedin_url:
            payload["linkedinUrl"] = linkedin_url
        if tags:
            payload["tags"] = tags
        if custom_vars:
            payload["customVars"] = custom_vars

        if self.dry_run:
            print(f"  [dry-run] Would create contact: {email}")
            return {"id": f"dry_run_{email}"}
        data, status = self._request("POST", "contacts", json_body=payload)
        return data

    def create_contacts_bulk(self, contacts):
        """POST /contacts/bulk — each contact requires tags array."""
        if self.dry_run:
            print(f"  [dry-run] Would bulk create {len(contacts)} contacts")
            return {"created": len(contacts)}
        data, status = self._request("POST", "contacts/bulk",
                                     json_body={"contacts": contacts})
        return data

    def import_lead(self, seq_id, first_name, last_name, email, company,
                    linkedin_url=None, tags=None, custom_vars=None):
        """PUT /sequences/{id}/import-lead — create + enroll in one call.

        linkedinUrl: omit or null OK, empty string → 400.
        One contact per call (not bulk).
        """
        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "company": company,
        }
        # linkedinUrl: include only if truthy (omit entirely if None/empty)
        if linkedin_url:
            payload["linkedinUrl"] = linkedin_url
        if tags:
            payload["tags"] = tags
        if custom_vars:
            payload["customVars"] = custom_vars

        if self.dry_run:
            print(f"  [dry-run] Would import lead: {email} → seq {seq_id}")
            return True
        _, code = self._request("PUT", f"sequences/{seq_id}/import-lead",
                                json_body=payload, expect_204=True)
        return code == 204

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_analytics(self, seq_id, from_date, to_date):
        """GET /sequences/{id}/analytics — daily breakdown.

        Requires from_date and to_date (YYYY-MM-DD format).
        """
        data, status = self._request("GET", f"sequences/{seq_id}/analytics",
                                     params={"from_date": from_date, "to_date": to_date})
        return data

    def get_sequence_metrics(self, product_id=None, sequence_ids=None):
        """GET /sequence-metrics — workspace aggregates.

        Optional filters: product_id, sequence_ids (list).
        """
        params = {}
        if product_id:
            params["product_id"] = product_id
        if sequence_ids:
            for sid in sequence_ids:
                params.setdefault("sequence_ids[]", []).append(sid)

        # Build URL without workspace scope for this endpoint
        url = f"{SALESFORGE_BASE_URL}/workspaces/{__import__('salesforge.config', fromlist=['WORKSPACE_ID']).WORKSPACE_ID}/sequence-metrics"
        data, status = self._request("GET", "sequence-metrics", params=params)
        return data

    # ------------------------------------------------------------------
    # Threads
    # ------------------------------------------------------------------

    def list_threads(self, limit=50, offset=0):
        """GET /threads — list-only (no detail, no reply, no mark-read)."""
        data, status = self._request("GET", "threads",
                                     params={"limit": limit, "offset": offset})
        return data if data else {"data": [], "total": 0}

    # ------------------------------------------------------------------
    # DNC
    # ------------------------------------------------------------------

    def add_to_dnc(self, emails):
        """POST /dnc/bulk — write-only. Cannot list or remove.

        Body: {"dncs": ["email1", "email2"]} — array of strings, not objects.
        """
        if not emails:
            return {"created": 0}
        if self.dry_run:
            print(f"  [dry-run] Would add {len(emails)} emails to DNC")
            return {"created": len(emails)}
        data, status = self._request("POST", "dnc/bulk",
                                     json_body={"dncs": emails})
        return data

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def list_webhooks(self, limit=50, offset=0):
        """GET /integrations/webhooks — create + read only."""
        data, status = self._request("GET", "integrations/webhooks",
                                     params={"limit": limit, "offset": offset})
        return data if data else {"data": [], "total": 0}

    def create_webhook(self, name, event_type, url):
        """POST /integrations/webhooks — cannot update or delete after creation.

        Valid types: email_sent, email_opened, link_clicked, email_replied,
        linkedin_replied, contact_unsubscribed, email_bounced,
        positive_reply, negative_reply, label_changed.
        """
        if self.dry_run:
            print(f"  [dry-run] Would create webhook: {name} ({event_type})")
            return {"id": f"dry_run_webhook"}
        data, status = self._request("POST", "integrations/webhooks",
                                     json_body={"name": name, "type": event_type, "url": url})
        return data
