"""Recipe 8: Physician Champion Discovery Pipeline.

Finds endocrinologists and hospitalists who could champion Glucommander,
plus physician leaders from the executive endpoint.
Runs concurrently with ThreadPoolExecutor.
"""

import logging
import time
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from enrichment.db import get_conn, DB_PATH
from enrichment.recipes.recipe01_full_extract import _store_physicians

logger = logging.getLogger(__name__)
_lock = threading.Lock()

SPECIALTY_SEARCHES = [
    {"name": "Endocrinology", "filters": [
        {"propertyName": "primarySpecialty", "operatorType": "Contains", "value": "Endocrinology"}
    ]},
    {"name": "Hospital Medicine", "filters": [
        {"propertyName": "primarySpecialty", "operatorType": "Contains", "value": "Hospital Medicine"}
    ]},
    {"name": "Internal Medicine", "filters": [
        {"propertyName": "primarySpecialty", "operatorType": "Contains", "value": "Internal Medicine"}
    ]},
    {"name": "Medical Directors", "filters": [
        {"propertyName": "role", "operatorType": "Contains", "value": "Medical Director"}
    ]},
]


def get_icu_facilities(facilities: pd.DataFrame, min_icu_beds: int = 10) -> pd.DataFrame:
    """Filter to SAC hospitals with ICU beds."""
    fac = facilities.copy()
    fac["icu_n"] = pd.to_numeric(
        fac["Intensive Care Unit Beds"].astype(str).str.replace(",", ""),
        errors="coerce"
    ).fillna(0)

    return fac[
        (fac["icu_n"] >= min_icu_beds) &
        (fac["Hospital Type"].astype(str).str.strip() == "Short Term Acute Care Hospital")
    ].sort_values("icu_n", ascending=False)


def _process_facility(client, run_id, fac):
    """Process one facility for physician champions (thread-safe)."""
    def_id = fac["def_id"]
    try:
        all_physicians = []
        for search in SPECIALTY_SEARCHES:
            physicians = client.search_physicians(def_id, search["filters"])
            all_physicians.extend(physicians)
            if physicians:
                logger.info(f"[recipe08] {def_id} {search['name']}: {len(physicians)} physicians")

        # Store physicians with thread-safe connection
        stored = _store_physicians(
            None, run_id, def_id, all_physicians,
            fac["facility_name"], fac["parent_system"])

        # Check for physician leaders in executives
        physician_leaders = client.search_executives(def_id, [
            {"propertyName": "physicianLeader", "operatorType": "True"}
        ])
        for pl in physician_leaders:
            logger.info(f"[recipe08] {def_id} Physician leader: "
                        f"{pl.get('firstName')} {pl.get('lastName')} - {pl.get('standardizedTitle')}")

        return {"def_id": def_id, "ok": True, "contacts": stored, "leaders": len(physician_leaders)}
    except Exception as e:
        logger.error(f"[recipe08] Failed {def_id}: {e}")
        return {"def_id": def_id, "ok": False, "contacts": 0, "leaders": 0}


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 8: Physician Champion Pipeline."""
    scope = config.get("scope", "enterprise")
    workers = config.get("workers", 5)
    logger.info(f"[recipe08] Starting physician champion discovery, scope={scope}, workers={workers}")

    icu_facs = get_icu_facilities(facilities)
    logger.info(f"[recipe08] {len(icu_facs)} SAC facilities with ICU beds >= 10")

    # Filter by scope
    if scope == "enterprise":
        ent_systems = parents[parents["Segment"].astype(str).str.strip() == "Enterprise/Strategic"]
        client_col = "Glytec Client - 8.31.25"
        ent_systems = ent_systems[ent_systems[client_col].astype(str).str.strip() != "Current Client"]
        ent_names = set(ent_systems["System Name"].astype(str).str.strip())
        icu_facs = icu_facs[icu_facs["Highest Level Parent"].astype(str).str.strip().isin(ent_names)]
        logger.info(f"[recipe08] Filtered to {len(icu_facs)} Enterprise facilities")

    # Build work list
    all_facs = []
    for _, row in icu_facs.iterrows():
        fac_def_id = row.get("Definitive ID")
        try:
            fac_def_id = int(float(str(fac_def_id).strip()))
        except (ValueError, TypeError):
            continue
        all_facs.append({
            "def_id": fac_def_id,
            "facility_name": str(row.get("Hospital Name", "")),
            "parent_system": str(row.get("Highest Level Parent", "")),
        })

    total_facs = len(all_facs)

    # Resume — skip facilities already with physicians
    conn = get_conn()
    conn.execute("UPDATE runs SET facilities_targeted = ? WHERE id = ?", (total_facs, run_id))
    conn.commit()
    already_done = set()
    for r in conn.execute("SELECT DISTINCT definitive_id FROM physicians").fetchall():
        already_done.add(r[0])
    conn.close()

    todo = [f for f in all_facs if f["def_id"] not in already_done]
    skipped = total_facs - len(todo)
    logger.info(f"[recipe08] {total_facs} total, {skipped} already have physicians, {len(todo)} remaining")

    completed = skipped
    failed = 0
    total_contacts = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_facility, client, run_id, fac): fac for fac in todo}
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
                    f"[recipe08] PROGRESS: {done_count}/{len(todo)} done "
                    f"({completed} total, {total_contacts} physicians, {failed} failed) | "
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
                    logger.warning("[recipe08] Failed to update run progress (non-fatal)")

    elapsed = time.time() - start_time
    logger.info(f"[recipe08] DONE in {elapsed/60:.1f}m: {completed} completed, "
                f"{failed} failed, {total_contacts} physicians")

    return {
        "facilities_completed": completed,
        "facilities_failed": failed,
        "contacts_found": total_contacts,
    }
