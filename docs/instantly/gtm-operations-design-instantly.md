# GTM Operations Design — Instantly MCP + API + SQLite Homebase

**Date:** 2026-02-20
**Context:** Glytec AI SDR — outbound GTM system for Glucommander (insulin management for hospitals)
**Goal:** Operate the entire outbound system through an AI agent using Instantly's MCP server as the primary interface, falling back to direct API calls only where MCP coverage gaps exist. SQLite remains the operational homebase for planning, enrichment, ICP matching, and anything Instantly doesn't store.

---

## Part 0 — Instantly MCP Deep Dive: What's Available Where

### Architecture Overview

Instantly exposes two programmatic interfaces:

1. **MCP Server** (`instantly-mcp v1.0.1`) — 38 tools over Streamable HTTP at `https://mcp.instantly.ai/mcp/{API_KEY}`. This is the primary interface for the AI agent. The agent calls tools directly — no SDK, no scripts, no wrappers. Each tool maps to one or more REST operations and handles pagination, validation, and error formatting natively.

2. **REST API V2** (`https://api.instantly.ai/api/v2`) — ~169 endpoints with Bearer token auth and 168+ granular scopes. Covers everything MCP does plus ~131 additional endpoints for advanced features. Required only when MCP doesn't expose a capability.

### The 38 MCP Tools — Categorized

#### Accounts (6 tools) — Full lifecycle management

| Tool | What it does | Maps to API |
|------|-------------|-------------|
| `list_accounts` | Cursor-paginated listing (100/page). Filter by domain (search), status, provider_code, tag_ids | GET /accounts |
| `get_account` | Single account by email. Returns connection status, provider, warmup config/progress, daily limits, sending gaps, tracking domain | GET /accounts/{email} |
| `create_account` | Create IMAP/SMTP account. Required: email, first_name, last_name, provider_code, IMAP+SMTP credentials | POST /accounts |
| `update_account` | Partial update: warmup settings, daily_limit (1-100), sending_gap (0-1440 min), slow ramp, tracking domain, inbox placement test limit | PATCH /accounts/{email} |
| `manage_account_state` | Actions: pause, resume, enable_warmup, disable_warmup, test_vitals (IMAP/SMTP connectivity check) | POST /accounts/{email}/pause, POST /accounts/warmup/enable, etc. |
| `delete_account` | Permanent deletion with confirmation | DELETE /accounts/{email} |

**MCP coverage: Complete.** Every account operation is available. No API fallback needed.

#### Campaigns (8 tools) — Full lifecycle management

| Tool | What it does | Maps to API |
|------|-------------|-------------|
| `create_campaign` | Two-step process: Step 1 with name/subject/body discovers senders; Step 2 with email_list assigns them. Supports sequences (1-10 steps), A/B variants, scheduling, tracking, company-level controls | POST /campaigns |
| `list_campaigns` | Cursor-paginated. Filter by name (search) and tag_ids. Returns status, lead counts, performance metrics | GET /campaigns |
| `get_campaign` | Full details: sequences, schedules, sender accounts, tracking settings, status | GET /campaigns/{id} |
| `update_campaign` | Partial update: name, sequences (email steps), email_list (senders), daily_limit (1-50), sending gaps, tracking, stop rules, company controls, CC/BCC, evergreen, variant optimization | PATCH /campaigns/{id} |
| `activate_campaign` | Launch campaign. Prerequisites: sender accounts, leads, sequences, schedule configured | POST /campaigns/{id}/launch |
| `pause_campaign` | Immediately stops sending, leads remain enrolled | POST /campaigns/{id}/pause |
| `delete_campaign` | Permanent deletion with confirmation | DELETE /campaigns/{id} |
| `search_campaigns_by_contact` | Find all campaigns a contact email is enrolled in | POST /campaigns/search-by-contact |

**MCP coverage: Complete for core operations.** The only campaign API endpoint not exposed via MCP is `activate-all-sending-accounts`, which is a rare bulk action.

#### Leads (12 tools) — Full CRUD + bulk operations

| Tool | What it does | Maps to API |
|------|-------------|-------------|
| `list_leads` | Cursor-paginated. Filter by campaign, list_id, list_ids, status, created_after/before, search (name/email), contact state (contacted/not contacted/completed/active), distinct_contacts (dedup) | POST /leads/list |
| `get_lead` | By UUID. Returns: contact details, custom variables, campaign/list membership, sequence status, interest status | GET /leads/{id} (via lead lookup) |
| `create_lead` | Required: email. Optional: campaign, first_name, last_name, company_name, phone, website, personalization, interest status, list_id, assigned_to, skip_if_in_workspace/campaign/list, blocklist_id, verify_leads_on_import, custom_variables | POST /leads |
| `update_lead` | Partial update. WARNING: custom_variables REPLACES entire object (must merge). Fields: personalization, website, name, company, phone, interest status, assigned_to, custom_variables | PATCH /leads/{id} |
| `list_lead_lists` | Cursor-paginated. Filter by enrichment task, search | GET /lead-lists |
| `create_lead_list` | name (required), has_enrichment_task, owned_by | POST /lead-lists |
| `update_lead_list` | name, enrichment settings, owner | PATCH /lead-lists/{id} |
| `get_verification_stats_for_lead_list` | Email verification breakdown: valid, invalid/bounced, risky, unknown | GET /lead-lists/{id} (stats) |
| `add_leads_to_campaign_or_list_bulk` | Up to 1,000 leads per call, 10-100x faster than create_lead. Provide campaign_id OR list_id (not both). Each lead needs minimum email | POST /leads/bulk |
| `delete_lead` | Permanent deletion | DELETE /leads/{id} |
| `delete_lead_list` | Permanent deletion | DELETE /lead-lists/{id} |
| `move_leads_to_campaign_or_list` | Move/copy between campaigns and lists. Background job for large operations. Source: specific IDs, or search + campaign/list filter | POST /leads/move |

**MCP coverage: Complete for all standard operations.** Leads are fully mutable — create, read, update, delete, bulk add, move. Filters actually work. Custom variables supported.

#### Emails / Unibox (6 tools) — Read, reply, verify

| Tool | What it does | Maps to API |
|------|-------------|-------------|
| `list_emails` | Cursor-paginated. Filter by campaign, lead, account, etc. | GET /emails |
| `get_email` | Full content: subject, body, attachments, thread info, tracking data, AI interest score, associated lead/campaign | GET /emails/{id} |
| `reply_to_email` | SENDS A REAL EMAIL. Requires reply_to_uuid and active sender (eaccount). Confirmation required | POST /emails/reply |
| `count_unread_emails` | Total unread across all accounts | GET /emails/unread/count |
| `verify_email` | Email deliverability check (5-45 seconds). Returns verification_status | POST /email-verification |
| `mark_thread_as_read` | Mark all emails in a thread as read | POST /emails/threads/{id}/mark-as-read |

**MCP coverage: Complete for operational use.** Critical improvement: the agent can reply to emails and mark threads as read — no UI required.

#### Analytics (3 tools) — Campaign + warmup metrics

| Tool | What it does | Maps to API |
|------|-------------|-------------|
| `get_campaign_analytics` | Opens, clicks, replies, bounces. Filter by campaign_id(s) and date range. Omit campaign_id for workspace-wide stats. Use campaign_ids array for multi-campaign | GET /campaigns/analytics |
| `get_daily_campaign_analytics` | Day-by-day breakdown: sent, opens/rate, clicks/rate, replies/rate, bounces. Filter by campaign status (0=Draft, 1=Active, 2=Paused, 3=Completed) | GET /campaigns/analytics/daily |
| `get_warmup_analytics` | Per-account warmup metrics: emails sent/received, inbox placement | POST /accounts/warmup-analytics |

**MCP coverage: Core analytics covered.** API-only: step-level analytics (`GET /campaigns/analytics/steps`), campaign analytics overview, and account daily sending analytics.

#### Background Jobs (2 tools) — Async operation tracking

| Tool | What it does | Maps to API |
|------|-------------|-------------|
| `list_background_jobs` | Cursor-paginated listing | GET /background-jobs |
| `get_background_job` | Job type, status (pending/running/completed/failed), progress | GET /background-jobs/{id} |

**MCP coverage: Complete.**

#### Server (1 tool) — Meta

| Tool | What it does |
|------|-------------|
| `get_server_info` | Server version, loaded tool categories, configuration |

### What MCP Does NOT Cover (~131 API Endpoints)

These capabilities require direct REST calls to `https://api.instantly.ai/api/v2`:

| Category | Endpoints | Why it matters |
|----------|-----------|----------------|
| **Lead Labels** | CRUD (5 endpoints) | AI-integrated lead categorization. Labels drive interest scoring and can trigger webhooks. Required for AI classification workflows |
| **Campaign Subsequences** | CRUD + pause/resume/sending-status (9 endpoints) | Behavior-triggered follow-up sequences. Conditions: reply content, CRM status, opens, clicks, campaign completion. Critical for multi-touch nurture |
| **Campaigns (API-only)** | 7 additional endpoints | duplicate, export, from-export, share, variables, sending-status, count-launched. Beyond MCP's 8 core tools |
| **Leads (API-only)** | 5 additional endpoints | bulk delete, subsequence move/remove, merge, bulk-assign, update-interest-status. Beyond MCP's 12 core tools |
| **Email Verification GET** | Poll verification status (1 endpoint) | MCP's `verify_email` triggers verification but returns immediately if >10s. Polling the result requires the API |
| **Inbox Placement — Tests** | Create/list/get/update/pause/resume (6 endpoints) | One-time and automated placement tests across ESPs and geographies. SPF/DKIM/DMARC validation, SpamAssassin scoring |
| **Inbox Placement — Analytics** | Per-email deliverability + aggregates (5 endpoints) | Per-recipient inbox vs spam breakdown, by ESP and geography |
| **Inbox Placement — Reports** | Blacklist + SpamAssassin (2 endpoints) | IP blacklist monitoring, domain reputation, spam score details |
| **SuperSearch Enrichment** | 10 endpoints | Lead discovery + AI-powered enrichment with 14+ model options. Major capability for contact research |
| **Webhooks** | Full CRUD + event types + test + resume (8 endpoints) | 19+ event types including custom label triggers. Essential for real-time event ingestion into SQLite |
| **Webhook Events** | 4 endpoints | Delivery log, retry tracking, summary, summary-by-date. Webhook observability |
| **Block List Entries** | CRUD + update (5 endpoints) | Domain and email-level blocking. Full lifecycle — create, list, get, update (PATCH), delete |
| **Custom Tags** | CRUD (5 endpoints) | Organize accounts and campaigns. Tags used as filters in MCP list operations |
| **Custom Tag Mappings** | Create/list/delete (3 endpoints) | Associate tags with accounts and campaigns |
| **Audit Log** | List with filters (1 endpoint) | Full activity tracking: API vs UI, IP, user, timestamps. 21 activity types |
| **Custom Prompt Templates** | CRUD (5 endpoints) | AI prompt templates for copywriting, personalization. 21+ AI models including Claude 4.5-sonnet, GPT-5, Gemini, Grok |
| **Sales Flows** | CRUD (5 endpoints) | Smart views for filtering leads by engagement behavior. Powerful query-based lead segmentation |
| **Email Templates** | CRUD (5 endpoints) | Reusable email templates stored in Instantly |
| **DFY Email Account Orders** | 7 endpoints | Managed email account ordering with domain checking. Done-for-you mailbox provisioning |
| **OAuth Initialization** | 3 endpoints | Google/Microsoft OAuth init + session polling. Programmatic initiation of browser-based consent flows |
| **Workspace Billing** | 2 endpoints | Plan + subscription details |
| **CRM Actions** | Phone numbers (2 endpoints) | Twilio phone number management |
| **API Key** | Create with scopes (1 endpoint) | Programmatic key creation with granular permissions |
| **Workspace** | List (1 endpoint) | Workspace enumeration |
| **Workspace Members** | CRUD (4 endpoints) | Team management: invite, update roles, remove |
| **Workspace Group Members** | CRUD (3 endpoints) | Group-level team management |
| **Account Campaign Mapping** | Read (1 endpoint) | Which campaigns an account is assigned to |

