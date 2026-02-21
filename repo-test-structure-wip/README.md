# GTM Engineering — Repo Structure

Production repo structure for Glytec's AI SDR system. Organized by **workflow phase** — the same philosophy as [`gtm-hello-world/`](../gtm-hello-world/), which serves as the working reference implementation.

Where `gtm-hello-world/` is a light, testable subset (23 seed contacts, 9 campaign templates, scripts you can run today), this structure is the production expansion: multi-source enrichment, full campaign operations, automated monitoring, CRM handoff, and ongoing research.

The guiding principle: **folders follow the work, not the capability.** Code is organized by *when* it runs in the campaign lifecycle, not *what kind* of technology it uses.

---

## The 12-Step Workflow

Every outbound campaign follows the same lifecycle, defined in [`gtm-hello-world/PROCESS.md`](../gtm-hello-world/PROCESS.md). Each step maps to a folder in this repo:

| Step | What happens | Folder | gtm-hello-world equivalent |
|------|-------------|--------|---------------------------|
| **1. Pick a Recipe-Campaign** | Choose a campaign template mapped to an enrichment recipe (R1-R10) | `campaigns/templates/` | `campaigns/*.md` |
| **2. Discover Contacts** | Run enrichment skills to pull ICP-matched contacts from data providers | `enrichment/` | `/dh-*` skills + enrichment DB queries |
| **3. Create Campaign** | Build the campaign shell: name, settings, daily limits | `outbound/sequencing/` | `create_campaign` MCP call |
| **4. Set Email Steps** | Add multi-step sequences with A/B variants and delay timing | `campaigns/copywriting/` + `outbound/sequencing/` | `update_campaign` MCP call |
| **5. Assign Senders** | Pick warmed, domain-diverse mailboxes | `outbound/sender-infra/` | `check_status.py` mailbox section |
| **6. Enroll Contacts** | Bulk-add contacts with custom variables (title, tier, signal, EHR) | `outbound/sequencing/` | `add_leads_to_campaign_or_list_bulk` |
| **7. Activate Campaign** | Pre-flight checklist, then go live | `outbound/sequencing/` | `activate_campaign` |
| **8. Daily Monitoring** | Pull metrics, run kill-switch checks (bounce >5%, spam >0.3%) | `monitoring/metrics/` + `monitoring/kill-switch/` | `pull_metrics.py --live` |
| **9. Reply Processing** | Classify sentiment, route positive replies, suppress negatives | `monitoring/replies/` | `process_replies.py --live` |
| **10. Weekly Reporting** | Dashboard review, week-over-week trends, mailbox health | `monitoring/reporting/` | `check_status.py` |
| **11. Monthly Signal Refresh** | Re-run R3 (leadership changes) and R9 (account enrichment) | `enrichment/signal-detection/` | `/dh-signals` skills |
| **12. Quarterly Contact Refresh** | Re-run R4 (tiered discovery), dedup, verify, score, plan next wave | `enrichment/recipes/` + `crm/data-hygiene/` | `/dh-accounts` skills |

---

## Folder Guide

### `enrichment/` — Steps 1-2: Build the Target List

Everything that turns raw data provider records into scored, ICP-matched contacts ready for outreach.

```
enrichment/
├── recipes/              # DH discovery recipes (R1-R10)
├── icp-scoring/          # ICP title matching + fit scoring
├── signal-detection/     # Trigger signals (leadership, EHR, M&A, financial)
└── enrichment-chains/    # Multi-source pipelines (DH -> ZoomInfo -> web research)
```

**`recipes/`** — The 10 Definitive Healthcare recipes that power contact discovery. Each recipe has a specific scope and output:

| Recipe | Name | Scope | Existing code |
|--------|------|-------|--------------|
| R1 | Full Contact Extraction | Single hospital | `enrichment/experiments/recipes/r1_*.py` |
| R2 | ICP-Matched Contacts | Single hospital | `enrichment/experiments/recipes/r2_*.py` |
| R3 | Leadership Changes | Parent system | `enrichment/experiments/recipes/r3_*.py` |
| R4 | Tiered ICP Discovery | Segment (Enterprise/Commercial) | `enrichment/experiments/recipes/r4_*.py` |
| R5 | EHR-Segmented Discovery | Segment + EHR vendor | `enrichment/experiments/recipes/r5_*.py` |
| R6 | Financial Distress | Segment | `enrichment/experiments/recipes/r6_*.py` |
| R7 | Territory Contacts | Rep assignment | `enrichment/experiments/recipes/r7_*.py` |
| R8 | Physician Champions | Single hospital | `enrichment/experiments/recipes/r8_*.py` |
| R9 | Account Enrichment Bundle | Segment | `enrichment/experiments/recipes/r9_*.py` |
| R10 | System-Wide Contacts | Parent system | `enrichment/experiments/recipes/r10_*.py` |

