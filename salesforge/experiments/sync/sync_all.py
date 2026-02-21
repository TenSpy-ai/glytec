"""Run all sync jobs.

Usage:
    python -m salesforge.sync.sync_all                # all sync jobs
    python -m salesforge.sync.sync_all sequences      # specific job
    python -m salesforge.sync.sync_all contacts        # specific job
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sync.pull_sequences import pull_sequences
from sync.pull_metrics import pull_metrics
from sync.pull_threads import pull_threads
from sync.pull_mailboxes import pull_mailboxes
from sync.pull_contacts import pull_contacts


SYNC_JOBS = {
    "sequences": pull_sequences,
    "metrics": pull_metrics,
    "threads": pull_threads,
    "mailboxes": pull_mailboxes,
    "contacts": pull_contacts,
}


def sync_all(jobs=None):
    """Run sync jobs. If jobs is None, run all."""
    targets = jobs or list(SYNC_JOBS.keys())
    print(f"\n[sync] Running {len(targets)} sync job(s)...\n")

    for name in targets:
        fn = SYNC_JOBS.get(name)
        if fn:
            try:
                fn()
            except Exception as e:
                print(f"[sync:{name}] ERROR: {e}")
        else:
            print(f"[sync] Unknown job: {name}")

    print(f"\n[sync] Done.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        sync_all(args)
    else:
        sync_all()
