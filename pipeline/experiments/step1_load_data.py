"""Step 1 — Load CSVs into SQLite (replaces 'data enters Clay')."""

import json
import re
import pandas as pd
from db import init_db, get_conn
from config import FACILITY_CSV, SUPPLEMENTAL_CSV, PARENT_CSV, ICP_CSV, ICP_JSON


def _parse_currency(val):
    """Parse strings like '$19,851,766' or '$-' into float."""
    if pd.isna(val):
        return None
    s = str(val).strip().replace("$", "").replace(",", "").strip()
    if s in ("", "-", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_int(val):
    """Parse strings like '191' or '38,726' into int."""
    if pd.isna(val):
        return None
    s = str(val).strip().replace(",", "").strip()
    if s in ("", "-", "—"):
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_float(val):
    """Parse numeric strings, stripping % signs."""
    if pd.isna(val):
        return None
    s = str(val).strip().replace("%", "").replace(",", "").replace("$", "").strip()
    if s in ("", "-", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_parent_accounts(conn):
    """Load Parent Account List CSV into accounts table."""
    df = pd.read_csv(PARENT_CSV)
    inserted = 0
    for _, row in df.iterrows():
        system_name = str(row.get("System Name", "")).strip()
        if not system_name:
            continue
        conn.execute(
            """INSERT OR IGNORE INTO accounts
               (system_name, definitive_id, sfdc_account_id, city, state,
                segment, facility_count, total_beds, avg_beds_per_facility,
                glytec_client, glytec_arr, gc_opp, cc_opp, total_opp,
                adj_total_opp, rank)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                system_name,
                str(row.get("Definitive ID (validate!!)", "")).strip() or None,
                str(row.get("SFDC Account ID", "")).strip() or None,
                str(row.get("City", "")).strip() or None,
                str(row.get("State", "")).strip() or None,
                str(row.get("Segment", "")).strip() or None,
                _parse_int(row.get("Facilities")),
                _parse_int(row.get("Beds")),
                _parse_float(row.get("Avg. Beds/Facility")),
                str(row.get("Glytec Client - 8.31.25", "")).strip() or None,
                _parse_currency(row.get("Glytec ARR - 8.31.25")),
                _parse_currency(row.get("GC $ Opp")),
                _parse_currency(row.get("CC $ Opp")),
                _parse_currency(row.get("Total $ Opp")),
                _parse_currency(row.get("Adj Total $ Opp")),
                _parse_int(row.get("Rank")),
            ),
        )
        inserted += 1
    conn.commit()
    print(f"[step1] Loaded {inserted} parent accounts")
    return inserted


def load_facilities(conn):
    """Load Facility List CSV (joined with Supplemental) into facilities table."""
    # Read main facility list
    fac = pd.read_csv(FACILITY_CSV, low_memory=False)
    # Read supplemental data
    sup = pd.read_csv(SUPPLEMENTAL_CSV, low_memory=False)

    # Standardize Definitive ID columns for join — strip whitespace
    fac["Definitive ID"] = fac["Definitive ID"].astype(str).str.strip()
    sup["Definitive ID"] = sup["Definitive ID"].astype(str).str.strip()

    # Left join: keep all facilities, add supplemental columns where available
    # Supplemental has Assigned Rep and overlapping columns — prefer supplemental
    # when available since it's the curated subset
    sup_cols_unique = ["Assigned Rep"]
    sup_for_join = sup[["Definitive ID"] + sup_cols_unique].drop_duplicates(
        subset=["Definitive ID"]
    )
    merged = fac.merge(sup_for_join, on="Definitive ID", how="left")

    # Filter out closed facilities
    merged_active = merged[merged["Closed"].astype(str).str.strip().str.upper() != "TRUE"]

    inserted = 0
    for _, row in merged_active.iterrows():
        hospital_name = str(row.get("Hospital Name", "")).strip()
        if not hospital_name:
            continue
        def_id = str(row.get("Definitive ID", "")).strip()

        conn.execute(
            """INSERT OR IGNORE INTO facilities
               (hospital_name, definitive_id, highest_level_parent, firm_type,
                hospital_type, city, state, ehr_inpatient, staffed_beds,
                net_operating_profit_margin, cms_overall_rating, readmission_rate,
                avg_length_of_stay, icu_beds, net_patient_revenue, assigned_rep,
                hospital_ownership, geographic_classification)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                hospital_name,
                def_id if def_id else None,
                str(row.get("Highest Level Parent", "")).strip() or None,
                str(row.get("Firm Type", "")).strip() or None,
                str(row.get("Hospital Type", "")).strip() or None,
                str(row.get("City", "")).strip() or None,
                str(row.get("State", "")).strip() or None,
                str(
                    row.get("Electronic Health/Medical Record - Inpatient", "")
                ).strip()
                or None,
                _parse_int(row.get("# of Staffed Beds")),
                _parse_float(row.get("Net Operating Profit Margin")),
                _parse_float(row.get("Hospital Compare Overall Rating")),
                _parse_float(row.get("All Cause Hospital-Wide Readmission Rate")),
                _parse_float(row.get("Average Length of Stay")),
                _parse_int(row.get("Intensive Care Unit Beds")),
                _parse_currency(row.get("Net Patient Revenue")),
                str(row.get("Assigned Rep", "")).strip() or None,
                str(row.get("Hospital ownership", "")).strip() or None,
                str(row.get("Geographic Classification", "")).strip() or None,
            ),
        )
        inserted += 1
    conn.commit()
    print(f"[step1] Loaded {inserted} facilities (active only)")
    return inserted


def load_icp_titles():
    """Load ICP titles from JSON into memory."""
    with open(ICP_JSON, "r") as f:
        titles = json.load(f)
    print(f"[step1] Loaded {len(titles)} ICP titles from {ICP_JSON.name}")
    return titles


def run():
    """Execute step 1."""
    print("\n=== Step 1: Load Data ===")
    init_db()
    conn = get_conn()
    try:
        acct_count = load_parent_accounts(conn)
        fac_count = load_facilities(conn)
        icp_titles = load_icp_titles()
        print(f"[step1] Done — {acct_count} accounts, {fac_count} facilities, {len(icp_titles)} ICP titles")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
