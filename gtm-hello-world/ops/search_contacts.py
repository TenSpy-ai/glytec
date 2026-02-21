"""
GTM Hello World — Search Contacts
Searches local DB + Instantly for contacts by email, name, account, ICP, or title.

Usage:
    python -m ops.search_contacts "HCA"                  # Search by account
    python -m ops.search_contacts "steven.dickson"        # Search by email/name
    python -m ops.search_contacts --icp "Decision Maker"  # Search by ICP category
    python -m ops.search_contacts --title "CNO"           # Search by title
"""

import sys

from config import DB_PATH
from db import get_conn
from mcp import InstantlyMCP, MCPError


def search_local_db(conn, query: str, icp: str | None = None,
                    title: str | None = None) -> list:
    """Search contacts in local DB. Auto-detects email vs name vs account."""
    if icp:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE icp_category LIKE ? ORDER BY icp_intent_score DESC",
            (f"%{icp}%",),
        ).fetchall()
    elif title:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE title LIKE ? ORDER BY icp_intent_score DESC",
            (f"%{title}%",),
        ).fetchall()
    elif "@" in query:
        # Email search
        rows = conn.execute(
            "SELECT * FROM contacts WHERE email LIKE ? ORDER BY icp_intent_score DESC",
            (f"%{query}%",),
        ).fetchall()
    else:
        # Name or account search
        rows = conn.execute(
            """SELECT * FROM contacts
               WHERE first_name LIKE ? OR last_name LIKE ?
                  OR account_name LIKE ? OR company_name LIKE ?
               ORDER BY icp_intent_score DESC""",
            (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"),
        ).fetchall()

    return [dict(r) for r in rows]


def search_instantly(mcp: InstantlyMCP, query: str) -> list:
    """Search leads in Instantly via MCP (filters work!)."""
    try:
        result = mcp.list_leads(search=query, limit=20)
        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = result.get("data", result.get("items", []))
        return items
    except MCPError:
        return []


def print_local_results(contacts: list) -> None:
    """Print local DB search results."""
    if not contacts:
        print("  (no matches in local DB)")
        return

    print(f"  {'Name':<25s} {'Title':<25s} {'Account':<25s} {'Email':<35s} {'ICP':>4s}")
    print(f"  {'-'*25} {'-'*25} {'-'*25} {'-'*35} {'---':>4s}")
    for c in contacts:
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}"
        print(f"  {name:<25s} {(c.get('title') or '—'):<25s} "
              f"{(c.get('account_name') or '—'):<25s} "
              f"{(c.get('email') or '—'):<35s} {c.get('icp_intent_score', 0):>4d}")


def print_instantly_results(leads: list) -> None:
    """Print Instantly search results."""
    if not leads:
        print("  (no matches in Instantly)")
        return

    print(f"  {'Email':<35s} {'Name':<25s} {'Company':<25s} {'Status':<10s}")
    print(f"  {'-'*35} {'-'*25} {'-'*25} {'-'*10}")
    for lead in leads:
        email = lead.get("email", "—")[:35]
        name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
        company = (lead.get("company_name") or "—")[:25]
        status = lead.get("lead_status", lead.get("status", "—"))
        print(f"  {email:<35s} {name:<25s} {company:<25s} {str(status):<10s}")


def check_campaign_enrollment(mcp: InstantlyMCP, email: str) -> None:
    """Check which campaigns a contact is enrolled in."""
    try:
        campaigns = mcp.search_campaigns_by_contact(email)
        if campaigns:
            print(f"\n--- Campaign Enrollment for {email} ---")
            for c in campaigns:
                name = c.get("name", c.get("campaign_name", "—"))
                print(f"  {name}")
        else:
            print(f"\n  {email} — not enrolled in any campaigns")
    except MCPError:
        pass


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m ops.search_contacts <query>")
        print("  <query>     — email, name, or account to search")
        print("  --icp <cat> — filter by ICP category")
        print("  --title <t> — filter by title")
        return

    # Parse args
    icp = None
    title = None
    query_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--icp" and i + 1 < len(args):
            icp = args[i + 1]
            i += 2
        elif args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        else:
            query_parts.append(args[i])
            i += 1
    query = " ".join(query_parts)

    mcp = InstantlyMCP()

    print(f"\nGTM Hello World — Search Contacts")
    print(f"Query: {query or icp or title}\n")

    # Local DB search
    if DB_PATH.exists():
        conn = get_conn()
        print("--- Local DB Results ---")
        local = search_local_db(conn, query, icp=icp, title=title)
        print_local_results(local)
        print(f"  ({len(local)} matches)")
        conn.close()

        # Check campaign enrollment for email matches
        if local and "@" in query:
            check_campaign_enrollment(mcp, query)

    # Instantly search (only for non-ICP/title queries)
    if query and not icp and not title:
        print("\n--- Instantly Results ---")
        instantly_results = search_instantly(mcp, query)
        print_instantly_results(instantly_results)
        print(f"  ({len(instantly_results)} matches)")


if __name__ == "__main__":
    main()
