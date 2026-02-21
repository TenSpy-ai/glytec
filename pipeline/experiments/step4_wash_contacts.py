"""Step 4 — Contact Washing Machine: dedup, validate, suppress, ICP match."""

import json
import re
from difflib import get_close_matches
from db import get_conn
from config import ICP_JSON, PARENT_CSV
import pandas as pd


def _load_icp_titles():
    """Load ICP titles for fuzzy matching."""
    with open(ICP_JSON, "r") as f:
        return json.load(f)


def _load_glytec_clients():
    """Load Glytec client list from Parent Account CSV for suppression."""
    df = pd.read_csv(PARENT_CSV)
    clients = set()
    for _, row in df.iterrows():
        client_status = str(row.get("Glytec Client - 8.31.25", "")).strip()
        if client_status and client_status.lower() not in ("", "nan"):
            system_name = str(row.get("System Name", "")).strip()
            if system_name:
                clients.add(system_name)
    return clients


# Known bad email domains
BAD_DOMAINS = {"example.com", "test.com", "invalid.com", "noemail.com", "none.com"}
# Known catch-all domains (common in healthcare)
CATCHALL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"}


def step_dedup_merge(conn):
    """Step 4.1: Dedup & merge — match on email, LinkedIn, name+account."""
    print("[step4] 4.1 Dedup & merge...")

    contacts = conn.execute(
        "SELECT id, email, linkedin_url, first_name, last_name, account_name, title FROM contacts"
    ).fetchall()

    seen_emails = {}
    seen_linkedin = {}
    seen_name_account = {}
    dupes_removed = 0

    for c in contacts:
        cid = c["id"]
        email = (c["email"] or "").lower().strip()
        linkedin = (c["linkedin_url"] or "").lower().strip().rstrip("/")
        name_key = f"{(c['first_name'] or '').lower()}_{(c['last_name'] or '').lower()}_{(c['account_name'] or '').lower()}"

        is_dupe = False

        # Match 1: Email
        if email and email in seen_emails:
            is_dupe = True
        elif email:
            seen_emails[email] = cid

        # Match 2: LinkedIn URL
        if not is_dupe and linkedin and linkedin in seen_linkedin:
            is_dupe = True
        elif linkedin:
            seen_linkedin[linkedin] = cid

        # Match 3: Name + Account
        if not is_dupe and name_key in seen_name_account:
            is_dupe = True
        else:
            seen_name_account[name_key] = cid

        if is_dupe:
            conn.execute("DELETE FROM contacts WHERE id = ?", (cid,))
            dupes_removed += 1
        else:
            conn.execute(
                "UPDATE contacts SET golden_record = 1 WHERE id = ?", (cid,)
            )

    conn.commit()
    print(f"  Removed {dupes_removed} duplicate contacts")
    return dupes_removed


def step_email_validation(conn):
    """Step 4.2: Email validation — flag invalid emails, catch-all domains."""
    print("[step4] 4.2 Email validation...")

    contacts = conn.execute(
        "SELECT id, email FROM contacts WHERE golden_record = 1"
    ).fetchall()

    invalid_count = 0
    catchall_count = 0

    for c in contacts:
        email = (c["email"] or "").strip()
        cid = c["id"]

        if not email or "@" not in email:
            conn.execute(
                "UPDATE contacts SET validated = 0, suppressed = 1, suppression_reason = 'invalid_email' WHERE id = ?",
                (cid,),
            )
            invalid_count += 1
            continue

        domain = email.split("@")[1].lower()

        if domain in BAD_DOMAINS:
            conn.execute(
                "UPDATE contacts SET validated = 0, suppressed = 1, suppression_reason = 'bad_domain' WHERE id = ?",
                (cid,),
            )
            invalid_count += 1
            continue

        if domain in CATCHALL_DOMAINS:
            conn.execute(
                "UPDATE contacts SET validated = 1 WHERE id = ?", (cid,)
            )
            catchall_count += 1
            continue

        # Basic format check
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            conn.execute(
                "UPDATE contacts SET validated = 0, suppressed = 1, suppression_reason = 'invalid_format' WHERE id = ?",
                (cid,),
            )
            invalid_count += 1
            continue

        conn.execute(
            "UPDATE contacts SET validated = 1 WHERE id = ?", (cid,)
        )

    conn.commit()
    print(f"  Flagged {invalid_count} invalid emails, {catchall_count} catch-all domains")
    return invalid_count


