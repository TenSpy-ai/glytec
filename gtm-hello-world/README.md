# GTM Hello World

A light, testable implementation of the Glytec GTM system. This folder contains everything needed to run outbound campaigns end-to-end: campaign designs, a SQLite database, seed data, tracking scripts, an autopilot orchestrator, and 16 slash commands for day-to-day operations.

## Quick Start

```bash
cd gtm-hello-world

# 1. Create and seed the database
python seed_db.py

# 2. Check the status dashboard
python check_status.py

# 3. Pull metrics (dry run — inserts placeholder zeros)
python pull_metrics.py

# 4. Process replies (dry run — processes any existing email_threads)
python process_replies.py

# 5. Push positive replies to Clay (dry run — shows payloads)
python push_to_clay.py
```

For the full 12-step operational playbook, see [PROCESS.md](PROCESS.md).

## Environment Variables

Set in `.env` at the project root (`/Users/oliviagao/project/glytec/.env`):

```
INSTANTLY_API_KEY=your_key_here          # Instantly API key — used for MCP + REST API auth
CLAY_WEBHOOK_URL=https://hooks.clay.com/your_webhook_here  # Clay webhook for positive reply push
```

| Variable | Required | Used by |
|----------|----------|---------|
| `INSTANTLY_API_KEY` | Yes | `mcp.py` (MCP protocol), `api.py` (REST API), `pull_metrics.py`, `process_replies.py` |
| `CLAY_WEBHOOK_URL` | For Clay push | `push_to_clay.py` — skips push gracefully if not set |

## Architecture

**MCP-first approach:** All Instantly operations use the MCP protocol client (`mcp.py`) as the primary interface — 38 tools over Streamable HTTP (JSON-RPC 2.0) at `https://mcp.instantly.ai/mcp/{API_KEY}`. The REST API client (`api.py`) is only used for endpoints with no MCP tool (currently just block list).

All scripts default to **dry run** mode. Use `--live` for real API calls. Read operations (list, get, count) always execute; write operations return mock data in dry-run mode.

## Folder Structure

```
gtm-hello-world/
├── README.md                        # This file
├── PROCESS.md                       # 12-step operational playbook
├── config.py                        # Paths, env vars, constants, API helpers
├── config_server.py                 # Stdlib HTTP server — serves tracker + config API (port 8099)
├── db.py                            # Shared get_conn() + log_api_call()
├── mcp.py                           # Instantly MCP protocol client (38 tools)
├── api.py                           # Instantly REST API client (block list fallback)
├── query_builder.py                 # Chainable contact query builder + natural language parser
├── autopilot.py                     # Campaign orchestrator (7-step pipeline) + daily monitor
├── seed_db.py                       # Create 14-table schema + insert seed data
├── check_status.py                  # Status dashboard from DB
├── pull_metrics.py                  # Pull Instantly analytics → metric_snapshots
├── process_replies.py               # Reply scanning + sentiment classification
├── push_to_clay.py                  # Positive reply → Clay webhook
├── ops/                             # Operational command scripts
│   ├── launch_campaign.py           # Full campaign lifecycle (create → enroll → activate)
│   ├── enroll_contacts.py           # Bulk enroll contacts into existing campaign
│   ├── campaign_status.py           # Campaign overview with stats
│   ├── toggle_campaign.py           # Pause or activate a campaign
│   ├── mailbox_health.py            # Sending account connectivity + warmup
│   ├── block_list.py                # Block list (DNC) — add/list/remove
│   ├── search_contacts.py           # Hybrid local DB + Instantly search
│   ├── account_view.py              # Account detail from local DB
│   └── verify_emails.py             # Email deliverability verification
├── sync/
│   └── sync_all.py                  # Full sync from Instantly (5 jobs)
├── campaigns/
│   ├── 01-new-in-role.md            # R3 → Leadership change outreach
│   ├── 02-priority-account.md       # R4 → Tier-based high-value targeting
│   ├── 03-ehr-epic.md               # R5 → Epic DIY calculator liability
│   ├── 04-ehr-cerner.md             # R5 → Oracle/Cerner transition urgency
│   ├── 05-ehr-meditech.md           # R5 → MEDITECH modernization
│   ├── 06-financial-recovery.md     # R6 → CMS penalties + margin pressure
│   ├── 07-territory-outreach.md     # R7 → Rep-aligned territory outreach
│   ├── 08-physician-champion.md     # R8 → Clinical champion strategy
│   └── 09-account-deep-dive.md      # R1/R2/R9/R10 → Account intelligence template
└── data/
    └── (gtm_hello_world.db — created by seed_db.py)
```

## Scripts

### Infrastructure