**For full field-level schemas, request/response examples, and gotchas on all API-only endpoints, see [`docs/instantly/instantly-api.md`](instantly/instantly-api.md) — sections 4–28 cover every resource listed above.**

### Decision Framework: MCP vs API vs SQLite

```
For any operation, follow this priority:

1. MCP tool exists?     → Use MCP (agent calls directly, no code needed)
2. API endpoint exists? → Use direct REST call (script or agent HTTP tool)
3. Neither?             → SQLite + local logic
```

### MCP Coverage Summary

| Domain | MCP Tools | API-Only Endpoints | Coverage |
|--------|-----------|-------------------|----------|
| Accounts | 6 | 2 (batch warmup, daily analytics) | 95% |
| Campaigns | 8 | 7 (duplicate, export, from-export, share, variables, sending-status, count-launched) | 95% of daily ops |
| Leads | 12 | 5 (bulk delete, subsequence move/remove, merge, bulk-assign, update-interest-status) | ~80% |
| Emails | 6 | 2 (forward, delete email) | 85% |
| Analytics | 3 | 4 (step analytics, overview, account daily, vitals) | 55% |
| Background Jobs | 2 | 0 | 100% |
| Lead Labels | 0 | 5 | 0% — API only |
| Subsequences | 0 | 9 | 0% — API only |
| Inbox Placement | 0 | 13 (6 tests + 5 analytics + 2 reports) | 0% — API only |
| Webhooks | 0 | 8 | 0% — API only |
| Webhook Events | 0 | 4 (delivery log, retry, summary, summary-by-date) | 0% — API only |
| Block List | 0 | 5 (includes PATCH update) | 0% — API only |
| SuperSearch Enrichment | 0 | 10 (lead discovery + AI enrichment, 14+ models) | 0% — API only |
| Tags/Mappings | 0 | 8 | 0% — API only |
| Admin (audit, keys, workspace) | 0 | 10 | 0% — API only |
| Templates/Flows/Prompts | 0 | 15 | 0% — API only |
| DFY Email Accounts | 0 | 7 (managed mailbox ordering + domain checks) | 0% — API only |
| OAuth Initialization | 0 | 3 (Google/Microsoft init + session polling) | 0% — API only |
| Workspace Billing | 0 | 2 (plan + subscription) | 0% — API only |
| **Total** | **38** | **~131** | **MCP handles ~22% of endpoints but covers ~85% of daily operational actions** |

The 38 MCP tools cover the high-frequency operations (account management, campaign CRUD, lead CRUD, email reading/replying, analytics). The ~131 API-only endpoints are mostly setup-once or low-frequency operations (webhooks, tags, placement tests, templates, SuperSearch, admin).

### Verified MCP Behavior (from QA testing — 2026-02-21)

> Full test results with 38-tool behavior matrix: [`docs/instantly/api-test-results.md`](api-test-results.md)

**Protocol details verified by testing:**
- MCP URL: `https://mcp.instantly.ai/sse?api_key={api_key}` (SSE transport)
- All tool arguments **must be nested under a `params` key**: `{"arguments": {"params": {...}}}`
- Responses can be `dict`, `list`, or plain `str` (when workspace is empty) — always type-check
- Pagination key is `items` (not `data`)

**`create_campaign` MCP schema differs from REST API:**
- MCP accepts: `name` (required), `subject` (required), `body` (required), plus optional `email_list`, `timing_from`/`timing_to`, `timezone`, `daily_limit`, `email_gap`, `stop_on_reply`, `sequence_steps`, `step_delay_days`, `sequence_subjects`, `sequence_bodies`
- MCP does **NOT** accept: `campaign_schedule` or `sequences` (these are REST-only)
- Fails with `{"success": false, "stage": "no_accounts"}` when no sending accounts exist

**Environment constraints (current):**
- 0 sending accounts → campaign creation untestable live
- Block list REST writes → 403 (plan restriction, local DB is fallback)
- `verify_email` takes 5-45 seconds per call

---

## Part 0.5 — Enrichment Pipeline: Where Contacts & Signals Come From

Before any campaign runs, contacts need to be discovered, enriched, and scored. The enrichment pipeline — built on the Definitive Healthcare HospitalView API — is that foundation. It has already been run and produced the data that will fuel the first campaigns.

### The Enrichment Database

**Location:** `enrichment/data/enrichment.db` (SQLite, WAL mode, ~280 MB)

**Total records: 814,700+** across 8 tables:

| Table | Records | What's in it |
|-------|---------|-------------|
| `executives` | 156,080 | Hospital executives — name, title, email, phone, LinkedIn, position level, ICP match status |
| `physicians` | 252,016 | Physicians — NPI, specialty, Medicare data, practice phone, affiliated facilities |
| `trigger_signals` | 301,510 | Leadership changes, EHR migrations, M&A activity, affiliation changes, new facilities |
| `account_enrichment` | 105,131 | Quality penalties (HAC, readmission, VBP), financials (margins, revenue), GPO/IDN memberships |
| `api_calls` | 38,175 | Full API call log with response times, retries, pagination state |
| `runs` | 23 | Recipe execution tracking with status, duration, facility counts |

### Contact Coverage

**Executives (156,080):**
- 17,557 ICP-matched (11.2% match rate across 12 matched titles)
- 59.5% have a primary email address
- 90.9% have a LinkedIn URL
- 99.99% have a phone number
- Position levels: 52.2% Manager/Director, 15.9% C-Level, 2.1% VP

**Physicians (252,016):**
- 112,237 unique NPIs
- 82.6% have Medicare claims data
- 97.6% have a practice phone number
- Specialties: endocrinology, hospital medicine, internal medicine, medical directors

**ICP matching:** 66 titles from the ICP taxonomy + 2 synthetic titles (Chief Medical Officer, Chief of Medicine) = 68 total. 12 titles matched in the data:

| Matched Title | Count |
|--------------|-------|
| Director, Pharmacy | 4,592 |
| CNO (Chief Nursing Officer) | 2,341 |
| CEO | 2,143 |
| Director, Inpatient Nursing | 2,080 |
| CMO (Chief Medical Officer) | 1,912 |
| CFO | 1,757 |
| COO | 1,429 |
| Chief Pharmacy Officer | 339 |
| Chief Compliance Officer | 280 |
| CQO (Chief Quality Officer) | 273 |
| CMIO | 223 |
| Chief Strategy Officer | 188 |

### The 10 Enrichment Recipes

The pipeline has 10 recipes. 5 have been executed; 5 are available but haven't run yet.

| # | Recipe | Status | What it produces |
|---|--------|--------|-----------------|
| R1 | Full Contact Extraction | **Not yet run** | Every contact at a single hospital (test/on-demand use) |
| R2 | ICP-Matched Discovery | **Not yet run** | ICP-targeted executives at a single hospital (test/on-demand use) |
| R3 | Leadership Changes | **Executed** — 4,251 facilities, 5.9h | 301,510 trigger signals (recently-updated executives, title changes, departures) |
| R4 | Tiered Discovery | **Executed** — 4,251 facilities, 10.5h | 156,080 executives with ICP matching (17,557 ICP-matched) |
| R5 | EHR-Segmented Discovery | **Not yet run** | Contacts segmented by EHR vendor (Epic/Cerner/MEDITECH) |
| R6 | Financial Distress + Quality | **Executed** — 1,189 facilities, 5.9h | 2,993 contacts at negative-margin hospitals + 1,819 quality penalties |
| R7 | Geographic / Rep Territory | **Not yet run** | Contacts filtered by sales rep territory assignment |
| R8 | Physician Champions | **Executed** — 1,387 facilities, 7.3h | 252,016 physicians (endocrinologists, hospitalists, internists, med directors) |
| R9 | Account Bundle | **Executed** — 4,249 facilities, 6.1h | 105,131 records (quality, financial, membership enrichment) |
| R10 | Every Contact at Company | **Not yet run** | Exhaustive per-system extraction (all contacts at a parent system) |

### Schedule for Unrun Recipes

| Recipe | When to run | Why |
|--------|------------|-----|
| R5 (EHR-Segmented) | Before first EHR-targeted campaigns | Segments contacts by Epic/Cerner/MEDITECH so campaigns can target by EHR vendor |
| R7 (Geographic/Territory) | Before territory-based campaigns | Filters contacts by assigned rep so outreach aligns with territory ownership |
| R1, R2, R10 | On-demand per-hospital deep dives | When a specific account becomes high-priority or a deal progresses — get exhaustive contact coverage for that system |

### Monthly Re-Run Plan

| Cadence | Recipes | Purpose |
|---------|---------|---------|
| **Monthly** | R3 (Leadership Changes) + R9 (Account Bundle) | Catch new leadership hires/departures, financial shifts, quality penalty updates, membership changes |
| **Quarterly** | R4 (Tiered Discovery) | Full ICP contact coverage refresh — new hires, title changes, email updates across all 4,251 target facilities |
| **On-demand** | R1, R2, R10 | Deep dives when accounts escalate in priority |

### How Enrichment Feeds Into Campaigns

```
enrichment/data/enrichment.db          ← DH HospitalView API (814K+ records)
        │
        ▼
  Campaign targeting queries           ← "Give me CNOs at Epic hospitals with 500+ beds"
        │
        ▼
  docs/campaigns/*.md                  ← Campaign design files (human-reviewed)
        │
        ▼
  Instantly via MCP                    ← create_campaign → add_leads_bulk → activate
        │
        ▼
  SQLite homebase                      ← metric_snapshots, reply_sentiment, engagement_events
        │
        ▼
  Clay → Salesforce                    ← Positive replies pushed downstream
```

The enrichment DB is **read-only from the campaign system's perspective** — it's populated by `enrichment/runner.py` and queried for targeting. Campaign execution data (metrics, replies, sentiment) flows into the SQLite homebase, not back into the enrichment DB.

---

## Part 1 — GTM Team User Stories

### Campaign Planning

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| P1 | Clayton | plan a campaign targeting Epic hospitals with 500+ beds in the Southeast | I can systematically work through high-value segments |
| P2 | Clayton | draft 3 email subject/body variants for a campaign before pushing anything | I can review and iterate on copy without touching Instantly |
| P3 | Clayton | save successful email templates for reuse across campaigns | I don't rewrite the same angles from scratch |
| P4 | Clayton | track campaign ideas in a backlog with priority/status | I know what's coming next and nothing falls through |
| P5 | Clayton | see which accounts have never been contacted vs. already in a sequence | I avoid double-contacting and find untouched accounts |

### Campaign Execution

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| E1 | Clayton | create a campaign in Instantly, load email steps, assign senders, and enroll contacts in one flow | the entire campaign launch is automated |
| E2 | Clayton | activate a campaign | sending starts |
| E3 | Clayton | pause a campaign | sending stops immediately |
| E4 | Clayton | delete a test campaign from Instantly | I keep the workspace clean |
| E5 | Clayton | A/B test two subject lines on the same step | I can learn what resonates |
| E6 | Reagan | enroll a new batch of contacts into an existing active campaign | I can add late-arriving contacts without rebuilding |

