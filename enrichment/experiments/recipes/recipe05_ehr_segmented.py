"""Recipe 5: EHR-Segmented Contact Discovery.

Uses CSV EHR data (97% populated) to segment hospitals and pull contacts
with EHR-specific ICP weighting.
"""

import logging
import pandas as pd
from enrichment.db import get_conn
from enrichment.recipes.recipe01_full_extract import _store_executives

logger = logging.getLogger(__name__)

# EHR-specific search strategies
EHR_STRATEGIES = {
    "Epic": {
        "priority_batches": [
            {"name": "IT/Informatics", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Informati"}
            ]},
        ],
        "message_angle": "DIY calculator liability",
    },
    "Oracle Cerner": {
        "priority_batches": [
            {"name": "C-Suite", "filters": [
                {"propertyName": "positionLevel", "operatorType": "In", "value": ["C-Level", "Vice President"]}
            ]},
        ],
        "message_angle": "Oracle transition urgency",
    },
    "MEDITECH": {
        "priority_batches": [
            {"name": "Quality", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Quality"}
            ]},
        ],
        "message_angle": "Modernization",
    },
}

# Common batches for all EHR types
COMMON_BATCHES = [
    {"name": "Pharmacy", "filters": [
        {"propertyName": "department", "operatorType": "Contains", "value": "Pharm"}
    ]},
    {"name": "Endocrinology", "filters": [
        {"propertyName": "standardizedTitle", "operatorType": "Contains", "value": "Endocrin"}
    ]},
]


def classify_ehr(ehr_string: str) -> str:
    """Classify EHR vendor from CSV string."""
    if not ehr_string or pd.isna(ehr_string):
        return "Unknown"
    ehr_lower = str(ehr_string).lower()
    if "epic" in ehr_lower:
        return "Epic"
    if "cerner" in ehr_lower or "oracle" in ehr_lower:
        return "Oracle Cerner"
    if "meditech" in ehr_lower:
        return "MEDITECH"
    return "Other"


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 5: EHR-Segmented Discovery."""
    scope = config.get("scope", "enterprise")
    logger.info(f"[recipe05] Starting EHR-segmented discovery, scope={scope}")

    # Classify all facilities by EHR
    facilities = facilities.copy()
    facilities["ehr_class"] = facilities["Electronic Health/Medical Record - Inpatient"].apply(classify_ehr)

    # Filter by scope if needed
    if scope == "enterprise":
        ent_systems = parents[parents["Segment"].astype(str).str.strip() == "Enterprise/Strategic"]
        ent_names = set(ent_systems["System Name"].astype(str).str.strip())
        facilities = facilities[facilities["Highest Level Parent"].astype(str).str.strip().isin(ent_names)]

    ehr_counts = facilities["ehr_class"].value_counts()
    for ehr, count in ehr_counts.items():
        logger.info(f"[recipe05] {ehr}: {count} facilities")

    total_completed = 0
    total_failed = 0
    total_contacts = 0

    for _, row in facilities.iterrows():
        def_id = row.get("Definitive ID")
        try:
            def_id = int(float(str(def_id).strip()))
        except (ValueError, TypeError):
            continue

        ehr_class = row.get("ehr_class", "Unknown")
        facility_name = str(row.get("Hospital Name", ""))
        parent_system = str(row.get("Highest Level Parent", ""))
        hospital_type = str(row.get("Hospital Type", ""))
        ehr_vendor = str(row.get("Electronic Health/Medical Record - Inpatient", ""))

        # Get EHR-specific + common search batches
        strategy = EHR_STRATEGIES.get(ehr_class, {})
        batches = strategy.get("priority_batches", []) + COMMON_BATCHES

        conn = get_conn()
        all_executives = {}

        try:
            for batch in batches:
                executives = client.search_executives(def_id, batch["filters"])
                for ex in executives:
                    eid = ex.get("executiveId")
                    if eid and eid not in all_executives:
                        all_executives[eid] = ex

            exec_list = list(all_executives.values())
            stored = _store_executives(
                conn, run_id, def_id, exec_list,
                facility_name, parent_system, hospital_type, ehr_vendor, "")

            # Apply ICP matching
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
            conn.commit()

            total_contacts += stored
            total_completed += 1

        except Exception as e:
            total_failed += 1
            logger.error(f"[recipe05] Failed {def_id}: {e}")
        finally:
            conn.close()

    return {
        "facilities_completed": total_completed,
        "facilities_failed": total_failed,
        "contacts_found": total_contacts,
    }
