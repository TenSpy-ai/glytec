"""Step 7 — Pull Metrics: fetch analytics and threads from Salesforge."""

import json
import datetime
import requests
from db import get_conn
from config import (
    salesforge_headers,
    workspace_url,
    API_LOG_PATH,
    BOUNCE_THRESHOLD,
    SPAM_THRESHOLD,
)


def _log_api_call(conn, endpoint, method, params, response_code, response_summary):
    """Log API call to both SQLite and markdown file."""
    conn.execute(
        """INSERT INTO api_log (endpoint, method, params, response_code, response_summary)
           VALUES (?, ?, ?, ?, ?)""",
        (endpoint, method, json.dumps(params) if params else None, response_code, response_summary),
    )

    with open(API_LOG_PATH, "a") as f:
        ts = datetime.datetime.now().isoformat()
        f.write(f"\n### {ts}\n")
        f.write(f"- **{method}** `{endpoint}`\n")
        if params:
            f.write(f"- Params: `{json.dumps(params)[:200]}`\n")
        f.write(f"- Response: {response_code} — {response_summary}\n")


def fetch_sequences(conn):
    """Fetch all sequences from Salesforge."""
    endpoint = workspace_url("sequences")
    params = {"limit": 100, "offset": 0}

    resp = requests.get(endpoint, headers=salesforge_headers(), params=params)
    _log_api_call(conn, endpoint, "GET", params, resp.status_code, f"Fetched sequences: {resp.text[:150]}")

    if resp.status_code != 200:
        print(f"[step7] Failed to fetch sequences: HTTP {resp.status_code}")
        return []

    data = resp.json()
    sequences = data if isinstance(data, list) else data.get("sequences", data.get("data", []))
    print(f"[step7] Found {len(sequences)} sequences in Salesforge")
    return sequences


def fetch_analytics(conn, seq_id, seq_name):
    """Fetch analytics for a specific sequence."""
    # Use a 90-day window
    to_date = datetime.date.today().isoformat()
    from_date = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()

    endpoint = workspace_url(f"sequences/{seq_id}/analytics")
    params = {"from_date": from_date, "to_date": to_date}

    resp = requests.get(endpoint, headers=salesforge_headers(), params=params)
    _log_api_call(
        conn, endpoint, "GET", params, resp.status_code,
        f"Analytics for {seq_name}: {resp.text[:150]}",
    )

    if resp.status_code != 200:
        return None

    return resp.json()


def fetch_threads(conn):
    """Fetch recent reply threads."""
    endpoint = workspace_url("threads")
    params = {"limit": 20}

    resp = requests.get(endpoint, headers=salesforge_headers(), params=params)
    _log_api_call(conn, endpoint, "GET", params, resp.status_code, f"Threads: {resp.text[:150]}")

    if resp.status_code != 200:
        print(f"[step7] Failed to fetch threads: HTTP {resp.status_code}")
        return []

    data = resp.json()
    return data if isinstance(data, list) else data.get("threads", data.get("data", []))


def check_kill_switches(analytics, seq_name):
    """Check if any sequences exceed kill-switch thresholds."""
    alerts = []
    if not analytics:
        return alerts

    # Try to extract rates from analytics data
    total_sent = 0
    total_bounced = 0
    total_spam = 0

    if isinstance(analytics, list):
        for day in analytics:
            total_sent += day.get("sent", day.get("emailsSent", 0)) or 0
            total_bounced += day.get("bounced", day.get("bounces", 0)) or 0
            total_spam += day.get("spam", day.get("spamComplaints", 0)) or 0
    elif isinstance(analytics, dict):
        total_sent = analytics.get("totalSent", analytics.get("sent", 0)) or 0
        total_bounced = analytics.get("totalBounced", analytics.get("bounced", 0)) or 0
        total_spam = analytics.get("totalSpam", analytics.get("spam", 0)) or 0

    if total_sent > 0:
        bounce_rate = total_bounced / total_sent
        spam_rate = total_spam / total_sent

        if bounce_rate > BOUNCE_THRESHOLD:
            alerts.append(f"ALERT: {seq_name} bounce rate {bounce_rate:.1%} exceeds {BOUNCE_THRESHOLD:.0%} threshold!")
        if spam_rate > SPAM_THRESHOLD:
            alerts.append(f"ALERT: {seq_name} spam rate {spam_rate:.2%} exceeds {SPAM_THRESHOLD:.1%} threshold!")

    return alerts


def run():
    """Execute step 7."""
    print("\n=== Step 7: Pull Metrics ===")

    # Initialize API log
    with open(API_LOG_PATH, "a") as f:
        f.write(f"\n\n## Step 7 — Pull Metrics\n")
        f.write(f"Run at: {datetime.datetime.now().isoformat()}\n")

    conn = get_conn()
    try:
        # Fetch sequences
        sequences = fetch_sequences(conn)
        if not sequences:
            print("[step7] No sequences found")
            conn.commit()
            return

        all_alerts = []

        print(f"\n{'='*70}")
        print(f"  SALESFORGE SEQUENCE REPORT — {datetime.date.today().isoformat()}")
        print(f"{'='*70}")

        for seq in sequences:
            seq_id = seq.get("id") or seq.get("sequenceId")
            seq_name = seq.get("name", "Unknown")
            status = seq.get("status", "unknown")
            contact_count = seq.get("contactCount", seq.get("contacts", "?"))

            print(f"\n  [{status.upper()}] {seq_name}")
            print(f"    ID: {seq_id}")
            print(f"    Contacts: {contact_count}")

            # Fetch analytics for active/completed sequences
            if seq_id:
                analytics = fetch_analytics(conn, seq_id, seq_name)
                if analytics:
                    # Try to print key metrics
                    if isinstance(analytics, dict):
                        for key in ("totalSent", "totalOpened", "totalReplied", "totalBounced", "totalClicked", "sent", "opened", "replied", "bounced"):
                            val = analytics.get(key)
                            if val is not None:
                                print(f"    {key}: {val}")
                    elif isinstance(analytics, list) and analytics:
                        # Sum up daily analytics
                        totals = {}
                        for day in analytics:
                            for k, v in day.items():
                                if isinstance(v, (int, float)):
                                    totals[k] = totals.get(k, 0) + v
                        for k, v in totals.items():
                            print(f"    {k}: {v}")

                    # Check kill switches
                    alerts = check_kill_switches(analytics, seq_name)
                    all_alerts.extend(alerts)

        # Fetch threads (recent replies)
        print(f"\n{'='*70}")
        print(f"  RECENT THREADS")
        print(f"{'='*70}")
        threads = fetch_threads(conn)
        if threads:
            for t in threads[:10]:
                subject = t.get("subject", t.get("title", "No subject"))
                from_email = t.get("from", t.get("fromEmail", "unknown"))
                print(f"  - {subject} (from: {from_email})")
        else:
            print("  No recent threads found")

        # Print alerts
        if all_alerts:
            print(f"\n{'='*70}")
            print(f"  KILL-SWITCH ALERTS")
            print(f"{'='*70}")
            for alert in all_alerts:
                print(f"  {alert}")
        else:
            print(f"\n  No kill-switch alerts — all sequences within thresholds")

        conn.commit()
        print(f"\n[step7] Done — reviewed {len(sequences)} sequences, {len(threads)} threads")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
