"""Recipe 3: Network Leadership Change Detection.

Scans all facilities in target parent systems for recently updated executives
(leadership changes). Stores trigger signals. Runs concurrently.
"""

import logging
import time
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from enrichment.db import get_conn, DB_PATH

logger = logging.getLogger(__name__)
_lock = threading.Lock()


def get_system_facilities(parent_name: str, facilities: pd.DataFrame) -> list[dict]:
    """Get all facilities for a parent system from CSV."""
    mask = facilities["Highest Level Parent"].astype(str).str.strip() == parent_name.strip()
    system_facs = facilities[mask]
    result = []
    for _, row in system_facs.iterrows():
        def_id = row.get("Definitive ID")
        try:
            def_id = int(float(str(def_id).strip()))
        except (ValueError, TypeError):
            continue
        result.append({
            "definitive_id": def_id,
            "hospital_name": str(row.get("Hospital Name", "")),
            "hospital_type": str(row.get("Hospital Type", "")),
            "ehr_vendor": str(row.get("Electronic Health/Medical Record - Inpatient", "")),
            "staffed_beds": row.get("# of Staffed Beds"),
            "icu_beds": row.get("Intensive Care Unit Beds"),
        })
    return result


def detect_leadership_changes(client, def_id: int):
    """Check for recently updated executives (leadership change signal)."""
    return client.search_executives(def_id, [
        {"propertyName": "lastUpdatedDate", "operatorType": "GreaterThan", "value": "2025-12-01"},
    ])


def _process_facility(client, run_id, fac, parent_name):
    """Process one facility for leadership changes (thread-safe)."""
    def_id = fac["definitive_id"]
    try:
        changed = detect_leadership_changes(client, def_id)
        if changed:
            conn = sqlite3.connect(str(DB_PATH), timeout=60)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            for ex in changed:
                conn.execute(
                    """INSERT INTO trigger_signals
                       (run_id, definitive_id, signal_type, signal_source,
                        signal_date, summary, facility_name)
                       VALUES (?,?,?,?,?,?,?)""",
                    (run_id, def_id, "leadership_change", "executive_update",
                     ex.get("lastUpdatedDate"),
                     f"{ex.get('firstName')} {ex.get('lastName')} - {ex.get('standardizedTitle')}",
                     fac["hospital_name"]),
                )
            conn.commit()
            conn.close()
        return {"def_id": def_id, "ok": True, "signals": len(changed), "name": fac["hospital_name"]}
    except Exception as e:
        logger.error(f"[recipe03] Failed {def_id} ({fac['hospital_name']}): {e}")
        return {"def_id": def_id, "ok": False, "signals": 0, "name": fac["hospital_name"]}


def get_target_systems(parents: pd.DataFrame, scope: str) -> list[str]:
    """Get target parent system names by scope."""
    client_col = "Glytec Client - 8.31.25"
    non_clients = parents[parents[client_col].astype(str).str.strip() != "Current Client"]

    if scope == "enterprise":
        target = non_clients[non_clients["Segment"].astype(str).str.strip() == "Enterprise/Strategic"]
    elif scope == "commercial":
        target = non_clients[non_clients["Segment"].astype(str).str.strip() == "Commercial"]
    elif scope == "all":
        target = non_clients[non_clients["Segment"].astype(str).str.strip() != "Government"]
    else:
        target = non_clients

    return list(target["System Name"].astype(str).str.strip().unique())


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 3: Network Leadership Change Detection."""
    scope = config.get("scope", "enterprise")
    parent_name = config.get("parent")
    workers = config.get("workers", 5)

    # Single parent or batch
    if parent_name:
        system_names = [parent_name]
    else:
        system_names = get_target_systems(parents, scope)

    logger.info(f"[recipe03] Scanning {len(system_names)} parent systems for leadership changes, workers={workers}")

    # Build facility list
    all_facs = []
    for sname in system_names:
        for fac in get_system_facilities(sname, facilities):
            fac["_parent"] = sname
            all_facs.append(fac)

    total_facs = len(all_facs)

    # Resume — skip already-scanned facilities
    conn = get_conn()
    conn.execute("UPDATE runs SET facilities_targeted = ? WHERE id = ?", (total_facs, run_id))
    conn.commit()
    already_done = set()
    for row in conn.execute(
        "SELECT DISTINCT definitive_id FROM trigger_signals WHERE signal_type='leadership_change' AND signal_source='executive_update'"
    ).fetchall():
        already_done.add(row[0])
    conn.close()

    todo = [f for f in all_facs if f["definitive_id"] not in already_done]
    skipped = total_facs - len(todo)
    logger.info(f"[recipe03] {total_facs} total facilities, {skipped} already scanned, {len(todo)} remaining")

    completed = skipped
    failed = 0
    total_signals = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_facility, client, run_id, fac, fac["_parent"]): fac for fac in todo}
        done_count = 0
        for fut in as_completed(futures):
            result = fut.result()
            done_count += 1
            if result["ok"]:
                with _lock:
                    completed += 1
                    total_signals += result["signals"]
                if result["signals"] > 0:
                    logger.info(f"[recipe03] {result['def_id']} ({result['name']}): {result['signals']} leadership changes")
            else:
                with _lock:
                    failed += 1

            if done_count % 50 == 0 or done_count == len(todo):
                elapsed = time.time() - start_time
                rate = done_count / elapsed if elapsed > 0 else 0
                remaining = (len(todo) - done_count) / rate if rate > 0 else 0
                logger.info(
                    f"[recipe03] PROGRESS: {done_count}/{len(todo)} done "
                    f"({total_signals} signals found, {failed} failed) | "
                    f"{rate:.1f} fac/s | ETA {remaining/60:.0f}m"
                )
                try:
                    uconn = sqlite3.connect(str(DB_PATH), timeout=60)
                    uconn.execute("PRAGMA journal_mode=WAL")
                    uconn.execute("PRAGMA busy_timeout=60000")
                    uconn.execute(
                        "UPDATE runs SET facilities_completed=?, facilities_failed=?, contacts_found=? WHERE id=?",
                        (completed, failed, total_signals, run_id))
                    uconn.commit()
                    uconn.close()
                except Exception:
                    logger.warning("[recipe03] Failed to update run progress (non-fatal)")

    elapsed = time.time() - start_time
    logger.info(f"[recipe03] DONE in {elapsed/60:.1f}m: {completed} scanned, "
                f"{total_signals} leadership changes found, {failed} failed")

    return {
        "facilities_completed": completed,
        "facilities_failed": failed,
        "contacts_found": total_signals,
    }
