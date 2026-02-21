# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Glytec AI SDR — an AI-powered Sales Development Representative targeting hospital systems for Glytec's insulin management solutions. The system has three layers:

1. **Enrichment pipeline** — Definitive Healthcare API → 10 recipes → 814K+ records in SQLite
2. **Outbound operations** — Campaign creation, enrollment, monitoring, reply handling
3. **Downstream integration** — Positive replies → Clay webhook → Salesforce

## Environment

- Python 3.11, virtualenv at `.venv/`
- Activate: `source .venv/bin/activate`
- Auth keys in `.env`: `DATAGEN_API_KEY`, `INSTANTLY_API_KEY`, `DH_API_KEY`, `CLAY_WEBHOOK_URL`
- Install SDK: `pip install datagen-python-sdk`

## Project Structure

```
glytec/
├── data/                           # Source CSVs (facilities, accounts, ICP titles)
├── enrichment/                     # DH enrichment pipeline
│   ├── experiments/
│   │   ├── runner.py               # CLI orchestrator for recipes
│   │   ├── db.py                   # SQLite schema + utilities
│   │   ├── dh_client.py            # Definitive Healthcare API client
│   │   ├── icp_matcher.py          # 66-title ICP matching engine
│   │   └── recipes/                # 10 recipe scripts (R1-R10)
│   └── data/enrichment.db          # 814K+ records, 8 tables
├── pipeline/                       # Legacy 7-step pipeline (load→score→enrich→wash→compose→push→metrics)
├── gtm-hello-world/                # Primary GTM implementation (Instantly)
│   ├── ops/                        # 9 operational scripts (launch, enroll, toggle, search, etc.)
│   ├── sync/                       # Sync scripts (pull from Instantly API)
│   ├── campaigns/                  # 9 campaign MD files with email sequences
│   ├── data/                       # SQLite DB (created by seed_db.py)
│   ├── mcp.py                      # Instantly MCP wrapper (38 tools)
│   ├── api.py                      # Instantly REST API v2 client
│   ├── db.py                       # 12-table operational schema
│   ├── config.py                   # Paths, env vars, constants, thresholds
│   ├── config_server.py            # Stdlib HTTP server for config editing
│   ├── tracker.html                # Interactive campaign tracker + docs
│   ├── PROCESS.md                  # 12-step operational playbook
│   └── seed_db.py, check_status.py, pull_metrics.py, process_replies.py, push_to_clay.py
├── docs/
│   ├── instantly/                  # Instantly MCP + API design docs
│   └── salesforge/                 # Salesforge API reference (legacy archive)
└── .claude/
    ├── commands/                   # 14 /instantly-* commands for Instantly operations
    └── skills/                     # 3 /dh-* skills for enrichment recipes
```

## Skills (Enrichment — `/dh-*`)

Skills wrap the enrichment recipes with smart argument parsing and post-run reporting.

| Skill | Recipes | Usage |
|-------|---------|-------|
| `/dh-contacts` | R1, R2, R8, R10 | Single-hospital or single-system contact discovery |
| `/dh-accounts` | R4, R5, R6 | Batch discovery by segment, EHR vendor, or financial distress |
| `/dh-signals` | R3, R7, R9 | Trigger signals, territory contacts, account enrichment |

**Quick reference:**
- `/dh-contacts 2151` — Full extraction at Def ID 2151 (R1)
- `/dh-contacts icp 2151` — ICP-matched contacts (R2)
- `/dh-contacts physicians 2151` — Physician champions (R8)
- `/dh-contacts "Tenet Healthcare"` — Every contact in a system (R10)
- `/dh-accounts enterprise` — Tiered ICP discovery (R4)
- `/dh-accounts ehr enterprise` — EHR-segmented discovery (R5)
- `/dh-accounts distress enterprise` — Financial distress targeting (R6)
- `/dh-signals "CommonSpirit Health"` — Leadership changes (R3)
- `/dh-signals rep Clayton` — Territory contacts (R7)
- `/dh-signals enrich enterprise` — Account enrichment bundle (R9)

## Commands (Instantly Operations — `/instantly-*`)

Commands wrap Instantly operational scripts in `gtm-hello-world/`. All DRY-RUN by default.

| Command | What it does |
|---------|-------------|
| `/instantly-launch` | Create and launch a campaign (full lifecycle) |
| `/instantly-enroll` | Add contacts to an existing campaign |
| `/instantly-metrics` | Pull metrics + dashboard + kill-switch check |
| `/instantly-replies` | Pull reply threads, classify sentiment, triage |
| `/instantly-campaigns` | List all campaigns with inline stats |
| `/instantly-toggle` | Pause or activate a campaign |
| `/instantly-search` | Search contacts (auto-detects email, name, account, ICP, title) |
| `/instantly-account` | Account details + contacts + engagement |
| `/instantly-sync` | Full sync from Instantly API |
| `/instantly-dnc` | Block list — add, list, or remove entries (reversible) |
| `/instantly-mailbox-health` | Check mailbox connectivity + warmup status |
| `/instantly-status` | Full operational dashboard |
| `/instantly-verify` | Verify emails before enrollment |
| `/instantly-clay-push` | Push positive replies to Clay webhook → Salesforce |

