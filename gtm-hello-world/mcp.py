"""
GTM Hello World — Instantly MCP Protocol Client (PRIMARY)
Calls the 38 Instantly MCP tools over Streamable HTTP using JSON-RPC 2.0.

Usage:
    from mcp import InstantlyMCP
    client = InstantlyMCP()               # uses config defaults
    client = InstantlyMCP(dry_run=False)   # override dry-run

Dry-run behavior:
    - Read operations (list_*, get_*, count_*) always execute against live API
    - Write operations (create_*, update_*, delete_*, activate_*, pause_*) return
      mock data with dry_run_ prefix IDs when dry_run=True

Logging:
    Every _call_tool invocation is logged to the api_log table with interface="mcp".
"""

import json
import time
import urllib.request
import urllib.error

from config import INSTANTLY_API_KEY, INSTANTLY_MCP_URL_TEMPLATE, DRY_RUN
from db import get_conn, log_api_call


class InstantlyMCP:
    """MCP protocol client for Instantly.ai (38 tools over Streamable HTTP)."""

    def __init__(self, api_key=None, dry_run=None):
        self.api_key = api_key or INSTANTLY_API_KEY
        self.mcp_url = INSTANTLY_MCP_URL_TEMPLATE.format(api_key=self.api_key)
        self.dry_run = dry_run if dry_run is not None else DRY_RUN
        self._request_id = 0
        self._session_id = None
        self._initialized = False

    # ------------------------------------------------------------------
    # Protocol internals
    # ------------------------------------------------------------------

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _send_jsonrpc(self, method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC 2.0 request to the MCP server.

        Returns the result dict on success, raises on error.
        """
        body = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._next_id(),
        }
        if params is not None:
            body["params"] = params

        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        req = urllib.request.Request(
            self.mcp_url, data=data, headers=headers, method="POST",
        )

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                # Capture session ID from response headers
                session_id = resp.headers.get("Mcp-Session-Id")
                if session_id:
                    self._session_id = session_id

                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read().decode("utf-8")
                duration_ms = int((time.time() - start) * 1000)

                if "text/event-stream" in content_type:
                    # Parse SSE — extract the last data line that contains JSON
                    return self._parse_sse(raw), duration_ms
                else:
                    result = json.loads(raw)
                    return result, duration_ms

        except urllib.error.HTTPError as e:
            duration_ms = int((time.time() - start) * 1000)
            error_body = e.read().decode("utf-8")
            raise MCPError(e.code, error_body, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            raise MCPError(0, str(e), duration_ms)

    def _parse_sse(self, raw: str) -> dict:
        """Parse SSE response, return the JSON-RPC result from the last data line."""
        last_data = None
        for line in raw.split("\n"):
            if line.startswith("data: "):
                last_data = line[6:]
        if last_data:
            return json.loads(last_data)
        return {}

    def _ensure_initialized(self) -> None:
        """Perform MCP initialize handshake if not yet done."""
        if self._initialized:
            return

        result, _ = self._send_jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "gtm-hello-world", "version": "1.0"},
        })

        # Send initialized notification (no id, no response expected)
        try:
            body = json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            if self._session_id:
                headers["Mcp-Session-Id"] = self._session_id
            req = urllib.request.Request(
                self.mcp_url, data=body, headers=headers, method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass  # Notification failures are non-fatal

        self._initialized = True

    def _call_tool(self, tool_name: str, arguments: dict | None = None) -> dict:
        """Call an MCP tool and return the result.

        Handles initialization, logging, and error extraction.
        """
        self._ensure_initialized()

        params = {"name": tool_name}
        if arguments:
            # Instantly MCP tools expect arguments nested under a "params" key
            if "params" not in arguments:
                params["arguments"] = {"params": arguments}
            else:
                params["arguments"] = arguments

        start = time.time()
        try:
            response, duration_ms = self._send_jsonrpc("tools/call", params)
        except MCPError as e:
            # Log the failure
            try:
                conn = get_conn()
                log_api_call(conn, "mcp", tool_name, "CALL",
                             arguments, e.code, f"ERROR: {e.message[:200]}",
                             e.duration_ms)
                conn.close()
            except Exception:
                pass
            raise

        # Extract content from MCP response
        result_data = response.get("result", response)
        content = result_data.get("content", [])

        # MCP tool results come as content blocks — extract text
        extracted = self._extract_content(content) if content else result_data

        # Log success
        duration_ms_total = int((time.time() - start) * 1000)
        try:
            conn = get_conn()
            summary = json.dumps(extracted)[:200] if extracted else "empty"
            log_api_call(conn, "mcp", tool_name, "CALL",
                         arguments, 200, summary, duration_ms_total)
            conn.close()
        except Exception:
            pass

        return extracted

    def _extract_content(self, content: list) -> dict | list | str:
        """Extract usable data from MCP content blocks.

        MCP returns content as [{type: "text", text: "..."}, ...].
        The text is usually JSON.
        """
        if not content:
            return {}

        # Try to parse the first text block as JSON
        for block in content:
            if block.get("type") == "text":
                text = block["text"]
                try:
                    return json.loads(text)
                except (json.JSONDecodeError, TypeError):
                    return text

        return content

    # ------------------------------------------------------------------
    # Accounts (6 tools)
    # ------------------------------------------------------------------

    def list_accounts(self, search=None, status=None, limit=100,
                      starting_after=None) -> dict:
        """List sending accounts (cursor-paginated)."""
        args = {"limit": limit}
        if search:
            args["search"] = search
        if status is not None:
            args["status"] = status
        if starting_after:
            args["starting_after"] = starting_after
        return self._call_tool("list_accounts", args)

    def get_account(self, email: str) -> dict:
        """Get a single sending account by email."""
        return self._call_tool("get_account", {"email": email})

    def create_account(self, email: str, first_name: str, last_name: str,
                       provider_code: int, imap_host: str, imap_port: int,
                       imap_username: str, imap_password: str,
                       smtp_host: str, smtp_port: int,
                       smtp_username: str, smtp_password: str,
                       **kwargs) -> dict:
        """Create a new IMAP/SMTP sending account."""
        if self.dry_run:
            print(f"  [dry-run] Would create account: {email}")
            return {"email": email, "id": f"dry_run_{email}"}
        args = {
            "email": email, "first_name": first_name, "last_name": last_name,
            "provider_code": provider_code,
            "imap_host": imap_host, "imap_port": imap_port,
            "imap_username": imap_username, "imap_password": imap_password,
            "smtp_host": smtp_host, "smtp_port": smtp_port,
            "smtp_username": smtp_username, "smtp_password": smtp_password,
            **kwargs,
        }
        return self._call_tool("create_account", args)

    def update_account(self, email: str, **kwargs) -> dict:
        """Update account settings (warmup, daily_limit, sending_gap, etc.)."""
        if self.dry_run:
            print(f"  [dry-run] Would update account: {email} → {kwargs}")
            return {"email": email, **kwargs}
        return self._call_tool("update_account", {"email": email, **kwargs})

    def manage_account_state(self, email: str, action: str) -> dict:
        """Manage account state: pause, resume, enable_warmup, disable_warmup, test_vitals."""
        valid = {"pause", "resume", "enable_warmup", "disable_warmup", "test_vitals"}
        if action not in valid:
            raise ValueError(f"Invalid action '{action}' — must be one of {valid}")
        if self.dry_run and action != "test_vitals":
            print(f"  [dry-run] Would {action} account: {email}")
            return {"email": email, "action": action, "status": "dry_run"}
        return self._call_tool("manage_account_state",
                               {"email": email, "action": action})

    def delete_account(self, email: str) -> bool:
        """Permanently delete a sending account."""
        if self.dry_run:
            print(f"  [dry-run] Would delete account: {email}")
            return True
        result = self._call_tool("delete_account", {"email": email})
        return bool(result)

    # ------------------------------------------------------------------
    # Campaigns (8 tools)
    # ------------------------------------------------------------------

    def create_campaign(self, name: str, subject: str = "",
                        body: str = "",
                        campaign_schedule: dict | None = None,
                        sequences: list | None = None,
                        email_list: list | None = None,
                        **kwargs) -> dict:
        """Create a new campaign.

        MCP tool requires: name, subject, body.
        Optional: email_list, timing_from, timing_to, timezone, daily_limit,
                  email_gap, stop_on_reply, etc.

        Legacy params (campaign_schedule, sequences) are translated to the
        actual MCP schema for backward compatibility.
        """
        if self.dry_run:
            print(f"  [dry-run] Would create campaign: {name}")
            return {"id": f"dry_run_{name}", "name": name}

        args = {"name": name, **kwargs}

        # Direct subject/body (preferred)
        if subject:
            args["subject"] = subject
        if body:
            args["body"] = body

        # Legacy: extract subject/body from sequences if not provided directly
        if sequences and "subject" not in args:
            steps = sequences[0].get("steps", []) if sequences else []
            if steps:
                step = steps[0]
                variants = step.get("variants", [])
                src = variants[0] if variants else step
                args.setdefault("subject", src.get("subject", ""))
                args.setdefault("body", src.get("body", ""))

        # Legacy: extract timing from campaign_schedule
        if campaign_schedule:
            scheds = campaign_schedule.get("schedules", [])
            if scheds:
                timing = scheds[0].get("timing", {})
                if timing.get("from"):
                    args.setdefault("timing_from", timing["from"])
                if timing.get("to"):
                    args.setdefault("timing_to", timing["to"])
                tz = scheds[0].get("timezone")
                if tz:
                    args.setdefault("timezone", tz)

        if email_list:
            args["email_list"] = email_list

        return self._call_tool("create_campaign", args)

    def list_campaigns(self, search=None, limit=100,
                       starting_after=None) -> dict:
        """List campaigns (cursor-paginated)."""
        args = {"limit": limit}
        if search:
            args["search"] = search
        if starting_after:
            args["starting_after"] = starting_after
        return self._call_tool("list_campaigns", args)

    def get_campaign(self, campaign_id: str) -> dict:
        """Get full campaign details."""
        return self._call_tool("get_campaign", {"campaign_id": campaign_id})

    def update_campaign(self, campaign_id: str, **kwargs) -> dict:
        """Update campaign settings, sequences, or sender accounts.

        WARNING: custom_variables update REPLACES entire object — merge first.
        """
        if self.dry_run:
            print(f"  [dry-run] Would update campaign {campaign_id}: {list(kwargs.keys())}")
            return {"id": campaign_id, **kwargs}
        return self._call_tool("update_campaign",
                               {"campaign_id": campaign_id, **kwargs})

    def activate_campaign(self, campaign_id: str) -> bool:
        """Activate (launch) a campaign.

        Prerequisites: senders, leads, sequences, schedule all configured.
        """
        if self.dry_run:
            print(f"  [dry-run] Would activate campaign: {campaign_id}")
            return True
        result = self._call_tool("activate_campaign",
                                 {"campaign_id": campaign_id})
        return bool(result)

    def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign. Stops sending immediately; leads stay enrolled."""
        if self.dry_run:
            print(f"  [dry-run] Would pause campaign: {campaign_id}")
            return True
        result = self._call_tool("pause_campaign",
                                 {"campaign_id": campaign_id})
        return bool(result)

    def delete_campaign(self, campaign_id: str) -> bool:
        """Permanently delete a campaign."""
        if self.dry_run:
            print(f"  [dry-run] Would delete campaign: {campaign_id}")
            return True
        result = self._call_tool("delete_campaign",
                                 {"campaign_id": campaign_id})
        return bool(result)

    def search_campaigns_by_contact(self, email: str) -> list:
        """Find all campaigns a contact email is enrolled in."""
        result = self._call_tool("search_campaigns_by_contact",
                                 {"email": email})
        if isinstance(result, list):
            return result
        return result.get("data", result.get("campaigns", []))

    # ------------------------------------------------------------------
    # Leads (12 tools)
    # ------------------------------------------------------------------

    def list_leads(self, campaign_id=None, list_id=None, search=None,
                   limit=100, starting_after=None, **kwargs) -> dict:
        """List leads (cursor-paginated). Uses POST body, not GET params."""
        args = {"limit": limit, **kwargs}
        if campaign_id:
            args["campaign_id"] = campaign_id
        if list_id:
            args["list_id"] = list_id
        if search:
            args["search"] = search
        if starting_after:
            args["starting_after"] = starting_after
        return self._call_tool("list_leads", args)

    def get_lead(self, lead_id: str) -> dict:
        """Get a single lead by UUID."""
        return self._call_tool("get_lead", {"id": lead_id})

    def create_lead(self, email: str, campaign=None, **kwargs) -> dict:
        """Create a single lead. Required: email."""
        if self.dry_run:
            print(f"  [dry-run] Would create lead: {email}")
            return {"id": f"dry_run_{email}", "email": email}
        args = {"email": email, **kwargs}
        if campaign:
            args["campaign"] = campaign
        return self._call_tool("create_lead", args)

    def update_lead(self, lead_id: str, **kwargs) -> dict:
        """Update a lead. WARNING: custom_variables REPLACES entire object."""
        if self.dry_run:
            print(f"  [dry-run] Would update lead {lead_id}: {list(kwargs.keys())}")
            return {"id": lead_id, **kwargs}
        return self._call_tool("update_lead", {"id": lead_id, **kwargs})

    def add_leads_bulk(self, campaign_id=None, list_id=None,
                       leads: list | None = None, **kwargs) -> dict:
        """Bulk add up to 1,000 leads per call.

        Provide campaign_id OR list_id, not both.
        Each lead needs minimum: email.
        """
        if not leads:
            return {"status": "no_leads"}
        if self.dry_run:
            print(f"  [dry-run] Would bulk add {len(leads)} leads")
            return {"status": "dry_run", "count": len(leads)}
        args = {"leads": leads, **kwargs}
        if campaign_id:
            args["campaign_id"] = campaign_id
        if list_id:
            args["list_id"] = list_id
        return self._call_tool("add_leads_to_campaign_or_list_bulk", args)

    def list_lead_lists(self, search=None, limit=100,
                        starting_after=None) -> dict:
        """List lead lists (cursor-paginated)."""
        args = {"limit": limit}
        if search:
            args["search"] = search
        if starting_after:
            args["starting_after"] = starting_after
        return self._call_tool("list_lead_lists", args)

    def create_lead_list(self, name: str, **kwargs) -> dict:
        """Create a new lead list."""
        if self.dry_run:
            print(f"  [dry-run] Would create lead list: {name}")
            return {"id": f"dry_run_{name}", "name": name}
        return self._call_tool("create_lead_list", {"name": name, **kwargs})

    def update_lead_list(self, list_id: str, **kwargs) -> dict:
        """Update a lead list."""
        if self.dry_run:
            print(f"  [dry-run] Would update lead list {list_id}")
            return {"id": list_id, **kwargs}
        return self._call_tool("update_lead_list", {"id": list_id, **kwargs})

    def get_verification_stats(self, list_id: str) -> dict:
        """Get email verification breakdown for a lead list."""
        return self._call_tool("get_verification_stats_for_lead_list",
                               {"id": list_id})

    def delete_lead(self, lead_id: str) -> bool:
        """Permanently delete a lead."""
        if self.dry_run:
            print(f"  [dry-run] Would delete lead: {lead_id}")
            return True
        result = self._call_tool("delete_lead", {"id": lead_id})
        return bool(result)

    def delete_lead_list(self, list_id: str) -> bool:
        """Permanently delete a lead list."""
        if self.dry_run:
            print(f"  [dry-run] Would delete lead list: {list_id}")
            return True
        result = self._call_tool("delete_lead_list", {"id": list_id})
        return bool(result)

    def move_leads(self, **kwargs) -> dict:
        """Move/copy leads between campaigns and lists."""
        if self.dry_run:
            print(f"  [dry-run] Would move leads: {kwargs}")
            return {"status": "dry_run"}
        return self._call_tool("move_leads_to_campaign_or_list", kwargs)

    # ------------------------------------------------------------------
    # Emails / Unibox (6 tools)
    # ------------------------------------------------------------------

    def list_emails(self, campaign_id=None, lead=None, limit=100,
                    starting_after=None, **kwargs) -> dict:
        """List emails (cursor-paginated)."""
        args = {"limit": limit, **kwargs}
        if campaign_id:
            args["campaign_id"] = campaign_id
        if lead:
            args["lead"] = lead
        if starting_after:
            args["starting_after"] = starting_after
        return self._call_tool("list_emails", args)

    def get_email(self, email_id: str) -> dict:
        """Get full email content and metadata."""
        return self._call_tool("get_email", {"id": email_id})

    def reply_to_email(self, reply_to_uuid: str, body: str,
                       eaccount: str, subject: str) -> dict:
        """Reply to an email. SENDS A REAL EMAIL — requires --live mode.

        reply_to_uuid: the UUID of the email being replied to
        eaccount: the sender account email address
        """
        if self.dry_run:
            print(f"  [dry-run] Would reply to email {reply_to_uuid}")
            print(f"    From: {eaccount}")
            print(f"    Subject: {subject}")
            print(f"    Body: {body[:100]}...")
            return {"status": "dry_run", "reply_to_uuid": reply_to_uuid}
        return self._call_tool("reply_to_email", {
            "reply_to_uuid": reply_to_uuid,
            "body": body,
            "eaccount": eaccount,
            "subject": subject,
        })

    def count_unread_emails(self) -> int:
        """Count unread emails across all accounts."""
        result = self._call_tool("count_unread_emails")
        if isinstance(result, (int, float)):
            return int(result)
        return result.get("count", result.get("unread", 0))

    def verify_email(self, email: str) -> dict:
        """Verify email deliverability (5-45 seconds).

        Returns verification_status. Per-address, no bulk.
        """
        return self._call_tool("verify_email", {"email": email})

    def mark_thread_as_read(self, thread_id: str) -> bool:
        """Mark all emails in a thread as read."""
        if self.dry_run:
            print(f"  [dry-run] Would mark thread {thread_id} as read")
            return True
        result = self._call_tool("mark_thread_as_read",
                                 {"thread_id": thread_id})
        return bool(result)

    # ------------------------------------------------------------------
    # Analytics (3 tools)
    # ------------------------------------------------------------------

    def get_campaign_analytics(self, campaign_id=None, campaign_ids=None,
                               start_date=None, end_date=None) -> dict:
        """Get campaign analytics (opens, clicks, replies, bounces).

        Omit campaign_id for workspace-wide stats.
        Use campaign_ids array for multi-campaign.
        """
        args = {}
        if campaign_id:
            args["campaign_id"] = campaign_id
        if campaign_ids:
            args["campaign_ids"] = campaign_ids
        if start_date:
            args["start_date"] = start_date
        if end_date:
            args["end_date"] = end_date
        return self._call_tool("get_campaign_analytics", args or None)

    def get_daily_campaign_analytics(self, status=None) -> dict:
        """Get day-by-day campaign analytics.

        Filter by campaign status code (0=Draft, 1=Active, 2=Paused, 3=Completed).
        """
        args = {}
        if status is not None:
            args["status"] = status
        return self._call_tool("get_daily_campaign_analytics", args or None)

    def get_warmup_analytics(self, emails: list) -> dict:
        """Get warmup metrics for specific accounts."""
        return self._call_tool("get_warmup_analytics", {"emails": emails})

    # ------------------------------------------------------------------
    # Background Jobs (2 tools)
    # ------------------------------------------------------------------

    def list_background_jobs(self, limit=100, starting_after=None) -> dict:
        """List background jobs (cursor-paginated)."""
        args = {"limit": limit}
        if starting_after:
            args["starting_after"] = starting_after
        return self._call_tool("list_background_jobs", args)

    def get_background_job(self, job_id: str) -> dict:
        """Get background job status and progress."""
        return self._call_tool("get_background_job", {"id": job_id})


class MCPError(Exception):
    """Error from MCP protocol call."""

    def __init__(self, code: int, message: str, duration_ms: int = 0):
        self.code = code
        self.message = message
        self.duration_ms = duration_ms
        super().__init__(f"MCP error {code}: {message}")
