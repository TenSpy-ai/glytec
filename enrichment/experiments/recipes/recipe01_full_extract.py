"""Recipe 1: Full Contact Extraction for a Single Hospital.

Given a Definitive ID, pull every conceivable contact: executives, physicians,
RFP contacts, and news-derived leadership changes.
"""

import logging
from enrichment.db import get_conn

logger = logging.getLogger(__name__)


def _store_executives(conn, run_id: int, def_id: int, executives: list,
                      facility_name: str, parent_system: str, hospital_type: str,
                      ehr_vendor: str, segment: str):
    """Store executive records, deduplicating by executive_id + definitive_id.

    Uses its own connection for thread safety in concurrent scenarios.
    """
    import sqlite3
    from enrichment.db import DB_PATH
    stored = 0
    local_conn = sqlite3.connect(str(DB_PATH), timeout=60)
    local_conn.execute("PRAGMA journal_mode=WAL")
    local_conn.execute("PRAGMA busy_timeout=60000")
    for ex in executives:
        try:
            local_conn.execute(
                """INSERT OR IGNORE INTO executives
                   (run_id, definitive_id, person_id, executive_id,
                    first_name, last_name, prefix, suffix, credentials, gender,
                    department, position_level, standardized_title, title,
                    primary_email, direct_email, direct_phone, location_phone,
                    mobile_phone, linkedin_url, physician_flag, physician_leader,
                    executive_npi, last_updated_date,
                    facility_name, parent_system, hospital_type, ehr_vendor, segment)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, def_id,
                 ex.get("personId"), ex.get("executiveId"),
                 ex.get("firstName"), ex.get("lastName"),
                 ex.get("prefix"), ex.get("suffix"),
                 ex.get("credentials"), ex.get("gender"),
                 ex.get("department"), ex.get("positionLevel"),
                 ex.get("standardizedTitle"), ex.get("title"),
                 ex.get("primaryEmail"), ex.get("directEmail"),
                 ex.get("directPhone"), ex.get("locationPhone"),
                 ex.get("mobilePhone"), ex.get("linkedinProfileURL"),
                 ex.get("physicianFlag"), ex.get("physicianLeader"),
                 ex.get("executiveNPI"), ex.get("lastUpdatedDate"),
                 facility_name, parent_system, hospital_type, ehr_vendor, segment),
            )
            stored += 1
        except Exception as e:
            logger.warning(f"Failed to store executive {ex.get('executiveId')}: {e}")
    local_conn.commit()
    local_conn.close()
    return stored


def _store_physicians(conn, run_id: int, def_id: int, physicians: list,
                      facility_name: str, parent_system: str):
    """Store physician records. Thread-safe: uses its own connection."""
    import sqlite3
    from enrichment.db import DB_PATH
    stored = 0
    local_conn = sqlite3.connect(str(DB_PATH), timeout=60)
    local_conn.execute("PRAGMA journal_mode=WAL")
    local_conn.execute("PRAGMA busy_timeout=60000")
    for ph in physicians:
        try:
            local_conn.execute(
                """INSERT OR IGNORE INTO physicians
                   (run_id, definitive_id, person_id, npi,
                    first_name, last_name, credentials, role, gender,
                    primary_specialty, primary_practice_city, primary_practice_state,
                    primary_practice_phone, primary_hospital_affiliation,
                    primary_hospital_def_id, secondary_hospital_affiliation,
                    secondary_hospital_def_id, medicare_payments,
                    medicare_unique_patients, num_procedures,
                    facility_name, parent_system)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, def_id,
                 ph.get("personId"), ph.get("npi"),
                 ph.get("firstName"), ph.get("lastName"),
                 ph.get("credentials"), ph.get("role"), ph.get("gender"),
                 ph.get("primarySpecialty"),
                 ph.get("primaryPracticeCity"), ph.get("primaryPracticeState"),
                 ph.get("primaryPracticeLocationPhone"),
                 ph.get("primaryHospitalAffiliation"),
                 ph.get("primaryHospitalAffiliationDefinitiveID"),
                 ph.get("secondaryHospitalAffiliation"),
                 ph.get("secondaryHospitalAffiliationDefinitiveID"),
                 ph.get("medicareClaimPayments"),
                 ph.get("medicareUniquePatients"),
                 ph.get("numberOfMedicalProcedures"),
                 facility_name, parent_system),
            )
            stored += 1
        except Exception as e:
            logger.warning(f"Failed to store physician {ph.get('npi')}: {e}")
    local_conn.commit()
    local_conn.close()
    return stored