**`icp-scoring/`** — 66-title ICP taxonomy with department, category, intent score, and job level. Contacts are scored against this to determine tier (Priority/Active/Nurture/Monitor). Existing: `enrichment/experiments/icp_matcher.py` + `data/AI SDR_ICP Titles_*.csv`.

**`signal-detection/`** — Trigger events that indicate buying readiness: leadership changes (new_hire, title_change, role_change), EHR migrations, M&A activity, financial distress (CMS penalties, margin decline), expansion announcements. Monthly refresh via R3 and R9. Existing: 301K+ trigger signals in `enrichment/data/enrichment.db`.

**`enrichment-chains/`** — Multi-source pipelines that chain providers so each fills gaps the previous one left. Example: DH for org data and titles, ZoomInfo for verified email/phone, Firecrawl for web research context. No single source has everything.

---

### `campaigns/` — Steps 3-4: Campaign Design

Campaign templates and messaging frameworks. The *what* of outreach — content, structure, and personalization logic — separate from the *how* of execution.

```
campaigns/
├── templates/            # Campaign markdown files (like gtm-hello-world/campaigns/)
└── copywriting/          # Persona x EHR x financial messaging frameworks
```

**`templates/`** — One markdown file per campaign type, exactly like `gtm-hello-world/campaigns/`. Each template specifies: target audience, enrichment recipe, email steps with A/B variants, custom variables, and enrollment criteria.

**Recipe-Campaign Mapping** (from `gtm-hello-world/PROCESS.md`):

| Template | Recipe | Target audience |
|----------|--------|----------------|
| 01-new-in-role.md | R3 | Leaders with recent title/role changes |
| 02-priority-account.md | R4 | High-value accounts by score and opportunity |
| 03-ehr-epic.md | R5 | Epic hospitals |
| 04-ehr-cerner.md | R5 | Cerner hospitals |
| 05-ehr-meditech.md | R5 | MEDITECH hospitals |
| 06-financial-recovery.md | R6 | Financially distressed systems |
| 07-territory-outreach.md | R7 | Rep-assigned territories |
| 08-physician-champion.md | R8 | Physician advocates for insulin management |
| 09-account-deep-dive.md | R1/R2/R9/R10 | Single-account deep targeting |

**`copywriting/`** — Persona-based messaging frameworks. Each contact's role maps to a messaging frame: CFO gets ROI language, CNO gets patient safety language, CMO gets clinical outcomes. Layer in EHR vendor context (Epic vs Cerner pain points) and financial signals (CMS penalties, margin pressure). Existing: `data/AI SDR_Glytec_New Story_Magnetic Messaging Framework_*.docx`.

---

### `outbound/` — Steps 5-7: Execution

The machinery that turns enriched contacts and campaign templates into sent emails.

```
outbound/
├── sequencing/           # Create campaigns, set steps, enroll, activate
├── sender-infra/         # Mailbox health, warmup, domain rotation
└── deliverability/       # Inbox placement, domain reputation
```

**`sequencing/`** — Full campaign lifecycle operations: create sequence, set email steps with A/B variants, assign mailboxes, bulk-enroll contacts with custom variables, activate, pause, resume. All dry-run by default. Existing: `salesforge/ops/` scripts (launch, enroll, toggle).

**`sender-infra/`** — Mailbox management: warmup monitoring, connectivity checks, domain rotation strategy. Selection criteria: Active status, warmup score >85, domain diversity per recipient company. Existing: `salesforge/sync/` for mailbox sync, `/sf-mailbox-health` command.

**`deliverability/`** — Inbox placement monitoring, domain reputation tracking, spam trap avoidance. The feedback loop between sending and deliverability — if metrics degrade, the system should surface it before campaigns are damaged.

---

### `monitoring/` — Steps 8-10: The Daily Operations Loop

The biggest gap in any abstract capability-organized repo. In `gtm-hello-world/`, this is three scripts (`pull_metrics.py`, `process_replies.py`, `check_status.py`) that are the most-run code in the entire system. They deserve a top-level home.