| Script | What it does |
|--------|-------------|
| `config.py` | Loads env vars, defines paths, constants, thresholds, API helpers |
| `db.py` | Shared `get_conn()` (SQLite + WAL mode) and `log_api_call()` |
| `mcp.py` | `InstantlyMCP` class — 38 MCP tools over Streamable HTTP (JSON-RPC 2.0) |
| `api.py` | `InstantlyAPI` class — REST API fallback for block list endpoints |
| `query_builder.py` | `ContactQuery` chainable filter builder + `parse_natural_language()` NL parser for lead selection |
| `autopilot.py` | `Autopilot` 7-step orchestrator (resolve template → select → preflight → create → enroll → activate → record) + `run_monitor()` daily cycle |
| `seed_db.py` | Creates 14-table schema + inserts seed data (10 accounts, 10 contacts, 3 mailboxes) |
| `config_server.py` | Local HTTP server (port 8099) — serves tracker.html + `/config`, `/dashboard`, `/tables`, `/runs/{id}` APIs |

### Root Scripts

| Script | What it does | Flag |
|--------|-------------|------|
| `check_status.py` | Prints 8-view dashboard from DB (accounts, contacts, campaigns, metrics, replies, events, API log, mailboxes) | — |
| `pull_metrics.py` | Pulls campaign analytics via MCP into `metric_snapshots`, runs kill-switch check | `--live` |
| `process_replies.py` | Pulls emails via MCP, classifies sentiment (positive/negative/neutral/OOO), triages for follow-up | `--live` |
| `push_to_clay.py` | Pushes unpushed positive replies to Clay webhook | `--live` |

### Operations (`ops/`)

| Script | What it does | Flag |
|--------|-------------|------|
| `launch_campaign.py` | Full lifecycle: create campaign → assign senders → bulk enroll → optionally activate | `--live` |
| `enroll_contacts.py` | Bulk enroll contacts into existing campaign (1000/call), deduped against block list | `--live` |
| `campaign_status.py` | List campaigns from Instantly MCP + local DB with status/leads/recipe | `--live` |
| `toggle_campaign.py` | Pause or activate a campaign via MCP | `--live` |
| `mailbox_health.py` | List sending accounts, test vitals, warmup analytics | `--live` |
| `block_list.py` | Block list CRUD via REST API (add/list/remove — reversible!) | `--live` |
| `search_contacts.py` | Hybrid search: local DB + Instantly MCP, auto-detects email/name/account | `--live` |
| `account_view.py` | Account detail: info, contacts, campaigns, sentiment, engagement (DB only) | — |
| `verify_emails.py` | Verify email deliverability via MCP (single or batch from DB) | `--live` |

### Sync (`sync/`)

| Script | What it does | Flag |
|--------|-------------|------|
| `sync_all.py` | 5 sync jobs: campaigns, leads, emails, accounts, metrics from Instantly MCP | `--live` |

## Slash Commands

All 16 commands are in `.claude/commands/instantly-*.md`:

| Command | Description |
|---------|-------------|
| `/instantly-launch` | Launch a campaign — full lifecycle from creation to enrollment |
| `/instantly-enroll` | Enroll contacts into an existing campaign |
| `/instantly-campaigns` | Campaign overview with inline stats |
| `/instantly-toggle` | Pause or activate a campaign |
| `/instantly-metrics` | Pull metrics + dashboard + kill-switch check |
| `/instantly-replies` | Check replies, classify sentiment, triage |
| `/instantly-sync` | Full sync from Instantly (5 jobs) |
| `/instantly-mailbox-health` | Check account connectivity + warmup |
| `/instantly-dnc` | Block list — add/list/remove (reversible!) |
| `/instantly-search` | Search contacts — local DB + Instantly |
| `/instantly-account` | Account view — details + contacts + engagement |
| `/instantly-clay-push` | Push positive replies to Clay webhook |
| `/instantly-status` | Full operational dashboard from DB |
| `/instantly-verify` | Verify emails before enrollment |
| `/instantly-autopilot` | End-to-end campaign creation from template + NL lead criteria |
| `/instantly-monitor` | Daily monitoring: metrics + replies + Clay push + kill-switch |
| `/config-server` | Start config server (port 8099) + open tracker in browser |
| `/config-server-stop` | Stop the background config server |
| `/config-server-restart` | Restart server + open browser |
| `/config-server-logs` | Server status, DB stats, last 50 log lines |

## Seed Data

- **14 tables** — accounts, contacts, campaigns, campaign_contacts, metric_snapshots, reply_sentiment, clay_push_log, email_threads, engagement_events, mailboxes, api_log, block_list, autopilot_runs, autopilot_steps
- **10 accounts** — diverse health systems (HCA, Kaiser, Providence, etc.)
- **10 contacts** — ICP Decision Makers across different titles and departments
- **3 mailboxes** — Clayton Maike across warmed domains
- **email_verified** column on contacts — populated by `/instantly-verify`

## Relationship to Production Design

This hello-world is a **purposeful subset** of the full production schema in `docs/instantly/gtm-operations-design-instantly.md`. It has 14 tables (vs 20+ in production) and focuses on the core campaign lifecycle: accounts → contacts → campaigns → metrics → replies → Clay push, with autopilot orchestration and step-level tracking.
