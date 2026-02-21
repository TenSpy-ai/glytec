"""
GTM Hello World — Status Dashboard
Reads DB and prints formatted status report.

Usage:
    python check_status.py
"""

import sqlite3

from config import DB_PATH
from db import get_conn


def report_accounts(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("ACCOUNTS")
    print("=" * 60)
    rows = conn.execute(
        "SELECT system_name, segment, total_beds, primary_ehr, score, tier, total_opp "
        "FROM accounts ORDER BY score DESC"
    ).fetchall()
    if not rows:
        print("  (no accounts)")
        return
    print(f"  {'System':<30s} {'Beds':>6s} {'EHR':<10s} {'Score':>5s} {'Tier':<8s} {'Opp $':>12s}")
    print(f"  {'-'*30} {'-'*6} {'-'*10} {'-'*5} {'-'*8} {'-'*12}")
    for r in rows:
        opp = f"${r['total_opp']:,.0f}" if r["total_opp"] else "—"
        print(f"  {r['system_name']:<30s} {r['total_beds'] or 0:>6d} {r['primary_ehr'] or '':>10s} "
              f"{r['score'] or 0:>5.0f} {r['tier'] or '':<8s} {opp:>12s}")
    print(f"\n  Total: {len(rows)} accounts\n")


def report_contacts(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("CONTACTS")
    print("=" * 60)
    rows = conn.execute(
        "SELECT first_name, last_name, title, account_name, email, icp_intent_score "
        "FROM contacts ORDER BY icp_intent_score DESC"
    ).fetchall()
    if not rows:
        print("  (no contacts)")
        return
    print(f"  {'Name':<25s} {'Title':<25s} {'Account':<25s} {'Intent':>6s}")
    print(f"  {'-'*25} {'-'*25} {'-'*25} {'-'*6}")
    for r in rows:
        name = f"{r['first_name']} {r['last_name']}"
        print(f"  {name:<25s} {r['title']:<25s} {r['account_name']:<25s} {r['icp_intent_score']:>6d}")
    print(f"\n  Total: {len(rows)} contacts\n")


def report_campaigns(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("CAMPAIGNS")
    print("=" * 60)
    rows = conn.execute(
        "SELECT name, recipe, status, instantly_status, target_persona, step_count, daily_limit "
        "FROM campaigns ORDER BY id"
    ).fetchall()
    if not rows:
        print("  (no campaigns yet — create one using PROCESS.md)\n")
        return
    for r in rows:
        print(f"  [{r['status']}] {r['name']} (recipe {r['recipe']})")
        print(f"    Persona: {r['target_persona']} | Steps: {r['step_count']} | Daily limit: {r['daily_limit']}")
    print(f"\n  Total: {len(rows)} campaigns\n")


def report_metrics(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("METRIC SNAPSHOTS")
    print("=" * 60)
    rows = conn.execute(
        "SELECT m.snapshot_date, c.name AS campaign_name, m.sent, m.opened, m.replied, m.bounced, "
        "m.open_rate, m.reply_rate, m.bounce_rate "
        "FROM metric_snapshots m LEFT JOIN campaigns c ON m.campaign_id = c.id "
        "ORDER BY m.snapshot_date DESC LIMIT 10"
    ).fetchall()
    if not rows:
        print("  (no metrics yet — run pull_metrics.py)\n")
        return
    print(f"  {'Date':<12s} {'Campaign':<30s} {'Sent':>5s} {'Open':>5s} {'Reply':>5s} {'Bnce':>5s} {'Open%':>6s} {'Bnce%':>6s}")
    print(f"  {'-'*12} {'-'*30} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*6} {'-'*6}")
    for r in rows:
        open_pct = f"{r['open_rate']*100:.1f}%" if r["open_rate"] else "—"
        bnce_pct = f"{r['bounce_rate']*100:.1f}%" if r["bounce_rate"] else "—"
        print(f"  {r['snapshot_date']:<12s} {(r['campaign_name'] or '—'):<30s} "
              f"{r['sent']:>5d} {r['opened']:>5d} {r['replied']:>5d} {r['bounced']:>5d} {open_pct:>6s} {bnce_pct:>6s}")
    print()


def report_replies(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("REPLY SENTIMENT")
    print("=" * 60)
    rows = conn.execute(
        "SELECT sentiment, COUNT(*) as cnt, "
        "SUM(CASE WHEN pushed_to_clay = 1 THEN 1 ELSE 0 END) as pushed "
        "FROM reply_sentiment GROUP BY sentiment ORDER BY cnt DESC"
    ).fetchall()
    if not rows:
        print("  (no replies classified yet — run process_replies.py)\n")
        return
    for r in rows:
        print(f"  {r['sentiment']:<12s} {r['cnt']:>4d} total, {r['pushed']:>4d} pushed to Clay")
    print()


def report_engagement(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("ENGAGEMENT EVENTS (last 10)")
    print("=" * 60)
    rows = conn.execute(
        "SELECT event_type, contact_email, event_date, source "
        "FROM engagement_events ORDER BY event_date DESC LIMIT 10"
    ).fetchall()
    if not rows:
        print("  (no engagement events yet)\n")
        return
    for r in rows:
        print(f"  [{r['event_type']}] {r['contact_email']} @ {r['event_date']} ({r['source']})")
    print()


def report_api_activity(conn: sqlite3.Connection) -> None:
    print("=" * 60)
    print("API ACTIVITY (last 10)")
    print("=" * 60)
    rows = conn.execute(
        "SELECT timestamp, interface, tool_or_endpoint, response_code, duration_ms "
        "FROM api_log ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()
    if not rows:
        print("  (no API calls logged yet)\n")
        return
    for r in rows:
        code = r["response_code"] or "—"
        ms = f"{r['duration_ms']}ms" if r["duration_ms"] else "—"
        print(f"  {r['timestamp']} [{r['interface']}] {r['tool_or_endpoint']} -> {code} ({ms})")
    print()


def main() -> None:
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python seed_db.py")
        return

    conn = get_conn()
    try:
        print(f"\nGTM Hello World — Status Dashboard")
        print(f"Database: {DB_PATH}\n")

        report_accounts(conn)
        report_contacts(conn)
        report_campaigns(conn)
        report_metrics(conn)
        report_replies(conn)
        report_engagement(conn)
        report_api_activity(conn)

        # Mailbox summary
        print("=" * 60)
        print("MAILBOXES")
        print("=" * 60)
        rows = conn.execute(
            "SELECT email, daily_limit, status, warmup_status, warmup_score FROM mailboxes ORDER BY email"
        ).fetchall()
        if not rows:
            print("  (no mailboxes)")
        else:
            for r in rows:
                status = "Active" if r["status"] == 1 else "Inactive"
                warmup = "Warmed" if r["warmup_status"] == 1 else "Not warmed"
                print(f"  {r['email']:<40s} {status} | {warmup} | Score: {r['warmup_score']}")
        print()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
