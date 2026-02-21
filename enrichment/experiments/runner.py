"""CLI orchestrator for DH enrichment recipes.

Usage:
    python enrichment/runner.py --recipe 1 --def-id 2151          # single hospital
    python enrichment/runner.py --recipe 4 --scope enterprise     # batch by segment
    python enrichment/runner.py --recipe 10 --parent "Tenet Healthcare"
    python enrichment/runner.py --resume --run-id 5               # resume failed run
    python enrichment/runner.py --recipe 4 --scope enterprise --live  # real API calls
"""

import argparse
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

ENRICHMENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ENRICHMENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(ENRICHMENT_DIR))

from enrichment.db import init_db, get_conn, start_run, finish_run, DB_PATH
from enrichment.dh_client import DHClient
from enrichment.icp_matcher import ICPMatcher

# Recipe imports
from enrichment.recipes import (
    recipe01_full_extract,
    recipe02_icp_match,
    recipe03_network_map,
    recipe04_tiered_discovery,
    recipe05_ehr_segmented,
    recipe06_financial_distress,
    recipe07_geo_territory,
    recipe08_physician_champion,
    recipe09_account_bundle,
    recipe10_every_contact,
)

RECIPES = {
    1: ("Full Contact Extraction", recipe01_full_extract),
    2: ("ICP-Matched Contact Discovery", recipe02_icp_match),
    3: ("Full Network Contact Map", recipe03_network_map),
    4: ("Tiered Discovery", recipe04_tiered_discovery),
    5: ("EHR-Segmented Discovery", recipe05_ehr_segmented),
    6: ("Financial Distress + Quality", recipe06_financial_distress),
    7: ("Geographic / Rep Territory", recipe07_geo_territory),
    8: ("Physician Champion Pipeline", recipe08_physician_champion),
    9: ("Comprehensive Account Bundle", recipe09_account_bundle),
    10: ("Every Contact at Company", recipe10_every_contact),
}

LOG_DIR = Path(__file__).resolve().parent / "logs"


