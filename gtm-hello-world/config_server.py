#!/usr/bin/env python3
"""
GTM Hello World — Config Server

Minimal stdlib-only HTTP server that:
  - Serves static files (tracker.html, etc.) from the gtm-hello-world directory
  - Exposes GET /config and PUT /config to read/write config.py constants
  - Binds to 127.0.0.1 only (local access)

Usage:
    python config_server.py              # default port 8099
    python config_server.py --port 9000  # custom port
"""

import argparse
import json
import re
import socketserver
import sqlite3
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.py"
DB_PATH = Path(__file__).resolve().parent / "data" / "gtm_hello_world.db"

# Constants that can be edited via the API
EDITABLE = {
    "DRY_RUN":                {"type": "bool"},
    "BOUNCE_RATE_LIMIT":      {"type": "float"},
    "SPAM_RATE_LIMIT":        {"type": "float"},
    "UNSUBSCRIBE_RATE_LIMIT": {"type": "float"},
    "POSITIVE_THRESHOLD":     {"type": "float"},
    "NEGATIVE_THRESHOLD":     {"type": "float"},
}

# Read-only constants to expose
READ_ONLY = [
    "DB_PATH",
    "ENRICHMENT_DB_PATH",
    "CAMPAIGNS_DIR",
    "INSTANTLY_BASE_URL",
    "INSTANTLY_MCP_URL_TEMPLATE",
]


# ── Threading + Task Management ────────────────────────────────────────────


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


@dataclass
class TaskRecord:
    id: str
    type: str  # "autopilot", "monitor", "preview"
    config: dict
    status: str = "running"  # running, completed, failed, cancelled
    progress: str = ""
    steps: list = field(default_factory=list)
    result: dict | None = None
    error: str | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None


