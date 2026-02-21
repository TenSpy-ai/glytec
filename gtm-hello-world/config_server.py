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
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.py"

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


class ConfigHandler(SimpleHTTPRequestHandler):
    """Extends SimpleHTTPRequestHandler with /config API endpoints."""

    def do_GET(self):
        if self.path == "/config":
            self._send_json(200, read_config())
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

    def do_OPTIONS(self):
        if self.path == "/config":
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
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        # Compact log format
        sys.stderr.write(f"[config_server] {args[0]}\n")


def main():
    parser = argparse.ArgumentParser(description="GTM Hello World config server")
    parser.add_argument("--port", type=int, default=8099, help="Port (default: 8099)")
    args = parser.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), ConfigHandler)
    print(f"Config server running at http://localhost:{args.port}")
    print(f"  Tracker: http://localhost:{args.port}/tracker.html")
    print(f"  Config API: http://localhost:{args.port}/config")
    print(f"  Editing: {CONFIG_PATH}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