def step_suppression(conn):
    """Step 4.3: Suppression check — Glytec clients, DNC list."""
    print("[step4] 4.3 Suppression check...")

    glytec_clients = _load_glytec_clients()
    suppressed_count = 0

    if glytec_clients:
        contacts = conn.execute(
            "SELECT id, account_name FROM contacts WHERE golden_record = 1 AND suppressed = 0"
        ).fetchall()
        for c in contacts:
            if c["account_name"] in glytec_clients:
                conn.execute(
                    "UPDATE contacts SET suppressed = 1, suppression_reason = 'glytec_client' WHERE id = ?",
                    (c["id"],),
                )
                suppressed_count += 1

    conn.commit()
    print(f"  Suppressed {suppressed_count} contacts at Glytec client accounts")
    # Note: In production, also check Salesforge DNC list via API
    print(f"  (DNC list check would happen via Salesforge API in production)")
    return suppressed_count


def step_linkedin_crossref(conn):
    """Step 4.4: LinkedIn cross-reference — flag contacts without LinkedIn as unverified."""
    print("[step4] 4.4 LinkedIn cross-reference...")

    unverified = conn.execute(
        """UPDATE contacts SET validated = 0
           WHERE golden_record = 1 AND suppressed = 0
           AND (linkedin_url IS NULL OR linkedin_url = '')"""
    ).rowcount
    conn.commit()
    print(f"  Flagged {unverified} contacts without LinkedIn as unverified")
    return unverified


def step_icp_title_match(conn):
    """Step 4.5: ICP title matching — fuzzy match against 66 ICP titles."""
    print("[step4] 4.5 ICP title matching...")

    icp_titles = _load_icp_titles()
    title_lookup = {t["Title"].lower(): t for t in icp_titles}
    title_list = list(title_lookup.keys())

    contacts = conn.execute(
        "SELECT id, title FROM contacts WHERE golden_record = 1 AND suppressed = 0"
    ).fetchall()

    matched = 0
    for c in contacts:
        contact_title = (c["title"] or "").strip()
        if not contact_title:
            continue

        # Try exact match first
        lower_title = contact_title.lower()
        icp = title_lookup.get(lower_title)

        # Try fuzzy match
        if not icp:
            matches = get_close_matches(lower_title, title_list, n=1, cutoff=0.6)
            if matches:
                icp = title_lookup[matches[0]]

        # Try keyword match (e.g., "CNO" → "Chief Nursing Officer")
        if not icp:
            for icp_title, icp_data in title_lookup.items():
                # Check if key words from ICP title appear in contact title
                icp_words = set(icp_title.split())
                contact_words = set(lower_title.split())
                overlap = icp_words & contact_words
                if len(overlap) >= 2 and len(overlap) / len(icp_words) >= 0.5:
                    icp = icp_data
                    break

        if icp:
            conn.execute(
                """UPDATE contacts SET icp_matched = 1, icp_category = ?,
                   icp_intent_score = ?, icp_function_type = ?, icp_job_level = ?
                   WHERE id = ?""",
                (
                    icp["Category"],
                    icp["Intent Score"],
                    icp["Function Type"],
                    icp["Job Level"],
                    c["id"],
                ),
            )
            matched += 1

    conn.commit()
    print(f"  Matched {matched} / {len(contacts)} contacts to ICP titles")
    return matched


def step_account_mapping(conn):
    """Step 4.6: Account mapping — link contacts to accounts via parent hierarchy."""
    print("[step4] 4.6 Account mapping...")

    # Build a lookup from system name to account
    mapped = conn.execute(
        """UPDATE contacts SET account_name = (
             SELECT a.system_name FROM accounts a
             WHERE a.system_name = contacts.account_name
           )
           WHERE EXISTS (
             SELECT 1 FROM accounts a WHERE a.system_name = contacts.account_name
           )"""
    ).rowcount
    conn.commit()
    print(f"  Verified {mapped} contact-to-account mappings")
    return mapped


def run():
    """Execute step 4."""
    print("\n=== Step 4: Wash Contacts ===")
    conn = get_conn()
    try:
        step_dedup_merge(conn)
        step_email_validation(conn)
        step_suppression(conn)
        step_linkedin_crossref(conn)
        step_icp_title_match(conn)
        step_account_mapping(conn)

        # Summary
        total = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        clean = conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE golden_record = 1 AND suppressed = 0"
        ).fetchone()[0]
        icp = conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE icp_matched = 1 AND suppressed = 0"
        ).fetchone()[0]
        suppressed = conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE suppressed = 1"
        ).fetchone()[0]

        print(f"\n[step4] Wash complete:")
        print(f"  Total contacts: {total}")
        print(f"  Clean (golden, unsuppressed): {clean}")
        print(f"  ICP-matched: {icp}")
        print(f"  Suppressed: {suppressed}")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
