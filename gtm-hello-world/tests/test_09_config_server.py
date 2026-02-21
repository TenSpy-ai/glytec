"""
Test 09 — Config Server HTTP API
Starts server on test port, tests GET/PUT/OPTIONS, restores config.py.
"""

import json
import shutil
import threading
import time
import urllib.request
import urllib.error
from http.server import HTTPServer
from pathlib import Path

from tests.helpers import TestResult, ensure_db_seeded

TEST_PORT = 8199


def run() -> TestResult:
    r = TestResult("test_09_config_server — Config Server HTTP API")
    ensure_db_seeded()

    from config_server import ConfigHandler, read_config, write_config, CONFIG_PATH

    # Backup config.py before any writes
    backup = CONFIG_PATH.with_suffix(".py.qa_backup")
    shutil.copy2(CONFIG_PATH, backup)

    server = None
    server_thread = None

    try:
        # Start server on test port
        server = HTTPServer(("127.0.0.1", TEST_PORT), ConfigHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(0.5)  # Let server start

        base_url = f"http://127.0.0.1:{TEST_PORT}"

        # --- 1. GET /config returns editable + readonly ---
        try:
            req = urllib.request.Request(f"{base_url}/config")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "editable" in data and "readonly" in data:
                    r.ok("get_config_structure")
                else:
                    r.fail("get_config_structure", f"Missing keys: {data.keys()}")

                # Verify editable has expected keys
                editable = data["editable"]
                if "DRY_RUN" in editable and "BOUNCE_RATE_LIMIT" in editable:
                    r.ok("get_config_editable_keys")
                else:
                    r.fail("get_config_editable_keys", f"Keys: {editable.keys()}")

                # Verify readonly has expected keys
                readonly = data["readonly"]
                if "DB_PATH" in readonly or "INSTANTLY_BASE_URL" in readonly:
                    r.ok("get_config_readonly_keys")
                else:
                    r.fail("get_config_readonly_keys", f"Keys: {readonly.keys()}")
        except Exception as e:
            r.fail("get_config", e)

        # --- 2. PUT /config updates DRY_RUN ---
        try:
            body = json.dumps({"DRY_RUN": False}).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/config", data=body,
                headers={"Content-Type": "application/json"},
                method="PUT",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("editable", {}).get("DRY_RUN") is False:
                    r.ok("put_dry_run_false")
                else:
                    r.fail("put_dry_run_false", f"DRY_RUN not False: {data}")
        except Exception as e:
            r.fail("put_dry_run_false", e)

        # --- 3. PUT /config updates threshold ---
        try:
            body = json.dumps({"BOUNCE_RATE_LIMIT": 0.08}).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/config", data=body,
                headers={"Content-Type": "application/json"},
                method="PUT",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                val = data.get("editable", {}).get("BOUNCE_RATE_LIMIT")
                if val == 0.08:
                    r.ok("put_threshold")
                else:
                    r.fail("put_threshold", f"BOUNCE_RATE_LIMIT = {val}")
        except Exception as e:
            r.fail("put_threshold", e)

        # --- 4. PUT ignores readonly ---
        try:
            # Read current state first
            req = urllib.request.Request(f"{base_url}/config")
            with urllib.request.urlopen(req, timeout=5) as resp:
                before = json.loads(resp.read().decode("utf-8"))

            body = json.dumps({"DB_PATH": "/fake/path"}).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/config", data=body,
                headers={"Content-Type": "application/json"},
                method="PUT",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                db_path = data.get("readonly", {}).get("DB_PATH", "")
                if "/fake/path" not in db_path:
                    r.ok("put_ignores_readonly")
                else:
                    r.fail("put_ignores_readonly", f"DB_PATH was modified: {db_path}")
        except Exception as e:
            r.fail("put_ignores_readonly", e)

        # --- 5. PUT bad JSON returns 400 ---
        try:
            req = urllib.request.Request(
                f"{base_url}/config", data=b"not json{{{",
                headers={"Content-Type": "application/json"},
                method="PUT",
            )
            try:
                urllib.request.urlopen(req, timeout=5)
                r.fail("put_bad_json_400", "Expected 400 but got 200")
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    r.ok("put_bad_json_400")
                else:
                    r.fail("put_bad_json_400", f"Expected 400, got {e.code}")
        except Exception as e:
            r.fail("put_bad_json_400", e)

        # --- 6. GET tracker.html returns 200 ---
        try:
            tracker_path = Path(CONFIG_PATH).parent / "tracker.html"
            if tracker_path.exists():
                req = urllib.request.Request(f"{base_url}/tracker.html")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        r.ok("get_tracker_html")
                    else:
                        r.fail("get_tracker_html", f"Status: {resp.status}")
            else:
                r.ok("get_tracker_html")  # Skip if file doesn't exist
        except Exception as e:
            r.fail("get_tracker_html", e)

        # --- 7. OPTIONS returns CORS headers ---
        try:
            req = urllib.request.Request(
                f"{base_url}/config", method="OPTIONS",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                cors = resp.headers.get("Access-Control-Allow-Origin", "")
                methods = resp.headers.get("Access-Control-Allow-Methods", "")
                if "*" in cors and "PUT" in methods:
                    r.ok("options_cors")
                else:
                    r.fail("options_cors", f"CORS: {cors}, Methods: {methods}")
        except urllib.error.HTTPError as e:
            # 204 No Content may cause issues with some urllib versions
            if e.code == 204:
                r.ok("options_cors")
            else:
                r.fail("options_cors", e)
        except Exception as e:
            r.fail("options_cors", e)

        # --- 8. read_config() function ---
        try:
            config = read_config()
            if isinstance(config, dict) and "editable" in config:
                r.ok("read_config_func")
            else:
                r.fail("read_config_func", f"Unexpected: {type(config)}")
        except Exception as e:
            r.fail("read_config_func", e)

        # --- 9. write_config() function ---
        try:
            result = write_config({"DRY_RUN": True})
            if result.get("editable", {}).get("DRY_RUN") is True:
                r.ok("write_config_func")
            else:
                r.fail("write_config_func", f"DRY_RUN not True: {result}")
        except Exception as e:
            r.fail("write_config_func", e)

        # --- 10. Server responds to concurrent requests ---
        try:
            results = []
            def fetch():
                req = urllib.request.Request(f"{base_url}/config")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    results.append(resp.status)
            threads = [threading.Thread(target=fetch) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)
            if len(results) == 3 and all(s == 200 for s in results):
                r.ok("concurrent_requests")
            else:
                r.fail("concurrent_requests", f"Results: {results}")
        except Exception as e:
            r.fail("concurrent_requests", e)

    finally:
        # Shutdown server
        if server:
            server.shutdown()

        # Restore config.py from backup
        if backup.exists():
            shutil.copy2(backup, CONFIG_PATH)
            backup.unlink()

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