class TaskManager:
    """Thread-safe in-memory task store."""

    def __init__(self):
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = threading.Lock()

    def create(self, task_type: str, config: dict) -> str:
        task_id = uuid.uuid4().hex[:12]
        task = TaskRecord(id=task_id, type=task_type, config=config)
        with self._lock:
            self._tasks[task_id] = task
        return task_id

    def get(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 20) -> list[dict]:
        with self._lock:
            tasks = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)[:limit]
            return [self._serialize(t) for t in tasks]

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != "running":
                return False
            task.cancel_event.set()
            task.status = "cancelled"
            task.completed_at = datetime.now().isoformat()
            return True

    def update_progress(self, task_id: str, step_name: str, detail: str = ""):
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == "running":
                task.progress = step_name
                task.steps.append({"step": step_name, "detail": detail,
                                   "at": datetime.now().isoformat()})

    def complete(self, task_id: str, result: dict):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = "completed"
                task.result = result
                task.completed_at = datetime.now().isoformat()

    def fail(self, task_id: str, error: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = "failed"
                task.error = error
                task.completed_at = datetime.now().isoformat()

    def _serialize(self, task: TaskRecord) -> dict:
        return {
            "id": task.id, "type": task.type, "config": task.config,
            "status": task.status, "progress": task.progress,
            "steps": task.steps, "result": task.result, "error": task.error,
            "created_at": task.created_at, "completed_at": task.completed_at,
        }

    def serialize_one(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            return self._serialize(task) if task else None


task_manager = TaskManager()


# ── Task execution functions ───────────────────────────────────────────────

def _is_dry_run_forced() -> bool:
    """Check if config.py forces DRY_RUN=True."""
    try:
        text = CONFIG_PATH.read_text()
        m = re.search(r'^DRY_RUN\s*=\s*(.+?)(?:\s*#.*)?$', text, re.MULTILINE)
        return m and m.group(1).strip() == "True"
    except Exception:
        return True


def execute_autopilot(task_id: str, config: dict):
    """Run autopilot in a daemon thread."""
    task = task_manager.get(task_id)
    if not task:
        return

    try:
        from autopilot import Autopilot, AutopilotConfig
        from query_builder import ContactQuery, parse_natural_language

        # Safety: force dry-run if config.py says so
        live = config.get("live", False)
        if _is_dry_run_forced() and live:
            live = False
            task_manager.update_progress(task_id, "safety_override",
                                         "DRY_RUN=True in config.py — forcing dry-run mode")

        if task.cancel_event.is_set():
            return

        # Build query from natural language or structured params
        task_manager.update_progress(task_id, "building_query",
                                     f"Template: {config.get('template')}, Query: {config.get('query')}")

        query_str = config.get("query", "")
        query = parse_natural_language(query_str) if query_str else ContactQuery()

        if task.cancel_event.is_set():
            return

        ap_config = AutopilotConfig(
            template=config.get("template", "01-new-in-role"),
            query=query,
            schedule_type=config.get("schedule_type", "weekday"),
            daily_limit=config.get("daily_limit", 30),
            live=live,
        )

        task_manager.update_progress(task_id, "starting_autopilot",
                                     f"Mode: {'LIVE' if live else 'DRY RUN'}")

        # Run the autopilot — it prints progress to stdout
        result = Autopilot().run(ap_config)

        task_manager.update_progress(task_id, "done",
                                     f"Status: {result.get('status')}, Contacts: {result.get('contact_count', 0)}")
        task_manager.complete(task_id, result)

    except Exception as e:
        task_manager.fail(task_id, str(e))


def execute_monitor(task_id: str):
    """Run monitor cycle in a daemon thread."""
    task = task_manager.get(task_id)
    if not task:
        return

    try:
        from autopilot import run_monitor

        live = not _is_dry_run_forced()
        task_manager.update_progress(task_id, "starting_monitor",
                                     f"Mode: {'LIVE' if live else 'DRY RUN'}")

        if task.cancel_event.is_set():
            return

        result = run_monitor(live=live)

        task_manager.update_progress(task_id, "done",
                                     f"Campaigns: {result.get('metrics_count', 0)}, "
                                     f"Replies: {result.get('replies_processed', 0)}")
        task_manager.complete(task_id, result)

    except Exception as e:
        task_manager.fail(task_id, str(e))


def execute_preview(task_id: str, template_key: str):
    """Resolve a template and return its data."""
    try:
        from autopilot import list_all_templates, resolve_template

        task_manager.update_progress(task_id, "resolving_template", template_key)
        info = resolve_template(template_key)
        templates = list_all_templates()
        match = next((t for t in templates if t["id"] == template_key or t["filename"].replace(".md", "") == template_key), None)
        result = match or {"name": info.name, "recipe": info.recipe, "filename": info.filename}
        task_manager.complete(task_id, result)

    except Exception as e:
        task_manager.fail(task_id, str(e))


def start_task(task_type: str, config: dict) -> str:
    """Create a task and start it in a daemon thread."""
    task_id = task_manager.create(task_type, config)

    if task_type == "autopilot":
        t = threading.Thread(target=execute_autopilot, args=(task_id, config), daemon=True)
    elif task_type == "monitor":
        t = threading.Thread(target=execute_monitor, args=(task_id,), daemon=True)
    elif task_type == "preview":
        t = threading.Thread(target=execute_preview, args=(task_id, config.get("template", "")), daemon=True)
    else:
        task_manager.fail(task_id, f"Unknown task type: {task_type}")
        return task_id

    t.start()
    return task_id


def read_config() -> dict:
    """Parse config.py and extract editable + read-only values."""
    text = CONFIG_PATH.read_text()
    result = {"editable": {}, "readonly": {}}

    for name, meta in EDITABLE.items():
        pattern = rf'^{name}\s*=\s*(.+?)(?:\s*#.*)?$'
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            raw = m.group(1).strip()
            if meta["type"] == "bool":
                result["editable"][name] = raw == "True"
            elif meta["type"] == "float":
                result["editable"][name] = float(raw)

    for name in READ_ONLY:
        pattern = rf'^{name}\s*=\s*(.+?)(?:\s*#.*)?$'
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            raw = m.group(1).strip()
            # Strip quotes for string literals
            if raw.startswith('"') and raw.endswith('"'):
                result["readonly"][name] = raw.strip('"')
            else:
                result["readonly"][name] = raw

    return result


def write_config(updates: dict) -> dict:
    """Update editable constants in config.py. Returns the new state."""
    text = CONFIG_PATH.read_text()

    for name, value in updates.items():
        if name not in EDITABLE:
            continue
        meta = EDITABLE[name]
        if meta["type"] == "bool":
            replacement = "True" if value else "False"
        elif meta["type"] == "float":
            replacement = str(float(value))

        # Replace the value while preserving inline comments
        pattern = rf'^({name}\s*=\s*)(.+?)(\s*#.*)$'
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            text = text[:m.start()] + m.group(1) + replacement + m.group(3) + text[m.end():]
        else:
            # No inline comment variant
            pattern2 = rf'^({name}\s*=\s*)(.+)$'
            m2 = re.search(pattern2, text, re.MULTILINE)
            if m2:
                text = text[:m2.start()] + m2.group(1) + replacement + text[m2.end():]

    CONFIG_PATH.write_text(text)
    return read_config()


def read_dashboard() -> dict:
    """Read dashboard data from the local DB."""
    if not DB_PATH.exists():
        return {"error": "Database not found", "campaigns": [], "metrics": [],
                "sentiment": {}, "autopilot_runs": [], "mailboxes": []}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    def rows_to_dicts(rows):
        return [dict(r) for r in rows]

    campaigns = rows_to_dicts(conn.execute(
        """SELECT c.id, c.name, c.instantly_campaign_id, c.instantly_status,
                  c.recipe, c.status, c.daily_limit, c.email_gap,
                  c.launched_at, c.created_at,
                  COUNT(cc.id) AS enrolled,
                  COALESCE(m.sent, 0) AS sent,
                  COALESCE(m.opened, 0) AS opened,
                  COALESCE(m.replied, 0) AS replied,
                  COALESCE(m.bounced, 0) AS bounced,
                  m.open_rate, m.reply_rate, m.bounce_rate,
                  m.snapshot_date AS last_metric_date
           FROM campaigns c
           LEFT JOIN campaign_contacts cc ON c.id = cc.campaign_id
           LEFT JOIN metric_snapshots m ON c.id = m.campaign_id
                AND m.snapshot_date = (SELECT MAX(snapshot_date) FROM metric_snapshots WHERE campaign_id = c.id)
           GROUP BY c.id
           ORDER BY c.created_at DESC"""
    ).fetchall())

    metrics = rows_to_dicts(conn.execute(
        """SELECT m.*, c.name AS campaign_name
           FROM metric_snapshots m
           JOIN campaigns c ON m.campaign_id = c.id
           ORDER BY m.snapshot_date DESC, c.name
           LIMIT 50"""
    ).fetchall())

    sentiment_rows = conn.execute(
        """SELECT sentiment, COUNT(*) AS cnt
           FROM reply_sentiment
           GROUP BY sentiment"""
    ).fetchall()
    sentiment = {r["sentiment"]: r["cnt"] for r in sentiment_rows}

    autopilot_runs = rows_to_dicts(conn.execute(
        """SELECT id, template, campaign_name, instantly_campaign_id,
                  contact_count, sender_count, schedule_type,
                  mode, status, error_message, steps_completed,
                  duration_ms, created_at, completed_at
           FROM autopilot_runs
           ORDER BY created_at DESC
           LIMIT 20"""
    ).fetchall())

    mailboxes = rows_to_dicts(conn.execute(
        """SELECT email, first_name, last_name, daily_limit, status,
                  warmup_status, warmup_score, last_synced_at
           FROM mailboxes
           ORDER BY email"""
    ).fetchall())

    conn.close()
    return {
        "campaigns": campaigns,
        "metrics": metrics,
        "sentiment": sentiment,
        "autopilot_runs": autopilot_runs,
        "mailboxes": mailboxes,
    }


TABLES_WHITELIST = [
    "accounts", "contacts", "campaigns", "campaign_contacts",
    "metric_snapshots", "reply_sentiment", "clay_push_log",
    "email_threads", "engagement_events", "mailboxes",
    "api_log", "block_list", "autopilot_runs", "autopilot_steps",
]


def read_table(table: str, limit: int = 500, offset: int = 0) -> dict:
    """Read rows from a single table. Returns {columns, rows, total, limit, offset}."""
    if table not in TABLES_WHITELIST:
        return {"error": f"Unknown table: {table}"}
    if not DB_PATH.exists():
        return {"error": "Database not found", "columns": [], "rows": [], "total": 0}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    rows_raw = conn.execute(
        f"SELECT * FROM {table} ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()

    columns = rows_raw[0].keys() if rows_raw else []
    rows = [dict(r) for r in rows_raw]

    conn.close()
    return {"table": table, "columns": list(columns), "rows": rows,
            "total": total, "limit": limit, "offset": offset}


def read_run_detail(run_id: int) -> dict:
    """Read a single autopilot run with its steps."""
    if not DB_PATH.exists():
        return {"error": "Database not found"}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    row = conn.execute("SELECT * FROM autopilot_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": f"Run {run_id} not found"}

    run = dict(row)
    steps = [dict(r) for r in conn.execute(
        """SELECT id, step_number, step_name, status, detail, data_json,
                  duration_ms, started_at, completed_at
           FROM autopilot_steps
           WHERE run_id = ?
           ORDER BY step_number""",
        (run_id,),
    ).fetchall()]

    conn.close()
    return {"run": run, "steps": steps}


def read_all_tables_summary() -> dict:
    """Return row counts for every table."""
    if not DB_PATH.exists():
        return {"error": "Database not found", "tables": {}}

    conn = sqlite3.connect(str(DB_PATH))
    counts = {}
    for t in TABLES_WHITELIST:
        counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    conn.close()
    return {"tables": counts}


class ConfigHandler(SimpleHTTPRequestHandler):
    """Extends SimpleHTTPRequestHandler with /config, /dashboard, and /tables API endpoints."""

    def do_GET(self):
        if self.path == "/config":
            self._send_json(200, read_config())
        elif self.path == "/dashboard":
            self._send_json(200, read_dashboard())
        elif self.path == "/tables":
            self._send_json(200, read_all_tables_summary())
        elif self.path.startswith("/runs/"):
            parts = self.path.split("/")
            try:
                run_id = int(parts[2]) if len(parts) > 2 else 0
                self._send_json(200, read_run_detail(run_id))
            except (ValueError, IndexError):
                self._send_json(400, {"error": "Invalid run ID"})
        elif self.path == "/templates":
            from autopilot import list_all_templates
            self._send_json(200, list_all_templates())
        elif self.path == "/api/tasks":
            self._send_json(200, task_manager.list_tasks())
        elif self.path.startswith("/api/tasks/"):
            task_id = self.path.split("/")[3].split("?")[0]
            data = task_manager.serialize_one(task_id)
            if data:
                self._send_json(200, data)
            else:
                self._send_json(404, {"error": "Task not found"})
        elif self.path.startswith("/tables/"):
            parts = self.path.split("/")
            table = parts[2].split("?")[0] if len(parts) > 2 else ""
            # Parse query params for limit/offset
            limit, offset = 500, 0
            if "?" in self.path:
                from urllib.parse import parse_qs, urlparse
                qs = parse_qs(urlparse(self.path).query)
                limit = min(int(qs.get("limit", [500])[0]), 2000)
                offset = int(qs.get("offset", [0])[0])
            self._send_json(200, read_table(table, limit, offset))
        else:
            super().do_GET()

    def do_PUT(self):
        if self.path == "/config":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                updates = json.loads(body)
                result = write_config(updates)
                self._send_json(200, result)
            except (json.JSONDecodeError, ValueError) as e:
                self._send_json(400, {"error": str(e)})
        else:
            self.send_error(405)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"

        if self.path == "/api/tasks":
            try:
                data = json.loads(body)
                task_type = data.get("type")
                config = data.get("config", {})
                if task_type not in ("autopilot", "monitor", "preview"):
                    self._send_json(400, {"error": f"Invalid task type: {task_type}. Must be autopilot, monitor, or preview."})
                    return
                task_id = start_task(task_type, config)
                self._send_json(201, {"id": task_id, "status": "running"})
            except (json.JSONDecodeError, ValueError) as e:
                self._send_json(400, {"error": str(e)})

        elif self.path.startswith("/api/tasks/") and self.path.endswith("/cancel"):
            task_id = self.path.split("/")[3]
            if task_manager.cancel(task_id):
                self._send_json(200, {"id": task_id, "status": "cancelled"})
            else:
                self._send_json(404, {"error": "Task not found or not running"})
        else:
            self.send_error(405)

    def do_OPTIONS(self):
        if (self.path in ("/config", "/dashboard", "/tables", "/templates", "/api/tasks")
                or self.path.startswith("/tables/") or self.path.startswith("/runs/")
                or self.path.startswith("/api/tasks/")):
            self.send_response(204)
            self._cors_headers()
            self.end_headers()
        else:
            self.send_error(405)

    def _send_json(self, code, data):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        # Compact log format
        sys.stderr.write(f"[config_server] {args[0]}\n")


def main():
    parser = argparse.ArgumentParser(description="GTM Hello World config server")
    parser.add_argument("--port", type=int, default=8099, help="Port (default: 8099)")
    args = parser.parse_args()

    server = ThreadedHTTPServer(("127.0.0.1", args.port), ConfigHandler)
    print(f"Config server running at http://localhost:{args.port}")
    print(f"  Tracker: http://localhost:{args.port}/tracker.html")
    print(f"  Config API: http://localhost:{args.port}/config")
    print(f"  Dashboard API: http://localhost:{args.port}/dashboard")
    print(f"  Tables API: http://localhost:{args.port}/tables")
    print(f"  Tasks API: http://localhost:{args.port}/api/tasks")
    print(f"  Editing: {CONFIG_PATH}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
