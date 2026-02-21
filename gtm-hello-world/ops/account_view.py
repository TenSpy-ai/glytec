"""
GTM Hello World — Account View
Shows account details + contacts + engagement from local DB.

Usage:
    python -m ops.account_view "HCA"            # Search by system name
    python -m ops.account_view --all             # List all accounts
"""

import sys

from config import DB_PATH
from db import get_conn


def find_account(conn, query: str) -> dict | None:
    """Find an account by system name (partial match)."""
    row = conn.execute(
        "SELECT * FROM accounts WHERE system_name LIKE ? ORDER BY score DESC LIMIT 1",
        (f"%{query}%",),
    ).fetchone()
    return dict(row) if row else None


def get_contacts_for_account(conn, system_name: str) -> list:
    """Get all contacts at an account."""
    rows = conn.execute(
        "SELECT * FROM contacts WHERE account_name = ? ORDER BY icp_intent_score DESC",
        (system_name,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_campaigns_for_account(conn, system_name: str) -> list:
    """Get campaigns that have contacts from this account enrolled."""
    rows = conn.execute(
        """SELECT DISTINCT camp.name, camp.recipe, camp.status, camp.instantly_status,
                  COUNT(cc.id) as enrolled_count
           FROM campaigns camp
           JOIN campaign_contacts cc ON camp.id = cc.campaign_id
           JOIN contacts c ON cc.contact_id = c.id
           WHERE c.account_name = ?
           GROUP BY camp.id
           ORDER BY camp.id""",
        (system_name,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_engagement_for_account(conn, system_name: str) -> list:
    """Get recent engagement events for contacts at this account."""
    rows = conn.execute(
        """SELECT ee.event_type, ee.contact_email, ee.event_date, ee.source
           FROM engagement_events ee
           JOIN contacts c ON ee.contact_email = c.email
           WHERE c.account_name = ?
           ORDER BY ee.event_date DESC LIMIT 10""",
        (system_name,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_sentiment_for_account(conn, system_name: str) -> list:
    """Get reply sentiment for contacts at this account."""
    rows = conn.execute(
        """SELECT rs.contact_email, rs.sentiment, rs.sentiment_confidence,
                  rs.pushed_to_clay, rs.created_at
           FROM reply_sentiment rs
           JOIN contacts c ON rs.contact_email = c.email
           WHERE c.account_name = ?
           ORDER BY rs.created_at DESC""",
        (system_name,),
    ).fetchall()
    return [dict(r) for r in rows]


def print_account_detail(account: dict, contacts: list, campaigns: list,
                         engagement: list, sentiment: list) -> None:
    """Print full account view."""
    print(f"\n  {'='*60}")
    print(f"  {account['system_name']}")
    print(f"  {'='*60}")
    print(f"  Segment:    {account.get('segment', '—')}")
    print(f"  Total Beds: {account.get('total_beds', '—'):,}")
    print(f"  EHR:        {account.get('primary_ehr', '—')}")
    print(f"  Score:      {account.get('score', '—')}")
    print(f"  Tier:       {account.get('tier', '—')}")
    opp = account.get("total_opp")
    print(f"  Total Opp:  ${opp:,.0f}" if opp else "  Total Opp:  —")
    print(f"  Rep:        {account.get('assigned_rep', '—')}")

    # Contacts
    print(f"\n  --- Contacts ({len(contacts)}) ---")
    if contacts:
        for c in contacts:
            name = f"{c.get('first_name', '')} {c.get('last_name', '')}"
            verified = c.get("email_verified", "—")
            print(f"  {name:<25s} {c.get('title', '—'):<25s} "
                  f"{c.get('email', '—'):<35s} ICP:{c.get('icp_intent_score', 0)} "
                  f"V:{verified}")
    else:
        print("  (no contacts)")

    # Campaigns
    print(f"\n  --- Campaigns ({len(campaigns)}) ---")
    if campaigns:
        for camp in campaigns:
            print(f"  [{camp.get('status', '—')}] {camp.get('name', '—')} "
                  f"({camp.get('recipe', '—')}) — {camp.get('enrolled_count', 0)} enrolled")
    else:
        print("  (no campaigns)")

    # Sentiment
    print(f"\n  --- Reply Sentiment ({len(sentiment)}) ---")
    if sentiment:
        for s in sentiment:
            clay = "→ Clay" if s.get("pushed_to_clay") else ""
            print(f"  [{s['sentiment']}] {s['contact_email']} "
                  f"(conf: {s.get('sentiment_confidence', 0):.2f}) {clay}")
    else:
        print("  (no replies)")

    # Engagement
    print(f"\n  --- Recent Engagement ({len(engagement)}) ---")
    if engagement:
        for e in engagement:
            print(f"  [{e['event_type']}] {e['contact_email']} "
                  f"@ {e.get('event_date', '—')} ({e.get('source', '—')})")
    else:
        print("  (no engagement events)")


def list_all_accounts(conn) -> None:
    """Print summary of all accounts."""
    rows = conn.execute(
        "SELECT system_name, segment, total_beds, primary_ehr, score, tier, total_opp "
        "FROM accounts ORDER BY score DESC"
    ).fetchall()

    print(f"  {'System':<30s} {'Beds':>6s} {'EHR':<10s} {'Score':>5s} {'Tier':<8s} {'Opp $':>12s}")
    print(f"  {'-'*30} {'-'*6} {'-'*10} {'-'*5} {'-'*8} {'-'*12}")
    for r in rows:
        opp = f"${r['total_opp']:,.0f}" if r["total_opp"] else "—"
        print(f"  {r['system_name']:<30s} {r['total_beds'] or 0:>6d} "
              f"{r['primary_ehr'] or '':>10s} {r['score'] or 0:>5.0f} "
              f"{r['tier'] or '':<8s} {opp:>12s}")
    print(f"\n  Total: {len(rows)} accounts")


def main() -> None:
    args = sys.argv[1:]

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run: python seed_db.py")
        return

    conn = get_conn()
    try:
        print("\nGTM Hello World — Account View\n")

        if not args or args[0] == "--all":
            list_all_accounts(conn)
            return

        query = " ".join(args)
        account = find_account(conn, query)
        if not account:
            print(f"  No account matching '{query}'")
            print("\n  Available accounts:")
            list_all_accounts(conn)
            return

        contacts = get_contacts_for_account(conn, account["system_name"])
        campaigns = get_campaigns_for_account(conn, account["system_name"])
        engagement = get_engagement_for_account(conn, account["system_name"])
        sentiment = get_sentiment_for_account(conn, account["system_name"])

        print_account_detail(account, contacts, campaigns, engagement, sentiment)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