def _store_rfp_contacts(conn, run_id: int, def_id: int, rfps: list,
                        facility_name: str):
    """Store RFP contact records."""
    stored = 0
    for rfp in rfps:
        contact = rfp.get("contact", {}) or {}
        if not contact.get("name") and not contact.get("email"):
            continue
        try:
            conn.execute(
                """INSERT INTO rfp_contacts
                   (run_id, definitive_id, rfp_id, contact_name, contact_email,
                    contact_phone, contact_title, rfp_type, rfp_category,
                    rfp_classification, date_posted, date_due, posting_link,
                    description, facility_name)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, def_id,
                 rfp.get("definitiveRfpId"),
                 contact.get("name"), contact.get("email"),
                 contact.get("phone"), contact.get("title"),
                 rfp.get("type"), rfp.get("category"),
                 rfp.get("classification"),
                 rfp.get("datePosted"), rfp.get("dateDue"),
                 rfp.get("postingLink"), rfp.get("description"),
                 facility_name),
            )
            stored += 1
        except Exception as e:
            logger.warning(f"Failed to store RFP contact: {e}")
    conn.commit()
    return stored


def _store_news(conn, run_id: int, def_id: int, news: list,
                facility_name: str):
    """Store news-derived contacts (People on the Move type)."""
    stored = 0
    for article in news:
        intel_type = article.get("intelligenceType", "")
        if "People" not in intel_type:
            continue
        body = article.get("bodyOfArticle", "")[:500]
        try:
            conn.execute(
                """INSERT INTO news_contacts
                   (run_id, definitive_id, intelligence_type, publication_date,
                    news_title, body_excerpt, facility_name)
                   VALUES (?,?,?,?,?,?,?)""",
                (run_id, def_id, intel_type,
                 article.get("publicationDate"),
                 article.get("newsEventTitle"),
                 body, facility_name),
            )
            stored += 1
        except Exception as e:
            logger.warning(f"Failed to store news contact: {e}")
    conn.commit()
    return stored


def extract_single_hospital(client, run_id: int, def_id: int,
                            facility_name: str = "", parent_system: str = "",
                            hospital_type: str = "", ehr_vendor: str = "",
                            segment: str = ""):
    """Full extraction for one hospital. Returns counts dict."""
    conn = get_conn()
    result = {"executives": 0, "physicians": 0, "rfp_contacts": 0, "news": 0}

    try:
        # 1. All executives
        logger.info(f"[recipe01] Pulling executives for {def_id} ({facility_name})")
        executives = client.get_executives(def_id)
        result["executives"] = _store_executives(
            conn, run_id, def_id, executives,
            facility_name, parent_system, hospital_type, ehr_vendor, segment)
        logger.info(f"[recipe01] {def_id}: {result['executives']} executives stored")

        # 2. All physicians
        logger.info(f"[recipe01] Pulling physicians for {def_id}")
        physicians = client.get_physicians(def_id)
        result["physicians"] = _store_physicians(
            conn, run_id, def_id, physicians, facility_name, parent_system)
        logger.info(f"[recipe01] {def_id}: {result['physicians']} physicians stored")

        # 3. RFP contacts
        logger.info(f"[recipe01] Pulling RFPs for {def_id}")
        rfps = client.get_requests(def_id)
        result["rfp_contacts"] = _store_rfp_contacts(
            conn, run_id, def_id, rfps, facility_name)
        logger.info(f"[recipe01] {def_id}: {result['rfp_contacts']} RFP contacts stored")

        # 4. News (People on the Move)
        logger.info(f"[recipe01] Pulling news for {def_id}")
        news = client.search_news(def_id, [
            {"propertyName": "intelligenceType", "operatorType": "Contains", "value": "People"},
            {"propertyName": "publicationDate", "operatorType": "GreaterThan", "value": "2025-06-01"},
        ])
        result["news"] = _store_news(conn, run_id, def_id, news, facility_name)
        logger.info(f"[recipe01] {def_id}: {result['news']} news items stored")

        # Update facility status
        total_contacts = result["executives"] + result["physicians"] + result["rfp_contacts"]
        conn.execute(
            """INSERT OR REPLACE INTO facility_status
               (definitive_id, hospital_name, parent_system, segment,
                last_processed_at, executives_found, physicians_found,
                rfp_contacts_found, news_signals_found, processing_status)
               VALUES (?,?,?,?,CURRENT_TIMESTAMP,?,?,?,?,?)""",
            (def_id, facility_name, parent_system, segment,
             result["executives"], result["physicians"],
             result["rfp_contacts"], result["news"], "completed"),
        )
        conn.commit()

    except Exception as e:
        logger.error(f"[recipe01] Failed for {def_id}: {e}")
        conn.execute(
            """INSERT OR REPLACE INTO facility_status
               (definitive_id, hospital_name, parent_system, segment,
                processing_status, error_message)
               VALUES (?,?,?,?,?,?)""",
            (def_id, facility_name, parent_system, segment, "failed", str(e)),
        )
        conn.commit()
        raise
    finally:
        conn.close()

    return result


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 1 for a single hospital."""
    def_id = config.get("def_id")
    if not def_id:
        raise ValueError("Recipe 1 requires --def-id")

    # Look up facility info from CSV
    fac_row = facilities[facilities["Definitive ID"].astype(str) == str(def_id)]
    if len(fac_row) > 0:
        row = fac_row.iloc[0]
        facility_name = str(row.get("Hospital Name", ""))
        parent_system = str(row.get("Highest Level Parent", ""))
        hospital_type = str(row.get("Hospital Type", ""))
        ehr_vendor = str(row.get("Electronic Health/Medical Record - Inpatient", ""))
    else:
        facility_name = ""
        parent_system = ""
        hospital_type = ""
        ehr_vendor = ""

    # Look up segment from parent account list
    segment = ""
    if parent_system:
        parent_row = parents[parents["System Name"].astype(str) == parent_system]
        if len(parent_row) > 0:
            segment = str(parent_row.iloc[0].get("Segment", ""))

    result = extract_single_hospital(
        client, run_id, def_id,
        facility_name=facility_name,
        parent_system=parent_system,
        hospital_type=hospital_type,
        ehr_vendor=ehr_vendor,
        segment=segment,
    )

    total = result["executives"] + result["physicians"] + result["rfp_contacts"]
    return {
        "facilities_completed": 1,
        "facilities_failed": 0,
        "contacts_found": total,
    }
