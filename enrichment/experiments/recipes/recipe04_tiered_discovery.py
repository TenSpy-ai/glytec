"""Recipe 4: Tiered Contact Discovery Using All CSV Data Sources.

Uses Parent Account List for prioritization, Facility List for account details,
and ICP Titles for filtering. Processes Enterprise/Strategic first, then Commercial.
Runs facilities concurrently using ThreadPoolExecutor.
"""

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from enrichment.db import get_conn
from enrichment.recipes.recipe03_network_map import get_system_facilities
from enrichment.recipes.recipe02_icp_match import icp_discover_hospital

logger = logging.getLogger(__name__)

# Thread-safe counters
_lock = threading.Lock()


def get_target_systems(parents: pd.DataFrame, scope: str) -> list[dict]:
    """Get target parent systems filtered by scope, excluding Glytec clients."""
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

    opp_col = "Adj Total $ Opp"
    if opp_col in target.columns:
        target = target.copy()
        target["_opp_sort"] = pd.to_numeric(
            target[opp_col].astype(str).str.replace(r'[$,]', '', regex=True),
            errors="coerce"
        ).fillna(0)
        target = target.sort_values("_opp_sort", ascending=False)

    systems = []
    for _, row in target.iterrows():
        system_name = str(row.get("System Name", "")).strip()
        if not system_name:
            continue
        systems.append({
            "system_name": system_name,
            "segment": str(row.get("Segment", "")).strip(),
            "sfdc_account_id": str(row.get("SFDC Account ID", "")).strip(),
            "rank": row.get("Rank"),
        })
    return systems


def _process_facility(client, matcher, run_id, fac, system_name, segment):
    """Process a single facility (designed to run in a thread)."""
    def_id = fac["definitive_id"]
    try:
        result = icp_discover_hospital(
            client, matcher, run_id, def_id,
            facility_name=fac["hospital_name"],
            parent_system=system_name,
            hospital_type=fac["hospital_type"],
            ehr_vendor=fac["ehr_vendor"],
            segment=segment,
        )
        return {"def_id": def_id, "ok": True, "contacts": result["executives"],
                "icp": result.get("icp_matched", 0), "name": fac["hospital_name"]}
    except Exception as e:
        logger.error(f"[recipe04] Failed {def_id} ({fac['hospital_name']}): {e}")
        return {"def_id": def_id, "ok": False, "contacts": 0, "icp": 0, "name": fac["hospital_name"]}


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 4: Tiered Discovery with concurrency."""
    scope = config.get("scope", "enterprise")
    workers = config.get("workers", 5)
    logger.info(f"[recipe04] Starting tiered discovery, scope={scope}, workers={workers}")

    target_systems = get_target_systems(parents, scope)
    logger.info(f"[recipe04] {len(target_systems)} target parent systems")

    # Build full facility list and count
    conn = get_conn()
    all_facs = []
    for sys_info in target_systems:
        facs = get_system_facilities(sys_info["system_name"], facilities)
        for fac in facs:
            fac["_system"] = sys_info["system_name"]
            fac["_segment"] = sys_info["segment"]
        all_facs.extend(facs)

    total_facs = len(all_facs)
    conn.execute("UPDATE runs SET facilities_targeted = ? WHERE id = ?",
                 (total_facs, run_id))
    conn.commit()

    # Check already-processed
    already_done = set()
    for row in conn.execute("SELECT DISTINCT definitive_id FROM executives").fetchall():
        already_done.add(row[0])
    conn.close()

    # Filter to only unprocessed
    todo = [f for f in all_facs if f["definitive_id"] not in already_done]
    skipped = total_facs - len(todo)

    logger.info(f"[recipe04] {total_facs} total facilities, {skipped} already done, {len(todo)} remaining")

    total_completed = skipped
    total_failed = 0
    total_contacts = 0
    start_time = time.time()

    # Process concurrently
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for fac in todo:
            fut = pool.submit(
                _process_facility, client, matcher, run_id,
                fac, fac["_system"], fac["_segment"],
            )
            futures[fut] = fac

        done_count = 0
        for fut in as_completed(futures):
            result = fut.result()
            done_count += 1

            if result["ok"]:
                total_completed += 1
                total_contacts += result["contacts"]
            else:
                total_failed += 1

            # Progress report every 25 facilities
            if done_count % 25 == 0 or done_count == len(todo):
                elapsed = time.time() - start_time
                rate = done_count / elapsed if elapsed > 0 else 0
                remaining = (len(todo) - done_count) / rate if rate > 0 else 0
                logger.info(
                    f"[recipe04] PROGRESS: {done_count}/{len(todo)} done "
                    f"({total_completed} total, {total_contacts} contacts, "
                    f"{total_failed} failed) | "
                    f"{rate:.1f} fac/s | ETA {remaining/60:.0f}m"
                )

                # Update run record (non-fatal if locked)
                try:
                    import sqlite3 as _sql
                    from enrichment.db import DB_PATH as _dbp
                    _c = _sql.connect(str(_dbp), timeout=60)
                    _c.execute("PRAGMA journal_mode=WAL")
                    _c.execute("PRAGMA busy_timeout=60000")
                    _c.execute(
                        "UPDATE runs SET facilities_completed=?, facilities_failed=?, contacts_found=? WHERE id=?",
                        (total_completed, total_failed, total_contacts, run_id))
                    _c.commit()
                    _c.close()
                except Exception:
                    logger.warning("[recipe04] Failed to update run progress (non-fatal)")

    elapsed = time.time() - start_time
    logger.info(f"[recipe04] DONE in {elapsed/60:.1f}m: {total_completed} completed, "
                f"{total_failed} failed, {total_contacts} contacts")

    return {
        "facilities_completed": total_completed,
        "facilities_failed": total_failed,
        "contacts_found": total_contacts,
    }