```
monitoring/
├── metrics/              # Daily analytics pull, snapshots, trends
├── kill-switch/          # Bounce/spam/unsub threshold auto-pause
├── replies/              # Sentiment classification, intent routing
└── reporting/            # Weekly, monthly, quarterly dashboards
```

**`metrics/`** — Daily pull of campaign analytics: sent, opened, replied, bounced, unsubscribed. Snapshot storage for trend analysis. Existing: `salesforge/ops/` metrics scripts, `/sf-metrics` command.

**`kill-switch/`** — Automatic campaign pausing when safety thresholds are breached:
- Bounce rate > 5% — pause immediately
- Spam rate > 0.3% — pause and investigate
- Unsubscribe rate > 2% — pause and review content

This is the safe-by-default pattern from `gtm-hello-world/PROCESS.md` Step 8. No campaign should run unsupervised without kill-switch protection. Existing: threshold checks in `pull_metrics.py`.

**`replies/`** — Sentiment classification and intent routing. When a reply comes in: classify (interested, not now, wrong person, OOO, unsubscribe, DNC), assign follow-up action, route positive replies toward CRM handoff. Existing: `process_replies.py`, `/sf-replies` command.

**`reporting/`** — Aggregated dashboards at weekly, monthly, and quarterly cadence. Week-over-week trend comparison, reply sentiment breakdown, Clay push status, mailbox health, API error rates. Existing: `check_status.py`, `/sf-campaigns` command.

---

### `crm/` — CRM Handoff

Positive outbound replies become CRM records and pipeline opportunities.

```
crm/
├── clay-sync/            # Positive replies -> Clay webhook -> Salesforce
├── data-hygiene/         # Dedup, validation, suppression, DNC
└── pipeline/             # Meeting attribution, funnel reporting
```

**`clay-sync/`** — The bridge from outbound to Salesforce. Positive replies are pushed to a Clay webhook, which handles enrichment and Salesforce record creation. This is a one-way push — Clay does the CRM logic. Existing: `push_to_clay.py`, `CLAY_WEBHOOK_URL` in `.env`.

**`data-hygiene/`** — Deduplication, email validation, suppression list management, DNC enforcement, catch-all domain detection, stale contact cleanup. Bad data compounds: one duplicate creates two emails creates one spam complaint creates a domain reputation hit. Quarterly refresh (Step 12) depends on clean dedup. Existing: `/sf-dnc` command.

**`pipeline/`** — Meeting attribution and funnel reporting. Track which campaigns and contacts convert to meetings, opportunities, and revenue. The answer to "is outbound working?" at the business level, not the email metrics level.

---

### `research/` — Account Intelligence

Deeper research beyond structured data providers. Enrichment gives you *who* to contact; research tells you *what to say* and *why now*.

```
research/
├── prospect-briefs/      # Auto-generated account summaries for reps
├── web-crawling/         # Firecrawl/Perplexity research
└── competitive/          # Competitor presence + displacement opportunities
```

**`prospect-briefs/`** — One-page account briefs generated before rep calls: org summary, key contacts, recent trigger signals, financial health, competitive landscape, suggested talk tracks. Everything a rep needs to sound prepared, generated in seconds.

**`web-crawling/`** — Automated web research on target accounts: press releases, job postings (hiring signals), board minutes, RFP announcements, conference presentations. Structured data providers miss a lot — the web fills the gaps.

**`competitive/`** — Competitor tracking: which accounts use competing insulin management products, contract renewal timing, pain points the competitor doesn't solve, displacement messaging angles.

---

### `lib/` — Shared Infrastructure

Reusable code that any folder can import. The DRY foundation so new scripts don't reinvent plumbing.

```
lib/
├── config/               # Environment, API keys, thresholds, constants
├── db/                   # Schema, migrations, seed data
└── clients/              # API client wrappers (reusable across all folders)
```

**`config/`** — Centralized configuration: API keys from `.env`, safety thresholds (bounce 5%, spam 0.3%, unsub 2%), daily send limits, ICP score cutoffs, tier definitions. Existing: `gtm-hello-world/config.py`.

**`db/`** — Database schema definitions, migration scripts, seed data. The system is database-centric — SQLite is the source of truth for contacts, campaigns, metrics, and replies. Existing schemas: `enrichment/experiments/db.py` (8 tables, 814K records), `salesforge/db.py` (20 tables), `gtm-hello-world/seed_db.py` (11 tables).

**`clients/`** — API client wrappers for external services: Salesforge, Instantly, Definitive Healthcare, Clay, Warmforge. Auth, rate limiting, error handling, and logging in one place so every script doesn't reimplement it. Existing: `enrichment/experiments/dh_client.py` for DH.

