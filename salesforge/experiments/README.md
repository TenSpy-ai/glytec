# Salesforge GTM Operations System

Production-grade modular system for running Glytec's outbound GTM via code + SQLite, with Salesforge as the sending engine.

## Status

**Everything in this directory is operational.** Despite living under `experiments/`, this is a complete, tested GTM ops platform — not experimental code.

### Core Library

| File | Status | What it does |
|------|--------|-------------|
| `config.py` | **Operational** | API keys, scoring weights, tier thresholds, kill-switch params |
| `db.py` | **Operational** | 20-table SQLite schema with WAL mode, 15 indexes, ICP seed data |
| `api.py` | **Operational** | Full Salesforge API client with all verified endpoint rules baked in |
| `scoring.py` | **Operational** | 6-factor account scoring model (bed count, margin, EHR, CMS, triggers, coverage) |
| `icp.py` | **Operational** | 66-title ICP matcher (exact -> fuzzy -> keyword, 0.6 cutoff) |
| `compose.py` | **Operational** | 3-layer message engine (persona x EHR angle x financial urgency) |
| `migrate_from_pipeline.py` | **Utility** | One-time migration from pipeline v1 DB. Run once, not part of regular ops |

### ops/ — 25 Operational Scripts

All operational. See `ops/README.md` for the full catalog.

### sync/ — 6 Sync Jobs

All operational. See `sync/README.md` for details.

## Quick Start

```bash
cd salesforge/experiments/

# 1. Initialize database (20 tables + 15 indexes + 66 ICP titles)
python db.py

# 2. Migrate data from pipeline
python migrate_from_pipeline.py

# 3. Check mailbox health (live API)
python ops/mailbox_health.py

# 4. View campaigns
python ops/campaign_status.py

# 5. Search contacts
python ops/search_contacts.py --name "Clayton"

# 6. Launch a campaign (dry-run by default)
python ops/launch_campaign.py --campaign-name "Q1 Test" --dry-run
```

## Claude Code Commands

| Command | What it does |
|---------|-------------|
| `/project:sf-campaigns` | Campaign overview with stats |
| `/project:sf-metrics` | Sync + dashboard + kill-switch |
| `/project:sf-replies` | Pull and show reply threads |
| `/project:sf-mailbox-health` | Mailbox connectivity check |
| `/project:sf-sync` | Full data sync from Salesforge |
| `/project:sf-launch` | Launch a new campaign |
| `/project:sf-toggle` | Pause or activate a campaign |
| `/project:sf-enroll` | Enroll contacts in a campaign |
| `/project:sf-search` | Search contacts (auto-detect type) |
| `/project:sf-account` | Account detail view |
| `/project:sf-dnc` | Add to Do Not Contact list |

## What's Real vs Local

### Real (hits Salesforge API)
- Sequence CRUD (create, read, update name, delete)
- Step content (PUT replaces all steps)
- Mailbox assignment (PUT replaces all)
- Contact enrollment (import-lead)
- Campaign activate/pause
- Analytics pull (GET /analytics)
- Thread list (GET /threads)
- DNC add (POST /dnc/bulk)
- Mailbox list (GET /mailboxes)

### Local Only (SQLite)
- Contact search (API filters broken)
- Contact updates (no update API)
- Reply thread status tracking (handled, needs_follow_up)
- Campaign planning and backlog
- Email draft management
- Metric snapshots and trends
- Account scoring and tier assignment
- DNC list management (API is write-only)
- Suppression logic
- Meeting attribution

### Requires Salesforge UI
- Reconnect disconnected mailboxes
- Reply to prospect emails
- Delete/update webhooks
- Remove from DNC list
- Create new mailboxes
- View A/B variant-level metrics

## Dry-Run Mode

All campaign operations default to `DRY_RUN=True`. Pass `--live` to execute real API calls. The system always shows a preview before making changes.

## Database

SQLite at `salesforge/db/gtm_ops.db` with WAL mode. 20 tables covering: accounts, facilities, contacts, ICP titles, campaigns, campaign contacts, campaign steps, email templates, engagement events, reply threads, mailboxes, mailbox health log, DNC list, metric snapshots, account engagement, API log, sync state, UI tasks, and meetings.