def setup_logging(run_id: int, recipe: str) -> logging.Logger:
    """Configure file + console logging for a run."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"run_{run_id}_{recipe}_{ts}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(str(log_file))
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(ch)

    logging.info(f"Logging to {log_file}")
    return logger


def load_facility_data():
    """Load facility and parent account data from CSVs via pandas."""
    import pandas as pd

    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    facility_csv = data_dir / "AI SDR_Facility List_1.23.26.csv"
    parent_csv = data_dir / "AI SDR_Parent Account List_1.23.26.csv"
    supplemental_csv = data_dir / "AI SDR_Facility List_Supplemental Data_1.23.26.csv"

    facilities = pd.read_csv(facility_csv, low_memory=False)
    parents = pd.read_csv(parent_csv, low_memory=False)
    supplemental = pd.read_csv(supplemental_csv, low_memory=False)

    # Filter active only
    facilities = facilities[facilities["Closed"].astype(str).str.strip().str.upper() != "TRUE"]

    # Merge supplemental rep assignments
    sup_for_join = supplemental[["Definitive ID", "Assigned Rep"]].drop_duplicates(subset=["Definitive ID"])
    facilities = facilities.merge(sup_for_join, on="Definitive ID", how="left")

    return facilities, parents, supplemental


def show_status():
    """Print comprehensive status of all enrichment data."""
    conn = get_conn()

    print("\n" + "=" * 70)
    print("  DH ENRICHMENT PIPELINE — STATUS REPORT")
    print("=" * 70)

    # Runs
    runs = conn.execute(
        "SELECT id, recipe, status, scope, facilities_targeted, "
        "facilities_completed, facilities_failed, contacts_found, "
        "started_at, finished_at FROM runs ORDER BY id"
    ).fetchall()
    print(f"\n--- RUNS ({len(runs)} total) ---")
    print(f"{'ID':>4} {'Recipe':<12} {'Status':<10} {'Scope':<15} {'Target':>7} {'Done':>6} {'Fail':>5} {'Contacts':>9} {'Started':<20}")
    for r in runs:
        print(f"{r[0]:4d} {r[1]:<12} {r[2]:<10} {str(r[3]):<15} {r[4] or 0:7d} {r[5]:6d} {r[6]:5d} {r[7]:9d} {str(r[8])[:19]}")

    # Overall counts
    total_execs = conn.execute("SELECT COUNT(*) FROM executives").fetchone()[0]
    total_icp = conn.execute("SELECT COUNT(*) FROM executives WHERE icp_matched = 1").fetchone()[0]
    total_phys = conn.execute("SELECT COUNT(*) FROM physicians").fetchone()[0]
    total_rfp = conn.execute("SELECT COUNT(*) FROM rfp_contacts").fetchone()[0]
    total_news = conn.execute("SELECT COUNT(*) FROM news_contacts").fetchone()[0]
    total_signals = conn.execute("SELECT COUNT(*) FROM trigger_signals").fetchone()[0]
    total_enrichment = conn.execute("SELECT COUNT(*) FROM account_enrichment").fetchone()[0]
    total_facs = conn.execute("SELECT COUNT(DISTINCT definitive_id) FROM executives").fetchone()[0]
    total_api = conn.execute("SELECT COUNT(*) FROM api_calls").fetchone()[0]

    print(f"\n--- TOTALS ---")
    print(f"  Unique facilities processed: {total_facs}")
    print(f"  Executives:                  {total_execs}")
    print(f"  ICP-matched executives:      {total_icp} ({total_icp/total_execs*100:.1f}%)" if total_execs else "  ICP-matched: 0")
    print(f"  Physicians:                  {total_phys}")
    print(f"  RFP contacts:                {total_rfp}")
    print(f"  News items:                  {total_news}")
    print(f"  Trigger signals:             {total_signals}")
    print(f"  Account enrichment records:  {total_enrichment}")
    print(f"  API calls made:              {total_api}")

    # ICP breakdown
    if total_icp > 0:
        icp = conn.execute(
            "SELECT icp_title, COUNT(*) cnt FROM executives WHERE icp_matched = 1 "
            "GROUP BY icp_title ORDER BY cnt DESC"
        ).fetchall()
        print(f"\n--- ICP MATCH DISTRIBUTION ---")
        for r in icp:
            print(f"  {r[1]:5d}  {r[0]}")

    # Position level breakdown
    if total_execs > 0:
        levels = conn.execute(
            "SELECT position_level, COUNT(*) cnt FROM executives "
            "GROUP BY position_level ORDER BY cnt DESC"
        ).fetchall()
        print(f"\n--- POSITION LEVEL ---")
        for r in levels:
            print(f"  {r[1]:5d}  {r[0]}")

    # Top parent systems
    if total_execs > 0:
        systems = conn.execute(
            "SELECT parent_system, COUNT(*) cnt, "
            "SUM(CASE WHEN icp_matched = 1 THEN 1 ELSE 0 END) icp "
            "FROM executives GROUP BY parent_system ORDER BY cnt DESC LIMIT 15"
        ).fetchall()
        print(f"\n--- TOP PARENT SYSTEMS ---")
        print(f"{'System':<45} {'Execs':>6} {'ICP':>5}")
        for r in systems:
            print(f"  {str(r[0])[:43]:<43} {r[1]:6d} {r[2]:5d}")

    conn.close()
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="DH Enrichment Runner")
    parser.add_argument("--recipe", type=int, help="Recipe number (1-10)")
    parser.add_argument("--def-id", type=int, help="Single Definitive ID")
    parser.add_argument("--parent", type=str, help="Parent system name")
    parser.add_argument("--scope", type=str, help="Scope: enterprise, commercial, all")
    parser.add_argument("--rep", type=str, help="Rep name for territory recipes")
    parser.add_argument("--live", action="store_true", help="Run live (default: dry-run)")
    parser.add_argument("--workers", type=int, default=5, help="Concurrent workers (default: 5)")
    parser.add_argument("--resume", action="store_true", help="Resume a failed run")
    parser.add_argument("--run-id", type=int, help="Run ID to resume")
    parser.add_argument("--status", action="store_true", help="Show status of all runs and exit")
    args = parser.parse_args()

    # Status mode — print summary and exit
    if args.status:
        init_db()
        show_status()
        sys.exit(0)

    if not args.recipe and not args.resume:
        parser.error("--recipe is required (or --resume --run-id N)")

    # Initialize DB
    init_db()

    dry_run = not args.live
    mode = "LIVE" if args.live else "DRY RUN"
    recipe_num = args.recipe
    recipe_name, recipe_module = RECIPES.get(recipe_num, (None, None))

    if not recipe_module:
        print(f"Unknown recipe: {recipe_num}. Available: {list(RECIPES.keys())}")
        sys.exit(1)

    # Build config
    config = {
        "recipe": recipe_num,
        "def_id": args.def_id,
        "parent": args.parent,
        "scope": args.scope,
        "rep": args.rep,
        "dry_run": dry_run,
        "workers": args.workers,
    }

    # Determine scope description
    scope_desc = args.scope or ("single" if args.def_id else "parent" if args.parent else "unknown")

    # Create run record
    run_id = start_run(
        recipe=f"recipe{recipe_num:02d}",
        scope=scope_desc,
        facilities_targeted=0,  # Updated by recipe
        config=config,
    )

    # Setup logging
    setup_logging(run_id, f"recipe{recipe_num:02d}")
    logging.info(f"=== Recipe {recipe_num}: {recipe_name} ({mode}) ===")
    logging.info(f"Run ID: {run_id}")
    logging.info(f"Config: {json.dumps(config)}")

    # Create DH client
    client = DHClient(db_path=str(DB_PATH), dry_run=dry_run)
    client.set_run_id(run_id)

    # Create ICP matcher
    matcher = ICPMatcher()

    # Load facility data
    logging.info("Loading facility and parent account data from CSVs...")
    facilities, parents, supplemental = load_facility_data()
    logging.info(f"Loaded {len(facilities)} active facilities, {len(parents)} parent accounts")

    # Run the recipe
    try:
        result = recipe_module.run(
            client=client,
            matcher=matcher,
            run_id=run_id,
            facilities=facilities,
            parents=parents,
            supplemental=supplemental,
            config=config,
        )

        facilities_completed = result.get("facilities_completed", 0)
        facilities_failed = result.get("facilities_failed", 0)
        contacts_found = result.get("contacts_found", 0)

        finish_run(run_id, "completed", facilities_completed, facilities_failed, contacts_found)
        logging.info(f"=== Recipe {recipe_num} COMPLETE ===")
        logging.info(f"Facilities: {facilities_completed} completed, {facilities_failed} failed")
        logging.info(f"Contacts found: {contacts_found}")

    except KeyboardInterrupt:
        logging.warning("Interrupted by user")
        conn = get_conn()
        fac_completed = conn.execute(
            "SELECT COUNT(*) FROM facility_status WHERE processing_status='completed'"
        ).fetchone()[0]
        conn.close()
        finish_run(run_id, "partial", fac_completed, 0, 0)
        sys.exit(1)

    except Exception as e:
        logging.error(f"Recipe failed: {e}", exc_info=True)
        finish_run(run_id, "failed", 0, 0, 0)
        sys.exit(1)


if __name__ == "__main__":
    main()