### Monitoring & Response

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| M1 | Clayton | see today's sends, opens, replies, and bounces across all campaigns at a glance | I know what's working and what's not |
| M2 | Clayton | auto-pause any campaign where bounce >5% or spam >0.3% | I protect domain reputation |
| M3 | Reagan | see all replies that came in today, with the message content | I can respond to interested prospects |
| M4 | Reagan | reply to a prospect directly from the AI agent | I can respond without switching to the UI |
| M5 | Reagan | mark a reply as "handled" or "needs follow-up" | I can track my reply workflow |
| M6 | Clayton | know which mailboxes are disconnected or unhealthy | I can fix them before they cause bounces |
| M7 | Clayton | test mailbox connectivity proactively | I catch problems before they affect deliverability |
| M8 | Clayton | add a prospect to the block list after they opt out | they never get another email |

### Contact Management

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| C1 | Clayton | search contacts by email, name, title, account, or ICP category | I can find anyone fast |
| C2 | Clayton | see all contacts at a specific account with their engagement history | I know who we've talked to and what happened |
| C3 | Clayton | update a contact's title, company, or custom variables when data changes | the record stays accurate across Instantly and local DB |
| C4 | Clayton | delete a contact from Instantly when they're permanently invalid | I keep the workspace clean |
| C5 | Clayton | see which contacts are suppressed and why | I can audit suppression logic |
| C6 | Clayton | bulk-import contacts from a CSV with ICP matching | I can load new lists efficiently |
| C7 | Clayton | verify a contact's email before enrolling them | I protect deliverability from bad addresses |

### Reporting

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| R1 | Pat | see week-over-week outbound metrics for all campaigns | I can track overall program health |
| R2 | Pat | compare campaign A vs campaign B performance side-by-side | I know which approach works better |
| R3 | Clayton | see which EHR segment (Epic/Cerner/MEDITECH) has the best open/reply rates | I can double down on what works |
| R4 | Clayton | see which persona tier (CNO/CFO/CQO/CEO) responds most | I can refine targeting |
| R5 | Pat | see pipeline attribution — which campaigns generated meetings | I can report ROI to leadership |
| R6 | Clayton | see historical trends over 30/60/90 days | I can spot patterns and seasonality |

### Account Strategy

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| A1 | Clayton | see account scores and tiers, sorted by opportunity | I know where to focus |
| A2 | Clayton | re-score accounts when new data arrives | tiers stay current |
| A3 | Clayton | see account-level engagement (any contact at this account opened/replied?) | I know which accounts are warm |
| A4 | Clayton | plan the next wave of outreach by picking untouched Priority/Active accounts | I systematically work the list |

### Campaign Design & Content

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| CD1 | Clayton | draft campaign copy in markdown files before pushing to Instantly | I can review, iterate, and version-control messaging without touching the platform |
| CD2 | Clayton | version campaign designs with target segment, messaging angle, and step content in `.md` files | every campaign has a documented design rationale and audit trail |
| CD3 | Clayton | track which campaign designs converted to live campaigns | I can measure the design-to-launch pipeline and identify bottlenecks |

### Deliverability (NEW — Instantly-specific)

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| D1 | Clayton | run inbox placement tests across ESPs before launching a campaign | I know my emails land in inbox, not spam |
| D2 | Clayton | see per-ESP and per-geography placement results | I can identify deliverability problems by provider |
| D3 | Clayton | monitor IP blacklist status and SpamAssassin scores | I catch reputation problems early |
| D4 | Clayton | track warmup progress per mailbox | I know when mailboxes are ready for campaign use |
| D5 | Clayton | configure behavior-triggered subsequences on campaigns | interested but non-responsive leads get automatic follow-ups |

---

## Part 2 — Capability Map: MCP + API + SQLite

For each user story: what MCP provides, what the direct API adds, what SQLite fills, and what requires the UI.

### Campaign Planning (P1–P5)

| Story | MCP | API | SQLite | UI Required? |
|-------|-----|-----|--------|-------------|
| P1 | Nothing — planning is local | Nothing | `campaign_ideas` table with targeting criteria, segment, EHR, geo filters | No |
| P2 | Nothing — drafting is local | Nothing | `email_drafts` table with variants, approval status | No |
| P3 | Nothing — drafting is local | `GET/POST/PATCH /email-templates` — Instantly stores reusable templates natively | `email_templates` table with tags, performance history. Sync to Instantly for use in campaigns | No |
| P4 | Nothing — backlog is local | Nothing | `campaign_ideas` table with priority, status, notes | No |
| P5 | `list_campaigns` returns all campaigns with lead counts. `list_leads` with campaign filter + `search_campaigns_by_contact` to find which contacts are enrolled where | Nothing beyond MCP | `campaign_contacts` junction tracks which contacts are in which campaigns + their account. Cross-reference with accounts table for untouched identification | No |

### Campaign Execution (E1–E6)

| Story | MCP | API | SQLite | UI Required? |
|-------|-----|-----|--------|-------------|
| E1 | `create_campaign` (Step 1: name/subject/body; Step 2: email_list) → `add_leads_to_campaign_or_list_bulk` (up to 1,000 leads/call) | Nothing beyond MCP | Track campaign<>sequence mapping, enrolled contacts, step content | No |
| E2 | `activate_campaign` — prerequisites: senders, leads, sequences, schedule | Nothing beyond MCP | Update local status | No |
| E3 | `pause_campaign` — immediately stops sending, leads remain | Nothing beyond MCP | Update local status | No |
| E4 | `delete_campaign` — permanent, confirmation required | Nothing beyond MCP | Remove from local tracking | No |
| E5 | `create_campaign` with `sequence_subjects[]` and `sequence_bodies[]` for A/B variants. `update_campaign` with `auto_variant_select` for AI-optimized variant selection | Nothing beyond MCP | Track variant performance locally | No |
| E6 | `add_leads_to_campaign_or_list_bulk` — up to 1,000 per call, works on active campaigns | Nothing beyond MCP | Add to campaign_contacts | No |

### Monitoring & Response (M1–M8)

| Story | MCP | API | SQLite | UI Required? |
|-------|-----|-----|--------|-------------|
| M1 | `get_campaign_analytics` (omit campaign_id for all campaigns). `get_daily_campaign_analytics` for day-by-day breakdown | `GET /campaigns/analytics/steps` for per-step breakdown (API only) | Store daily metric snapshots for trending. Cross-reference with campaign metadata for segment/persona breakdowns | No |
| M2 | `get_campaign_analytics` for bounce rate → `pause_campaign` to stop sending. Bounce protect is also built into Instantly (`disable_bounce_protect` flag) | Nothing beyond MCP | Kill-switch logic runs locally. Log every auto-pause event | No |
| M3 | `list_emails` filtered by date/campaign + `get_email` for full content including AI interest score | Nothing beyond MCP | Store email data locally. Track reply status | No |
| M4 | `reply_to_email` — SENDS REAL EMAIL via MCP. Requires reply_to_uuid and active sender account | Nothing beyond MCP | Log the reply locally | **No — agent can reply directly** |
| M5 | `mark_thread_as_read` — marks all emails in thread as read | Nothing beyond MCP | `reply_status` field on local email mirror (new/reviewed/needs-follow-up/handled/archived) | No |
| M6 | `list_accounts` filtered by status (-1/-2/-3 for errors). `get_account` for details including disconnect reason | Nothing beyond MCP | Store mailbox health snapshots for trending. Alert on disconnect | **Partial — reconnecting OAuth mailboxes requires UI** |
| M7 | `manage_account_state` with action `test_vitals` — proactive IMAP/SMTP connectivity check | Nothing beyond MCP | Log test results | No |
| M8 | Nothing via MCP | `POST /block-list-entries` — add email or domain to block list. `GET /block-list-entries` to audit. `DELETE /block-list-entries/{id}` to remove | Maintain local block list mirror for quick lookups | No |

### Contact Management (C1–C7)

| Story | MCP | API | SQLite | UI Required? |
|-------|-----|-----|--------|-------------|
| C1 | `list_leads` with search filter (name/email), campaign filter, status filter, date filters. **Filters actually work.** `search_campaigns_by_contact` to find all campaigns for an email | Nothing beyond MCP for basic search | Primary search for non-Instantly fields (title, ICP category, account) is local. SQLite provides the enriched 60+ field contact model | No |
| C2 | `list_leads` filtered by company_name or campaign + `list_emails` filtered by lead for engagement history. `get_lead` returns open/reply/click counts per lead | Nothing beyond MCP | contacts + campaign_contacts + engagement_events tables. Full account-level rollup from contact events | No |
| C3 | `update_lead` — partial update of first_name, last_name, company_name, phone, website, personalization, custom_variables. **WARNING: custom_variables REPLACES entire object — always merge** | Nothing beyond MCP | Update locally AND push to Instantly. Instantly contact stays in sync (unlike previous platform where contacts were immutable) | No |
| C4 | `delete_lead` — permanently removes from Instantly | Nothing beyond MCP | Flag suppressed locally with reason, then delete from Instantly | No |
| C5 | `list_leads` with status filter. Local suppression reasons tracked in SQLite | `GET /block-list-entries` to audit blocked domains/emails | contacts table with suppressed flag + suppression_reason. Block list mirror | No |
| C6 | `add_leads_to_campaign_or_list_bulk` — up to 1,000 per call with custom_variables, skip_if_in_workspace/campaign/list dedup, verify_leads_on_import | Nothing beyond MCP | Full ICP matching pipeline runs locally before push. Bulk add is 10-100x faster than individual create | No |
| C7 | `verify_email` — email deliverability check (5-45 seconds) | `GET /email-verification/{email}` to poll async results | Log verification status locally | No |

### Reporting (R1–R6)

| Story | MCP | API | SQLite | UI Required? |
|-------|-----|-----|--------|-------------|
| R1 | `get_daily_campaign_analytics` — day-by-day sent, opens/rate, clicks/rate, replies/rate, bounces. Filter by status to include only active/paused campaigns | `GET /campaigns/analytics/overview` for aggregate workspace view | Store daily snapshots. Compute week-over-week deltas locally | No |
| R2 | `get_campaign_analytics` with `campaign_ids` array — multi-campaign comparison in one call | `GET /campaigns/analytics/steps` for step-level comparison | Side-by-side queries against metric_snapshots table | No |
| R3 | No MCP segment-level breakdown — analytics are per-campaign only | Same limitation at API level | Tag campaigns with EHR segment in SQLite. Aggregate metrics by segment locally | No |
| R4 | No MCP persona-level breakdown | Same limitation at API level | Tag contacts with ICP category. Cross-reference engagement events with contact persona | No |
| R5 | No pipeline/opportunity data in Instantly | Same limitation | Requires Salesforce integration or manual tracking. `meetings` table for pipeline attribution | No (but needs external data) |
| R6 | `get_daily_campaign_analytics` returns daily data over arbitrary date ranges | Nothing beyond MCP | Store daily snapshots for arbitrary historical queries | No |

### Account Strategy (A1–A4)

| Story | MCP | API | SQLite | UI Required? |
|-------|-----|-----|--------|-------------|
| A1 | Nothing — scoring is local | Nothing | accounts table with score, tier, segment, opportunity $ | No |
| A2 | Nothing — scoring is local | Nothing | Re-run scoring model against updated data | No |
| A3 | `list_leads` filtered by company_name returns all leads at a company with open/reply/click counts. `get_campaign_analytics` per campaign for rollup | Nothing beyond MCP | Aggregate engagement events by contact to account rollup | No |
| A4 | `search_campaigns_by_contact` to check if any contact at an account has been enrolled | Nothing beyond MCP | campaign_contacts tracks enrollment. Accounts with zero enrolled contacts = untouched | No |

### Deliverability (D1–D5)

