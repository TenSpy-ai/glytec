"""Step 3 — Enrich Contacts: Firecrawl web scraping + pre-filled research results."""

import json
import datetime
from db import get_conn
from config import DRY_RUN, PIPELINE_DIR

# Pre-filled enrichment data for demo — what Firecrawl/Perplexity/Claygent would return
PREFILLED_CONTACTS = [
    # HCA Healthcare
    {"first_name": "Sam", "last_name": "Hazen", "title": "Chief Executive Officer", "company": "HCA Healthcare", "account_name": "HCA Healthcare (FKA Hospital Corporation of America)", "email": "sam.hazen@hcahealthcare.com", "linkedin_url": "https://linkedin.com/in/samhazen", "source": "web_scraping"},
    {"first_name": "Bill", "last_name": "Rutherford", "title": "Chief Financial Officer", "company": "HCA Healthcare", "account_name": "HCA Healthcare (FKA Hospital Corporation of America)", "email": "bill.rutherford@hcahealthcare.com", "linkedin_url": "https://linkedin.com/in/billrutherford", "source": "web_scraping"},
    {"first_name": "Jennifer", "last_name": "Berres", "title": "Chief Nursing Officer", "company": "HCA Healthcare", "account_name": "HCA Healthcare (FKA Hospital Corporation of America)", "email": "jennifer.berres@hcahealthcare.com", "linkedin_url": "https://linkedin.com/in/jenniferberres", "source": "web_scraping"},
    {"first_name": "Michael", "last_name": "Cuffe", "title": "Chief Medical Officer", "company": "HCA Healthcare", "account_name": "HCA Healthcare (FKA Hospital Corporation of America)", "email": "michael.cuffe@hcahealthcare.com", "linkedin_url": "", "source": "web_scraping"},
    # CommonSpirit Health
    {"first_name": "Wright", "last_name": "Lassiter", "title": "Chief Executive Officer", "company": "CommonSpirit Health", "account_name": "CommonSpirit Health", "email": "wright.lassiter@commonspirit.org", "linkedin_url": "https://linkedin.com/in/wrightlassiter", "source": "web_scraping"},
    {"first_name": "Daniel", "last_name": "Morissette", "title": "Chief Financial Officer", "company": "CommonSpirit Health", "account_name": "CommonSpirit Health", "email": "daniel.morissette@commonspirit.org", "linkedin_url": "https://linkedin.com/in/danielmorissette", "source": "web_scraping"},
    {"first_name": "Kathleen", "last_name": "Sanford", "title": "Chief Nursing Officer", "company": "CommonSpirit Health", "account_name": "CommonSpirit Health", "email": "kathleen.sanford@commonspirit.org", "linkedin_url": "https://linkedin.com/in/kathleensanford", "source": "web_scraping"},
    # Ascension Health
    {"first_name": "Joseph", "last_name": "Impicciche", "title": "Chief Executive Officer", "company": "Ascension", "account_name": "Ascension Health", "email": "joseph.impicciche@ascension.org", "linkedin_url": "https://linkedin.com/in/josephimpicciche", "source": "web_scraping"},
    {"first_name": "Robert", "last_name": "Henkel", "title": "Chief Operating Officer", "company": "Ascension", "account_name": "Ascension Health", "email": "robert.henkel@ascension.org", "linkedin_url": "", "source": "web_scraping"},
    {"first_name": "Lisa", "last_name": "Mazzocco", "title": "Chief Quality Officer", "company": "Ascension", "account_name": "Ascension Health", "email": "lisa.mazzocco@ascension.org", "linkedin_url": "https://linkedin.com/in/lisamazzocco", "source": "web_scraping"},
    # Trinity Health
    {"first_name": "Mike", "last_name": "Slubowski", "title": "Chief Executive Officer", "company": "Trinity Health", "account_name": "Trinity Health (FKA CHE Trinity Health)", "email": "mike.slubowski@trinity-health.org", "linkedin_url": "https://linkedin.com/in/mikeslubowski", "source": "web_scraping"},
    {"first_name": "Benjamin", "last_name": "Carter", "title": "Chief Financial Officer", "company": "Trinity Health", "account_name": "Trinity Health (FKA CHE Trinity Health)", "email": "benjamin.carter@trinity-health.org", "linkedin_url": "", "source": "web_scraping"},
    {"first_name": "Patricia", "last_name": "Maryland", "title": "Chief Nursing Officer", "company": "Trinity Health", "account_name": "Trinity Health (FKA CHE Trinity Health)", "email": "patricia.maryland@trinity-health.org", "linkedin_url": "https://linkedin.com/in/patriciamaryland", "source": "web_scraping"},
    # Providence
    {"first_name": "Erik", "last_name": "Wexler", "title": "Chief Executive Officer", "company": "Providence", "account_name": "Providence St Joseph Health (AKA Providence)", "email": "erik.wexler@providence.org", "linkedin_url": "https://linkedin.com/in/erikwexler", "source": "web_scraping"},
    {"first_name": "Greg", "last_name": "Hoffman", "title": "Chief Financial Officer", "company": "Providence", "account_name": "Providence St Joseph Health (AKA Providence)", "email": "greg.hoffman@providence.org", "linkedin_url": "https://linkedin.com/in/greghoffman", "source": "web_scraping"},
    # Tenet Healthcare
    {"first_name": "Saum", "last_name": "Sutaria", "title": "Chief Executive Officer", "company": "Tenet Healthcare", "account_name": "Tenet Healthcare", "email": "saum.sutaria@tenethealth.com", "linkedin_url": "https://linkedin.com/in/saumsutaria", "source": "web_scraping"},
    {"first_name": "Sun", "last_name": "Park", "title": "Chief Financial Officer", "company": "Tenet Healthcare", "account_name": "Tenet Healthcare", "email": "sun.park@tenethealth.com", "linkedin_url": "", "source": "web_scraping"},
    {"first_name": "Andrea", "last_name": "Walsh", "title": "Chief Nursing Officer", "company": "Tenet Healthcare", "account_name": "Tenet Healthcare", "email": "andrea.walsh@tenethealth.com", "linkedin_url": "https://linkedin.com/in/andreawalsh", "source": "web_scraping"},
    # Universal Health Services
    {"first_name": "Marc", "last_name": "Miller", "title": "Chief Executive Officer", "company": "Universal Health Services", "account_name": "Universal Health Services", "email": "marc.miller@uhsinc.com", "linkedin_url": "https://linkedin.com/in/marcmiller", "source": "web_scraping"},
    {"first_name": "Steve", "last_name": "Filton", "title": "Chief Financial Officer", "company": "Universal Health Services", "account_name": "Universal Health Services", "email": "steve.filton@uhsinc.com", "linkedin_url": "https://linkedin.com/in/stevefilton", "source": "web_scraping"},
]