## Commands (Config Server — `/config-server-*`)

Manage the local config server that serves `tracker.html` and exposes a config editing API.

| Command | What it does |
|---------|-------------|
| `/config-server` | Start server on port 8099 + open tracker in browser |
| `/config-server-stop` | Stop the background server |
| `/config-server-restart` | Restart server + open browser (use after editing server/tracker files) |
| `/config-server-logs` | Server status, DB stats, last 50 log lines |

## Data Files (`data/`)

| File | Contents |
|------|----------|
| `AI SDR_Facility List_1.23.26.csv` | Hospital facilities with beds, revenue, EHR, ICU stats, geo, ownership |
| `AI SDR_Facility List_Supplemental Data_1.23.26.csv` | Same facilities with rep assignments and additional clinical detail |
| `AI SDR_Parent Account List_1.23.26.csv` | Ranked parent health systems with bed counts, segment, opportunity $ |
| `AI SDR_ICP Titles_2.12.26.csv` | Ideal Customer Profile titles with department, category, intent score, job level |
| `AI SDR_Glytec_New Story_Magnetic Messaging Framework_1.28.26.docx` | Messaging framework for outreach |

Key join fields: `Definitive ID` links facilities across CSVs; `Highest Level Parent` groups facilities under parent systems.

## Databases

| Database | Location | Records | Purpose |
|----------|----------|---------|---------|
| Enrichment DB | `enrichment/data/enrichment.db` | 814K+ | DH contacts, physicians, trigger signals, account enrichment |
| Pipeline DB | `pipeline/glytec_v1.db` | — | Legacy: 6-table scoring + messaging pipeline |
| Hello World DB | `gtm-hello-world/data/gtm_hello_world.db` | 23 seed | 12-table operational DB for Instantly GTM |

## GTM Hello World (`gtm-hello-world/`)

Light testable implementation for running campaigns via Instantly MCP.

- **Quick start:** `cd gtm-hello-world && python seed_db.py && python check_status.py`
- **Test suite:** `cd gtm-hello-world && python -m tests.run_all` — 186 tests, 4-phase parallel runner
- **Playbook:** `PROCESS.md` — 12-step guide from contact discovery to quarterly refresh
- **Tracker:** `tracker.html` — interactive HTML progress tracker (open in browser)
- **9 campaigns** mapping to enrichment recipes R1-R10

### Architecture

- **MCP-first:** `mcp.py` calls 38 Instantly tools over Streamable HTTP (JSON-RPC 2.0). `api.py` is REST fallback for block list only.
- **Dry-run default:** All scripts use `DRY_RUN=True`. Reads always execute; writes return mock data. Pass `--live` for real calls.
- **No external deps:** Uses `urllib.request` (not requests library) — stdlib only.

### Instantly MCP Gotchas

- **Arguments must be wrapped in `params` key** — `{"arguments": {"params": {...}}}`, not `{"arguments": {...}}`
- **`create_campaign` uses `subject`/`body`** — NOT `campaign_schedule` or `sequences` (REST API schema differs from MCP tool schema)
- Campaign creation fails with `{"success": false, "stage": "no_accounts"}` when no sending accounts are connected
- `custom_variables` update REPLACES entire object — merge before updating
- `list_leads` uses POST body, not GET params
- Response types can be `dict`, `list`, or `str` (plain string when workspace is empty) — always type-check
- Pagination uses `items` key (not `data`)
- Block list endpoint is REST-only (`/block-lists-entries` with hyphens) — writes return 403 on current plan
- `email_list` is array of email strings, not IDs
- `skip_if_in_workspace=true` on bulk add prevents cross-campaign dupes
- `search_campaigns_by_contact` returns str when empty — known bug, calls `.get()` on str
- See `docs/instantly/api-test-results.md` for full verified behavior matrix (38 tools)

## Datagen SDK (tool execution in code)

- Execute tools by alias: `client.execute_tool("<tool_alias>", params)`
- Tool aliases: `mcp_<Provider>_<tool_name>` for connected MCP servers, or first-party like `listTools`, `searchTools`, `getToolDetails`
- **Always be schema-first**: confirm params via `getToolDetails` before calling a tool

### Required workflow

1. Verify `DATAGEN_API_KEY` exists (ask user if missing)
2. Create client: `from datagen_sdk import DatagenClient; client = DatagenClient()`
3. Discover tool alias with `searchTools` (never guess)
4. Confirm schema with `getToolDetails`
5. Execute with `client.execute_tool(tool_alias, params)`
6. Errors: 401/403 = bad key or unconnected MCP server; 400/422 = wrong params, re-check schema

### Quick reference

```python
from datagen_sdk import DatagenClient
client = DatagenClient()

client.execute_tool("listTools")                                    # all tools
client.execute_tool("searchTools", {"query": "send email"})         # search by intent
client.execute_tool("getToolDetails", {"tool_name": "mcp_Gmail_gmail_send_email"})  # schema
```

## Datagen MCP vs SDK

- **MCP**: interactive discovery/debugging of tool names and schemas
- **SDK**: execution in scripts and apps via `DatagenClient`
- In Claude Code (has shell access), prefer writing and running local SDK scripts over `executeCode`