| Story | MCP | API | SQLite | UI Required? |
|-------|-----|-----|--------|-------------|
| D1 | Nothing via MCP | `POST /inbox-placement-tests` — create one-time or automated test. `GET /inbox-placement-tests/email-service-provider-options` for ESP list | Store test results locally | No |
| D2 | Nothing via MCP | `GET /inbox-placement-analytics` — per-email deliverability with sender/recipient ESP, geography, spam flag, SPF/DKIM/DMARC | Aggregate results by ESP and geo for dashboards | No |
| D3 | Nothing via MCP | `GET /inbox-placement-reports` — SpamAssassin scores, IP blacklist counts, domain blacklist details | Store and trend blacklist data | No |
| D4 | `get_warmup_analytics` — per-account warmup metrics via MCP. `get_account` shows warmup config and progress | Nothing beyond MCP | Store warmup snapshots for trending | No |
| D5 | Nothing via MCP | `POST /subsequences` — create behavior-triggered follow-ups. Conditions: crm_status, lead_activity (open/click/completed-no-reply), reply_contains | Track subsequence status locally | No |

---

## Part 3 — Complete Gap Analysis

### Things that MUST go through the Instantly UI

| Task | Why | Frequency |
|------|-----|-----------|
| Reconnect OAuth mailboxes (Google/Microsoft) | OAuth re-authorization requires browser-based flow. Can be **initiated** via API (`POST /oauth/google/init`, `POST /oauth/microsoft/init`) and polled (`GET /oauth/session/status/{sessionId}`), but the user must still complete the browser-based consent flow | As needed (check daily via `list_accounts` status filter) |
| Initial mailbox setup for Google/Microsoft | OAuth connection flow requires browser. API can initiate and poll, but user must complete consent | Onboarding only |
| View Instantly's built-in AI interest scoring UI | AI scoring runs automatically; results accessible via API (`ai_interest_value` on emails) but the visual analysis interface is UI-only | Optional |

That's it. Three items, and two of them are onboarding-only OAuth flows. Everything else is fully automatable.

### Things the API covers but MCP doesn't (require direct REST calls)

| Capability | API Endpoints | When needed |
|-----------|---------------|-------------|
| Lead Labels (CRUD) | 5 endpoints | Setup: define interest labels for AI classification. Then ongoing for label management |
| Campaign Subsequences (CRUD + control) | 9 endpoints | Campaign setup: create behavior-triggered follow-ups. Ongoing for pause/resume |
| Email Verification polling | 1 endpoint (GET) | After verify_email returns "pending" (>10s checks). Poll until complete |
| Inbox Placement Testing | 7 endpoints | Pre-launch: test deliverability. Ongoing for automated recurring tests |
| Inbox Placement Analytics | 1 endpoint | After placement tests: analyze per-ESP/geo results |
| Inbox Placement Reports | 1 endpoint | After placement tests: check blacklist + SpamAssassin |
| Webhooks (CRUD + test + resume) | 8 endpoints | Setup: configure event listeners. Rare updates thereafter |
| Block List Entries (CRUD) | 4 endpoints | Ongoing: add opt-outs, audit, remove false positives |
| Custom Tags (CRUD) | 5 endpoints | Setup: create account/campaign tags for filtering |
| Custom Tag Mappings | 3 endpoints | Setup: assign tags to accounts/campaigns |
| Audit Log | 1 endpoint | On-demand: investigate activity, audit API usage |
| Custom Prompt Templates | 5 endpoints | Setup: define AI prompts for personalization |
| Sales Flows | 5 endpoints | Setup: create smart views for lead filtering |
| Email Templates | 5 endpoints | Ongoing: manage reusable email templates in Instantly |
| CRM Actions | 2 endpoints | Rare: Twilio phone number management |
| API Key creation | 1 endpoint | Onboarding only |
| Workspace + Members | 8 endpoints | Rare: team management |
| Account Campaign Mapping | 1 endpoint | On-demand: audit which campaigns use which accounts |

### Things the MCP can do and eliminates previous workarounds

| Previously a gap | Now solved by |
|-----------------|---------------|
| No contact search/filter | `list_leads` with working search, status, campaign, date filters |
| No contact update | `update_lead` — partial update of all fields including custom_variables |
| No contact delete | `delete_lead` — permanent removal from workspace |
| No reply to emails | `reply_to_email` — sends real email from the agent |
| No mark-as-read | `mark_thread_as_read` — marks entire thread read |
| No mailbox management | `create_account`, `update_account`, `manage_account_state`, `delete_account` — full lifecycle |
| No mailbox connectivity testing | `manage_account_state` with test_vitals action |
| DNC is write-only | Block list CRUD via API (create + list + get + delete). MCP doesn't cover this but API does |
| Filters broken on list endpoints | Instantly filters work correctly on all MCP tools |
| No campaign delete | `delete_campaign` — permanent deletion |
| Cannot update campaigns | `update_campaign` — partial update of any campaign setting |
| No bulk enrollment | `add_leads_to_campaign_or_list_bulk` — up to 1,000 leads per call |

### Things that are still SQLite-only (no Instantly equivalent)

| Capability | Why SQLite |
|-----------|-----------|
| Campaign planning / ideation | Instantly has no planning or backlog concept |
| ICP matching and scoring | 66-title taxonomy, fuzzy matching, scoring model — all custom logic |
| Account scoring and tiering | Composite scoring from facility data, financials, clinical metrics |
| Account-level engagement rollup | Instantly tracks per-lead, not per-account |
| Segment/persona analytics | Requires cross-referencing campaign metadata with contact ICP data |
| Historical metric trending | Daily snapshots for 30/60/90 day analysis |
| Pipeline attribution (meetings) | Requires Salesforce or manual entry |
| Reply workflow tracking | Status tracking (new/reviewed/handled) is a custom workflow |
| Data enrichment orchestration | Multi-source enrichment pipeline |
| Messaging framework storage | Layer1/Layer2/Layer3 composition model |
| Email template performance history | Track open/reply rates across template reuse |

### Things that are fully automatable via MCP

| Operation | MCP Tool | Notes |
|-----------|----------|-------|
| Create campaign | `create_campaign` | Two-step: Step 1 creates + discovers senders, Step 2 assigns them |
| Set email content + A/B variants | `create_campaign` or `update_campaign` | sequence_subjects[], sequence_bodies[] for variants. Up to 10 steps |
| Assign sender accounts | `create_campaign` (Step 2) or `update_campaign` | email_list array of sender addresses |
| Enroll contacts (single) | `create_lead` with campaign param | Full field set + custom_variables |
| Enroll contacts (bulk) | `add_leads_to_campaign_or_list_bulk` | Up to 1,000 per call, 10-100x faster |
| Activate campaign | `activate_campaign` | Checks prerequisites automatically |
| Pause campaign | `pause_campaign` | Immediate stop |
| Delete campaign | `delete_campaign` | Permanent with confirmation |
| Update campaign settings | `update_campaign` | Any field: sequences, senders, limits, tracking, etc. |
| Pull campaign metrics | `get_campaign_analytics` | Multi-campaign, date-filtered, or workspace-wide |
| Pull daily metrics | `get_daily_campaign_analytics` | Day-by-day with rates |
| Pull warmup metrics | `get_warmup_analytics` | Per-account warmup health |
| List reply emails | `list_emails` | Filter by campaign, lead, account |
| Read full email content | `get_email` | Body, attachments, AI interest score, thread info |
| Reply to email | `reply_to_email` | Sends real email — no UI needed |
| Mark thread as read | `mark_thread_as_read` | All emails in thread |
| Count unread emails | `count_unread_emails` | Workspace-wide |
| Verify email address | `verify_email` | Deliverability check, 5-45 seconds |
| List mailbox health | `list_accounts` (filter status) | Status -1/-2/-3 = error states |
| Test mailbox connectivity | `manage_account_state` (test_vitals) | Proactive IMAP/SMTP check |
| Pause/resume mailbox | `manage_account_state` | pause, resume actions |
| Enable/disable warmup | `manage_account_state` | enable_warmup, disable_warmup actions |
| Update mailbox settings | `update_account` | daily_limit, sending_gap, warmup config, tracking domain |
| Create mailbox | `create_account` | IMAP/SMTP credentials required |
| Delete mailbox | `delete_account` | Permanent with confirmation |
| Search leads | `list_leads` | Working filters: name, email, campaign, status, date, contacted state |
| Update lead data | `update_lead` | Partial update — name, company, phone, custom_variables |
| Delete lead | `delete_lead` | Permanent removal |
| Move leads between campaigns | `move_leads_to_campaign_or_list` | Background job for large ops |
| Find campaigns for a contact | `search_campaigns_by_contact` | All campaigns an email is enrolled in |
| Manage lead lists | `create_lead_list`, `update_lead_list`, `delete_lead_list`, `list_lead_lists` | Full CRUD |
| Check lead list verification stats | `get_verification_stats_for_lead_list` | Valid/invalid/risky/unknown breakdown |
| Track async operations | `list_background_jobs`, `get_background_job` | Status polling for bulk ops |

---

## Part 4 — SQLite Homebase Schema

### Design Principles

1. **Campaign designs live in markdown files** — human-readable, version-controlled in `docs/campaigns/`. Each campaign `.md` file specifies target segment, messaging angle, step content, and A/B variants. Markdown is the starting point; SQLite tracks execution, not design
2. **SQLite is dedicated to operational tracking** — daily metric snapshots, lead status, reply sentiment, engagement events, and sync state. Not for campaign copywriting or planning prose
3. **Enrichment data lives in a separate database** — `enrichment/data/enrichment.db` (814K+ records, 8 tables) built by the DH pipeline. This feeds into campaign targeting but is not duplicated into the homebase DB
4. **Instantly is the sending engine AND contact store** — we push to it, pull metrics from it, and it maintains its own contact records that stay in sync with ours
5. **Every table has timestamps** — created_at and updated_at for auditability
6. **instantly_id links local records to Instantly** — UUIDs, nullable (not everything gets pushed)
7. **Soft deletes** — suppressed/archived flags instead of row deletion
8. **Instantly field names** — where data comes from Instantly, use their field names (snake_case, UUIDs)
9. **Custom variables are flat JSON only** — Instantly's `custom_variables`/`payload` field accepts only flat key:value pairs (string, number, boolean, null). No nested objects or arrays. Violation causes silent data loss

### Tables

