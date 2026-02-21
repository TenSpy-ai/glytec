# Pipeline V1 — Local Outbound Pipeline

Local replica of the full 7-step outbound pipeline. Uses SQLite as the local Clay/Salesforce substitute, CSV data as the source of truth, and the Salesforge API for the outbound layer.

## Status

| File | Status | Notes |
|------|--------|-------|
| `config.py` | **Operational** | Central config (API keys, scoring weights, paths, kill-switch thresholds) |
| `db.py` | **Operational** | SQLite schema (6 tables: accounts, facilities, contacts, sequences, messages, api_log) |
| `run_pipeline.py` | **Operational** | CLI orchestrator (`--live`, `--steps 1,2,3`) |
| `step1_load_data.py` | **Operational** | CSV ingestion (1,683 accounts, 8,458 facilities) |
| `step2_score_accounts.py` | **Operational** | 6-factor scoring model; trigger signals are hardcoded for top ~15 accounts (stand-in for DH/Clay data) |
| `step3_enrich_contacts.py` | **Experiment** | Pre-filled demo contacts + simulated Firecrawl API calls. In production this would use DH API + Firecrawl + Claygent |
| `step4_wash_contacts.py` | **Operational** | Full wash pipeline: dedup, validate, suppress, LinkedIn check, ICP match, account map |
| `step5_compose_messages.py` | **Operational** | 3-layer message composition (persona + EHR + financial + trigger signal hook) |
| `step6_push_to_salesforge.py` | **Operational** | Salesforge sequence creation + enrollment. Verified API patterns with 20+ gotchas documented in code |
| `step7_pull_metrics.py` | **Operational** | Analytics pull, thread sync, kill-switch threshold monitoring |

**Summary:** 9 of 10 files are operational. Step 3 is the only true experiment — it simulates contact enrichment that would come from external APIs in production. The rest is a working local pipeline.

## Quick Start

```bash
cd pipeline/experiments/
python run_pipeline.py              # dry-run (default)
python run_pipeline.py --live       # live Salesforge API calls
python run_pipeline.py --steps 1,2  # run specific steps only
```

## Scoring Model (Step 2)

| Factor | Weight | Logic |
|--------|--------|-------|
| Bed count | 20% | >=600=100, 400-599=80, 200-399=60, 100-199=40, <100=20 |
| Operating margin | 15% | Negative=100, 0-5%=70, 5-10%=40, >10%=20 |
| EHR vendor | 20% | MEDITECH=100, Cerner=90, Other=80, Epic=40 |
| CMS quality | 15% | 1-star=100, 2=80, 3=60, 4=40, 5=20 |
| Trigger signal | 20% | Pre-filled for top accounts: 100 if signal, 20 if not |
| Contact coverage | 10% | >=15=100, 10-14=70, 5-9=40, <5=20 |

**Tiers:** Priority (80-100), Active (60-79), Nurture (40-59), Monitor (<40)

## Message Composition (Step 5)

1. **Persona layer** — Maps ICP title to messaging frame (CNO=safety, CFO=ROI, CQO=compliance, CEO=strategic)
2. **EHR layer** — Maps facility EHR to angle (Epic=unvalidated calc liability, Cerner=Oracle transition risk, MEDITECH=modernization)
3. **Financial layer** — Maps margin to urgency (negative=savings, healthy=competitive differentiation)
4. **Signal hook** — Trigger signal as personalized opening line

## Production Mapping

| Pipeline Step | Production System |
|--------------|-------------------|
| Step 1 (Load Data) | Clay data ingestion from DH API / ZoomInfo |
| Step 2 (Score) | Clay scoring formulas -> Salesforce Account Score field |
| Step 3 (Enrich) | Firecrawl + Perplexity + Claygent via Clay |
| Step 4 (Wash) | Clay dedup + NeverBounce/ZeroBounce + Salesforce suppression |
| Step 5 (Compose) | Claude API message generation with 3-layer framework |
| Step 6 (Push) | Clay -> Salesforce -> Salesforge sequence creation |
| Step 7 (Metrics) | Salesforge webhooks -> Salesforce -> dashboard |

## Internal Dependencies

```
run_pipeline.py
  +-- config.py
  +-- db.py
  +-- step1 -> config, db, pandas
  +-- step2 -> config, db
  +-- step3 -> config, db
  +-- step4 -> config, db, pandas, difflib
  +-- step5 -> config, db, step2 (TRIGGER_SIGNALS)
  +-- step6 -> config, db, requests
  +-- step7 -> config, db, requests
```

## Environment

Requires `SALESFORGE_API_KEY` in `.env` at project root. Auth uses raw key (no Bearer prefix).
