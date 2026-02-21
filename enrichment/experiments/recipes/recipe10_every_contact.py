"""Recipe 10: Every Contact at a Company.

Exhaustive extraction: every executive, physician, RFP contact, and
news-mentioned person at every facility in a parent system.
"""

import logging
import pandas as pd
from enrichment.db import get_conn
from enrichment.recipes.recipe01_full_extract import (
    extract_single_hospital, _store_executives, _store_physicians,
    _store_rfp_contacts, _store_news,
)
from enrichment.recipes.recipe03_network_map import get_system_facilities

logger = logging.getLogger(__name__)


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 10: Every Contact at Company."""
    parent_name = config.get("parent")
    def_id = config.get("def_id")

    if not parent_name and not def_id:
        raise ValueError("Recipe 10 requires --parent '<System Name>' or --def-id")

    if def_id:
        # Single hospital — delegate to recipe 1
        from enrichment.recipes.recipe01_full_extract import run as run_r1
        return run_r1(client, matcher, run_id, facilities, parents, supplemental, config)

    logger.info(f"[recipe10] Starting exhaustive extraction for '{parent_name}'")

    # Step 1: Get all facilities from CSV
    system_facs = get_system_facilities(parent_name, facilities)
    logger.info(f"[recipe10] CSV: {len(system_facs)} facilities for '{parent_name}'")

    # Step 2: Also search DH API for facilities not in CSV
    api_facs_parent = client.search_hospitals([
        {"propertyName": "networkParentName", "operatorType": "Equals", "value": parent_name},
        {"propertyName": "companyStatus", "operatorType": "Equals", "value": "Active"},
    ])
    api_facs_network = client.search_hospitals([
        {"propertyName": "networkName", "operatorType": "Contains", "value": parent_name},
        {"propertyName": "companyStatus", "operatorType": "Equals", "value": "Active"},
    ])

    # Merge all facility IDs
    csv_ids = {f["definitive_id"] for f in system_facs}
    api_ids = set()
    api_fac_map = {}
    for fac in api_facs_parent + api_facs_network:
        fid = fac.get("definitiveId")
        if fid and fid not in csv_ids:
            api_ids.add(fid)
            api_fac_map[fid] = fac

    if api_ids:
        logger.info(f"[recipe10] API found {len(api_ids)} additional facilities not in CSV")
        for fid, fac in api_fac_map.items():
            system_facs.append({
                "definitive_id": fid,
                "hospital_name": fac.get("facilityName", ""),
                "hospital_type": fac.get("hospitalType", ""),
                "ehr_vendor": "",
                "staffed_beds": None,
                "icu_beds": None,
            })

    total_facs = len(system_facs)
    logger.info(f"[recipe10] Total facilities to process: {total_facs}")

    # Look up segment
    segment = ""
    parent_row = parents[parents["System Name"].astype(str).str.strip() == parent_name.strip()]
    if len(parent_row) > 0:
        segment = str(parent_row.iloc[0].get("Segment", ""))

    completed = 0
    failed = 0
    total_contacts = 0

    for i, fac in enumerate(system_facs):
        fac_id = fac["definitive_id"]
        logger.info(f"[recipe10] [{i+1}/{total_facs}] Processing {fac_id} ({fac['hospital_name']})")

        try:
            result = extract_single_hospital(
                client, run_id, fac_id,
                facility_name=fac["hospital_name"],
                parent_system=parent_name,
                hospital_type=fac["hospital_type"],
                ehr_vendor=fac["ehr_vendor"],
                segment=segment,
            )

            contacts = result["executives"] + result["physicians"] + result["rfp_contacts"]
            total_contacts += contacts
            completed += 1

            logger.info(f"[recipe10] {fac_id}: {result['executives']} execs, "
                        f"{result['physicians']} physicians, "
                        f"{result['rfp_contacts']} RFP, {result['news']} news")

        except Exception as e:
            failed += 1
            logger.error(f"[recipe10] Failed {fac_id}: {e}")

    # Apply ICP matching to all discovered executives
    conn = get_conn()
    unmatched = conn.execute(
        "SELECT executive_id, definitive_id, standardized_title, department, position_level "
        "FROM executives WHERE run_id = ? AND icp_matched = 0",
        (run_id,)
    ).fetchall()

    icp_matched = 0
    for row in unmatched:
        match = matcher.match(row["standardized_title"], row["department"], row["position_level"])
        if match:
            conn.execute(
                """UPDATE executives SET
                   icp_matched = 1, icp_title = ?, icp_department = ?,
                   icp_category = ?, icp_intent_score = ?,
                   icp_function_type = ?, icp_job_level = ?
                   WHERE executive_id = ? AND definitive_id = ?""",
                (match["icp_title"], match["icp_department"],
                 match["icp_category"], match["icp_intent_score"],
                 match["icp_function_type"], match["icp_job_level"],
                 row["executive_id"], row["definitive_id"]),
            )
            icp_matched += 1
    conn.commit()
    conn.close()

    logger.info(f"[recipe10] ICP matching: {icp_matched}/{len(unmatched)} executives matched")

    return {
        "facilities_completed": completed,
        "facilities_failed": failed,
        "contacts_found": total_contacts,
    }