---

## Key Patterns

These patterns are proven in `gtm-hello-world/` and carry forward into production:

### Safe by Default (Dry-Run)

Every script that touches an external API runs in **dry-run mode** by default. It logs what it *would* do without doing it. Pass `--live` to execute for real. This means you can run any script safely to see what it does before committing to API calls.

```bash
python pull_metrics.py          # dry-run: shows what would be fetched
python pull_metrics.py --live   # live: actually pulls from API
```

### Database-Centric

SQLite is the local source of truth. Contacts, campaigns, metrics, replies, and API calls are all stored locally before and after API operations. This means:
- You can query state without hitting external APIs
- Operations are auditable (every API call is logged)
- Recovery from failures is possible (replay from local state)

### Recipe-Driven Campaigns

Every campaign maps to an enrichment recipe (R1-R10). The recipe determines *who* gets contacted. The campaign template determines *what* they receive. This separation means you can reuse the same recipe across different messaging strategies, or the same messaging template across different contact sets.

### Sentiment Classification

Reply processing uses AI interest scoring combined with keyword overrides to classify intent. Positive replies route to CRM handoff (Clay webhook). Negative replies suppress further outreach. OOO replies are archived and retried later. The goal: no reply goes unhandled for more than 24 hours.

### Kill-Switch Monitoring

Automated safety thresholds that pause campaigns before they cause damage:
- **Bounce >5%** — bad data, pause immediately to protect domain reputation
- **Spam >0.3%** — content or targeting issue, pause and investigate
- **Unsub >2%** — messaging misalignment, pause and review

---

## What Exists vs What's Planned

Mapping existing code to where it lives in this structure:

| Existing code | Current location | Production folder |
|--------------|-----------------|-------------------|
| 10 DH recipes (R1-R10) | `enrichment/experiments/recipes/` | `enrichment/recipes/` |
| DH API client | `enrichment/experiments/dh_client.py` | `lib/clients/` |
| ICP matcher (66 titles) | `enrichment/experiments/icp_matcher.py` | `enrichment/icp-scoring/` |
| SQLite schema + utilities | `enrichment/experiments/db.py` | `lib/db/` |
| Recipe CLI runner | `enrichment/experiments/runner.py` | `enrichment/recipes/` |
| Campaign launch ops | `salesforge/ops/` | `outbound/sequencing/` |
| Enrollment ops | `salesforge/ops/` | `outbound/sequencing/` |
| Metrics sync | `salesforge/ops/` + `salesforge/sync/` | `monitoring/metrics/` |
| Reply processing | `salesforge/ops/` | `monitoring/replies/` |
| Mailbox sync | `salesforge/sync/` | `outbound/sender-infra/` |
| 20-table ops schema | `salesforge/db.py` | `lib/db/` |
| 9 campaign templates | `gtm-hello-world/campaigns/` | `campaigns/templates/` |
| Metrics pull script | `gtm-hello-world/pull_metrics.py` | `monitoring/metrics/` |
| Reply processor | `gtm-hello-world/process_replies.py` | `monitoring/replies/` |
| Clay push script | `gtm-hello-world/push_to_clay.py` | `crm/clay-sync/` |
| Status dashboard | `gtm-hello-world/check_status.py` | `monitoring/reporting/` |
| Config + constants | `gtm-hello-world/config.py` | `lib/config/` |
| Seed data script | `gtm-hello-world/seed_db.py` | `lib/db/` |
| 12-step playbook | `gtm-hello-world/PROCESS.md` | This README |
| Messaging framework | `data/AI SDR_*_Messaging Framework_*.docx` | `campaigns/copywriting/` |
| ICP titles CSV | `data/AI SDR_ICP Titles_*.csv` | `enrichment/icp-scoring/` |
| Enrichment DB (814K records) | `enrichment/data/enrichment.db` | `enrichment/` (data dir) |

### Not yet built

| Folder | Status |
|--------|--------|
| `enrichment/enrichment-chains/` | Planned — multi-source chaining beyond DH |
| `outbound/deliverability/` | Planned — inbox placement monitoring |
| `monitoring/kill-switch/` | Partially exists in `pull_metrics.py` threshold checks, needs standalone module |
| `crm/pipeline/` | Planned — meeting attribution and funnel reporting |
| `research/prospect-briefs/` | Planned — auto-generated account summaries |
| `research/web-crawling/` | Planned — Firecrawl/Perplexity integration |
| `research/competitive/` | Planned — competitor tracking |
