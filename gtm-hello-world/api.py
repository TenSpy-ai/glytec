"""
GTM Hello World — Instantly REST API Client (FALLBACK)
Only for endpoints with NO MCP tool. Currently: block list.

Usage:
    from api import InstantlyAPI
    client = InstantlyAPI()
    client = InstantlyAPI(dry_run=False)
"""

import json
import time
import urllib.request
import urllib.error

from config import INSTANTLY_API_KEY, DRY_RUN, instantly_headers, instantly_api_url
from db import get_conn, log_api_call


class InstantlyAPI:
    """REST API client for Instantly.ai endpoints not covered by MCP."""

    def __init__(self, api_key=None, dry_run=None):
        self.api_key = api_key or INSTANTLY_API_KEY
        self.dry_run = dry_run if dry_run is not None else DRY_RUN
        self._headers = instantly_headers()

    def _request(self, method: str, path: str, json_body: dict | None = None,
                 params: dict | None = None) -> tuple[dict | None, int]:
        """Make a REST API request with logging.

        Returns (response_data, status_code).
        """
        url = instantly_api_url(path)

        # Append query params to URL
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        data = json.dumps(json_body).encode("utf-8") if json_body else None

        req = urllib.request.Request(
            url, data=data, headers=self._headers, method=method,
        )

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                duration_ms = int((time.time() - start) * 1000)
                body = resp.read().decode("utf-8")
                status = resp.status

                self._log(path, method, json_body or params, status,
                          body[:200], duration_ms)

                if status == 204:
                    return None, status
                try:
                    return json.loads(body), status
                except (json.JSONDecodeError, ValueError):
                    return {"raw": body}, status

        except urllib.error.HTTPError as e:
            duration_ms = int((time.time() - start) * 1000)
            error_body = e.read().decode("utf-8")
            self._log(path, method, json_body or params, e.code,
                      error_body[:200], duration_ms)
            return None, e.code

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            self._log(path, method, json_body or params, 0,
                      str(e)[:200], duration_ms)
            return None, 0

    def _log(self, endpoint: str, method: str, params: dict | None,
             status_code: int, summary: str, duration_ms: int) -> None:
        """Log API call to SQLite."""
        try:
            conn = get_conn()
            log_api_call(conn, "api", endpoint, method, params,
                         status_code, summary, duration_ms)
            conn.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Block List (no MCP — REST only)
    # ------------------------------------------------------------------

    def list_block_list_entries(self, limit=100, starting_after=None) -> dict:
        """GET /block-lists-entries — list block list entries."""
        params = {"limit": limit}
        if starting_after:
            params["starting_after"] = starting_after
        data, status = self._request("GET", "block-lists-entries", params=params)
        return data or {"items": []}

    def create_block_list_entry(self, value: str) -> dict:
        """POST /block-lists-entries — add email or domain to block list.

        is_domain is auto-detected (read-only).
        """
        if self.dry_run:
            print(f"  [dry-run] Would block: {value}")
            return {"id": f"dry_run_{value}", "bl_value": value}
        data, status = self._request("POST", "block-lists-entries",
                                     json_body={"bl_value": value})
        if data:
            print(f"  [live] Blocked: {value} (HTTP {status})")
        else:
            print(f"  [live] Failed to block {value}: HTTP {status}")
        return data or {}

    def get_block_list_entry(self, entry_id: str) -> dict:
        """GET /block-lists-entries/{id} — get a single block list entry."""
        data, status = self._request("GET", f"block-lists-entries/{entry_id}")
        return data or {}

    def update_block_list_entry(self, entry_id: str, value: str) -> dict:
        """PATCH /block-lists-entries/{id} — update a block list entry."""
        if self.dry_run:
            print(f"  [dry-run] Would update block entry {entry_id} → {value}")
            return {"id": entry_id, "bl_value": value}
        data, status = self._request("PATCH", f"block-lists-entries/{entry_id}",
                                     json_body={"bl_value": value})
        return data or {}

    def delete_block_list_entry(self, entry_id: str) -> bool:
        """DELETE /block-lists-entries/{id} — remove from block list (reversible!)."""
        if self.dry_run:
            print(f"  [dry-run] Would unblock entry: {entry_id}")
            return True
        _, status = self._request("DELETE", f"block-lists-entries/{entry_id}")
        success = status in (200, 204)
        if success:
            print(f"  [live] Removed block entry: {entry_id}")
        else:
            print(f"  [live] Failed to remove block entry: HTTP {status}")
        return success