```sql
-- ===========================================
-- CORE ENTITIES
-- ===========================================

-- Parent health systems (from CSV + DH + scoring)
CREATE TABLE accounts (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name           TEXT NOT NULL UNIQUE,
    definitive_id         TEXT,
    sfdc_account_id       TEXT,
    city                  TEXT,
    state                 TEXT,
    segment               TEXT,       -- Enterprise/Strategic, Commercial, Partner Growth
    facility_count        INTEGER,
    total_beds            INTEGER,
    avg_beds_per_facility REAL,
    primary_ehr           TEXT,       -- Most common EHR across facilities
    operating_margin_avg  REAL,       -- Avg across facilities
    cms_rating_avg        REAL,       -- Avg CMS stars across facilities
    readmission_rate_avg  REAL,
    glytec_client         TEXT,       -- Y or blank
    glytec_arr            REAL,
    gc_opp                REAL,       -- Glucommander $ opportunity
    cc_opp                REAL,       -- CriticalCare $ opportunity
    total_opp             REAL,
    adj_total_opp         REAL,
    rank                  INTEGER,
    score                 REAL,       -- 0-100 composite score
    tier                  TEXT,       -- Priority/Active/Nurture/Monitor
    trigger_signal        TEXT,       -- Latest signal (EHR migration, new CNO, etc.)
    trigger_date          TEXT,       -- When the signal was detected
    assigned_rep          TEXT,
    notes                 TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual hospitals under accounts
CREATE TABLE facilities (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name             TEXT NOT NULL,
    definitive_id             TEXT UNIQUE,
    highest_level_parent      TEXT,     -- FK -> accounts.system_name
    city                      TEXT,
    state                     TEXT,
    firm_type                 TEXT,
    hospital_type             TEXT,
    hospital_ownership        TEXT,
    ehr_inpatient             TEXT,
    staffed_beds              INTEGER,
    icu_beds                  INTEGER,
    net_operating_profit_margin REAL,
    cms_overall_rating        REAL,
    readmission_rate          REAL,
    avg_length_of_stay        REAL,
    net_patient_revenue       REAL,
    assigned_rep              TEXT,
    created_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- All contacts (enriched locally, synced to Instantly)
CREATE TABLE contacts (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name              TEXT,
    last_name               TEXT,
    email                   TEXT,
    title                   TEXT,
    phone                   TEXT,
    company_name            TEXT,
    company_domain          TEXT,
    website                 TEXT,
    linkedin_url            TEXT,
    account_name            TEXT,       -- FK -> accounts.system_name
    facility_definitive_id  TEXT,       -- FK -> facilities.definitive_id

    -- ICP matching
    icp_category            TEXT,       -- Decision Maker / Influencer
    icp_intent_score        INTEGER,    -- 50-95
    icp_function_type       TEXT,       -- Clinical / Business
    icp_job_level           TEXT,       -- Executive, Director, Mid-Level, IC
    icp_department          TEXT,       -- From ICP taxonomy
    icp_matched             INTEGER DEFAULT 0,

    -- Data quality
    source                  TEXT,       -- zoominfo, dh, web_scraping, csv_import, manual
    email_verified          INTEGER DEFAULT 0,   -- Email verified via Instantly?
    verification_status     TEXT,       -- verified, invalid, risky, unknown, pending
    golden_record           INTEGER DEFAULT 0,   -- Survived dedup?
    suppressed              INTEGER DEFAULT 0,
    suppression_reason      TEXT,       -- glytec_client, blocked, opt_out, bounced, stale

    -- Instantly sync
    instantly_lead_id       TEXT,       -- UUID from Instantly (if pushed)
    instantly_list_id       TEXT,       -- Lead list UUID in Instantly
    instantly_status        INTEGER,    -- 1=Active, 2=Paused, 3=Completed, -1=Bounced, -2=Unsubscribed, -3=Skipped
    instantly_interest      INTEGER,    -- lt_interest_status from Instantly
    last_pushed_at          TIMESTAMP,  -- When last sent to Instantly
    last_synced_at          TIMESTAMP,  -- When last pulled from Instantly

    -- Engagement summary (from Instantly lead data)
    email_open_count        INTEGER DEFAULT 0,
    email_reply_count       INTEGER DEFAULT 0,
    email_click_count       INTEGER DEFAULT 0,

    -- Personalization
    personalization         TEXT,       -- Custom personalization line for Instantly

    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email)
);

-- ICP title taxonomy (from ICP.json -- 66 titles)
CREATE TABLE icp_titles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    department      TEXT,
    title           TEXT,
    category        TEXT,       -- Decision Maker / Influencer
    intent_score    INTEGER,
    function_type   TEXT,       -- Clinical / Business
    job_level       TEXT        -- Executive, Director, Mid-Level, IC, Other
);


-- ===========================================
-- CAMPAIGN MANAGEMENT
-- ===========================================

-- Campaign ideas / backlog (not yet in Instantly)
CREATE TABLE campaign_ideas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    description     TEXT,
    target_segment  TEXT,       -- Epic Enterprise, Cerner Commercial, etc.
    target_ehr      TEXT,
    target_geo      TEXT,
    target_tier     TEXT,       -- Priority, Active, etc.
    target_persona  TEXT,       -- CNO, CFO, etc.
    priority        TEXT DEFAULT 'medium',  -- high, medium, low
    status          TEXT DEFAULT 'idea',    -- idea, planned, in_progress, launched, completed, archived
    estimated_contacts INTEGER,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Active campaigns (maps 1:1 to Instantly campaigns once launched)
CREATE TABLE campaigns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    idea_id         INTEGER REFERENCES campaign_ideas(id),

    -- Instantly link
    instantly_campaign_id TEXT,    -- UUID (null until pushed)
    instantly_status      INTEGER, -- 0=Draft, 1=Active, 2=Paused, 3=Completed, 4=Running Subsequences, -99=Suspended, -1=Unhealthy, -2=Bounce Protect

    -- Targeting metadata (for local analytics rollups)
    target_segment  TEXT,
    target_ehr      TEXT,
    target_geo      TEXT,
    target_tier     TEXT,
    target_persona  TEXT,

    -- Config
    step_count      INTEGER DEFAULT 1,
    sender_count    INTEGER DEFAULT 0,
    lead_count      INTEGER DEFAULT 0,
    daily_limit     INTEGER DEFAULT 30,   -- 1-50
    email_gap       INTEGER DEFAULT 10,   -- minutes
    stop_on_reply   INTEGER DEFAULT 1,
    stop_for_company INTEGER DEFAULT 0,
    match_lead_esp  INTEGER DEFAULT 0,
    open_tracking   INTEGER DEFAULT 0,
    link_tracking   INTEGER DEFAULT 0,
    pl_value        REAL,                 -- $ value per positive lead

    -- Status tracking
    status          TEXT DEFAULT 'draft',  -- draft, ready, active, paused, completed, archived
    launched_at     TIMESTAMP,
    paused_at       TIMESTAMP,
    completed_at    TIMESTAMP,

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Which contacts are in which campaigns
CREATE TABLE campaign_contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER NOT NULL REFERENCES campaigns(id),
    contact_id      INTEGER NOT NULL REFERENCES contacts(id),
    instantly_lead_id TEXT,      -- UUID of lead in this specific campaign context
    enrolled_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          TEXT DEFAULT 'enrolled',  -- enrolled, contacted, replied, bounced, unsubscribed, completed, skipped

    -- Engagement summary (from Instantly lead-level data + events)
    emails_sent     INTEGER DEFAULT 0,
    emails_opened   INTEGER DEFAULT 0,
    emails_clicked  INTEGER DEFAULT 0,
    replied         INTEGER DEFAULT 0,
    reply_type      TEXT,       -- positive, negative, neutral, ooo
    bounced         INTEGER DEFAULT 0,
    interest_status INTEGER,    -- lt_interest_status from Instantly
    ai_interest     REAL,       -- ai_interest_value from email (0.0-1.0)

    -- Sequence progress
    last_step       INTEGER,    -- Last step executed (0-indexed)
    last_step_date  TIMESTAMP,
    sequence_complete INTEGER DEFAULT 0,

    UNIQUE(campaign_id, contact_id)
);

-- Campaign subsequences (behavior-triggered follow-ups, API-only)
CREATE TABLE campaign_subsequences (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id             INTEGER NOT NULL REFERENCES campaigns(id),
    instantly_subsequence_id TEXT,    -- UUID
    name                    TEXT NOT NULL,
    status                  INTEGER,  -- 0=Draft, 1=Active, 2=Paused, 3=Completed

    -- Trigger conditions
    trigger_type            TEXT,     -- crm_status, lead_activity, reply_contains
    trigger_crm_statuses    TEXT,     -- JSON array: [0,1,2,3,4,-1,-2,-3,-4]
    trigger_lead_activities TEXT,     -- JSON array: [2,4,91]
    trigger_reply_contains  TEXT,     -- keyword match

    step_count              INTEGER DEFAULT 1,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email steps within a campaign (our copy + sync status)
CREATE TABLE campaign_steps (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id         INTEGER NOT NULL REFERENCES campaigns(id),
    step_order          INTEGER NOT NULL,    -- 0-indexed
    step_name           TEXT,                -- "Initial email", "Follow-up 1", etc.
    delay_days          INTEGER DEFAULT 0,   -- Days to wait before sending

    -- Content
    email_subject       TEXT,
    email_body_html     TEXT,
    email_body_plain    TEXT,      -- Plain text version for reference

    -- Composition attribution
    layer1_persona      TEXT,      -- safety_workflow, roi_los, cms_compliance, etc.
    layer2_ehr          TEXT,      -- epic_liability, cerner_transition, meditech_modernize
    layer3_financial    TEXT,      -- margin_recovery, quality_leadership, etc.
    signal_hook         TEXT,      -- Personalized opening line

    -- A/B testing
    variant_index       INTEGER DEFAULT 0,   -- 0-based variant index
    variant_label       TEXT DEFAULT 'A',

    -- Instantly sync
    instantly_step_id   TEXT,      -- UUID (if available from API)
    synced_at           TIMESTAMP,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reusable email templates (local + optionally synced to Instantly)
CREATE TABLE email_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    category            TEXT,       -- cold_email, follow_up, case_study, direct_cta
    persona             TEXT,       -- CNO, CFO, CQO, CEO, COO, CMO, general
    ehr_segment         TEXT,       -- epic, cerner, meditech, any
    subject             TEXT,
    body_html           TEXT,
    body_plain          TEXT,
    tags                TEXT,       -- comma-separated
    times_used          INTEGER DEFAULT 0,
    avg_open_rate       REAL,       -- Updated from campaign performance
    avg_reply_rate      REAL,

    -- Instantly sync
    instantly_template_id TEXT,     -- UUID if synced to Instantly email templates

    notes               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ===========================================
-- ENGAGEMENT TRACKING
-- ===========================================

-- Individual engagement events (from webhooks or analytics pulls)
CREATE TABLE engagement_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    contact_id      INTEGER REFERENCES contacts(id),
    contact_email   TEXT,      -- Denormalized for quick lookup
    event_type      TEXT NOT NULL,  -- sent, opened, clicked, replied, bounced, unsubscribed, campaign_completed, account_error
    event_date      TIMESTAMP,
    metadata        TEXT,      -- JSON: reply content, bounce reason, link clicked, AI interest score, etc.
    source          TEXT DEFAULT 'api_pull',  -- api_pull, webhook, mcp_sync, manual
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email thread mirror (synced from Instantly Unibox via MCP)
CREATE TABLE email_threads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    instantly_thread_id TEXT UNIQUE,    -- UUID thread_id from Instantly
    instantly_email_id  TEXT,           -- UUID of the specific email
    campaign_id         INTEGER REFERENCES campaigns(id),
    contact_id          INTEGER REFERENCES contacts(id),
    contact_email       TEXT,
    contact_first_name  TEXT,
    contact_last_name   TEXT,
    subject             TEXT,
    body_text           TEXT,           -- Plain text content
    body_html           TEXT,           -- HTML content
    content_preview     TEXT,           -- First few lines
    sender_account      TEXT,           -- eaccount that sent/received

    -- Instantly metadata
    ue_type             INTEGER,        -- 1=Sent from campaign, 2=Received, 3=Sent manual, 4=Scheduled
    is_unread           INTEGER DEFAULT 1,
    is_auto_reply       INTEGER DEFAULT 0,
    ai_interest_value   REAL,           -- AI-scored interest (0.0-1.0)
    ai_assisted         INTEGER DEFAULT 0,
    i_status            INTEGER,        -- Interest status
    step_id             TEXT,           -- Campaign step UUID
    campaign_step       INTEGER,        -- Step index

    -- Our workflow tracking
    status              TEXT DEFAULT 'new',  -- new, reviewed, needs_follow_up, handled, archived
    sentiment           TEXT,       -- positive, negative, neutral, ooo (classified locally or via AI)
    handled_by          TEXT,       -- Clayton, Reagan
    handled_at          TIMESTAMP,
    follow_up_notes     TEXT,
    replied_via_mcp     INTEGER DEFAULT 0,  -- Did we reply via MCP?
    reply_sent_at       TIMESTAMP,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reply sentiment classification (authoritative record for downstream routing)
CREATE TABLE reply_sentiment (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    instantly_email_id      TEXT,           -- UUID of the reply email in Instantly
    thread_id               TEXT,           -- FK -> email_threads.instantly_thread_id
    campaign_id             INTEGER REFERENCES campaigns(id),
    contact_id              INTEGER REFERENCES contacts(id),
    contact_email           TEXT,

    -- Classification
    sentiment               TEXT NOT NULL,  -- positive, negative, neutral, ooo, bounce
    sentiment_confidence    REAL,           -- 0.0-1.0 confidence in classification
    classified_by           TEXT,           -- ai, manual, ai+confirmed
    classified_at           TIMESTAMP,

    -- Downstream push tracking
    pushed_to_clay          INTEGER DEFAULT 0,
    pushed_at               TIMESTAMP,
    clay_webhook_response   TEXT,           -- JSON response from Clay webhook
    salesforce_lead_id      TEXT,           -- SF Lead ID (populated after Clay→SF sync)
    salesforce_opportunity_id TEXT,         -- SF Opportunity ID (if deal progresses)

    notes                   TEXT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clay webhook push log (audit trail for every downstream push)
CREATE TABLE clay_push_log (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    reply_sentiment_id      INTEGER REFERENCES reply_sentiment(id),
    contact_email           TEXT,
    contact_first_name      TEXT,
    contact_last_name       TEXT,
    account_name            TEXT,
    campaign_name           TEXT,
    sentiment               TEXT,

    -- Webhook details
    webhook_url             TEXT,
    payload_json            TEXT,           -- Full JSON payload sent to Clay
    response_code           INTEGER,        -- HTTP response code from Clay
    response_body           TEXT,
    pushed_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Salesforce sync tracking
    salesforce_sync_status  TEXT DEFAULT 'pending',  -- pending, synced, failed
    salesforce_synced_at    TIMESTAMP
);


-- ===========================================
-- DELIVERABILITY & MAILBOX HEALTH
-- ===========================================

-- Mailbox inventory + health (fully managed via MCP)
CREATE TABLE mailboxes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    email               TEXT NOT NULL UNIQUE,    -- Email address (Instantly's primary key)
    first_name          TEXT,
    last_name           TEXT,
    provider_code       INTEGER,        -- 1=IMAP, 2=Google, 3=Microsoft, 4=AWS
    daily_limit         INTEGER,        -- Daily email sending limit
    sending_gap         INTEGER,        -- Minutes between emails
    enable_slow_ramp    INTEGER DEFAULT 0,

    -- Status
    status              INTEGER,        -- 1=Active, 2=Paused, -1=Connection Error, -2=Soft Bounce, -3=Sending Error
    status_message      TEXT,           -- JSON: error details

    -- Warmup
    warmup_status       INTEGER,        -- 0=Paused, 1=Active, -1=Banned, -2=Spam Folder Unknown, -3=Permanent Suspension
    warmup_limit        INTEGER,
    warmup_score        REAL,           -- stat_warmup_score from Instantly
    warmup_reply_rate   REAL,

    -- Tracking
    tracking_domain     TEXT,
    tracking_domain_status TEXT,

    -- Timestamps
    last_used_at        TIMESTAMP,      -- timestamp_last_used from Instantly
    warmup_start_at     TIMESTAMP,      -- timestamp_warmup_start from Instantly
    last_synced_at      TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily mailbox health snapshots
CREATE TABLE mailbox_health_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mailbox_email   TEXT NOT NULL,     -- FK -> mailboxes.email
    snapshot_date   DATE NOT NULL,
    status          INTEGER,
    warmup_status   INTEGER,
    warmup_score    REAL,
    daily_limit     INTEGER,

    -- Warmup analytics (from get_warmup_analytics MCP tool)
    warmup_emails_sent      INTEGER,
    warmup_emails_received  INTEGER,
    warmup_inbox_placement  REAL,       -- Inbox placement rate

    -- Vitals test result (from manage_account_state test_vitals)
    vitals_tested   INTEGER DEFAULT 0,
    vitals_passed   INTEGER,
    vitals_error    TEXT,

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mailbox_email, snapshot_date)
);

-- Block list mirror (API CRUD -- create, list, get, delete)
CREATE TABLE block_list (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    email_or_domain         TEXT NOT NULL UNIQUE,
    entry_type              TEXT,       -- email, domain
    reason                  TEXT,       -- opt_out, bounce, suppression, manual, spam_complaint
    source                  TEXT,       -- webhook, manual, csv_import, salesforce, auto_bounce
    instantly_block_id      TEXT,       -- UUID from Instantly (if pushed)
    added_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pushed_to_instantly     INTEGER DEFAULT 0,
    pushed_at               TIMESTAMP
);

-- Inbox placement test results (API-only)
CREATE TABLE inbox_placement_tests (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    instantly_test_id       TEXT UNIQUE,    -- UUID
    name                    TEXT,
    test_type               INTEGER,        -- 1=One-time, 2=Automated
    sending_method          INTEGER,        -- 1=From Instantly, 2=External
    status                  INTEGER,        -- 1=Active, 2=Paused, 3=Completed
    campaign_id             INTEGER REFERENCES campaigns(id),

    -- Results summary (aggregated from inbox_placement_analytics)
    total_sent              INTEGER DEFAULT 0,
    total_received          INTEGER DEFAULT 0,
    inbox_count             INTEGER DEFAULT 0,
    spam_count              INTEGER DEFAULT 0,
    inbox_rate              REAL,
    spf_pass_rate           REAL,
    dkim_pass_rate          REAL,
    dmarc_pass_rate         REAL,
    spam_assassin_score     REAL,
    blacklist_count         INTEGER DEFAULT 0,

    tested_at               TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ===========================================
-- REPORTING & METRICS
-- ===========================================

-- Daily metric snapshots per campaign (from MCP get_campaign_analytics / get_daily_campaign_analytics)
CREATE TABLE metric_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id         INTEGER REFERENCES campaigns(id),
    instantly_campaign_id TEXT,
    snapshot_date       DATE NOT NULL,

    -- Counts
    sent            INTEGER DEFAULT 0,
    opened          INTEGER DEFAULT 0,
    unique_opened   INTEGER DEFAULT 0,
    clicked         INTEGER DEFAULT 0,
    unique_clicked  INTEGER DEFAULT 0,
    replied         INTEGER DEFAULT 0,
    bounced         INTEGER DEFAULT 0,
    unsubscribed    INTEGER DEFAULT 0,
    new_leads       INTEGER DEFAULT 0,    -- New leads contacted that day

    -- Rates
    open_rate       REAL,
    reply_rate      REAL,
    bounce_rate     REAL,
    click_rate      REAL,

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id, snapshot_date)
);

-- Account-level engagement rollup
CREATE TABLE account_engagement (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name    TEXT NOT NULL,       -- FK -> accounts.system_name
    total_contacts  INTEGER DEFAULT 0,
    contacts_enrolled INTEGER DEFAULT 0,
    contacts_opened INTEGER DEFAULT 0,
    contacts_replied INTEGER DEFAULT 0,
    contacts_bounced INTEGER DEFAULT 0,
    contacts_clicked INTEGER DEFAULT 0,
    latest_campaign TEXT,
    latest_campaign_id INTEGER,
    latest_activity_date TIMESTAMP,
    avg_ai_interest REAL,               -- Average AI interest score across replies
    engagement_tier TEXT,   -- hot (replied), warm (opened), cold (sent, no open), untouched
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_name)
);


-- ===========================================
-- OPERATIONS
-- ===========================================

-- API/MCP call log (every external call)
CREATE TABLE api_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interface       TEXT DEFAULT 'mcp',    -- mcp, api_v2
    tool_or_endpoint TEXT,                 -- MCP tool name or API endpoint path
    method          TEXT,                  -- For API: GET/POST/PATCH/DELETE. For MCP: tool name
    params          TEXT,                  -- JSON
    response_code   INTEGER,              -- HTTP status (API) or null (MCP)
    response_summary TEXT,
    duration_ms     INTEGER               -- Execution time
);

-- Sync state tracking
CREATE TABLE sync_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity          TEXT NOT NULL UNIQUE,   -- contacts, campaigns, emails, mailboxes, metrics, block_list, lead_labels
    last_synced_at  TIMESTAMP,
    last_cursor     TEXT,                  -- Cursor for pagination (Instantly uses starting_after)
    total_records   INTEGER,
    notes           TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook configuration mirror (from API)
CREATE TABLE webhooks (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    instantly_webhook_id    TEXT UNIQUE,     -- UUID
    name                    TEXT,
    target_hook_url         TEXT,
    event_type              TEXT,            -- email_sent, email_opened, reply_received, etc.
    campaign_id             INTEGER REFERENCES campaigns(id),
    instantly_campaign_id   TEXT,            -- UUID filter (null = all campaigns)
    custom_interest_value   INTEGER,         -- For custom label events
    headers                 TEXT,            -- JSON: custom headers
    status                  INTEGER,         -- 1=Active, -1=Error
    error_timestamp         TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lead labels (from API -- AI-integrated categorization)
CREATE TABLE lead_labels (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    instantly_label_id      TEXT UNIQUE,     -- UUID
    label                   TEXT,            -- e.g. "Hot Lead"
    interest_status_label   TEXT,            -- positive / negative / neutral
    interest_status         INTEGER,         -- Auto-generated
    description             TEXT,
    use_with_ai             INTEGER DEFAULT 0,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom tags (from API)
CREATE TABLE custom_tags (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    instantly_tag_id        TEXT UNIQUE,     -- UUID
    name                    TEXT,
    tag_type                TEXT,            -- account, campaign
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UI tasks -- things that MUST be done in the Instantly UI
-- (Much smaller list than before -- only OAuth flows)
CREATE TABLE ui_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task            TEXT NOT NULL,
    category        TEXT,       -- mailbox_oauth, other
    priority        TEXT DEFAULT 'medium',
    status          TEXT DEFAULT 'pending',  -- pending, done
    context         TEXT,       -- Why this needs to happen
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP
);

-- Meetings / pipeline attribution (manual or from Salesforce)
CREATE TABLE meetings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id      INTEGER REFERENCES contacts(id),
    account_name    TEXT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    meeting_date    DATE,
    meeting_type    TEXT,       -- discovery, demo, follow_up
    outcome         TEXT,       -- scheduled, completed, no_show, rescheduled
    notes           TEXT,
    attributed_to   TEXT,       -- ai_sdr, manual, referral
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

```sql
-- Contacts
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_account ON contacts(account_name);
CREATE INDEX idx_contacts_icp ON contacts(icp_category, icp_function_type);
CREATE INDEX idx_contacts_suppressed ON contacts(suppressed);
CREATE INDEX idx_contacts_instantly ON contacts(instantly_lead_id);
CREATE INDEX idx_contacts_verified ON contacts(verification_status);

