# GTM Operations System — Complete Reference

**System:** `salesforge/` — Glytec outbound GTM operations
**Database:** SQLite at `salesforge/db/gtm_ops.db` (WAL mode)
**Sending Engine:** Salesforge API (`https://api.salesforge.ai/public/v2`)
**Auth:** Raw API key in `Authorization` header — NO `Bearer` prefix
**Default Mode:** DRY_RUN=True on all campaign operations

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Database Schema](#2-database-schema)
3. [Foundation Modules](#3-foundation-modules)
4. [Salesforge API Client](#4-salesforge-api-client)
5. [Scoring Model](#5-scoring-model)
6. [ICP Matching Engine](#6-icp-matching-engine)
7. [Message Composition Engine](#7-message-composition-engine)
8. [Operations Scripts](#8-operations-scripts)
9. [Sync Scripts](#9-sync-scripts)
10. [Claude Code Commands](#10-claude-code-commands)
11. [Data Migration](#11-data-migration)
12. [API Surface Rules](#12-api-surface-rules)
13. [Architecture Decisions](#13-architecture-decisions)

---

## 1. Architecture

### Design Principle

SQLite is the operational homebase. Salesforge is a dumb sending pipe. Every piece of data we care about lives locally — contacts, scores, ICP matches, engagement, metrics, reply status, DNC lists. Salesforge gets what it needs to send emails: sequences, steps, mailboxes, and enrolled contacts.

### Module Dependency Graph

```
config.py ← (everything imports this)
    ↓
db.py ← (everything that touches SQLite)
    ↓
api.py ← (anything that hits Salesforge)
    ↓
scoring.py ← account_tiers.py, plan_wave.py, migrate_from_pipeline.py
icp.py ← bulk_import.py, update_contact.py
compose.py ← launch_campaign.py, draft_emails.py

ops/*.py → config, db, api (as needed)
sync/*.py → config, db, api
```

### File Inventory

| Category | Files | Lines |
|----------|-------|-------|
| Foundation | config.py, db.py, api.py, scoring.py, icp.py, compose.py | 1,362 |
| Operations | 25 scripts in ops/ | 2,553 |
| Sync | 6 scripts in sync/ | 409 |
| Migration | migrate_from_pipeline.py | 129 |
| Total | 38 Python files | 4,453 |

---

## 2. Database Schema

20 tables organized into 5 logical groups. 15 indexes on high-query columns.

### Core Entities

#### `accounts` — Parent health systems (1,683 rows from CSV)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| system_name | TEXT UNIQUE | **Primary join key** — used by contacts.account_name, facilities.highest_level_parent, account_engagement.account_name |
| definitive_id | TEXT | Definitive Healthcare ID |
| sfdc_account_id | TEXT | Salesforce CRM ID |
| city, state | TEXT | HQ location |
| segment | TEXT | Enterprise/Strategic, Commercial, Partner Growth |
| facility_count | INTEGER | Number of hospitals in system |
| total_beds | INTEGER | Sum across all facilities |
| avg_beds_per_facility | REAL | |
| primary_ehr | TEXT | Most common EHR across facilities |
| operating_margin_avg | REAL | Avg across facilities |
| cms_rating_avg | REAL | Avg CMS stars |
| readmission_rate_avg | REAL | |
| glytec_client | TEXT | "Y" or blank — existing customer flag |
| glytec_arr | REAL | Annual recurring revenue (existing clients) |
| gc_opp | REAL | Glucommander opportunity $ |
| cc_opp | REAL | CriticalCare opportunity $ |
| total_opp | REAL | gc_opp + cc_opp |
| adj_total_opp | REAL | Risk-adjusted |
| rank | INTEGER | Original CSV rank |
| score | REAL | 0-100 composite score (from scoring model) |
| tier | TEXT | Priority (80-100) / Active (60-79) / Nurture (40-59) / Monitor (0-39) |
| trigger_signal | TEXT | Latest signal (EHR migration, new CNO, etc.) |
| trigger_date | TEXT | When signal detected |
| assigned_rep | TEXT | |
| notes | TEXT | |
| created_at, updated_at | TIMESTAMP | Auto-managed |

#### `facilities` — Individual hospitals (8,458 rows from CSV)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| hospital_name | TEXT | |
| definitive_id | TEXT UNIQUE | Links across CSVs |
| highest_level_parent | TEXT | **FK → accounts.system_name** |
| city, state | TEXT | |
| firm_type | TEXT | |
| hospital_type | TEXT | |
| hospital_ownership | TEXT | |
| ehr_inpatient | TEXT | Epic, Cerner, Meditech, etc. — used by scoring + compose |
| staffed_beds | INTEGER | Used by scoring (bed_count factor) |
| icu_beds | INTEGER | |
| net_operating_profit_margin | REAL | Used by scoring (margin factor) + compose (financial frame) |
| cms_overall_rating | REAL | Used by scoring (cms_quality factor) |
| readmission_rate | REAL | Used by scoring (bonus in cms_quality) |
| avg_length_of_stay | REAL | |
| net_patient_revenue | REAL | |
| assigned_rep | TEXT | |
| created_at | TIMESTAMP | |

#### `contacts` — All contacts (25 columns, 20 from migration)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| first_name, last_name | TEXT | |
| email | TEXT UNIQUE | **Primary dedup key** |
| title | TEXT | Stored locally even though Salesforge drops it |
| phone | TEXT | Stored locally even though Salesforge drops it |
| company | TEXT | |
| linkedin_url | TEXT | Must omit or null for import-lead — **empty string → 400** |
| account_name | TEXT | **FK → accounts.system_name** |
| facility_definitive_id | TEXT | **FK → facilities.definitive_id** |
| icp_category | TEXT | Decision Maker / Influencer |
| icp_intent_score | INTEGER | 50-95 |
| icp_function_type | TEXT | Clinical / Business |
| icp_job_level | TEXT | Executive, Director, Mid-Level, IC |
| icp_department | TEXT | From ICP taxonomy |
| icp_matched | INTEGER | 0/1 — did title match an ICP title? |
| source | TEXT | zoominfo, dh, web_scraping, csv_import, manual |
| validated | INTEGER | 0/1 — email validated? |
| golden_record | INTEGER | 0/1 — survived dedup? |
| suppressed | INTEGER | 0/1 |
| suppression_reason | TEXT | glytec_client, dnc, opt_out, bounced, stale |
| salesforge_lead_id | TEXT | lead_xxx from Salesforge |
| last_pushed_at | TIMESTAMP | |
| created_at, updated_at | TIMESTAMP | |

#### `icp_titles` — ICP taxonomy (66 titles from ICP.json)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| department | TEXT | Clinical Informatics, Critical Care, Endocrinology, etc. (13 departments) |
| title | TEXT | e.g., "Chief Nursing Officer", "VP of Pharmacy" |
| category | TEXT | Decision Maker / Influencer |
| intent_score | INTEGER | 50-95 (higher = more relevant) |
| function_type | TEXT | Clinical / Business |
| job_level | TEXT | Executive, Director, Mid-Level, IC, Other |

### Campaign Management

#### `campaign_ideas` — Backlog of planned campaigns

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | TEXT | |
| description | TEXT | |
| target_segment, target_ehr, target_geo, target_tier, target_persona | TEXT | Targeting criteria |
| priority | TEXT | high/medium/low (default: medium) |
| status | TEXT | idea → planned → in_progress → launched → completed → archived |
| estimated_contacts | INTEGER | |
| notes | TEXT | |
| created_at, updated_at | TIMESTAMP | |

#### `campaigns` — Active campaigns (maps 1:1 to Salesforge sequences)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | TEXT | |
| idea_id | INTEGER | FK → campaign_ideas.id |
| salesforge_seq_id | TEXT | seq_xxx (null until pushed to Salesforge) |
| salesforge_status | TEXT | draft/active/paused/completed/deleted |
| target_segment, target_ehr, target_geo, target_tier, target_persona | TEXT | For local analytics rollups |
| step_count | INTEGER | Default 1 |
| mailbox_count | INTEGER | Default 0 |
| contact_count | INTEGER | Default 0 |
| status | TEXT | draft/ready/active/paused/completed/archived |
| launched_at, paused_at, completed_at | TIMESTAMP | |
| created_at, updated_at | TIMESTAMP | |

#### `campaign_contacts` — Junction table: which contacts in which campaigns

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| campaign_id | INTEGER | FK → campaigns.id |
| contact_id | INTEGER | FK → contacts.id |
| enrolled_at | TIMESTAMP | |
| status | TEXT | enrolled/contacted/replied/bounced/unsubscribed/completed |
| emails_sent, emails_opened, emails_clicked | INTEGER | Rollup from engagement_events |
| replied | INTEGER | 0/1 |
| reply_type | TEXT | positive/negative/ooo/null |
| bounced | INTEGER | 0/1 |
| UNIQUE(campaign_id, contact_id) | | Dedup constraint |

#### `campaign_steps` — Email steps within a campaign

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| campaign_id | INTEGER | FK → campaigns.id |
| step_order | INTEGER | 0-indexed |
| step_name | TEXT | "Initial email", "Follow-up 1" |
| wait_days | INTEGER | Days after previous step |
| email_subject, email_body_html, email_body_plain | TEXT | Content |
| layer1_persona, layer2_ehr, layer3_financial | TEXT | Composition attribution |
| signal_hook | TEXT | Personalized opening line |
| variant_label | TEXT | Default 'A' |
| distribution_weight | INTEGER | Default 100 |
| salesforge_step_id, salesforge_variant_id | TEXT | stp_xxx, stpv_xxx |
| synced_at | TIMESTAMP | |
| created_at, updated_at | TIMESTAMP | |

#### `email_templates` — Reusable email templates

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | TEXT | |
| category | TEXT | cold_email, follow_up, case_study, direct_cta |
| persona | TEXT | CNO, CFO, CQO, CEO, COO, CMO, general |
| ehr_segment | TEXT | epic, cerner, meditech, any |
| subject, body_html, body_plain | TEXT | |
| tags | TEXT | Comma-separated |
| times_used | INTEGER | Default 0 |
| avg_open_rate, avg_reply_rate | REAL | Updated from campaign performance |
| notes | TEXT | |
| created_at, updated_at | TIMESTAMP | |

### Engagement Tracking

#### `engagement_events` — Individual events from webhooks/analytics

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| campaign_id | INTEGER | FK → campaigns.id |
| contact_id | INTEGER | FK → contacts.id |
| contact_email | TEXT | Denormalized for quick lookup |
| event_type | TEXT | sent/opened/clicked/replied/bounced/unsubscribed |
| event_date | TIMESTAMP | |
| metadata | TEXT | JSON: reply content, bounce reason, link, etc. |
| source | TEXT | api_pull/webhook/manual |
| created_at | TIMESTAMP | |

#### `reply_threads` — Reply thread mirror (API is list-only)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| salesforge_thread_id | TEXT UNIQUE | mth_xxx |
| campaign_id | INTEGER | FK → campaigns.id |
| contact_id | INTEGER | FK → contacts.id |
| contact_email, contact_first_name, contact_last_name | TEXT | |
| subject, content | TEXT | Reply content |
| reply_type | TEXT | ooo, lead_replied |
| sentiment | TEXT | positive/negative/neutral/ooo (classified locally) |
| mailbox_id | TEXT | |
| event_date | TIMESTAMP | |
| status | TEXT | new/reviewed/needs_follow_up/handled/archived |
| handled_by | TEXT | Clayton, Reagan, etc. |
| handled_at | TIMESTAMP | |
| follow_up_notes | TEXT | |
| created_at, updated_at | TIMESTAMP | |

### Deliverability & Mailbox Health

#### `mailboxes` — Mailbox inventory (21 mailboxes, all Clayton Maike)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| salesforge_id | TEXT UNIQUE | mbox_xxx |
| address | TEXT | |
| first_name, last_name | TEXT | |
| daily_email_limit | INTEGER | 30/day each |
| provider | TEXT | gmail, outlook |
| status | TEXT | active/disconnected |
| disconnect_reason | TEXT | |
| tracking_domain | TEXT | |
| last_synced_at | TIMESTAMP | |
| created_at, updated_at | TIMESTAMP | |

#### `mailbox_health_log` — Daily health snapshots

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| mailbox_id | INTEGER | FK → mailboxes.id |
| snapshot_date | DATE | |
| status | TEXT | |
| disconnect_reason | TEXT | |
| created_at | TIMESTAMP | |
| UNIQUE(mailbox_id, snapshot_date) | | One snapshot per day |

#### `dnc_list` — Local DNC mirror (API is write-only)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| email | TEXT UNIQUE | |
| reason | TEXT | opt_out/bounce/suppression/manual |
| source | TEXT | webhook/manual/csv_import/salesforce |
| added_at | TIMESTAMP | |
| pushed_to_salesforge | INTEGER | 0/1 — have we POST'd to /dnc/bulk? |
| pushed_at | TIMESTAMP | |

### Reporting & Metrics

#### `metric_snapshots` — Daily metrics per campaign

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| campaign_id | INTEGER | FK → campaigns.id |
| salesforge_seq_id | TEXT | |
| snapshot_date | DATE | |
| contacted, sent, opened, unique_opened | INTEGER | |
| clicked, unique_clicked, replied, bounced, unsubscribed | INTEGER | |
| open_rate, reply_rate, bounce_rate, click_rate | REAL | |
| created_at | TIMESTAMP | |
| UNIQUE(campaign_id, snapshot_date) | | One snapshot per campaign per day |

#### `account_engagement` — Account-level engagement rollup

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| account_name | TEXT UNIQUE | FK → accounts.system_name |
| total_contacts, contacts_enrolled, contacts_opened, contacts_replied, contacts_bounced | INTEGER | |
| latest_campaign | TEXT | |
| latest_activity_date | TIMESTAMP | |
| engagement_tier | TEXT | hot (replied)/warm (opened)/cold (sent, no open)/untouched |
| updated_at | TIMESTAMP | |

### Operations

#### `api_log` — Every external API call

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| timestamp | TIMESTAMP | |
| endpoint | TEXT | |
| method | TEXT | GET/POST/PUT/DELETE |
| params | TEXT | JSON |
| response_code | INTEGER | |
| response_summary | TEXT | |

#### `sync_state` — Sync job tracking

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| entity | TEXT UNIQUE | contacts/sequences/threads/mailboxes/metrics |
| last_synced_at | TIMESTAMP | |
| last_offset | INTEGER | For paginated sync |
| total_records | INTEGER | |
| notes | TEXT | |
| updated_at | TIMESTAMP | |

#### `ui_tasks` — Things that must be done in Salesforge UI

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| task | TEXT | e.g., "Reconnect mailbox cmaike@glytec-health.com" |
| category | TEXT | mailbox/webhook/reply/dnc |
| priority | TEXT | high/medium/low |
| status | TEXT | pending/done |
| context | TEXT | Why this needs to happen |
| created_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |

#### `meetings` — Pipeline attribution

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| contact_id | INTEGER | FK → contacts.id |
| account_name | TEXT | |
| campaign_id | INTEGER | FK → campaigns.id |
| meeting_date | DATE | |
| meeting_type | TEXT | discovery/demo/follow_up |
| outcome | TEXT | scheduled/completed/no_show/rescheduled |
| notes | TEXT | |
| attributed_to | TEXT | ai_sdr/manual/referral |
| created_at | TIMESTAMP | |

### Indexes (15)

```sql
idx_contacts_email          ON contacts(email)
idx_contacts_account        ON contacts(account_name)
idx_contacts_icp            ON contacts(icp_category, icp_function_type)
idx_contacts_suppressed     ON contacts(suppressed)
idx_contacts_salesforge     ON contacts(salesforge_lead_id)
idx_campaigns_sf            ON campaigns(salesforge_seq_id)
idx_campaign_contacts_cid   ON campaign_contacts(campaign_id)
idx_campaign_contacts_contact ON campaign_contacts(contact_id)
idx_engagement_campaign     ON engagement_events(campaign_id)
idx_engagement_contact      ON engagement_events(contact_id)
idx_engagement_type         ON engagement_events(event_type)
idx_metrics_campaign        ON metric_snapshots(campaign_id, snapshot_date)
idx_dnc_email               ON dnc_list(email)
idx_reply_threads_status    ON reply_threads(status)
idx_account_engagement      ON account_engagement(engagement_tier)
```

### Key Relationships

```
accounts.system_name ← contacts.account_name
accounts.system_name ← facilities.highest_level_parent
accounts.system_name ← account_engagement.account_name

contacts.id ← campaign_contacts.contact_id
contacts.id ← engagement_events.contact_id
contacts.id ← reply_threads.contact_id
contacts.id ← meetings.contact_id
contacts.email = dnc_list.email (suppression check)

campaigns.id ← campaign_contacts.campaign_id
campaigns.id ← campaign_steps.campaign_id
campaigns.id ← engagement_events.campaign_id
campaigns.id ← metric_snapshots.campaign_id
campaigns.id ← meetings.campaign_id
campaigns.idea_id → campaign_ideas.id

mailboxes.id ← mailbox_health_log.mailbox_id
```

---

## 3. Foundation Modules

### `config.py` (89 lines)

Central configuration. All modules import from here.

**Constants:**

| Constant | Value | Used By |
|----------|-------|---------|
| `SALESFORGE_API_KEY` | From `.env` | api.py |
| `SALESFORGE_BASE_URL` | `https://api.salesforge.ai/public/v2` | api.py |
| `WORKSPACE_ID` | `wks_05g6m7nsyweyerpgf0wuq` | api.py |
| `PRODUCT_ID` | `prod_jfxqn21476u6o3m5ocogi` | api.py (create_sequence) |
| `DB_PATH` | `salesforge/db/gtm_ops.db` | db.py |
| `PIPELINE_DB_PATH` | `pipeline/glytec_v1.db` | migrate_from_pipeline.py |
| `ICP_JSON` | `outbound/ICP.json` | db.py (seeding), icp.py |
| `DRY_RUN` | `True` | All ops scripts |
| `BOUNCE_THRESHOLD` | `0.05` (5%) | kill_switch.py |
| `SPAM_THRESHOLD` | `0.003` (0.3%) | kill_switch.py |

**Scoring Weights:**
```python
SCORING_WEIGHTS = {
    "bed_count": 0.20,
    "margin": 0.15,
    "ehr": 0.20,
    "cms_quality": 0.15,
    "trigger_signal": 0.20,
    "contact_coverage": 0.10,
}
```

**Tier Thresholds:**
```python
TIER_THRESHOLDS = {
    "Priority": (80, 100),
    "Active": (60, 79),
    "Nurture": (40, 59),
    "Monitor": (0, 39),
}
```

**Functions:**

| Function | Signature | Returns |
|----------|-----------|---------|
| `enable_live_mode()` | `()` | Sets DRY_RUN=False |
| `salesforge_headers()` | `()` | `{"Authorization": key, "Content-Type": "application/json"}` |
| `workspace_url(path)` | `(path: str = "")` | Full workspace-scoped URL |

### `db.py` (436 lines)

Database schema + initialization. Creates all 20 tables, 15 indexes, and seeds ICP titles.

**Functions:**

| Function | Signature | Behavior |
|----------|-----------|----------|
| `init_db()` | `()` | Creates parent dirs, all tables (CREATE IF NOT EXISTS), all indexes, seeds icp_titles from ICP.json if empty. Enables WAL mode. Idempotent — safe to call repeatedly. |
| `get_conn()` | `() → sqlite3.Connection` | Returns connection with `row_factory = sqlite3.Row` and WAL mode. All ops scripts use this. |

**sqlite3.Row behavior note:** Row objects support `row["column"]` bracket access but do NOT support `.get()`. All code must use `row["col"]` directly.

---

## 4. Salesforge API Client

### `api.py` (406 lines) — `SalesforgeClient`

Wraps every verified Salesforge API endpoint. Every method encodes the exact rules discovered through testing (documented in `docs/salesforge/salesforge-api-rules.md`).

**Constructor:**
```python
SalesforgeClient(dry_run=None)  # defaults to config.DRY_RUN
```

In dry-run mode, all write methods log `[DRY RUN]` and return mock data instead of making HTTP calls.

### Sequence Methods

| Method | Signature | API Call | Notes |
|--------|-----------|----------|-------|
| `list_sequences` | `(limit=50, offset=0)` | GET /sequences | Filters broken — must filter client-side |
| `get_sequence` | `(seq_id)` | GET /sequences/{id} | Returns steps + mailboxes |
| `create_sequence` | `(name)` | POST /sequences | Auto-fills productId, language="american_english", timezone="America/New_York" |
| `update_sequence` | `(seq_id, **kwargs)` | PUT /sequences/{id} | Only allows: name, openTrackingEnabled, clickTrackingEnabled. Blocks productId (500), language (ignored), timezone (ignored) |
| `delete_sequence` | `(seq_id)` | DELETE /sequences/{id} | Returns 204. Only destructive DELETE that works. |
| `set_status` | `(seq_id, status)` | PUT /sequences/{id}/status | status must be "active" or "paused". Cannot go back to draft. |

### Step Methods

| Method | Signature | API Call | Notes |
|--------|-----------|----------|-------|
| `update_steps` | `(seq_id, steps)` | PUT /sequences/{id}/steps | **Replaces ALL steps.** Min 1 step. Each step needs distributionStrategy. Each variant needs label + status. |

### Mailbox Methods

| Method | Signature | API Call | Notes |
|--------|-----------|----------|-------|
| `list_mailboxes` | `(limit=100, offset=0)` | GET /mailboxes | Read-only — no create/update/delete via API |
| `get_mailbox` | `(mailbox_id)` | GET /mailboxes/{id} | |
| `assign_mailboxes` | `(seq_id, mailbox_ids)` | PUT /sequences/{id}/mailboxes | **Full replacement.** Empty array clears all. Invalid ID → 500. |
| `get_all_mailbox_ids` | `()` | GET /mailboxes | Helper: returns list of all mailbox IDs |

### Contact Methods

| Method | Signature | API Call | Notes |
|--------|-----------|----------|-------|
| `list_contacts` | `(limit=50, offset=0)` | GET /contacts | Only 8 fields returned. Filters broken. |
| `get_contact` | `(contact_id)` | GET /contacts/{id} | Same 8 fields as list |
| `create_contact` | `(first_name, last_name, email, company="", linkedin_url=None, tags=None, custom_vars=None)` | POST /contacts | Duplicate email → same lead ID (upsert). jobTitle/phone don't persist. |
| `create_contacts_bulk` | `(contacts)` | POST /contacts/bulk | Each contact must have `tags` array |
| `import_lead` | `(seq_id, first_name, last_name, email, company, linkedin_url=None, tags=None, custom_vars=None)` | PUT /sequences/{id}/import-lead | Create + enroll in one call. **linkedinUrl must be omitted if None — empty string → 400.** |

### Analytics Methods

| Method | Signature | API Call | Notes |
|--------|-----------|----------|-------|
| `get_analytics` | `(seq_id, from_date, to_date)` | GET /sequences/{id}/analytics | Returns `{days: {date: metrics}, stats: {aggregates}}` |
| `get_sequence_metrics` | `(product_id=None, sequence_ids=None)` | GET /sequence-metrics | Workspace-level aggregates |

### Other Methods

| Method | Signature | API Call | Notes |
|--------|-----------|----------|-------|
| `list_threads` | `(limit=50, offset=0)` | GET /threads | List-only. No detail, reply, or mark-read. |
| `add_to_dnc` | `(emails)` | POST /dnc/bulk | Write-only. Body: `{"dncs": ["email"]}`. Cannot list or remove. |
| `list_webhooks` | `(limit=50, offset=0)` | GET /integrations/webhooks | Path is `/integrations/webhooks` not `/webhooks` |
| `create_webhook` | `(name, event_type, url)` | POST /integrations/webhooks | Cannot update or delete after creation |

### Internal Methods

| Method | Signature | Behavior |
|--------|-----------|----------|
| `_request` | `(method, path, json_body=None, params=None, expect_204=False)` | HTTP call with auth headers, JSON parsing, error logging |
| `_log` | `(endpoint, method, params, status_code, summary)` | Writes to `api_log` table + `salesforge/api-calls.md` markdown file |

---

## 5. Scoring Model

### `scoring.py` (164 lines)

6-factor weighted scoring model. Each factor produces a 0-100 sub-score. Final score is the weighted sum.

### Factor Weights

| Factor | Weight | Sub-score Source |
|--------|--------|-----------------|
| bed_count | 0.20 | accounts.total_beds |
| margin | 0.15 | AVG(facilities.net_operating_profit_margin) |
| ehr | 0.20 | Most common facilities.ehr_inpatient |
| cms_quality | 0.15 | AVG(facilities.cms_overall_rating) + readmission bonus |
| trigger_signal | 0.20 | Lookup in TRIGGER_SIGNALS dict (15 accounts) |
| contact_coverage | 0.10 | COUNT(contacts WHERE golden_record=1 AND suppressed=0) |

### Sub-score Functions

**`score_bed_count(total_beds)`** — Hospital system size proxy

| Beds | Score |
|------|-------|
| >= 600 | 100 |
| >= 400 | 80 |
| >= 200 | 60 |
| >= 100 | 40 |
| < 100 | 20 |

**`score_margin(conn, system_name)`** — Financial pressure (lower margin = higher score)

| Avg Margin | Score | Rationale |
|-----------|-------|-----------|
| < 0% | 100 | Negative margin — desperate for cost savings |
| <= 5% | 70 | Low margin — strong cost justification |
| <= 10% | 40 | Moderate margin |
| > 10% | 20 | Healthy margin — less urgency |

**`score_ehr(conn, system_name)`** — EHR vendor scoring (non-Epic = higher opportunity)

| EHR | Score | Rationale |
|-----|-------|-----------|
| MEDITECH | 100 | Legacy system, strongest case for modernization |
| CERNER / ORACLE | 90 | Oracle transition creates uncertainty |
| Other/Unknown | 80 | No incumbent lock-in |
| EPIC | 40 | Strongest incumbent, hardest to displace |

**`score_cms_quality(conn, system_name)`** — Quality metric scoring

| CMS Rating | Base Score |
|-----------|------------|
| <= 2 stars | 100 |
| <= 3 stars | 70 |
| <= 4 stars | 40 |
| > 4 stars | 20 |

Bonus: +10 if avg readmission rate > 15.5%

**`score_trigger_signal(system_name)`** — Pre-identified trigger signals

Returns 100 if the system is in the TRIGGER_SIGNALS dict (15 health systems with known triggers like EHR migrations, new leadership, mergers). Returns 20 otherwise.

**TRIGGER_SIGNALS** (15 entries):
Includes accounts like HCA Healthcare, CommonSpirit, Ascension, Tenet Healthcare, etc. — each with a specific trigger (e.g., "Oracle Cerner → Oracle Health migration in progress", "New CNO appointed Q4 2025").

**`score_contact_coverage(conn, system_name)`** — How many contacts we have

| Contacts | Score |
|----------|-------|
| >= 15 | 100 |
| >= 10 | 70 |
| >= 5 | 40 |
| < 5 | 20 |

Falls back to facility count as proxy if no contacts found.

### Tier Assignment

```python
def assign_tier(score):
    # Priority: 80-100
    # Active: 60-79
    # Nurture: 40-59
    # Monitor: 0-39
```

### Current Distribution (after migration)

| Tier | Count | Notes |
|------|-------|-------|
| Priority | 0 | Top scores ~78, threshold is 80. contact_coverage drags down when scoring runs before contact enrichment. |
| Active | 222 | |
| Nurture | 1,351 | |
| Monitor | 110 | |

---

## 6. ICP Matching Engine

### `icp.py` (53 lines)

Matches contact titles against the 66-title ICP taxonomy. Three-stage matching strategy.

### ICP Taxonomy (66 titles across 13 departments)

| Department | Titles | Example |
|-----------|--------|---------|
| Clinical Informatics | 6 | Chief Clinical Informatics Officer, VP Clinical Informatics |
| Critical Care | 4 | Director of Critical Care, Medical Director of ICU |
| Endocrinology | 5 | Chief of Endocrinology, Endocrine Service Line Director |
| Executive Leadership | 8 | CEO, COO, CFO, CNO, CMO, CIO, CQO, Chief Strategy Officer |
| Finance | 5 | VP of Finance, Controller, Revenue Cycle Director |
| Hospital Medicine | 4 | Chief Hospitalist, Hospital Medicine Director |
| Innovation | 3 | Chief Innovation Officer, VP Digital Health |
| Nursing | 7 | VP Nursing, Director of Nursing, Nurse Manager ICU |
| Patient Safety | 4 | Chief Patient Safety Officer, VP Patient Safety |
| Pharmacy | 6 | Chief Pharmacy Officer, VP Pharmacy Services |
| Quality Improvement | 5 | VP Quality, Director Quality Improvement |
| Strategy | 4 | VP Corporate Strategy, Business Development Director |
| Surgery | 5 | Chief of Surgery, Perioperative Services Director |

### Matching Strategy

**`match_title(contact_title, icp_titles=None)`**

1. **Exact match** — case-insensitive string equality against all 66 ICP titles
2. **Fuzzy match** — `difflib.get_close_matches(contact_title, all_titles, n=1, cutoff=0.6)` — 60% similarity threshold
3. **Keyword overlap** — tokenize both strings, require >= 2 overlapping words AND >= 50% of the ICP title's words present

Returns the matching ICP dict (department, title, category, intent_score, function_type, job_level) or None.

### Functions

| Function | Signature | Returns |
|----------|-----------|---------|
| `load_icp_titles()` | `()` | List of dicts from ICP.json |
| `match_title` | `(contact_title, icp_titles=None)` | ICP dict or None |

---

## 7. Message Composition Engine

### `compose.py` (214 lines)

3-layer message composition. Combines persona-specific framing, EHR-specific angles, and financial urgency into personalized outreach emails.

### Layer 1: Persona Frames (8 entries)

Each frame provides a subject line template and an opening paragraph template.

| Persona Key | Target Roles | Frame Theme |
|-------------|-------------|-------------|
| Chief Nursing Officer | CNO, VP Nursing | Safety + nurse workflow |
| Chief Financial Officer | CFO, VP Finance | ROI + LOS reduction |
| Chief Quality Officer | CQO, VP Quality | CMS compliance + readmissions |
| Chief Executive Officer | CEO, President | Strategic transformation |
| Chief Operating Officer | COO, VP Operations | Operational efficiency |
| Chief Medical Officer | CMO, Chief Physician | Clinical outcomes |
| Director | Director-level | Department-specific improvement |
| default | Everyone else | General glycemic management |

Templates use `{company}` and `{beds}` placeholders.

### Layer 2: EHR Angles (5 entries)

Vendor-specific messaging that highlights technology-related risk/opportunity.

| EHR Key | Angle |
|---------|-------|
| EPIC | Epic integration gaps — glycemic management as an overlay |
| CERNER | Oracle Health transition uncertainty — need for independent solutions |
| ORACLE | Same as CERNER — Oracle rebranding creates opportunity |
| MEDITECH | Legacy system limitations — modernization imperative |
| default | EHR-agnostic clinical decision support |

### Layer 3: Financial Frames (4 entries)

Urgency-tiered based on operating margin.

| Margin Category | Threshold | Urgency Level |
|----------------|-----------|---------------|
| negative | < 0% | Highest — "cost recovery imperative" |
| low | <= 5% | High — "margin pressure" |
| moderate | <= 10% | Medium — "operational efficiency" |
| healthy | > 10% | Low — "quality leadership" positioning |

### Composition Flow

```python
compose_message(contact, account, facility) → {
    "subject": str,        # From persona frame template
    "body": str,           # Persona opening + EHR angle + financial frame
    "layer1_persona": str, # e.g., "safety_workflow"
    "layer2_ehr": str,     # e.g., "epic_liability"
    "layer3_financial": str, # e.g., "margin_recovery"
    "signal_hook": str     # Personalized opening from TRIGGER_SIGNALS (or None)
}
```

If a trigger signal exists for the account (from TRIGGER_SIGNALS in scoring.py), it's prepended as a hook: e.g., *"With your recent Oracle Health migration, there's a critical window..."*

---

## 8. Operations Scripts

25 scripts in `ops/`. Each is a standalone CLI tool. All follow the pattern: import config/db/api → query/act → display results.

### Campaign Lifecycle

#### `launch_campaign.py` (232 lines) — E1: Full campaign lifecycle

**CLI:** `python ops/launch_campaign.py --campaign-name "Name" [--live] [--tier X] [--ehr X] [--persona X] [--activate]`

**Flow:**
1. Query eligible contacts: `golden_record=1 AND suppressed=0 AND icp_matched=1` + tier/ehr/persona filters
2. Filter against DNC list
3. Preview: contact count, sample contacts, email content
4. POST /sequences → draft + 1 empty step
5. PUT /steps → email content (with distributionStrategy, label, status on variants)
6. PUT /mailboxes → assign all workspace mailboxes
7. PUT /import-lead → enroll each contact (linkedinUrl omitted if None)
8. (Optional) PUT /status → activate
9. Save to local campaigns + campaign_contacts tables

**Data flow:** contacts + accounts → API → campaigns + campaign_contacts

#### `toggle_campaign.py` (103 lines) — E2/E3: Activate or pause

**CLI:** `python ops/toggle_campaign.py <name> <activate|pause> [--live]`

**Flow:**
1. Search sequences by name (paginated, client-side filter)
2. Confirm single match
3. PUT /status → "active" or "paused"
4. Update local campaign record (salesforge_status, launched_at/paused_at)

**Warning:** Activating starts sending emails immediately.

#### `delete_campaign.py` (75 lines) — E4: Delete sequence

**CLI:** `python ops/delete_campaign.py <name> [--live]`

**Flow:** Find sequence → DELETE /sequences/{id} (204) → update local status to "deleted"

**Warning:** Irreversible. Cannot undo.

#### `ab_test.py` (131 lines) — E5: A/B variant setup

**CLI:** `python ops/ab_test.py --campaign "Name" [--step 0] [--split "50/50"] [--subject-a "..."] [--subject-b "..."] [--live]`

**Flow:**
1. Fetch sequence detail (includes current steps)
2. Parse split ratio (e.g., "50/50" → weights 50, 50)
3. Build multi-variant step with distributionStrategy="custom"
4. PUT /steps with full array (replaces ALL steps — must send complete data)

#### `enroll_contacts.py` (149 lines) — E6: Add contacts to existing campaign

**CLI:** `python ops/enroll_contacts.py --campaign "Name" [--tier X] [--ehr X] [--account X] [--persona X] [--live]`

**Flow:**
1. Find campaign locally or via API
2. Query eligible contacts with filters
3. Dedup against already-enrolled contacts (campaign_contacts table)
4. Filter DNC list
5. PUT /import-lead for each contact
6. Update campaign_contacts junction table

### Monitoring

#### `campaign_status.py` (141 lines) — Campaign overview

**CLI:** `python ops/campaign_status.py [active|paused|draft|completed] [detail <name>]`

**Flow:** GET /sequences (paginated) → cross-reference local DB → display table with status icons, lead counts, open/reply/bounce rates. Detail mode shows steps, mailboxes, targeting metadata.

#### `pull_metrics.py` (122 lines) — M1: Metrics dashboard

**CLI:** `python ops/pull_metrics.py [<campaign_name>] [30d|60d|90d]`

**Flow:** GET /sequences → GET /analytics per sequence → save metric_snapshots → display per-campaign + aggregate totals.

#### `kill_switch.py` (83 lines) — M2: Auto-pause on threshold breach

**CLI:** `python ops/kill_switch.py [--live]`

**Thresholds:** bounce > 5% → pause. Checks all active sequences. Updates local campaign status.

#### `check_replies.py` (124 lines) — M3/M4: Reply thread workflow

**CLI:** `python ops/check_replies.py [all] [<count>]`

**Flow:** GET /threads → upsert to reply_threads → show unhandled. `mark_reply(thread_id, status, handler, notes)` for workflow tracking (new → reviewed → needs_follow_up → handled → archived).

#### `mailbox_health.py` (131 lines) — M5: Mailbox connectivity

**CLI:** `python ops/mailbox_health.py`

**Flow:** GET /mailboxes → upsert mailboxes table → log to mailbox_health_log → create ui_tasks for disconnected mailboxes. Disconnected mailboxes must be reconnected via Salesforge UI.

#### `add_to_dnc.py` (varies) — M6: DNC management

**CLI:** `python ops/add_to_dnc.py <email(s)> [--reason X] [--live]`

**Flow:** Insert to local dnc_list + POST /dnc/bulk (if live) + suppress contact locally. **Irreversible** — Salesforge DNC entries cannot be removed via API.

### Contact Management

#### `search_contacts.py` (112 lines) — C1: Multi-field search

**CLI:** `python ops/search_contacts.py [--name X] [--email X] [--account X] [--icp X] [--title X] [--limit 25]`

Also accepts free-text: auto-detects type (@ → email, CNO/CFO → title, "Decision Maker" → ICP category).

**Why local:** Salesforge API filters are broken on all contact list endpoints. Every filter param is accepted but doesn't actually filter.

#### `account_view.py` (104 lines) — C2/A3: Account detail

**CLI:** `python ops/account_view.py <account name>`

**Output:** Account metadata (tier, score, beds, segment, opportunity $) → contacts list with ICP + suppressed status → campaign engagement rollup → top 10 facilities with beds/EHR/state.

#### `update_contact.py` (99 lines) — C3: Local field updates

**CLI:** `python ops/update_contact.py --email x@y.com [--title "New Title"] [--phone X] [--company X] [--linkedin X] [--account X]`

Updates local DB only. No Salesforge update API exists. Re-runs ICP matching via `match_title()` if title changes.

#### `view_suppressed.py` (68 lines) — C4: Suppressed contacts report

**CLI:** `python ops/view_suppressed.py`

Groups suppressed contacts by reason (glytec_client, dnc, opt_out, bounced, stale) with counts and 5 samples each. Shows DNC push status.

#### `bulk_import.py` (97 lines) — C5: CSV import

**CLI:** `python ops/bulk_import.py <csv_path>`

**Flow:** Read CSV (flexible column names) → dedup by email → ICP match each title → INSERT OR IGNORE. Sets source='csv_import', validated=1, golden_record=1.

### Planning

#### `campaign_planner.py` (142 lines) — P1/P4/P5: Plan + backlog + coverage

**CLI:**
- `plan [--tier X] [--ehr X] [--segment X] [--persona X]` — Show eligible contacts grouped by criteria
- `backlog` — List campaign_ideas with priority/status
- `coverage` — Enrollment coverage % by tier

#### `draft_emails.py` (134 lines) — P2/P3: Draft management

**CLI:**
- `list [--campaign X]` — List campaign_steps with variant info
- `templates` — List reusable email_templates with usage stats
- `preview --campaign X` — Show subject + body preview

### Reporting

#### `weekly_metrics.py` (80 lines) — R1: Week-over-week

**CLI:** `python ops/weekly_metrics.py [--weeks 4]`

Groups metric_snapshots by ISO week. Shows deltas between consecutive weeks (contacted, open rate, reply rate).

#### `compare_campaigns.py` (97 lines) — R2: Side-by-side comparison

**CLI:** `python ops/compare_campaigns.py <name1> <name2> [name3...]`

Fetches API metrics for each campaign. Side-by-side table with: leads, contacted, open%, reply%, bounce%, click%.

#### `segment_report.py` (91 lines) — R3/R4: EHR + persona breakdowns

**CLI:** `python ops/segment_report.py [ehr|persona]`

- **ehr:** Groups campaigns by target_ehr, aggregates metrics
- **persona:** Groups contacts by icp_category + function + level

#### `trend_report.py` (79 lines) — R6: 30/60/90 day trends

**CLI:** `python ops/trend_report.py [--days 90]`

Rolling windows from metric_snapshots + daily breakdown for last 14 days.

#### `pipeline_report.py` (77 lines) — R5: Meeting attribution

**CLI:** `python ops/pipeline_report.py`

Queries meetings table. Groups by attribution source. Shows campaign→meeting conversion rate.

### Account Management

#### `account_tiers.py` (95 lines) — A1/A2: Scored list + rescore

**CLI:** `python ops/account_tiers.py [--rescore] [--tier X] [--limit 50]`

Displays accounts sorted by score. `--rescore` re-runs the full 6-factor scoring model on all 1,683 accounts.

#### `plan_wave.py` (70 lines) — A4: Find untouched accounts

**CLI:** `python ops/plan_wave.py [--tier X] [--limit 30]`

Finds Priority/Active accounts that have zero contacts in any campaign. Shows contact count, score, beds. "Here's who we haven't reached yet."

---

## 9. Sync Scripts

6 scripts in `sync/`. Pull data from Salesforge API into local SQLite.

### Sync Strategy

| Script | API Endpoint | Frequency | Target Table(s) |
|--------|-------------|-----------|-----------------|
| pull_sequences.py | GET /sequences | Every 15 min or on-demand | campaigns |
| pull_metrics.py | GET /analytics | Daily | metric_snapshots |
| pull_threads.py | GET /threads | Every 15 min | reply_threads |
| pull_mailboxes.py | GET /mailboxes | Daily | mailboxes |
| pull_contacts.py | GET /contacts | Weekly | contacts (salesforge_lead_id) |
| sync_all.py | (orchestrator) | On-demand | (delegates) |

### `pull_sequences.py` (74 lines)

Paginates through all sequences. For each: checks if campaign exists locally by salesforge_seq_id → updates existing (status, counts) or inserts new. Updates sync_state.

### `pull_metrics.py` (79 lines)

For each campaign in local DB (or from API if DB empty): calls GET /analytics with 30-day window → saves daily metric_snapshots with computed rates (open_rate, reply_rate, bounce_rate).

### `pull_threads.py` (65 lines)

Paginates through all threads. Only inserts new threads (checks salesforge_thread_id existence). Preserves existing reply status/workflow data. Counts new vs total.

### `pull_mailboxes.py` (71 lines)

Fetches mailbox list (limit=100, no pagination needed for 21 mailboxes). Updates existing records or inserts new. Fields: address, status, disconnect_reason, daily_limit, provider, tracking_domain.

### `pull_contacts.py` (67 lines)

Weekly full sync. Paginates through all Salesforge contacts. Matches to local records by email (case-insensitive). Updates salesforge_lead_id and last_pushed_at on matches. Tracks match/unmatched counts.

### `sync_all.py` (53 lines)

**CLI:** `python sync/sync_all.py [sequences] [metrics] [threads] [mailboxes] [contacts]`

Runs specified jobs (or all 5 if no args). Each job wrapped in try-except for independent failure handling.

---

## 10. Claude Code Commands

11 commands in `.claude/commands/sf-*.md`. All use the `sf-` prefix.

| Command | Script | $ARGUMENTS | Key Behavior |
|---------|--------|------------|--------------|
| `/project:sf-campaigns` | ops/campaign_status.py | "active", "paused", "detail <name>" | Lists sequences with inline stats |
| `/project:sf-metrics` | sync/pull_metrics.py → ops/pull_metrics.py → ops/kill_switch.py | campaign name, "30d"/"90d" | Chains: sync → dashboard → kill-switch |
| `/project:sf-replies` | ops/check_replies.py | "all", count | Shows unhandled threads, offers to mark |
| `/project:sf-mailbox-health` | ops/mailbox_health.py | (none) | Reports healthy/disconnected |
| `/project:sf-sync` | sync/sync_all.py | "sequences", "contacts", etc. | Runs sync jobs |
| `/project:sf-launch` | ops/launch_campaign.py | campaign name + filters | DRY-RUN default, shows preview |
| `/project:sf-toggle` | ops/toggle_campaign.py | name + "pause"/"activate" | Warns on activate (starts sending) |
| `/project:sf-enroll` | ops/enroll_contacts.py | campaign + filters | DRY-RUN default, dedup check |
| `/project:sf-search` | ops/search_contacts.py | free-text query | Auto-detects search type |
| `/project:sf-account` | ops/account_view.py | account name | Full detail + contacts + engagement |
| `/project:sf-dnc` | ops/add_to_dnc.py | email(s) + reason | Warns irreversible |

---

## 11. Data Migration

### `migrate_from_pipeline.py` (129 lines)

Copies data from `pipeline/glytec_v1.db` (6-table prototype) into `salesforge/db/gtm_ops.db` (20-table production schema).

**Migrated entities:**

| Entity | Source Table | Target Table | Count | Notes |
|--------|------------|-------------|-------|-------|
| Accounts | pipeline.accounts | salesforge.accounts | 1,683 | Maps 18 columns |
| Facilities | pipeline.facilities | salesforge.facilities | 8,458 | Handles missing hospital_ownership column |
| Contacts | pipeline.contacts | salesforge.contacts | 20 | Maps 18 columns including ICP fields |
| ICP Titles | outbound/ICP.json | salesforge.icp_titles | 66 | Seeded by db.init_db() |

**Dedup:** Uses INSERT OR IGNORE — safe to run multiple times.

**Known issue:** Pipeline facilities table may have `geographic_classification` column not in new schema — handled by explicit column mapping rather than `SELECT *` insert.

---

## 12. API Surface Rules

Complete reference is at `docs/salesforge/salesforge-api-rules.md`. Key rules that affect code:

### What NEVER Works

| Rule | Impact |
|------|--------|
| PATCH on any endpoint → 404 | Only GET/POST/PUT/DELETE exist |
| DELETE on anything except sequences → 404 | Contacts, webhooks, DNC are permanent |
| All list endpoint filters | Accepted but don't filter — must filter client-side |
| POST on sequence sub-resources → 404 | Must use PUT for mailboxes, contacts, import-lead |
| jobTitle/phone on contacts | Accepted at creation but not stored — use customVars |

### What You Can't Change After Creation

| Field | Attempt | Result |
|-------|---------|--------|
| productId on sequence | PUT /sequences | **500** — crashes API |
| language on sequence | PUT /sequences | 200 but silently ignored |
| timezone on sequence | PUT /sequences | 200 but silently ignored |
| Sequence status → draft | PUT /status | 400 — only active/paused valid |
| Contact fields | PUT/PATCH /contacts | 404 — no update endpoint |
| Webhook URL/type | PUT /webhooks | 404 — no update endpoint |
| DNC entries | DELETE /dnc | 404 — no remove endpoint |

### Replacement Behavior

| Endpoint | Behavior |
|----------|----------|
| PUT /steps | Replaces ALL steps. Omitted steps deleted. |
| PUT /mailboxes | Replaces ALL mailbox assignments. Empty array clears. |
| PUT /contacts (on sequence) | Enrolls (additive), but duplicate enrollment increments leadCount |

### Salesforge Sequence Lifecycle

```
POST /sequences → draft (auto-creates 1 empty step)
    ↓
PUT /steps → set email content
    ↓
PUT /mailboxes → assign sending mailboxes
    ↓
PUT /import-lead → enroll contacts (one per call)
    ↓
PUT /status → "active" (requires mailboxes)
    ↓↑
PUT /status → "paused" ↔ "active"
    ↓
DELETE /sequences → permanent deletion (204)
```

### Contact Model (Salesforge side)

Only 8 fields exist on a Salesforge contact: `id`, `firstName`, `lastName`, `email`, `company`, `linkedinUrl`, `tags`, `customVars`. Everything else (title, phone, department, score) must go through customVars or live in local SQLite only.

---

## 13. Architecture Decisions

### Why SQLite as the Operational Hub

Salesforge's API is a minimal sending engine — broken filters, no contact updates, no reply management, write-only DNC, list-only threads. Building a GTM operation on top of it requires a local system of record for everything the API can't do: contact search, engagement tracking, reply workflows, metric trends, campaign planning, account scoring.

SQLite was chosen over Postgres/MySQL because:
1. Zero infrastructure — runs on the same machine as the scripts
2. Single-file backup — `cp gtm_ops.db backup.db`
3. WAL mode gives concurrent read access during writes
4. 1,683 accounts / 8,458 facilities / ~20K contacts is well within SQLite limits
5. Every ops script is a standalone CLI tool — no server process needed

### Why DRY_RUN=True by Default

Every campaign operation (launch, toggle, enroll, DNC, delete) defaults to dry-run. Reasons:
1. Salesforge actions are partially irreversible (DNC can't be removed, activating starts sending)
2. Preview-then-confirm workflow catches targeting mistakes before emails go out
3. `--live` flag is an explicit opt-in to real API calls

### Why Local Contact Search (Not API)

Salesforge's contact list filters are broken. Every filter parameter (`tags`, `email`, `firstName`, `validation_status`, `search`) is accepted by the API but returns unfiltered results. The only reliable way to search is to paginate through all contacts client-side. Since we already have all contacts in SQLite with richer fields (title, ICP category, account, suppression), local search is both faster and more capable.

### Why PUT Not POST for Sub-resources

Salesforge uses PUT (not POST) for: mailboxes on sequences, contacts on sequences, import-lead. POST on these paths returns 404. This is non-standard REST, but it's the tested reality. The API client encodes this rule so callers don't need to remember.

### Why import-lead Over POST /contacts + PUT /contacts

`import-lead` creates the contact AND enrolls in the sequence in one call. Using the separate endpoints would require: POST /contacts → get lead_id → PUT /contacts with lead_id. Since contacts can't be updated after creation (no PUT/PATCH), and import-lead handles both operations atomically, it's the preferred enrollment path.

### Why All Mailboxes on Every Campaign

With 21 mailboxes all under Clayton Maike, there's no reason to segment mailbox assignment. Every campaign gets all 21 mailboxes (630 emails/day total capacity at 30/day each). If mailbox specialization becomes needed later, the `assign_mailboxes` method accepts a filtered list.

### Why Scoring Runs Before Enrichment Matters

The 6-factor scoring model includes `contact_coverage` (weight: 0.10). When scoring runs before contact enrichment (step 2 before step 3 in pipeline), most accounts show 0 contacts → low coverage score → no Priority accounts. The scoring model is correct; the issue is data ordering. Running `--rescore` after bulk contact import fixes this.
