# Enrichment — Definitive Healthcare Contact Discovery

Contact discovery and account enrichment system using the Definitive Healthcare HospitalView API. Queries DH for executives, physicians, quality/financial metrics, and trigger signals across Glytec's target hospital universe.

## Status

**Everything in this directory is operational.** The core library and all 10 recipes are production-quality tools tuned for Glytec's sales motion — not experiments.

### Core Library

| File | Status | What it does |
|------|--------|-------------|
| `db.py` | **Operational** | SQLite layer (9 tables: runs, api_calls, executives, physicians, rfp_contacts, news_contacts, trigger_signals, account_enrichment, facility_status). WAL mode, retry logic, thread-safe |
| `dh_client.py` | **Operational** | DH HospitalView API client. Auth, pagination, rate-limit retry (429/5xx), request logging, dry-run mode. 15+ endpoints (hospitals, executives, physicians, quality, financials, news, affiliations, memberships, RFPs) |
| `icp_matcher.py` | **Operational** | 66-title ICP matcher with 3-stage matching (exact -> keyword -> department/level scoring). 11 pre-built DH API search batches for targeted discovery (C-Suite, Pharmacy, Nursing, Quality, Safety, Informatics, Critical Care, Surgery, Endocrinology, Diabetes, Hospital Medicine) |
| `runner.py` | **Operational** | CLI orchestrator. Loads CSVs, inits DB, runs recipes. Supports `--live`, `--resume --run-id N`, `--workers N`, `--status` |

### recipes/ — 10 Discovery Recipes

All operational. See `recipes/README.md` for the full catalog.

## Quick Start

```bash
cd enrichment/experiments/

# Check run history and totals
python runner.py --status

# Dry-run a recipe (default)
python runner.py recipe01 --hospital-id 1234

# Live run
python runner.py recipe04 --live --workers 5

# Resume a partial run
python runner.py recipe04 --live --resume --run-id 42
```

## Database

SQLite at `enrichment/data/enrichment.db`. 9 tables:

| Table | Contents |
|-------|----------|
| `runs` | Recipe execution log (recipe, status, start/end, stats) |
| `api_calls` | Full DH API call audit trail (endpoint, params, status, response time) |
| `executives` | DH executive records with ICP match metadata |
| `physicians` | DH physician records (endocrinologists, hospitalists, etc.) |
| `rfp_contacts` | Contacts found through RFP/bid data |
| `news_contacts` | Leadership changes detected through DH news feed |
| `trigger_signals` | Sales trigger signals (leadership change, EHR migration, M&A, financial distress) |
| `account_enrichment` | Quality metrics (HAC, readmission, VBP) + financial metrics (margin, utilization, IT budget) |
| `facility_status` | Processing status per facility per recipe (for resume support) |

## Environment

Requires `DH_API_KEY` in `.env` at project root. Dry-run is default — pass `--live` to make real API calls.