# Pre-filled enrichment signals (what Perplexity/Claygent would find)
ENRICHMENT_SIGNALS = {
    "HCA Healthcare (FKA Hospital Corporation of America)": {
        "ehr_migration": "Oracle Cerner → Oracle Health transition in progress; insulin modules being rebuilt",
        "leadership_change": None,
        "glycemic_initiative": "2025 patient safety goal includes hypoglycemia reduction",
        "financial_note": "Q3 2025 revenue $17.5B; margin pressure from staffing costs",
    },
    "CommonSpirit Health": {
        "ehr_migration": "Epic rollout to remaining 30% of facilities ongoing",
        "leadership_change": "New CNO Kathleen Sanford appointed Oct 2025",
        "glycemic_initiative": "Systemwide glycemic management committee formed Q4 2025",
        "financial_note": "Operating margin recovered to 1.2% in FY2025",
    },
    "Ascension Health": {
        "ehr_migration": "Oracle Cerner standardization across all facilities by mid-2026",
        "leadership_change": None,
        "glycemic_initiative": "CMS quality improvement plan includes glycemic control metrics",
        "financial_note": "Revenue $28.3B but operating loss of $1.8B in FY2025",
    },
    "Trinity Health (FKA CHE Trinity Health)": {
        "ehr_migration": None,
        "leadership_change": None,
        "glycemic_initiative": "RFP for enterprise glycemic management technology issued Dec 2025",
        "financial_note": "Strong margin at 3.1%; investing in tech modernization",
    },
    "Providence St Joseph Health (AKA Providence)": {
        "ehr_migration": "Epic fully deployed but insulin calculator module flagged in Joint Commission audit",
        "leadership_change": None,
        "glycemic_initiative": "Providence Research Network studying inpatient glycemic outcomes",
        "financial_note": "Revenue $29B; capital budget includes clinical decision support tools",
    },
}


