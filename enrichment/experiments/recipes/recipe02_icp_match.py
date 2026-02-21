"""Recipe 2: ICP-Matched Contact Discovery.

Uses the 66 ICP titles to run targeted executive searches per hospital,
then scores and ranks contacts by ICP match quality.
"""

import logging
from enrichment.db import get_conn
from enrichment.recipes.recipe01_full_extract import _store_executives

logger = logging.getLogger(__name__)


def icp_discover_hospital(client, matcher, run_id: int, def_id: int,
                          facility_name: str = "", parent_system: str = "",
                          hospital_type: str = "", ehr_vendor: str = "",
                          segment: str = ""):
    """Run ICP-targeted executive searches for one hospital.

    Thread-safe: uses short-lived DB connections for writes.
    """
    import sqlite3
    from enrichment.db import DB_PATH
    all_executives = {}  # keyed by executiveId to dedup

    # Get search batches from ICP matcher
    batches = matcher.get_search_batches()

    for batch in batches:
        logger.info(f"[recipe02] {def_id}: searching batch '{batch['name']}'")
        executives = client.search_executives(def_id, batch["filters"])

        for ex in executives:
            eid = ex.get("executiveId")
            if eid and eid not in all_executives:
                all_executives[eid] = ex

    # Store all discovered executives (uses its own connection internally)
    exec_list = list(all_executives.values())
    stored = _store_executives(
        None, run_id, def_id, exec_list,
        facility_name, parent_system, hospital_type, ehr_vendor, segment)

    # Apply ICP matching to stored executives with a short-lived connection
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    matched = 0
    for ex in exec_list:
        match = matcher.match(
            ex.get("standardizedTitle", ""),
            ex.get("department", ""),
            ex.get("positionLevel", ""),
        )
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
                 ex.get("executiveId"), def_id),
            )
            matched += 1
            logger.info(f"[icp_matcher] Matched '{ex.get('standardizedTitle')}' -> "
                        f"{match['icp_title']} (intent={match['icp_intent_score']}, "
                        f"{match['icp_category']})")

    conn.commit()
    conn.close()

    logger.info(f"[recipe02] {def_id}: {stored} execs, {matched} ICP matches")
    return {"executives": stored, "icp_matched": matched}


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 2 for a single hospital or batch."""
    def_id = config.get("def_id")
    if not def_id:
        raise ValueError("Recipe 2 requires --def-id")

    # Look up facility info
    fac_row = facilities[facilities["Definitive ID"].astype(str) == str(def_id)]
    facility_name = parent_system = hospital_type = ehr_vendor = segment = ""
    if len(fac_row) > 0:
        row = fac_row.iloc[0]
        facility_name = str(row.get("Hospital Name", ""))
        parent_system = str(row.get("Highest Level Parent", ""))
        hospital_type = str(row.get("Hospital Type", ""))
        ehr_vendor = str(row.get("Electronic Health/Medical Record - Inpatient", ""))

    if parent_system:
        parent_row = parents[parents["System Name"].astype(str) == parent_system]
        if len(parent_row) > 0:
            segment = str(parent_row.iloc[0].get("Segment", ""))

    result = icp_discover_hospital(
        client, matcher, run_id, def_id,
        facility_name, parent_system, hospital_type, ehr_vendor, segment)

    return {
        "facilities_completed": 1,
        "facilities_failed": 0,
        "contacts_found": result["executives"],
    }
