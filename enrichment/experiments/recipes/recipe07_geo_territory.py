"""Recipe 7: Contact Discovery by Geography and Rep Territory.

Uses Supplemental Data CSV for rep assignments, prioritizes facilities
within each territory by size and ICU activity.
"""

import logging
import pandas as pd
from enrichment.db import get_conn
from enrichment.recipes.recipe02_icp_match import icp_discover_hospital

logger = logging.getLogger(__name__)


def get_rep_facilities(facilities: pd.DataFrame, rep_name: str) -> pd.DataFrame:
    """Get facilities assigned to a specific rep, priority-sorted."""
    rep_facs = facilities[facilities["Assigned Rep"].astype(str).str.strip() == rep_name.strip()].copy()

    # Parse numeric columns for sorting
    rep_facs["beds_n"] = pd.to_numeric(
        rep_facs["# of Staffed Beds"].astype(str).str.replace(",", ""),
        errors="coerce"
    ).fillna(0)
    rep_facs["icu_n"] = pd.to_numeric(
        rep_facs["Intensive Care Unit Beds"].astype(str).str.replace(",", ""),
        errors="coerce"
    ).fillna(0)
    rep_facs["margin_n"] = pd.to_numeric(
        rep_facs["Net Operating Profit Margin"].astype(str).str.replace("%", ""),
        errors="coerce"
    ).fillna(0)

    # Priority: SAC hospitals first, then by beds descending
    type_priority = {
        "Short Term Acute Care Hospital": 0,
        "Critical Access Hospital": 1,
        "Long Term Acute Care Hospital": 2,
        "Rehabilitation Hospital": 3,
        "Psychiatric Hospital": 4,
    }
    rep_facs["type_rank"] = rep_facs["Hospital Type"].map(type_priority).fillna(5)
    rep_facs["has_icu"] = (rep_facs["icu_n"] > 0).astype(int)

    return rep_facs.sort_values(
        ["type_rank", "has_icu", "beds_n"],
        ascending=[True, False, False],
    )


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 7: Geographic/Rep Territory Discovery."""
    rep_name = config.get("rep")
    scope = config.get("scope")
    logger.info(f"[recipe07] Starting territory discovery, rep={rep_name}, scope={scope}")

    if rep_name:
        target_facs = get_rep_facilities(facilities, rep_name)
        logger.info(f"[recipe07] Rep '{rep_name}': {len(target_facs)} facilities")
    elif scope:
        # Group by state for geographic clustering
        target_facs = facilities.copy()
        if scope != "all":
            ent_systems = parents[parents["Segment"].astype(str).str.strip() == "Enterprise/Strategic"]
            ent_names = set(ent_systems["System Name"].astype(str).str.strip())
            target_facs = target_facs[
                target_facs["Highest Level Parent"].astype(str).str.strip().isin(ent_names)
            ]
    else:
        raise ValueError("Recipe 7 requires --rep '<name>' or --scope")

    total_completed = 0
    total_failed = 0
    total_contacts = 0

    for _, row in target_facs.iterrows():
        def_id = row.get("Definitive ID")
        try:
            def_id = int(float(str(def_id).strip()))
        except (ValueError, TypeError):
            continue

        facility_name = str(row.get("Hospital Name", ""))
        parent_system = str(row.get("Highest Level Parent", ""))
        hospital_type = str(row.get("Hospital Type", ""))
        ehr_vendor = str(row.get("Electronic Health/Medical Record - Inpatient", ""))

        try:
            result = icp_discover_hospital(
                client, matcher, run_id, def_id,
                facility_name=facility_name,
                parent_system=parent_system,
                hospital_type=hospital_type,
                ehr_vendor=ehr_vendor,
            )
            total_contacts += result["executives"]
            total_completed += 1

        except Exception as e:
            total_failed += 1
            logger.error(f"[recipe07] Failed {def_id}: {e}")

    return {
        "facilities_completed": total_completed,
        "facilities_failed": total_failed,
        "contacts_found": total_contacts,
    }