def _log_api_call(conn, endpoint, method, params, response_code, response_summary):
    """Log an API call to the api_log table."""
    conn.execute(
        """INSERT INTO api_log (endpoint, method, params, response_code, response_summary)
           VALUES (?, ?, ?, ?, ?)""",
        (endpoint, method, json.dumps(params) if params else None, response_code, response_summary),
    )


def insert_prefilled_contacts(conn):
    """Insert pre-filled demo contacts."""
    inserted = 0
    for contact in PREFILLED_CONTACTS:
        conn.execute(
            """INSERT INTO contacts
               (first_name, last_name, email, title, company, account_name,
                linkedin_url, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                contact["first_name"],
                contact["last_name"],
                contact["email"],
                contact["title"],
                contact["company"],
                contact["account_name"],
                contact["linkedin_url"] or None,
                contact["source"],
            ),
        )
        inserted += 1
    conn.commit()
    print(f"[step3] Inserted {inserted} pre-filled contacts for demo")
    return inserted


def run_firecrawl_enrichment(conn):
    """Simulate Firecrawl scraping for top Priority accounts.

    In production this would call firecrawl_map + firecrawl_scrape via Datagen SDK.
    Here we log what the API calls would be and use pre-filled results.
    """
    # Get top 10 Priority accounts
    accounts = conn.execute(
        """SELECT system_name, score FROM accounts
           WHERE tier = 'Priority' ORDER BY score DESC LIMIT 10"""
    ).fetchall()

    if not accounts:
        print("[step3] No Priority accounts found — skipping Firecrawl enrichment")
        return

    print(f"[step3] Simulating Firecrawl enrichment for {len(accounts)} Priority accounts...")

    for acct in accounts:
        name = acct["system_name"]
        # Simulate the Firecrawl map call
        domain = name.lower().split("(")[0].strip().replace(" ", "") + ".com"
        _log_api_call(
            conn,
            f"firecrawl_map({domain})",
            "POST",
            {"url": f"https://{domain}", "search": "leadership team about us"},
            200,
            f"Simulated — would discover leadership pages for {name}",
        )

        # Simulate the Firecrawl scrape call
        _log_api_call(
            conn,
            f"firecrawl_scrape({domain}/about/leadership)",
            "POST",
            {"url": f"https://{domain}/about/leadership", "formats": ["markdown"]},
            200,
            f"Simulated — would extract names/titles from {name} leadership page",
        )

        # Log enrichment signals
        signals = ENRICHMENT_SIGNALS.get(name)
        if signals:
            for signal_type, signal_value in signals.items():
                if signal_value:
                    print(f"  [{name[:30]}] {signal_type}: {signal_value[:70]}")

    conn.commit()
    print(f"[step3] Firecrawl enrichment logged for {len(accounts)} accounts")


def run():
    """Execute step 3."""
    print("\n=== Step 3: Enrich Contacts ===")
    conn = get_conn()
    try:
        contact_count = insert_prefilled_contacts(conn)
        run_firecrawl_enrichment(conn)
        total = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        print(f"[step3] Done — {total} total contacts in database")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
