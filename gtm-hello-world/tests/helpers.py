"""
GTM Hello World — Shared Test Utilities
TestResult collector, unique naming, cleanup helpers, common fixtures.
"""

import os
import sys
import time
import random
import threading

# Ensure gtm-hello-world is importable
GTM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if GTM_DIR not in sys.path:
    sys.path.insert(0, GTM_DIR)

TEST_PREFIX = "QA_TEST_"


def unique_name(label: str) -> str:
    """Return QA_TEST_{label}_{timestamp}_{random} — safe for parallel use."""
    ts = int(time.time_ns() // 1_000_000)  # milliseconds
    rand = format(random.randint(0, 0xFFFF), "04x")
    return f"{TEST_PREFIX}{label}_{ts}_{rand}"


# ---------------------------------------------------------------------------
# Standard test schedule + sequences for campaign creation
# ---------------------------------------------------------------------------

TEST_SCHEDULE = {
    "schedules": [{
        "name": "Weekdays",
        "timing": {"from": "08:00", "to": "17:00"},
        "days": {"1": True, "2": True, "3": True, "4": True, "5": True},
    }],
}

TEST_SEQUENCES = [{
    "steps": [{
        "type": "email",
        "subject": "QA Test — please ignore",
        "body": "<p>This is an automated QA test email. Please disregard.</p>",
        "variants": [],
    }],
}]

# Direct campaign params for the actual MCP create_campaign schema
TEST_SUBJECT = "QA Test — please ignore"
TEST_BODY = "<p>This is an automated QA test email. Please disregard.</p>"

TEST_EMAIL_DOMAIN = "qa-test-glytec.example.com"


def test_email(label: str) -> str:
    """Generate a unique test email that won't collide."""
    ts = int(time.time_ns() // 1_000_000)
    rand = format(random.randint(0, 0xFFFF), "04x")
    return f"{label}.{ts}.{rand}@{TEST_EMAIL_DOMAIN}"


# ---------------------------------------------------------------------------
# Client factories — each call returns a NEW instance (own MCP session)
# ---------------------------------------------------------------------------

def get_live_mcp():
    """Return a new InstantlyMCP(dry_run=False)."""
    from mcp import InstantlyMCP
    return InstantlyMCP(dry_run=False)


def get_dry_mcp():
    """Return a new InstantlyMCP(dry_run=True)."""
    from mcp import InstantlyMCP
    return InstantlyMCP(dry_run=True)


def get_live_api():
    """Return a new InstantlyAPI(dry_run=False)."""
    from api import InstantlyAPI
    return InstantlyAPI(dry_run=False)


def get_dry_api():
    """Return a new InstantlyAPI(dry_run=True)."""
    from api import InstantlyAPI
    return InstantlyAPI(dry_run=True)


# ---------------------------------------------------------------------------
# DB seeding — thread-safe
# ---------------------------------------------------------------------------

_seed_lock = threading.Lock()
_seed_done = False


def ensure_db_seeded():
    """Run seed_db.py if DB is missing or empty. Thread-safe."""
    global _seed_done
    if _seed_done:
        return
    with _seed_lock:
        if _seed_done:
            return
        from config import DB_PATH
        if not DB_PATH.exists():
            import seed_db
            seed_db.main()
        else:
            from db import get_conn
            conn = get_conn()
            row = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()
            conn.close()
            if row[0] == 0:
                import seed_db
                seed_db.main()
        _seed_done = True


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------

def cleanup_instantly_campaigns(mcp):
    """Delete all QA_TEST_* campaigns from Instantly."""
    try:
        result = mcp.list_campaigns(search=TEST_PREFIX, limit=100)
        if isinstance(result, str):
            return  # Empty workspace returns string
        items = result if isinstance(result, list) else result.get("items", result.get("data", []))
        if not isinstance(items, list):
            return
        for c in items:
            cid = c.get("id", "")
            name = c.get("name", "")
            if name.startswith(TEST_PREFIX):
                try:
                    mcp.pause_campaign(cid)
                except Exception:
                    pass
                try:
                    mcp.delete_campaign(cid)
                except Exception:
                    pass
    except Exception:
        pass


def cleanup_instantly_leads(mcp, emails: list):
    """Delete leads by email from Instantly."""
    for email in emails:
        try:
            result = mcp.list_leads(search=email, limit=10)
            if isinstance(result, str):
                continue  # Empty workspace
            items = result if isinstance(result, list) else result.get("items", result.get("data", []))
            if not isinstance(items, list):
                continue
            for lead in items:
                lid = lead.get("id", "")
                if lid:
                    mcp.delete_lead(lid)
        except Exception:
            pass


def cleanup_instantly_lead_lists(mcp):
    """Delete all QA_TEST_* lead lists from Instantly."""
    try:
        result = mcp.list_lead_lists(search=TEST_PREFIX, limit=100)
        if isinstance(result, str):
            return  # Empty workspace returns string
        items = result if isinstance(result, list) else result.get("items", result.get("data", []))
        if not isinstance(items, list):
            return
        for ll in items:
            lid = ll.get("id", "")
            name = ll.get("name", "")
            if name.startswith(TEST_PREFIX):
                try:
                    mcp.delete_lead_list(lid)
                except Exception:
                    pass
    except Exception:
        pass


def cleanup_blocklist_entries(api, entry_ids: list):
    """Delete block list entries by ID."""
    for eid in entry_ids:
        try:
            api.delete_block_list_entry(eid)
        except Exception:
            pass


def cleanup_db_test_rows(conn, campaign_name_prefix=TEST_PREFIX):
    """Remove QA test rows from local DB tables."""
    try:
        # Get campaign IDs matching prefix
        rows = conn.execute(
            "SELECT id FROM campaigns WHERE name LIKE ?",
            (f"{campaign_name_prefix}%",),
        ).fetchall()
        campaign_ids = [r[0] for r in rows]

        for cid in campaign_ids:
            conn.execute("DELETE FROM campaign_contacts WHERE campaign_id = ?", (cid,))
            conn.execute("DELETE FROM metric_snapshots WHERE campaign_id = ?", (cid,))
            conn.execute("DELETE FROM reply_sentiment WHERE campaign_id = ?", (cid,))
            conn.execute("DELETE FROM engagement_events WHERE campaign_id = ?", (cid,))
            conn.execute("DELETE FROM email_threads WHERE campaign_id = ?", (cid,))
            conn.execute("DELETE FROM clay_push_log WHERE campaign_name LIKE ?",
                         (f"{campaign_name_prefix}%",))

        conn.execute("DELETE FROM campaigns WHERE name LIKE ?",
                     (f"{campaign_name_prefix}%",))
        conn.execute("DELETE FROM block_list WHERE value LIKE ?",
                     (f"%{TEST_EMAIL_DOMAIN}%",))
        conn.commit()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# TestResult — thread-safe pass/fail collector
# ---------------------------------------------------------------------------

class TestResult:
    """Collects test pass/fail results. Thread-safe."""

    def __init__(self, suite_name: str):
        self.suite_name = suite_name
        self._results: list[tuple[str, bool, str | None]] = []
        self._lock = threading.Lock()

    def ok(self, name: str) -> None:
        with self._lock:
            self._results.append((name, True, None))

    def fail(self, name: str, err: str | Exception) -> None:
        with self._lock:
            self._results.append((name, False, str(err)))

    @property
    def passed(self) -> int:
        return sum(1 for _, ok, _ in self._results if ok)

    @property
    def failed(self) -> int:
        return sum(1 for _, ok, _ in self._results if not ok)

    @property
    def total(self) -> int:
        return len(self._results)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and self.total > 0

    def summary(self) -> str:
        lines = [f"\n{'=' * 60}", f"  {self.suite_name}", f"{'=' * 60}"]
        for name, ok, err in self._results:
            status = "PASS" if ok else "FAIL"
            line = f"  [{status}] {name}"
            if err:
                # Truncate long errors
                short = err.split("\n")[0][:120]
                line += f"\n         {short}"
            lines.append(line)
        lines.append(f"{'─' * 60}")
        lines.append(f"  {self.passed}/{self.total} passed, {self.failed} failed")
        lines.append(f"{'=' * 60}\n")
        return "\n".join(lines)
