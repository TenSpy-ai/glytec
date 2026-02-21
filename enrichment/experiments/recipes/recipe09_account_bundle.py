"""Recipe 9: Comprehensive Account Enrichment Bundle.

Combines CSV data (already have) with API data (quality, financials,
memberships, news) for each target hospital.
Runs facilities concurrently using ThreadPoolExecutor.
"""

import logging
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from enrichment.db import get_conn

logger = logging.getLogger(__name__)

_lock = threading.Lock()

# Key quality metrics to fetch
QUALITY_METRICS = ["hacPenalty", "hacPenaltyAdjustment", "readmissionPenalty", "vbpAdjustment"]

# Key financial metrics to fetch
FINANCIAL_METRICS = [
    "netOperatingMargin", "staffedBeds", "discharges", "employees",
    "avgLengthOfStay", "caseMixIndex", "bedUtilization",
    "budgetOperatingIT", "budgetCapitalIT", "incomeOperating",
    "cashOnHandDays", "badDebtArRatio",
]


def enrich_single_hospital(client, run_id: int, def_id: int,
                           facility_name: str = "", parent_system: str = ""):
    """Pull quality, financials, memberships, and news for one hospital.

    Thread-safe: uses its own short-lived connection with WAL mode.
    """
    import sqlite3
    from enrichment.db import DB_PATH
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    enrichment_counts = {"quality": 0, "financial": 0, "membership": 0, "news": 0}

    try:
        # 1. Quality metrics
        logger.info(f"[recipe09] {def_id}: pulling quality metrics")
        quality = client.get_quality(def_id)
        for q in quality:
            name = q.get("name", "")
            if any(m in name for m in QUALITY_METRICS):
                conn.execute(
                    """INSERT INTO account_enrichment
                       (run_id, definitive_id, data_type, metric_name,
                        metric_value, numeric_value, year, description)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (run_id, def_id, "quality", name,
                     q.get("value"), q.get("numericValue"),
                     q.get("year"), q.get("description")),
                )
                enrichment_counts["quality"] += 1

        # 2. Financial metrics
        logger.info(f"[recipe09] {def_id}: pulling financial metrics")
        financials = client.get_financials(def_id)
        for f in financials:
            name = f.get("name", "")
            if any(m in name for m in FINANCIAL_METRICS):
                conn.execute(
                    """INSERT INTO account_enrichment
                       (run_id, definitive_id, data_type, metric_name,
                        metric_value, numeric_value, year, description)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (run_id, def_id, "financial", name,
                     f.get("value"), f.get("numericValue"),
                     f.get("year"), f.get("description")),
                )
                enrichment_counts["financial"] += 1

        # 3. Memberships (GPO, ACO)
        logger.info(f"[recipe09] {def_id}: pulling memberships")
        memberships = client.get_memberships(def_id)
        for m in memberships:
            conn.execute(
                """INSERT INTO account_enrichment
                   (run_id, definitive_id, data_type, metric_name,
                    metric_value, description)
                   VALUES (?,?,?,?,?,?)""",
                (run_id, def_id, "membership",
                 m.get("type"), m.get("name"), m.get("subType")),
            )
            enrichment_counts["membership"] += 1

        # 4. News/trigger signals
        logger.info(f"[recipe09] {def_id}: pulling news signals")
        high_value_types = ["People", "Information Technology", "Merger",
                            "Affiliation", "Bankruptcy", "New Facility"]
        news = client.search_news(def_id, [
            {"propertyName": "publicationDate", "operatorType": "GreaterThan", "value": "2025-06-01"},
        ])
        for article in news:
            intel_type = article.get("intelligenceType", "")
            if any(t in intel_type for t in high_value_types):
                # Determine signal type
                signal_type = "other"
                if "People" in intel_type:
                    signal_type = "leadership_change"
                elif "Information Technology" in intel_type:
                    signal_type = "ehr_migration"
                elif "Merger" in intel_type:
                    signal_type = "m_and_a"
                elif "Affiliation" in intel_type:
                    signal_type = "affiliation_change"
                elif "Bankruptcy" in intel_type:
                    signal_type = "financial_distress"
                elif "New Facility" in intel_type:
                    signal_type = "new_facility"

                conn.execute(
                    """INSERT INTO trigger_signals
                       (run_id, definitive_id, signal_type, signal_source,
                        signal_date, summary, raw_json, facility_name)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (run_id, def_id, signal_type, "news",
                     article.get("publicationDate"),
                     article.get("newsEventTitle", "")[:200],
                     json.dumps(article)[:1000],
                     facility_name),
                )
                enrichment_counts["news"] += 1

        conn.commit()

        # Update facility status
        conn.execute(
            """UPDATE facility_status SET
               quality_metrics_found = ?, financial_metrics_found = ?,
               news_signals_found = ?, last_processed_at = CURRENT_TIMESTAMP
               WHERE definitive_id = ?""",
            (enrichment_counts["quality"], enrichment_counts["financial"],
             enrichment_counts["news"], def_id),
        )
        conn.commit()

        logger.info(f"[recipe09] {def_id}: quality={enrichment_counts['quality']}, "
                    f"financial={enrichment_counts['financial']}, "
                    f"membership={enrichment_counts['membership']}, "
                    f"news={enrichment_counts['news']}")

    except Exception as e:
        logger.error(f"[recipe09] Failed enrichment for {def_id}: {e}")
        raise
    finally:
        conn.close()

    return enrichment_counts


def run(client, matcher, run_id, facilities, parents, supplemental, config):
    """Run Recipe 9: Comprehensive Account Enrichment Bundle."""
    scope = config.get("scope", "enterprise")
    def_id = config.get("def_id")
    parent_name = config.get("parent")
    logger.info(f"[recipe09] Starting account enrichment, scope={scope}")

    if def_id:
        # Single hospital
        fac_row = facilities[facilities["Definitive ID"].astype(str) == str(def_id)]
        facility_name = str(fac_row.iloc[0].get("Hospital Name", "")) if len(fac_row) > 0 else ""
        parent_system = str(fac_row.iloc[0].get("Highest Level Parent", "")) if len(fac_row) > 0 else ""

        result = enrich_single_hospital(client, run_id, def_id, facility_name, parent_system)
        total = sum(result.values())
        return {"facilities_completed": 1, "facilities_failed": 0, "contacts_found": total}

    # Batch mode
    workers = config.get("workers", 5)

    if parent_name:
        target = facilities[facilities["Highest Level Parent"].astype(str).str.strip() == parent_name.strip()]
    elif scope == "enterprise":
        ent_systems = parents[parents["Segment"].astype(str).str.strip() == "Enterprise/Strategic"]
        client_col = "Glytec Client - 8.31.25"
        ent_systems = ent_systems[ent_systems[client_col].astype(str).str.strip() != "Current Client"]
        ent_names = set(ent_systems["System Name"].astype(str).str.strip())
        target = facilities[facilities["Highest Level Parent"].astype(str).str.strip().isin(ent_names)]
    else:
        target = facilities

    total_facs = len(target)
    logger.info(f"[recipe09] {total_facs} facilities to enrich, workers={workers}")

    # Build work list
    all_facs = []
    for _, row in target.iterrows():
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

    # Resume support — skip facilities already enriched in account_enrichment
    conn = get_conn()
    conn.execute("UPDATE runs SET facilities_targeted = ? WHERE id = ?", (len(all_facs), run_id))
    conn.commit()
    already_done = set()
    for row in conn.execute("SELECT DISTINCT definitive_id FROM account_enrichment").fetchall():
        already_done.add(row[0])
    conn.close()

    todo = [f for f in all_facs if f["def_id"] not in already_done]
    skipped = len(all_facs) - len(todo)
    logger.info(f"[recipe09] {len(all_facs)} total, {skipped} already enriched, {len(todo)} remaining")

    completed = skipped
    failed = 0
    total_enrichments = 0
    start_time = time.time()

    def _process_one(fac):
        try:
            result = enrich_single_hospital(
                client, run_id, fac["def_id"],
                fac["facility_name"], fac["parent_system"],
            )
            return {"def_id": fac["def_id"], "ok": True, "count": sum(result.values())}
        except Exception as e:
            logger.error(f"[recipe09] Failed {fac['def_id']}: {e}")
            return {"def_id": fac["def_id"], "ok": False, "count": 0}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_one, fac): fac for fac in todo}
        done_count = 0
        for fut in as_completed(futures):
            result = fut.result()
            done_count += 1
            if result["ok"]:
                with _lock:
                    completed += 1
                    total_enrichments += result["count"]
            else:
                with _lock:
                    failed += 1

            if done_count % 25 == 0 or done_count == len(todo):
                elapsed = time.time() - start_time
                rate = done_count / elapsed if elapsed > 0 else 0
                remaining = (len(todo) - done_count) / rate if rate > 0 else 0
                logger.info(
                    f"[recipe09] PROGRESS: {done_count}/{len(todo)} done "
                    f"({completed} total, {total_enrichments} enrichments, "
                    f"{failed} failed) | {rate:.1f} fac/s | ETA {remaining/60:.0f}m"
                )
                try:
                    uconn = sqlite3.connect(str(DB_PATH), timeout=60)
                    uconn.execute("PRAGMA journal_mode=WAL")
                    uconn.execute("PRAGMA busy_timeout=60000")
                    uconn.execute(
                        "UPDATE runs SET facilities_completed=?, facilities_failed=?, contacts_found=? WHERE id=?",
                        (completed, failed, total_enrichments, run_id))
                    uconn.commit()
                    uconn.close()
                except Exception:
                    logger.warning("[recipe09] Failed to update run progress (non-fatal)")

    elapsed = time.time() - start_time
    logger.info(f"[recipe09] DONE in {elapsed/60:.1f}m: {completed} completed, "
                f"{failed} failed, {total_enrichments} enrichments")

    return {
        "facilities_completed": completed,
        "facilities_failed": failed,
        "contacts_found": total_enrichments,
    }
