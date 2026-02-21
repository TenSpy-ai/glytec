"""Search contacts — multi-field local search (API filters broken).

Usage:
    python -m salesforge.ops.search_contacts --name "John"
    python -m salesforge.ops.search_contacts --email "john@example.com"
    python -m salesforge.ops.search_contacts --account "HCA"
    python -m salesforge.ops.search_contacts --icp "Decision Maker"
    python -m salesforge.ops.search_contacts --title "CNO"
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_conn


def search_contacts(name=None, email=None, account=None, icp=None,
                    title=None, limit=25):
    """Search local contacts database. API filters are broken — always search locally."""
    conn = get_conn()

    try:
        conditions = ["1=1"]
        params = []

        if name:
            conditions.append("(c.first_name LIKE ? OR c.last_name LIKE ? OR (c.first_name || ' ' || c.last_name) LIKE ?)")
            params.extend([f"%{name}%", f"%{name}%", f"%{name}%"])
        if email:
            conditions.append("c.email LIKE ?")
            params.append(f"%{email}%")
        if account:
            conditions.append("c.account_name LIKE ?")
            params.append(f"%{account}%")
        if icp:
            conditions.append("(c.icp_category LIKE ? OR c.icp_function_type LIKE ?)")
            params.extend([f"%{icp}%", f"%{icp}%"])
        if title:
            conditions.append("c.title LIKE ?")
            params.append(f"%{title}%")

        where = " AND ".join(conditions)
        query = f"""
            SELECT c.*, a.tier, a.score
            FROM contacts c
            LEFT JOIN accounts a ON c.account_name = a.system_name
            WHERE {where}
            ORDER BY c.icp_intent_score DESC NULLS LAST
            LIMIT ?
        """
        params.append(limit)

        results = conn.execute(query, params).fetchall()

        if not results:
            print("No contacts found matching your search.")
            return

        print(f"\n{'='*80}")
        print(f"  CONTACT SEARCH — {len(results)} results")
        print(f"{'='*80}\n")

        for c in results:
            suppressed_flag = " [SUPPRESSED]" if c["suppressed"] else ""
            icp_flag = f" | ICP: {c['icp_category']}" if c["icp_category"] else ""
            tier_flag = f" | Tier: {c['tier']}" if c["tier"] else ""
            print(f"  {c['first_name']} {c['last_name']} <{c['email']}>{suppressed_flag}")
            print(f"    Title: {c['title'] or '-'} | Company: {c['company'] or '-'}")
            print(f"    Account: {c['account_name'] or '-'}{tier_flag}{icp_flag}")
            if c["linkedin_url"]:
                print(f"    LinkedIn: {c['linkedin_url']}")
            print()

    finally:
        conn.close()


def auto_search(query_string):
    """Auto-detect search type from a free-text query."""
    q = query_string.strip()
    if "@" in q:
        search_contacts(email=q)
    elif q.upper() in ("DECISION MAKER", "INFLUENCER", "CLINICAL", "BUSINESS"):
        search_contacts(icp=q)
    elif any(kw in q.upper() for kw in ("CNO", "CFO", "CEO", "COO", "CMO", "CQO", "DIRECTOR", "VP")):
        search_contacts(title=q)
    else:
        # Try as name first, then account
        search_contacts(name=q)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name")
    parser.add_argument("--email")
    parser.add_argument("--account")
    parser.add_argument("--icp")
    parser.add_argument("--title")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("query", nargs="*", help="Free-text search (auto-detects type)")
    args = parser.parse_args()

    if args.name or args.email or args.account or args.icp or args.title:
        search_contacts(name=args.name, email=args.email, account=args.account,
                        icp=args.icp, title=args.title, limit=args.limit)
    elif args.query:
        auto_search(" ".join(args.query))
    else:
        print("Usage: search_contacts.py [--name X] [--email X] [--account X] [--icp X] [--title X] or free text")
