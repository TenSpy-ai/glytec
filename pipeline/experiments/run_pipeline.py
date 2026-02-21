"""Orchestrator — runs the V1 pipeline steps 1–7 in order."""

import argparse
import sys
import os
import time
import datetime

# Ensure pipeline directory is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DRY_RUN, enable_live_mode, DB_PATH, API_LOG_PATH


STEPS = {
    1: ("Load Data", "step1_load_data"),
    2: ("Score Accounts", "step2_score_accounts"),
    3: ("Enrich Contacts", "step3_enrich_contacts"),
    4: ("Wash Contacts", "step4_wash_contacts"),
    5: ("Compose Messages", "step5_compose_messages"),
    6: ("Push to Salesforge", "step6_push_to_salesforge"),
    7: ("Pull Metrics", "step7_pull_metrics"),
}


def parse_args():
    parser = argparse.ArgumentParser(description="Glytec AI SDR V1 Pipeline")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live mode (actually call Salesforge API). Default is dry-run.",
    )
    parser.add_argument(
        "--steps",
        type=str,
        default=None,
        help="Comma-separated list of steps to run (e.g., '1,2,3'). Default: all.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top accounts to enrich (step 3). Default: 10.",
    )
    return parser.parse_args()


def run_step(step_num):
    """Import and run a single step."""
    name, module_name = STEPS[step_num]
    module = __import__(module_name)
    module.run()


def main():
    args = parse_args()

    if args.live:
        enable_live_mode()

    mode = "LIVE" if not DRY_RUN else "DRY RUN"

    # Initialize API log
    with open(API_LOG_PATH, "w") as f:
        f.write("# API Call Log\n\n")
        f.write(f"Pipeline run started: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Mode: {mode}\n")

    # Determine which steps to run
    if args.steps:
        step_nums = [int(s.strip()) for s in args.steps.split(",")]
    else:
        step_nums = list(STEPS.keys())

    print("=" * 70)
    print(f"  GLYTEC AI SDR — V1 PIPELINE ({mode})")
    print(f"  Steps: {', '.join(str(s) for s in step_nums)}")
    print(f"  Database: {DB_PATH}")
    print("=" * 70)

    start = time.time()
    results = {}

    for step_num in step_nums:
        if step_num not in STEPS:
            print(f"\n[pipeline] Unknown step: {step_num}, skipping")
            continue

        name, _ = STEPS[step_num]
        step_start = time.time()

        try:
            run_step(step_num)
            elapsed = time.time() - step_start
            results[step_num] = ("OK", elapsed)
        except Exception as e:
            elapsed = time.time() - step_start
            results[step_num] = ("FAIL", elapsed)
            print(f"\n[pipeline] Step {step_num} ({name}) FAILED: {e}")
            import traceback
            traceback.print_exc()

    total_elapsed = time.time() - start

    # Summary
    print("\n" + "=" * 70)
    print(f"  PIPELINE SUMMARY")
    print("=" * 70)
    for step_num in step_nums:
        if step_num in results:
            name, _ = STEPS[step_num]
            status, elapsed = results[step_num]
            print(f"  Step {step_num} ({name}): {status} ({elapsed:.1f}s)")
    print(f"\n  Total time: {total_elapsed:.1f}s")
    print(f"  Mode: {mode}")
    print(f"  Database: {DB_PATH}")
    print(f"  API log: {API_LOG_PATH}")

    # Print database stats
    try:
        from db import get_conn
        conn = get_conn()
        accounts = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        scored = conn.execute("SELECT COUNT(*) FROM accounts WHERE score IS NOT NULL").fetchone()[0]
        facilities = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
        contacts = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        clean = conn.execute("SELECT COUNT(*) FROM contacts WHERE golden_record = 1 AND suppressed = 0").fetchone()[0]
        messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        sequences = conn.execute("SELECT COUNT(*) FROM sequences").fetchone()[0]
        api_calls = conn.execute("SELECT COUNT(*) FROM api_log").fetchone()[0]
        conn.close()

        print(f"\n  Database stats:")
        print(f"    Accounts:   {accounts} ({scored} scored)")
        print(f"    Facilities: {facilities}")
        print(f"    Contacts:   {contacts} ({clean} clean)")
        print(f"    Messages:   {messages}")
        print(f"    Sequences:  {sequences}")
        print(f"    API calls:  {api_calls}")
    except Exception:
        pass

    print("=" * 70)


if __name__ == "__main__":
    main()
