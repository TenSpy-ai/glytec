"""
GTM Hello World — QA Test Runner
Runs all test files in phased parallel execution.

Usage:
    python -m tests.run_all              # Full parallel run (4 phases)
    python -m tests.run_all --quick      # Skip e2e (phases 0-3 only)
    python -m tests.run_all --serial     # Force sequential (debugging)
    python -m tests.run_all test_03      # Run single file
"""

import importlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# Phase definitions: (phase_name, [module_names], parallel?)
PHASES = [
    ("Phase 0 — Foundation", ["test_00_db"], False),
    ("Phase 1 — Independent read + isolated", [
        "test_01_mcp_read",
        "test_02_api_blocklist",
        "test_05_email_tools",
        "test_08_replies_clay",
        "test_09_config_server",
    ], True),
    ("Phase 2 — MCP write tests", [
        "test_03_campaign_lifecycle",
        "test_04_lead_management",
    ], True),
    ("Phase 3 — Script integration", [
        "test_06_ops_scripts",
        "test_07_sync",
    ], True),
    ("Phase 4 — Capstone (E2E)", ["test_10_e2e"], False),
]


def run_module(module_name: str):
    """Import and run a single test module. Returns (module_name, TestResult)."""
    try:
        mod = importlib.import_module(f"tests.{module_name}")
        result = mod.run()
        return module_name, result
    except Exception as e:
        # Create a failed result for import/runtime errors
        from tests.helpers import TestResult
        r = TestResult(module_name)
        r.fail("module_load", e)
        return module_name, r


def run_phase(phase_name: str, modules: list, parallel: bool, serial_override: bool):
    """Run a phase of tests. Returns list of (module_name, TestResult)."""
    print(f"\n{'#' * 64}")
    print(f"  {phase_name} ({'parallel' if parallel and not serial_override else 'sequential'})")
    print(f"  Modules: {', '.join(modules)}")
    print(f"{'#' * 64}\n")

    start = time.time()
    results = []

    if parallel and not serial_override:
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(run_module, m): m for m in modules}
            for future in as_completed(futures):
                module_name, result = future.result()
                results.append((module_name, result))
                print(result.summary())
    else:
        for module_name in modules:
            _, result = run_module(module_name)
            results.append((module_name, result))
            print(result.summary())

    elapsed = time.time() - start
    phase_passed = all(r.all_passed for _, r in results)
    status = "PASSED" if phase_passed else "FAILED"
    print(f"  {phase_name}: {status} ({elapsed:.1f}s)\n")

    return results, phase_passed


def main():
    args = sys.argv[1:]

    quick = "--quick" in args
    serial = "--serial" in args
    single_file = None

    # Check for single file mode
    for arg in args:
        if arg.startswith("test_") and not arg.startswith("--"):
            single_file = arg
            break

    # Single file mode
    if single_file:
        print(f"\nRunning single file: {single_file}\n")
        _, result = run_module(single_file)
        print(result.summary())
        sys.exit(0 if result.all_passed else 1)

    # Full run
    print("\n" + "=" * 64)
    print("  GTM Hello World — QA Test Suite")
    print(f"  Mode: {'quick' if quick else 'full'} | {'serial' if serial else 'parallel'}")
    print("=" * 64)

    all_results = []
    suite_start = time.time()

    for phase_name, modules, parallel in PHASES:
        # Skip e2e in quick mode
        if quick and "test_10_e2e" in modules:
            print(f"\n  Skipping {phase_name} (--quick)")
            continue

        results, phase_passed = run_phase(phase_name, modules, parallel, serial)
        all_results.extend(results)

        # Stop on phase failure (later phases depend on earlier ones)
        if not phase_passed:
            print(f"\n  STOPPING: {phase_name} failed — skipping remaining phases")
            break

    # Final summary
    suite_elapsed = time.time() - suite_start
    total_tests = sum(r.total for _, r in all_results)
    total_passed = sum(r.passed for _, r in all_results)
    total_failed = sum(r.failed for _, r in all_results)
    all_ok = total_failed == 0 and total_tests > 0

    print("\n" + "=" * 64)
    print("  FINAL SUMMARY")
    print("=" * 64)
    for module_name, result in all_results:
        status = "PASS" if result.all_passed else "FAIL"
        print(f"  [{status}] {module_name}: {result.passed}/{result.total}")
    print(f"{'─' * 64}")
    print(f"  Total: {total_passed}/{total_tests} passed, {total_failed} failed")
    print(f"  Time:  {suite_elapsed:.1f}s")
    print(f"  {'ALL PASSED' if all_ok else 'FAILURES DETECTED'}")
    print("=" * 64 + "\n")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
