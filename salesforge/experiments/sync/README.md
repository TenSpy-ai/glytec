# sync/ — Salesforge Data Sync Jobs

6 sync scripts that pull live data from Salesforge API into local SQLite. All operational.

## Status: All Operational

These run regularly to keep local DB in sync with Salesforge state.

## Scripts

| Script | Syncs | Target Table | Frequency |
|--------|-------|-------------|-----------|
| `pull_sequences.py` | Sequence list + detail (contact count, step count, mailbox count) | campaigns | After any campaign change |
| `pull_metrics.py` | Daily analytics snapshots (opens, clicks, replies, bounces) | metric_snapshots | Daily |
| `pull_threads.py` | Reply threads, inserts new ones as "new" for manual review | reply_threads | Daily or on-demand |
| `pull_mailboxes.py` | Mailbox health (connected/disconnected status) | mailboxes, health_log | Daily |
| `pull_contacts.py` | Full contact sync, matches Salesforge contacts to local by email | contacts | Weekly |
| `sync_all.py` | Runs all 5 jobs sequentially, supports running individual jobs selectively | all | On-demand |

## Usage

```bash
# Run all sync jobs
python sync/sync_all.py

# Run individual jobs
python sync/pull_sequences.py
python sync/pull_metrics.py
python sync/pull_threads.py
```
