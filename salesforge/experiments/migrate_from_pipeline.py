"""Migrate data from pipeline/glytec_v1.db to salesforge/db/gtm_ops.db.

Copies accounts, facilities, and contacts from the V1 pipeline database
into the new 16-table GTM Operations schema.
"""

import sqlite3
import sys
from pathlib import Path

# Ensure imports work when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import PIPELINE_DB_PATH, DB_PATH
from db import init_db, get_conn


def migrate():
    """Copy accounts, facilities, and contacts from pipeline DB."""
    if not PIPELINE_DB_PATH.exists():
        print(f"[migrate] Pipeline DB not found at {PIPELINE_DB_PATH}")
        print(f"[migrate] Run the pipeline first: cd pipeline && python step1_load_data.py")
        return

    # Ensure target DB exists
    init_db()

    src = sqlite3.connect(str(PIPELINE_DB_PATH))
    src.row_factory = sqlite3.Row
    dst = get_conn()

    try:
        # --- Accounts ---
        src_accounts = src.execute("SELECT * FROM accounts").fetchall()
        migrated_accounts = 0
        for a in src_accounts:
            try:
                dst.execute(
                    """INSERT OR IGNORE INTO accounts
                       (system_name, definitive_id, sfdc_account_id, city, state, segment,
                        facility_count, total_beds, avg_beds_per_facility,
                        glytec_client, glytec_arr, gc_opp, cc_opp, total_opp, adj_total_opp,
                        rank, score, tier)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (a["system_name"], a["definitive_id"], a["sfdc_account_id"],
                     a["city"], a["state"], a["segment"],
                     a["facility_count"], a["total_beds"], a["avg_beds_per_facility"],
                     a["glytec_client"], a["glytec_arr"], a["gc_opp"], a["cc_opp"],
                     a["total_opp"], a["adj_total_opp"], a["rank"], a["score"], a["tier"]),
                )
                migrated_accounts += 1
            except Exception as e:
                pass  # Skip on conflict
        dst.commit()
        print(f"[migrate] Accounts: {migrated_accounts} migrated")

        # --- Facilities ---
        src_facilities = src.execute("SELECT * FROM facilities").fetchall()
        migrated_facilities = 0
        for f in src_facilities:
            try:
                dst.execute(
                    """INSERT OR IGNORE INTO facilities
                       (hospital_name, definitive_id, highest_level_parent, city, state,
                        firm_type, hospital_type, ehr_inpatient, staffed_beds,
                        net_operating_profit_margin, cms_overall_rating, readmission_rate,
                        avg_length_of_stay, icu_beds, net_patient_revenue, assigned_rep,
                        hospital_ownership)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f["hospital_name"], f["definitive_id"], f["highest_level_parent"],
                     f["city"], f["state"], f["firm_type"], f["hospital_type"],
                     f["ehr_inpatient"], f["staffed_beds"], f["net_operating_profit_margin"],
                     f["cms_overall_rating"], f["readmission_rate"], f["avg_length_of_stay"],
                     f["icu_beds"], f["net_patient_revenue"], f["assigned_rep"],
                     f["hospital_ownership"] if "hospital_ownership" in f.keys() else None),
                )
                migrated_facilities += 1
            except Exception:
                pass
        dst.commit()
        print(f"[migrate] Facilities: {migrated_facilities} migrated")

        # --- Contacts ---
        src_contacts = src.execute("SELECT * FROM contacts").fetchall()
        migrated_contacts = 0
        src_cols = [desc[0] for desc in src.execute("SELECT * FROM contacts LIMIT 1").description]
        for c in src_contacts:
            try:
                dst.execute(
                    """INSERT OR IGNORE INTO contacts
                       (first_name, last_name, email, title, company, linkedin_url,
                        account_name, facility_definitive_id,
                        icp_category, icp_intent_score, icp_function_type, icp_job_level,
                        icp_matched, source, validated, golden_record,
                        suppressed, suppression_reason)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (c["first_name"], c["last_name"], c["email"], c["title"],
                     c["company"], c["linkedin_url"], c["account_name"],
                     c["facility_definitive_id"],
                     c["icp_category"], c["icp_intent_score"],
                     c["icp_function_type"], c["icp_job_level"],
                     c["icp_matched"], c["source"], c["validated"], c["golden_record"],
                     c["suppressed"], c["suppression_reason"]),
                )
                migrated_contacts += 1
            except Exception:
                pass
        dst.commit()
        print(f"[migrate] Contacts: {migrated_contacts} migrated")

        # Summary
        total_accounts = dst.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        total_facilities = dst.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
        total_contacts = dst.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        total_icp = dst.execute("SELECT COUNT(*) FROM icp_titles").fetchone()[0]
        print(f"\n[migrate] GTM Ops DB summary:")
        print(f"  Accounts:   {total_accounts}")
        print(f"  Facilities: {total_facilities}")
        print(f"  Contacts:   {total_contacts}")
        print(f"  ICP Titles: {total_icp}")

    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    migrate()
