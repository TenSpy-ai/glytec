"""
GTM Hello World — Shared Database Utilities
Extracted from duplicated code across check_status.py, pull_metrics.py,
process_replies.py, and push_to_clay.py.
"""

import json
import sqlite3

from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    """Get a database connection with Row factory and WAL mode."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def log_api_call(conn: sqlite3.Connection, interface: str, endpoint: str,
                 method: str, params: dict | None, response_code: int | None,
                 summary: str, duration_ms: int | None = None) -> None:
    """Log every API/MCP call to api_log table."""
    try:
        conn.execute(
            """INSERT INTO api_log
               (interface, tool_or_endpoint, method, params, response_code,
                response_summary, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (interface, endpoint, method,
             json.dumps(params)[:500] if params else None,
             response_code, summary[:500] if summary else None, duration_ms),
        )
        conn.commit()
    except Exception:
        pass  # Don't let logging failures break operations
