"""Definitive Healthcare HospitalView API client.

Handles auth, pagination, rate limiting, retries, and all DH API gotchas.
"""

import os
import time
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DH_API_KEY = os.getenv("DH_API_KEY", "")
DH_BASE_URL = "https://api-data.defhc.com"

logger = logging.getLogger("dh_client")


class DHClient:
    """HTTP client for Definitive Healthcare HospitalView API."""

    def __init__(self, api_key: str = None, db_path: str = None, max_retries: int = 3,
                 concurrency: int = 5, dry_run: bool = True):
        self.api_key = api_key or DH_API_KEY
        self.base_url = DH_BASE_URL
        self.max_retries = max_retries
        self.concurrency = concurrency
        self.dry_run = dry_run
        self.db_path = db_path
        self.run_id = None
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        })

    def set_run_id(self, run_id: int):
        self.run_id = run_id

    def _log_api_call(self, endpoint: str, method: str, def_id: int,
                      params: dict, http_status: int, records: int,
                      response_time_ms: int, error: str = None, retry_count: int = 0):
        """Log API call to SQLite and Python logger."""
        if self.db_path:
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=1)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=1000")
                conn.execute(
                    """INSERT INTO api_calls
                       (run_id, endpoint, method, definitive_id, params_json,
                        http_status, records_returned, response_time_ms,
                        error_message, retry_count)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (self.run_id, endpoint, method, def_id,
                     json.dumps(params) if params else None,
                     http_status, records, response_time_ms, error, retry_count),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to log API call to DB: {e}")

        status_str = f"{http_status}" if http_status else "DRY_RUN"
        if error:
            logger.error(f"[dh_client] {method} {endpoint} -> {status_str} ({error})")
        else:
            logger.info(f"[dh_client] {method} {endpoint} -> {status_str} ({records} records, {response_time_ms}ms)")

    def _request(self, method: str, path: str, def_id: int = None,
                 params: dict = None, json_body=None, page_size: int = None,
                 page_offset: int = None) -> dict:
        """Make a single HTTP request with retries and logging."""
        url = f"{self.base_url}{path}"
        query_params = {}
        if page_size:
            query_params["page[size]"] = page_size
        if page_offset:
            query_params["page[offset]"] = page_offset

        if self.dry_run:
            self._log_api_call(path, method, def_id, params or json_body,
                               0, 0, 0)
            logger.info(f"[dh_client] DRY RUN: {method} {path}")
            return {"meta": {"totalRecords": 0, "totalPages": 0}, "data": []}

        last_error = None
        for attempt in range(self.max_retries + 1):
            start = time.time()
            try:
                if method.upper() == "GET":
                    resp = self.session.get(url, params=query_params, timeout=30)
                elif method.upper() == "POST":
                    resp = self.session.post(url, params=query_params,
                                             json=json_body, timeout=30)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                elapsed_ms = int((time.time() - start) * 1000)

                if resp.status_code == 429 or resp.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning(f"[dh_client] {method} {path} -> {resp.status_code} (retry {attempt+1}/{self.max_retries}, wait {wait}s)")
                    self._log_api_call(path, method, def_id, params or json_body,
                                       resp.status_code, 0, elapsed_ms,
                                       f"Retry {attempt+1}: HTTP {resp.status_code}",
                                       attempt)
                    if attempt < self.max_retries:
                        time.sleep(wait)
                        continue
                    last_error = f"HTTP {resp.status_code} after {self.max_retries} retries"
                    break

                data = resp.json()

                # Detect invalid hospital ID (returns 200 with null data)
                if isinstance(data.get("data"), dict):
                    d = data["data"]
                    if d.get("definitiveId") == 0 or d.get("facilityName") is None:
                        self._log_api_call(path, method, def_id, params or json_body,
                                           resp.status_code, 0, elapsed_ms,
                                           "Invalid hospital ID (definitiveId=0 or facilityName=null)")
                        return {"meta": {"totalRecords": 0, "totalPages": 0}, "data": None}

                # Count records
                records = 0
                if isinstance(data.get("data"), list):
                    records = len(data["data"])
                elif isinstance(data.get("data"), dict):
                    records = 1

                self._log_api_call(path, method, def_id, params or json_body,
                                   resp.status_code, records, elapsed_ms)
                return data

            except requests.exceptions.RequestException as e:
                elapsed_ms = int((time.time() - start) * 1000)
                last_error = str(e)
                logger.error(f"[dh_client] {method} {path} -> Exception: {e} (retry {attempt+1}/{self.max_retries})")
                self._log_api_call(path, method, def_id, params or json_body,
                                   0, 0, elapsed_ms, str(e), attempt)
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)

        # All retries exhausted
        self._log_api_call(path, method, def_id, params or json_body,
                           0, 0, 0, last_error, self.max_retries)
        return {"meta": {"totalRecords": 0, "totalPages": 0}, "data": [], "error": last_error}

    def _paginate(self, method: str, path: str, def_id: int = None,
                  json_body=None, page_size: int = 500) -> list:
        """Auto-paginate through all pages of results."""
        all_records = []
        page_offset = 1

        while True:
            result = self._request(method, path, def_id=def_id,
                                   json_body=json_body, page_size=page_size,
                                   page_offset=page_offset)

            if self.dry_run:
                return []

            data = result.get("data", [])
            if data is None:
                break
            if isinstance(data, list):
                all_records.extend(data)
            elif isinstance(data, dict):
                all_records.append(data)
                break

            meta = result.get("meta", {})
            total_pages = meta.get("totalPages", 1)
            if page_offset >= total_pages:
                break
            page_offset += 1

        return all_records

    # --- Hospital endpoints ---

    def get_hospital(self, def_id: int) -> dict:
        """Get single hospital by Definitive ID. Returns dict or None."""
        result = self._request("GET", f"/v1/hospitals/{def_id}", def_id=def_id)
        data = result.get("data")
        if data is None or (isinstance(data, dict) and data.get("definitiveId") == 0):
            return None
        return data

    def search_hospitals(self, filters: list[dict], page_size: int = 500) -> list[dict]:
        """Search hospitals with filters. Returns list of hospital dicts."""
        return self._paginate("POST", "/v1/hospitals/search",
                              json_body=filters, page_size=page_size)

    # --- Executive endpoints ---

    def get_executives(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get all executives at a hospital."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/executives",
                              def_id=def_id, page_size=page_size)

    def search_executives(self, def_id: int, filters: list[dict],
                          page_size: int = 500) -> list[dict]:
        """Search executives at a hospital with filters."""
        return self._paginate("POST", f"/v1/hospitals/{def_id}/executives/search",
                              def_id=def_id, json_body=filters, page_size=page_size)

    # --- Physician endpoints ---

    def get_physicians(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get all affiliated physicians at a hospital."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/physicians/affiliated",
                              def_id=def_id, page_size=page_size)

    def search_physicians(self, def_id: int, filters: list[dict],
                          page_size: int = 500) -> list[dict]:
        """Search physicians at a hospital with filters."""
        return self._paginate("POST", f"/v1/hospitals/{def_id}/physicians/affiliated/search",
                              def_id=def_id, json_body=filters, page_size=page_size)

    # --- Technology endpoints ---

    def get_technologies(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get current technology implementations at a hospital."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/technologies/currentimplementations",
                              def_id=def_id, page_size=page_size)

    # --- Quality endpoints ---

    def get_quality(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get quality metrics for a hospital."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/quality",
                              def_id=def_id, page_size=page_size)

    def search_quality(self, def_id: int, filters: list[dict],
                       page_size: int = 500) -> list[dict]:
        """Search quality metrics with filters."""
        return self._paginate("POST", f"/v1/hospitals/{def_id}/quality/search",
                              def_id=def_id, json_body=filters, page_size=page_size)

    # --- Financial endpoints ---

    def get_financials(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get financial metrics for a hospital."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/financials",
                              def_id=def_id, page_size=page_size)

    def search_financials(self, def_id: int, filters: list[dict],
                          page_size: int = 500) -> list[dict]:
        """Search financial metrics with filters."""
        return self._paginate("POST", f"/v1/hospitals/{def_id}/financials/search",
                              def_id=def_id, json_body=filters, page_size=page_size)

    # --- News endpoints ---

    def get_news(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get news and intelligence for a hospital."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/newsandintelligence",
                              def_id=def_id, page_size=page_size)

    def search_news(self, def_id: int, filters: list[dict],
                    page_size: int = 500) -> list[dict]:
        """Search news with filters."""
        return self._paginate("POST", f"/v1/hospitals/{def_id}/newsandintelligence/search",
                              def_id=def_id, json_body=filters, page_size=page_size)

    # --- Affiliation / Membership / RFP endpoints ---

    def get_affiliations(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get affiliated facilities."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/affiliations",
                              def_id=def_id, page_size=page_size)

    def get_memberships(self, def_id: int, page_size: int = 500) -> list[dict]:
        """Get memberships (GPO, ACO, CIN, HIE)."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/memberships",
                              def_id=def_id, page_size=page_size)

    def get_requests(self, def_id: int, page_size: int = 100) -> list[dict]:
        """Get RFPs/requests for a hospital."""
        return self._paginate("GET", f"/v1/hospitals/{def_id}/requests",
                              def_id=def_id, page_size=page_size)