-- Campaigns
CREATE INDEX idx_campaigns_instantly ON campaigns(instantly_campaign_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- Campaign contacts
CREATE INDEX idx_cc_campaign ON campaign_contacts(campaign_id);
CREATE INDEX idx_cc_contact ON campaign_contacts(contact_id);
CREATE INDEX idx_cc_instantly ON campaign_contacts(instantly_lead_id);

-- Engagement
CREATE INDEX idx_engagement_campaign ON engagement_events(campaign_id);
CREATE INDEX idx_engagement_contact ON engagement_events(contact_id);
CREATE INDEX idx_engagement_type ON engagement_events(event_type);
CREATE INDEX idx_engagement_date ON engagement_events(event_date);

-- Email threads
CREATE INDEX idx_threads_status ON email_threads(status);
CREATE INDEX idx_threads_instantly ON email_threads(instantly_thread_id);
CREATE INDEX idx_threads_campaign ON email_threads(campaign_id);
CREATE INDEX idx_threads_contact ON email_threads(contact_email);
CREATE INDEX idx_threads_unread ON email_threads(is_unread);

-- Metrics
CREATE INDEX idx_metrics_campaign ON metric_snapshots(campaign_id, snapshot_date);
CREATE INDEX idx_metrics_date ON metric_snapshots(snapshot_date);

-- Block list
CREATE INDEX idx_blocklist_entry ON block_list(email_or_domain);

-- Account engagement
CREATE INDEX idx_account_engagement ON account_engagement(engagement_tier);

-- Mailbox health
CREATE INDEX idx_mailbox_health ON mailbox_health_log(mailbox_email, snapshot_date);

-- Webhooks
CREATE INDEX idx_webhooks_event ON webhooks(event_type);

-- Lead labels
CREATE INDEX idx_labels_interest ON lead_labels(interest_status);

-- Reply sentiment
CREATE INDEX idx_sentiment_campaign ON reply_sentiment(campaign_id);
CREATE INDEX idx_sentiment_contact ON reply_sentiment(contact_email);
CREATE INDEX idx_sentiment_value ON reply_sentiment(sentiment);
CREATE INDEX idx_sentiment_pushed ON reply_sentiment(pushed_to_clay);

-- Clay push log
CREATE INDEX idx_clay_push_sentiment ON clay_push_log(reply_sentiment_id);
CREATE INDEX idx_clay_push_sf_status ON clay_push_log(salesforce_sync_status);
```

---

## Part 5 — Sync Strategy

### What to pull from Instantly and when

| Data | Method | Frequency | SQLite Target |
|------|--------|-----------|---------------|
| Campaign list + stats | MCP `list_campaigns` | Every 15 min or on-demand | campaigns (update counts + status) |
| Campaign detail | MCP `get_campaign` | On-demand | campaigns + campaign_steps (verify sync) |
| Daily analytics | MCP `get_daily_campaign_analytics` | Daily (cron or manual) | metric_snapshots |
| Campaign analytics | MCP `get_campaign_analytics` | Every 15 min or on-demand | metric_snapshots (aggregated) |
| Emails / replies | MCP `list_emails` + `get_email` | Every 15 min | email_threads (insert new, preserve workflow status) |
| Unread count | MCP `count_unread_emails` | Every 15 min | Quick health check — triggers full email sync if > 0 |
| Lead data | MCP `list_leads` (per campaign or per list) | Every 30 min or on-demand | contacts (update instantly_lead_id, status, engagement counts) |
| Lead verification stats | MCP `get_verification_stats_for_lead_list` | After bulk imports | contacts (update verification_status) |
| Mailbox health | MCP `list_accounts` + `get_account` | Daily or on-demand | mailboxes + mailbox_health_log |
| Warmup metrics | MCP `get_warmup_analytics` | Daily | mailbox_health_log (warmup fields) |
| Mailbox vitals | MCP `manage_account_state` (test_vitals) | Weekly proactive check | mailbox_health_log (vitals fields) |
| Background jobs | MCP `list_background_jobs` + `get_background_job` | After bulk operations | Inline — wait for completion |
| Block list | API `GET /block-list-entries` | Daily or on-demand | block_list |
| Webhooks | API `GET /webhooks` | On-demand | webhooks |
| Lead labels | API `GET /lead-labels` | On-demand | lead_labels |
| Custom tags | API `GET /custom-tags` | On-demand | custom_tags |
| Subsequence status | API `GET /subsequences/{id}` | On-demand | campaign_subsequences |
| Inbox placement results | API `GET /inbox-placement-analytics` + `GET /inbox-placement-reports` | After tests complete | inbox_placement_tests |
| Audit log | API `GET /audit-logs` | Weekly or on investigation | api_log (merge for forensics) |

### What to push to Instantly and when

| Data | Method | When |
|------|--------|------|
| New campaign | MCP `create_campaign` (two-step) | Campaign launch |
| Update campaign | MCP `update_campaign` | Content update, setting change |
| Assign senders | MCP `create_campaign` Step 2 or `update_campaign` | Campaign launch or sender rotation |
| Enroll contacts (single) | MCP `create_lead` | Individual add |
| Enroll contacts (bulk) | MCP `add_leads_to_campaign_or_list_bulk` (up to 1,000/call) | Campaign launch or batch add |
| Activate campaign | MCP `activate_campaign` | On command |
| Pause campaign | MCP `pause_campaign` | On command or auto-pause trigger |
| Delete campaign | MCP `delete_campaign` | Cleanup |
| Update lead data | MCP `update_lead` | Data correction, re-personalization |
| Delete lead | MCP `delete_lead` | Permanent suppression |
| Move leads | MCP `move_leads_to_campaign_or_list` | Campaign transitions |
| Reply to email | MCP `reply_to_email` | Response workflow |
| Mark thread read | MCP `mark_thread_as_read` | After processing |
| Verify email | MCP `verify_email` | Pre-enrollment validation |
| Create mailbox | MCP `create_account` | Onboarding new senders |
| Update mailbox | MCP `update_account` | Setting changes, warmup config |
| Pause/resume mailbox | MCP `manage_account_state` | Health management |
| Enable/disable warmup | MCP `manage_account_state` | Warmup lifecycle |
| Create lead list | MCP `create_lead_list` | Organizing leads |
| Add to block list | API `POST /block-list-entries` | Opt-out, bounce |
| Remove from block list | API `DELETE /block-list-entries/{id}` | False positive correction |
| Create webhook | API `POST /webhooks` | Event listener setup |
| Update/delete webhook | API `PATCH/DELETE /webhooks/{id}` | Maintenance |
| Test webhook | API `POST /webhooks/{id}/test` | Validation |
| Create lead label | API `POST /lead-labels` | AI classification setup |
| Create subsequence | API `POST /subsequences` | Behavior-triggered follow-ups |
| Create/sync email templates | API `POST/PATCH /email-templates` | Template management |
| Create custom tags | API `POST /custom-tags` | Organization |
| Create inbox placement test | API `POST /inbox-placement-tests` | Deliverability testing |

### Webhook event handling

Configure webhooks via the API (`POST /webhooks`) to receive real-time events. Instantly supports 19+ event types including custom label-triggered events. Webhooks are fully mutable — create, read, update, delete, test, and resume after errors.

| Webhook Event Type | Action |
|-------------------|--------|
| `email_sent` | Insert engagement_event, increment campaign_contacts.emails_sent |
| `email_opened` | Insert engagement_event, increment campaign_contacts.emails_opened |
| `email_link_clicked` | Insert engagement_event, increment campaign_contacts.emails_clicked |
| `reply_received` | Insert engagement_event, set campaign_contacts.replied=1, create email_threads entry |
| `email_bounced` | Insert engagement_event, set campaign_contacts.bounced=1, consider block list |
| `lead_unsubscribed` | Insert engagement_event, add to block_list, suppress contact |
| `campaign_completed` | Update campaigns.status='completed', set completed_at |
| `account_error` | Update mailboxes.status, create ui_task if OAuth reconnect needed |
| `lead_neutral` | Update campaign_contacts.interest_status |
| Custom label events | Update campaign_contacts.interest_status based on custom_interest_value |

### Sync Conflict Resolution

Because Instantly contacts are fully mutable (unlike the previous platform), we need conflict resolution:

| Field | Resolution |
|-------|-----------|
| first_name, last_name, company_name, phone | SQLite is source of truth (richer data from enrichment). Push to Instantly on change |
| email | Immutable — never changes after creation |
| custom_variables | SQLite is source of truth. On push, always send complete object (Instantly replaces, doesn't merge) |
| engagement counts (opens, replies, clicks) | Instantly is source of truth. Pull only, never push |
| status (lead status in campaign) | Instantly is source of truth. Pull to update local |
| interest_status | Instantly is source of truth (AI-scored). Pull to update local |
| suppressed/blocked | SQLite is source of truth for suppression decisions. Push block list entries to Instantly |

---

## Part 6 — Operational Workflows (MCP-First)

### Workflow 1: Campaign Launch

```
Agent receives: "Launch campaign targeting Epic hospitals 500+ beds in Southeast, CNO persona"

1. PLAN (SQLite only)
   - Query accounts: WHERE primary_ehr='Epic' AND total_beds>=500 AND state IN (...) AND tier IN ('Priority','Active')
   - Query contacts: JOIN on account, WHERE icp_category='Decision Maker' AND icp_department LIKE '%Nursing%' AND suppressed=0
   - Store in campaign_ideas with targeting metadata
   - Draft email content (subject + body + variants) in campaign_steps

2. VERIFY (MCP)
   - verify_email on any contacts not yet verified
   - Poll API GET /email-verification/{email} for pending results
   - Flag invalid/risky in contacts.verification_status

3. CREATE (MCP)
   - create_campaign: Step 1 with name, subject, body, sequence_steps, sequence_subjects, sequence_bodies, daily_limit, email_gap, stop_on_reply, stop_for_company
   - create_campaign: Step 2 with email_list (sender accounts)
   - Store instantly_campaign_id in campaigns table

4. ENROLL (MCP)
   - add_leads_to_campaign_or_list_bulk: up to 1,000 per call
   - Each lead: email, first_name, last_name, company_name, personalization, custom_variables (title, account, ICP tier, etc.)
   - skip_if_in_workspace=true to prevent double-enrollment
   - Update campaign_contacts and contacts.instantly_lead_id

5. ACTIVATE (MCP)
   - activate_campaign
   - Update campaigns.status='active', launched_at=now()

6. MONITOR (MCP, ongoing)
   - get_campaign_analytics every 15 min
   - get_daily_campaign_analytics daily
   - Auto-pause if bounce_rate > 5%: pause_campaign
```

### Workflow 2: Reply Processing

```
Agent receives: "Process today's replies"

1. SCAN (MCP)
   - count_unread_emails — quick check if there's anything new
   - list_emails filtered to recent dates, ue_type=2 (received)

2. READ (MCP)
   - get_email for each new email — full content, AI interest score, thread context

3. CLASSIFY (Local)
   - Use ai_interest_value from Instantly (0.0-1.0 scale)
   - Cross-reference with lead labels (from API)
   - Update email_threads: sentiment, status

4. SENTIMENT CLASSIFICATION (Local)
   - AI scores reply interest using Instantly's ai_interest_value + reply content analysis
   - Agent reviews and confirms/overrides the AI classification
   - Write to reply_sentiment table: sentiment (positive/negative/neutral/ooo/bounce),
     sentiment_confidence, classified_by (ai/manual)
   - This is the authoritative sentiment record used for downstream routing and per-campaign
     performance tracking

5. TRIAGE (Local + MCP)
   - Positive interest (ai_interest_value > 0.7): status='needs_follow_up', assigned_to='Reagan'
   - Negative/unsubscribe: mark_thread_as_read, add to block_list via API
   - OOO/auto-reply (is_auto_reply=1): mark_thread_as_read, status='archived'
   - Neutral: status='reviewed'

6. RESPOND (MCP)
   - For 'needs_follow_up' threads:
   - reply_to_email with crafted response
   - Update email_threads: replied_via_mcp=1, reply_sent_at=now(), status='handled'
   - mark_thread_as_read

7. CLAY PUSH (Local + HTTP)
   - For replies where sentiment='positive' in reply_sentiment:
   - Build webhook payload with contact info, campaign context, engagement data
   - Fire HTTP POST to Clay webhook URL
   - Log in clay_push_log: payload, response_code, salesforce_sync_status='pending'
   - Update reply_sentiment: pushed_to_clay=1, pushed_at=now()
   - Note: Sentiment data is aggregated per-campaign in SQLite to track which campaigns
     generate the most positive replies (see metric_snapshots + reply_sentiment JOIN)
```

### Workflow 3: Deliverability Health Check

```
Agent receives: "Run daily deliverability check"

1. MAILBOX HEALTH (MCP)
   - list_accounts with status filter for errors (-1, -2, -3)
   - For each error: get_account for details
   - For healthy accounts: manage_account_state test_vitals on random sample

2. WARMUP STATUS (MCP)
   - get_warmup_analytics for all warming accounts
   - Flag accounts with declining warmup_score
   - Flag accounts with warmup_status in banned/suspended states

3. CAMPAIGN HEALTH (MCP)
   - get_campaign_analytics for all active campaigns
   - Check bounce rates, complaint rates
   - Auto-pause campaigns exceeding thresholds: pause_campaign

4. INBOX PLACEMENT (API)
   - GET /inbox-placement-tests for recent test results
   - GET /inbox-placement-analytics for per-ESP breakdown
   - GET /inbox-placement-reports for blacklist + SpamAssassin

5. LOG (SQLite)
   - Insert into mailbox_health_log
   - Update metric_snapshots with campaign health data
   - Create ui_tasks for any OAuth mailboxes needing reconnection
```

### Workflow 4: Account Intelligence Rollup

```
Agent receives: "Update account engagement tiers"

1. PULL LEAD DATA (MCP)
   - For each active campaign: list_leads with campaign filter
   - For each lead: capture email_open_count, email_reply_count, email_click_count, lt_interest_status

2. AGGREGATE (SQLite)
   - Group contacts by account_name
   - Roll up: total enrolled, opened, replied, clicked, bounced
   - Calculate avg_ai_interest from email_threads.ai_interest_value
   - Determine engagement_tier:
     - hot: any contact replied with positive interest
     - warm: any contact opened but no positive reply
     - cold: contacts sent but no opens
     - untouched: no contacts enrolled from this account

3. UPDATE (SQLite)
   - UPSERT into account_engagement
   - Cross-reference with accounts table for scoring adjustments
```

---

## Part 7 — What We Build vs. What Instantly Gives Us

### Instantly gives us a complete outbound operations platform

```
Campaign creation       → create_campaign (MCP) — full config including A/B, scheduling, company controls
Campaign management     → update/activate/pause/delete_campaign (MCP) — full lifecycle
Contact management      → create/update/delete_lead (MCP) — fully mutable with working filters
Bulk enrollment         → add_leads_to_campaign_or_list_bulk (MCP) — 1,000 per call
Email operations        → list/get/reply_to_email + mark_thread_as_read (MCP) — read AND respond
Analytics               → get_campaign_analytics + get_daily_campaign_analytics (MCP) — multi-campaign + daily
Mailbox management      → full CRUD + warmup + vitals testing (MCP) — complete lifecycle
Email verification      → verify_email (MCP) — built-in deliverability check
Lead lists              → full CRUD (MCP) — organize and manage
Lead movement           → move_leads_to_campaign_or_list (MCP) — between campaigns/lists
Contact search          → list_leads with working filters (MCP) — search, status, campaign, date
Campaign search         → search_campaigns_by_contact (MCP) — find all campaigns for a contact
Background jobs         → list/get (MCP) — track async operations
Block list              → full CRUD (API) — domain and email blocking with list+delete
Webhooks                → full CRUD + test + resume (API) — 19+ event types, fully mutable
Lead labels             → full CRUD + AI integration (API) — AI-driven categorization
Subsequences            → full CRUD + control (API) — behavior-triggered follow-ups
Inbox placement         → full test + analytics + reports (API) — per-ESP/geo deliverability
Custom tags             → full CRUD + mappings (API) — organize accounts/campaigns
Email templates         → full CRUD (API) — reusable templates stored in Instantly
AI prompts              → full CRUD (API) — custom prompt templates with model selection
Sales flows             → full CRUD (API) — smart views for lead filtering
Audit log               → full query (API) — activity tracking with forensics
```

### We build the strategic layer

```
Campaign planning       → campaign_ideas + email drafting workflow
Account scoring         → 6-factor weighted model from facility data
ICP matching            → 66-title taxonomy with fuzzy matching
Contact enrichment      → Multi-source enrichment from ZoomInfo, DH, web scraping
                           Note: Instantly also offers SuperSearch Enrichment (10 API endpoints) for lead
                           discovery and AI-powered enrichment with 14+ model options. This overlaps with
                           our DH enrichment pipeline but could supplement it for contacts not in the DH database.
Segment analytics       → Tag campaigns by EHR/persona/geo, aggregate metrics locally
Account engagement      → Roll up contact-level events to account-level intelligence
Historical trending     → Daily metric snapshots for 30/60/90 day analysis
Pipeline attribution    → meetings table linking campaigns to business outcomes
Reply workflow          → Status tracking (new → reviewed → needs_follow_up → handled → archived)
Messaging framework     → Layer1/Layer2/Layer3 composition model
Kill-switch logic       → Poll analytics → check thresholds → auto-pause
Template performance    → Track open/reply rates across template reuse over time
Data quality pipeline   → Dedup, golden record, suppression logic
```

### The hard truth

Instantly is 60% of the system. SQLite + our code is 40%. That's a complete inversion from the previous architecture where the sending platform was 20% and we had to build 80%.

Here's what changed:

| Capability | Before | Now with Instantly |
|-----------|--------|-------------------|
| Contact CRUD | Create-only, filters broken, no update, no delete | Full CRUD with working filters, bulk operations |
| Reply handling | List-only, no reply, no mark-read | Full read + reply + mark-read via MCP agent |
| Mailbox management | Read-only, no create/update/delete | Full lifecycle: create, update, warmup, vitals, pause, resume, delete |
| Campaign management | Create + activate/pause/delete only | Full CRUD: create, update all settings, activate, pause, delete |
| Block list / DNC | Write-only (add to DNC, can't list or remove) | Full CRUD: add, list, get, delete |
| Webhooks | Create-only (can't update or delete) | Full CRUD + test + resume |
| Email verification | None | Built-in with MCP tool |
| Inbox placement testing | None | Full test + analytics + reports (per-ESP/geo) |
| AI interest scoring | None | Built-in on every email (ai_interest_value 0.0-1.0) |
| Subsequences | None | Behavior-triggered follow-ups with conditions |
| Company-level controls | None | stop_for_company, match_lead_esp, per-company limits |
| A/B optimization | Manual variant tracking | Auto-variant selection with AI optimization |
| Audit trail | None | Full audit log with API/UI distinction |
| MCP integration | None (required SDK wrapper scripts) | 38 native MCP tools — AI agent calls directly, no code |

The MCP layer is the fundamental difference. The AI agent doesn't write scripts, doesn't call APIs through wrapper code, doesn't need an SDK. It calls `create_campaign`, `add_leads_to_campaign_or_list_bulk`, `activate_campaign`, `reply_to_email` directly as tool invocations. The entire outbound operation becomes a conversation between the agent and the platform.

What we still build locally is the *strategic intelligence* layer: which accounts to target, which contacts to prioritize, what messaging to use, how to score engagement, and how to report on pipeline impact. That's the 40% that makes this an AI SDR rather than just an email sender.

---

## Part 8 — Downstream Integration: Clay → Salesforce

### The Flow

Positive replies are the output of the outbound system. They need to flow downstream into the CRM so the sales team can act on them. The integration path:

```
Positive reply detected in Instantly
  → Agent classifies sentiment (AI interest score + manual review)
  → Saved to reply_sentiment table in SQLite
  → Webhook fires to Clay with contact + campaign context
  → Clay enriches with additional data points (firmographics, technographics, social)
  → Clay creates/updates Salesforce Lead or Contact
  → Attached to Account, Activity logged
  → Salesforce sync status written back to clay_push_log
```

### What Triggers the Push

Only replies classified as `sentiment = 'positive'` get pushed downstream. Classification uses two signals:

1. **Instantly's AI interest scoring** — `ai_interest_value` (0.0–1.0) on every received email. Values > 0.7 are strong positive indicators
2. **Agent confirmation** — the agent reviews the AI score + reply content and confirms or overrides. Final sentiment written to `reply_sentiment` table

Negative, neutral, OOO, and bounce replies are tracked locally but never pushed to Clay.

### Webhook Payload to Clay

When a positive reply is confirmed, the agent fires an HTTP POST to a Clay webhook URL with:

```json
{
  "contact": {
    "email": "jane.doe@hospital.org",
    "first_name": "Jane",
    "last_name": "Doe",
    "title": "Chief Nursing Officer",
    "company": "Regional Medical Center",
    "account_name": "Regional Health System",
    "phone": "+1-555-0123",
    "linkedin_url": "https://linkedin.com/in/janedoe"
  },
  "campaign": {
    "name": "Epic Enterprise CNO Q1",
    "sequence_step": 2,
    "reply_content_preview": "Thanks for reaching out. We've been looking at insulin management...",
    "campaign_id": "inst_abc123"
  },
  "engagement": {
    "total_opens": 4,
    "total_replies": 1,
    "sentiment": "positive",
    "ai_interest_value": 0.85,
    "first_contact_date": "2026-02-10",
    "reply_date": "2026-02-18"
  }
}
```

### Clay's Role

Clay receives the webhook and:

1. **Enriches** the contact with additional data points not in our enrichment DB (social presence, company news, tech stack changes)
2. **Creates or updates** a Salesforce Lead (or Contact if the Account already exists)
3. **Attaches to the correct Account** using account_name matching or domain lookup
4. **Logs an Activity** on the Lead/Contact record with campaign context and reply content
5. **Notifies** the assigned rep (Clayton or the territory owner) via Salesforce alert

### SQLite Tracking

Every push is logged for reconciliation and debugging:

- **`reply_sentiment` table** — every classified reply with sentiment, confidence, classification source (AI vs manual), and downstream push status
- **`clay_push_log` table** — every webhook fired to Clay with full payload, response code, and Salesforce sync status (pending → synced → failed)

This creates a complete audit trail from reply → classification → Clay push → Salesforce record. Failed pushes can be retried; sync status mismatches can be investigated.

### Monthly Enrichment Refresh

The enrichment pipeline (`enrichment/runner.py`) should be re-run on a regular schedule to keep signals fresh:

| Cadence | Recipes | Purpose |
|---------|---------|---------|
| **Monthly** | R3 (Leadership Changes) + R9 (Account Bundle) | Catch new leadership hires/departures, financial shifts, membership changes, quality penalty updates |
| **Quarterly** | R4 (Tiered Discovery) | Full ICP contact coverage refresh — new hires at target hospitals, title changes, email updates |
| **On-demand** | R1, R2, R10 | Deep dives on specific hospitals/systems when an account becomes high-priority or a deal is progressing |

New signals from refreshed enrichment data feed back into campaign planning — a new CNO hire detected by R3 becomes a trigger for a personalized outreach sequence.

---

## Potential Future Enhancements

> These are not blockers — the system is fully functional today. Ideas for future improvement if/when the need arises.

| Enhancement | Area | Details |
|-------------|------|---------|
| Auto-pause on kill-switch breach | pull_metrics.py | Currently logs WARNING when bounce > 5%. Could auto-call `pause_campaign` and send an alert. |
| Pre-flight checklist validation | launch_campaign.py | Automated checks before activation: mailboxes assigned? leads enrolled? sequences configured? warmup score > 85? |
| Week-over-week trend queries | check_status.py | Automated `metric_snapshots` comparison across dates. Currently requires manual SQL. |
| Webhook retry logic | push_to_clay.py | Retry on 5xx with exponential backoff. Currently fails silently on HTTP errors. |
| Scheduled automation | Ops | Cron jobs or task scheduler for daily `pull_metrics` + `process_replies`, monthly signal refresh, quarterly contact refresh. |
| Domain diversity checker | launch_campaign.py | Warn if all assigned mailboxes share the same domain. Spread across domains for deliverability. |
| Contact scoring in DB | enroll | Apply ICP scoring logic from enrichment pipeline to hello-world contacts before enrollment. |
| Keyword admin UI | config_server.py | Let operators edit positive/negative/OOO keyword lists via the config UI instead of editing `process_replies.py` directly. |
