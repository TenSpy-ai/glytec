"""Recipe 6: Financial Distress + Quality Penalty Contact Discovery.

Pre-filters from CSV for negative-margin hospitals with ICU beds,
enriches with CMS quality penalties from API, then pulls contacts.
Runs concurrently with ThreadPoolExecutor.
"""

import logging
import time
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from enrichment.db import get_conn, DB_PATH
from enrichment.recipes.recipe02_icp_match import icp_discover_hospital

logger = logging.getLogger(__name__)
_lock = threading.Lock()


def get_distressed_facilities(facilities: pd.DataFrame) -> pd.DataFrame:
    """Filter to financially distressed facilities with ICU beds."""
    fac = facilities.copy()
    fac["margin"] = pd.to_numeric(
        fac["Net Operating Profit Margin"].astype(str).str.replace("%", "").str.strip(),
        errors="coerce"
    )
    fac["icu"] = pd.to_numeric(
        fac["Intensive Care Unit Beds"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    ).fillna(0)

    distressed = fac[(fac["margin"] < 0) & (fac["icu"] > 0)]
    return distressed.sort_values("margin", ascending=True)


def _process_facility(client, matcher, run_id, row):
    """Process a single distressed facility (thread-safe)."""
    def_id = row["def_id"]
    try:
        # Check for HAC penalties
        quality = client.search_quality(def_id, [
            {"propertyName": "name", "operatorType": "Contains", "value": "hacPenalty"},
        ])

        # Store quality metrics
        if quality:
            conn = sqlite3.connect(str(DB_PATH), timeout=60)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            for q in quality:
                conn.execute(
                    """INSERT INTO account_enrichment
                       (run_id, definitive_id, data_type, metric_name,
                        metric_value, numeric_value, year, description)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (run_id, def_id, "quality_penalty",
                     q.get("name"), q.get("value"),
                     q.get("numericValue"), q.get("year"),
                     q.get("description")),
                )
            conn.commit()
            conn.close()

        # Pull ICP-targeted contacts
        result = icp_discover_hospital(
            client, matcher, run_id, def_id,
            facility_name=row["facility_name"],
            parent_system=row["parent_system"],
            hospital_type=row["hospital_type"],
            ehr_vendor=row["ehr_vendor"],
            segment=row.get("segment", ""),
        )

        has_penalty = len(quality) > 0
        logger.info(f"[recipe06] {def_id} ({row['facility_name']}): margin={row['margin']:.1f}%, "
                    f"HAC penalty={has_penalty}, {result['executives']} execs, {result['icp_matched']} ICP")

        return {"def_id": def_id, "ok": True, "contacts": result["executives"]}
    except Exception as e:
        logger.error(f"[recipe06] Failed {def_id}: {e}")
        return {"def_id": def_id, "ok": False, "contacts": 0}


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 6: Financial Distress + Quality Penalty."""
    scope = config.get("scope", "enterprise")
    workers = config.get("workers", 5)
    logger.info(f"[recipe06] Starting financial distress discovery, scope={scope}, workers={workers}")

    distressed = get_distressed_facilities(facilities)
    logger.info(f"[recipe06] {len(distressed)} financially distressed facilities with ICU beds")

    # Filter by scope
    if scope == "enterprise":
        ent_systems = parents[parents["Segment"].astype(str).str.strip() == "Enterprise/Strategic"]
        client_col = "Glytec Client - 8.31.25"
        ent_systems = ent_systems[ent_systems[client_col].astype(str).str.strip() != "Current Client"]
        ent_names = set(ent_systems["System Name"].astype(str).str.strip())
        distressed = distressed[
            distressed["Highest Level Parent"].astype(str).str.strip().isin(ent_names)
        ]
        logger.info(f"[recipe06] Filtered to {len(distressed)} Enterprise facilities")

    # Build work list
    all_facs = []
    for _, row in distressed.iterrows():
        fac_def_id = row.get("Definitive ID")
        try:
            fac_def_id = int(float(str(fac_def_id).strip()))
        except (ValueError, TypeError):
            continue
        all_facs.append({
            "def_id": fac_def_id,
            "facility_name": str(row.get("Hospital Name", "")),
            "parent_system": str(row.get("Highest Level Parent", "")),
            "hospital_type": str(row.get("Hospital Type", "")),
            "ehr_vendor": str(row.get("Electronic Health/Medical Record - Inpatient", "")),
            "margin": row.get("margin", 0),
        })

    total_facs = len(all_facs)

    # Resume — skip already-processed
    conn = get_conn()
    conn.execute("UPDATE runs SET facilities_targeted = ? WHERE id = ?", (total_facs, run_id))
    conn.commit()
    already_done = set()
    for r in conn.execute("SELECT DISTINCT definitive_id FROM executives").fetchall():
        already_done.add(r[0])
    conn.close()

    todo = [f for f in all_facs if f["def_id"] not in already_done]
    skipped = total_facs - len(todo)
    logger.info(f"[recipe06] {total_facs} total, {skipped} already have contacts, {len(todo)} remaining")

    completed = skipped
    failed = 0
    total_contacts = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_facility, client, matcher, run_id, fac): fac for fac in todo}
        done_count = 0
        for fut in as_completed(futures):
            result = fut.result()
            done_count += 1
            if result["ok"]:
                with _lock:
                    completed += 1
                    total_contacts += result["contacts"]
            else:
                with _lock:
                    failed += 1

            if done_count % 25 == 0 or done_count == len(todo):
                elapsed = time.time() - start_time
                rate = done_count / elapsed if elapsed > 0 else 0
                remaining = (len(todo) - done_count) / rate if rate > 0 else 0
                logger.info(
                    f"[recipe06] PROGRESS: {done_count}/{len(todo)} done "
                    f"({completed} total, {total_contacts} contacts, {failed} failed) | "
                    f"{rate:.1f} fac/s | ETA {remaining/60:.0f}m"
                )
                try:
                    uconn = sqlite3.connect(str(DB_PATH), timeout=60)
                    uconn.execute("PRAGMA journal_mode=WAL")
                    uconn.execute("PRAGMA busy_timeout=60000")
                    uconn.execute(
                        "UPDATE runs SET facilities_completed=?, facilities_failed=?, contacts_found=? WHERE id=?",
                        (completed, failed, total_contacts, run_id))
                    uconn.commit()
                    uconn.close()
                except Exception:
                    logger.warning("[recipe06] Failed to update run progress (non-fatal)")

    elapsed = time.time() - start_time
    logger.info(f"[recipe06] DONE in {elapsed/60:.1f}m: {completed} completed, "
                f"{failed} failed, {total_contacts} contacts")

    return {
        "facilities_completed": completed,
        "facilities_failed": failed,
        "contacts_found": total_contacts,
    }
