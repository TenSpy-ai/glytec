# GTM Operations Design — Salesforge API + SQLite Homebase

**Date:** 2026-02-19
**Context:** Glytec AI SDR — outbound GTM system for Glucommander (insulin management for hospitals)
**Goal:** Stay out of the Salesforge UI as much as possible. Use a local SQLite database as the operational homebase for everything the API can't track.

---

## Part 1 — GTM Team User Stories

### Campaign Planning

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| P1 | Clayton | plan a campaign targeting Epic hospitals with 500+ beds in the Southeast | I can systematically work through high-value segments |
| P2 | Clayton | draft 3 email subject/body variants for a campaign before pushing anything | I can review and iterate on copy without touching Salesforge |
| P3 | Clayton | save successful email templates for reuse across campaigns | I don't rewrite the same angles from scratch |
| P4 | Clayton | track campaign ideas in a backlog with priority/status | I know what's coming next and nothing falls through |
| P5 | Clayton | see which accounts have never been contacted vs. already in a sequence | I avoid double-contacting and find untouched accounts |

### Campaign Execution

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| E1 | Clayton | create a sequence in Salesforge, load emails, assign mailboxes, and enroll contacts in one script | the entire campaign launch is automated |
| E2 | Clayton | activate a campaign | sending starts |
| E3 | Clayton | pause a campaign | sending stops immediately |
| E4 | Clayton | delete a test campaign from Salesforge | I keep the workspace clean |
| E5 | Clayton | A/B test two subject lines on the same step | I can learn what resonates |
| E6 | Reagan | enroll a new batch of contacts into an existing active campaign | I can add late-arriving contacts without rebuilding |

### Monitoring & Response

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| M1 | Clayton | see today's sends, opens, replies, and bounces across all campaigns at a glance | I know what's working and what's not |
| M2 | Clayton | auto-pause any campaign where bounce >5% or spam >0.3% | I protect domain reputation |
| M3 | Reagan | see all replies that came in today, with the message content | I can respond to interested prospects |
| M4 | Reagan | mark a reply as "handled" or "needs follow-up" | I can track my reply workflow |
| M5 | Clayton | know which mailboxes are disconnected or unhealthy | I can fix them before they cause bounces |
| M6 | Clayton | add a prospect to DNC after they opt out | they never get another email |

### Contact Management

| # | As... | I want to... | So that... |
|---|-------|-------------|-----------|
| C1 | Clayton | search contacts by email, name, title, account, or ICP category | I can find anyone fast |
| C2 | Clayton | see all contacts at a specific account with their engagement history | I know who we've talked to and what happened |
| C3 | Clayton | update a contact's title or other data when it changes | the record stays accurate |
| C4 | Clayton | see which contacts are suppressed and why | I can audit suppression logic |
| C5 | Clayton | bulk-import contacts from a CSV with ICP matching | I can load new lists efficiently |

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

---

## Part 2 — API Capability Map

For each user story: what the API provides, what SQLite fills, and what still requires the UI.

### Campaign Planning (P1–P5)

| Story | API | SQLite | UI Required? |
|-------|-----|--------|-------------|
| P1 | Nothing — planning is local | `campaigns` table with targeting criteria, segment, EHR, geo filters | No |
| P2 | Nothing — drafting is local | `email_drafts` table with variants, approval status | No |
| P3 | Nothing — templates are local | `email_templates` table with tags, performance history | No |
| P4 | Nothing — backlog is local | `campaign_ideas` table with priority, status, notes | No |
| P5 | GET /sequences returns all sequences, but no filter by account. GET /contacts returns all contacts but can't filter by sequence. | `campaign_contacts` junction tracks which contacts are in which campaigns + their account | No |

### Campaign Execution (E1–E6)

| Story | API | SQLite | UI Required? |
|-------|-----|--------|-------------|
| E1 | POST /sequences → PUT /steps → PUT /mailboxes → PUT /import-lead | Track campaign<>sequence mapping, enrolled contacts, step content | No |
| E2 | PUT /status {"status": "active"} | Update local status | No |
| E3 | PUT /status {"status": "paused"} | Update local status | No |
| E4 | DELETE /sequences/{id} → 204 | Remove from local tracking | No |
| E5 | PUT /steps with multiple variants + distributionStrategy:"custom" | Track variant performance locally | No |
| E6 | PUT /import-lead (one at a time) | Add to campaign_contacts | No |

### Monitoring & Response (M1–M6)

| Story | API | SQLite | UI Required? |
|-------|-----|--------|-------------|
| M1 | GET /analytics (per sequence, requires date range). GET /sequence-metrics (workspace aggregate). | Store daily metric snapshots for trending. Cross-reference with campaign metadata for segment/persona breakdowns. | No |
| M2 | GET /analytics for bounce rate → PUT /status to pause. | Kill-switch logic runs locally. Log every auto-pause event. | No |
| M3 | GET /threads — returns subject, content, contact name, replyType. **But: list only, no detail view, can't mark read.** | Store thread data locally. Track reply status (new/handled/needs-follow-up). | **Partial — replying to emails requires UI or external email client** |
| M4 | No API support — threads are read-only, no update. | `reply_status` field on local thread mirror | No (tracking is local) |
| M5 | GET /mailboxes — returns status, disconnectReason. **Cannot fix disconnected mailboxes via API.** | Store mailbox health snapshots for trend. Alert on disconnect. | **Yes — reconnecting mailboxes requires UI** |
| M6 | POST /dnc/bulk — adds email to DNC. **Cannot list or remove from DNC.** | Maintain local DNC mirror (since API is write-only). | No |

### Contact Management (C1–C5)

| Story | API | SQLite | UI Required? |
|-------|-----|--------|-------------|
| C1 | GET /contacts — **all filters broken** (email, search, firstName, tags). Must paginate all 7K+ contacts. | **Primary search/filter is local.** Full contact data in SQLite with indexes. | No |
| C2 | GET /contacts returns 8 fields only. No engagement/send history per contact. | contacts + campaign_contacts + engagement_events tables. Engagement from webhook events or analytics snapshots. | No |
| C3 | **No PUT or PATCH on contacts.** Cannot update any field via API. Re-POST with same email upserts only firstName, lastName, company — not customVars or tags. | **Update locally only.** Salesforge contact is a snapshot at enrollment time. | No (but Salesforge stays stale) |
| C4 | No suppression info from API. DNC list is write-only. | contacts table with suppressed flag + suppression_reason | No |
| C5 | POST /contacts or PUT /import-lead for enrollment | Full ICP matching pipeline runs locally | No |

### Reporting (R1–R6)

| Story | API | SQLite | UI Required? |
|-------|-----|--------|-------------|
| R1 | GET /analytics (per sequence, daily breakdown). GET /sequence-metrics (aggregates). | Store daily snapshots. Compute week-over-week deltas locally. | No |
| R2 | GET /analytics for each sequence separately. | Side-by-side queries against metric_snapshots table. | No |
| R3 | **API has no segment-level breakdown.** Analytics are per-sequence only. | Tag campaigns with EHR segment in SQLite. Aggregate metrics by segment locally. | No |
| R4 | **API has no persona-level breakdown.** | Tag contacts with ICP category. Cross-reference engagement events with contact persona. | No |
| R5 | **Salesforge has zero pipeline/opportunity data.** | Requires Salesforce integration or manual tracking. `meetings` table for pipeline attribution. | No (but needs external data) |
| R6 | GET /analytics with date ranges up to 90 days. | Store daily snapshots for arbitrary historical queries. | No |

### Account Strategy (A1–A4)

| Story | API | SQLite | UI Required? |
|-------|-----|--------|-------------|
| A1 | Nothing — scoring is local | accounts table with score, tier, segment, opportunity $ | No |
| A2 | Nothing — scoring is local | Re-run scoring model against updated data | No |
| A3 | **API has no account-level engagement view.** | Aggregate engagement events by contact → account rollup | No |
| A4 | **API can't tell you which accounts are untouched.** | campaign_contacts tracks engagement. Accounts with zero enrolled contacts = untouched. | No |

---

## Part 3 — Complete Gap Analysis

### Things that MUST go through the Salesforge UI

| Task | Why | Frequency |
|------|-----|-----------|
| Reconnect disconnected mailboxes | No API for mailbox management (create/update/delete all 404) | As needed (check daily) |
| Reply to prospect emails | GET /threads is list-only — no reply endpoint, no mark-read | Every reply |
| Delete webhooks | No DELETE on /integrations/webhooks | Rare |
| Update webhook URLs | No PUT on /integrations/webhooks | Rare |
| Remove email from DNC | No DELETE on /dnc/bulk | Rare |
| View DNC list | No GET on /dnc | When auditing |
| Create new mailboxes | No POST on /mailboxes | Rare (onboarding) |
| Change mailbox daily send limit | No PUT on /mailboxes | Rare |
| View A/B variant-level metrics | Analytics endpoint returns aggregate per step, not per variant | Per A/B test |

### Things the API can't do but we can work around with SQLite

| Gap | Workaround |
|-----|-----------|
| No contact search/filter | Full contact DB locally with indexed search |
| No contact update | Update locally; Salesforge contact is a point-in-time snapshot |
| No contact delete | Flag suppressed locally; don't re-enroll |
| No contact engagement history | Track via webhook events or periodic analytics pulls |
| No account-level view | Aggregate contact engagement to account level locally |
| No segment/persona analytics | Tag campaigns and contacts locally, compute breakdowns |
| No historical metric storage | Daily snapshots in metric_snapshots table |
| No DNC list read | Maintain local DNC mirror |
| No list of enrolled contacts per sequence | Track in campaign_contacts junction table |
| No campaign planning | campaign_ideas + email_drafts tables |
| No template library | email_templates table |
| Filters don't work on list endpoints | Paginate all + filter client-side, cache locally |

### Things that are fully automatable via API

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| Create sequence | POST /sequences | language: "american_english" |
| Set email content | PUT /steps | Replaces all steps — send full array |
| Assign mailboxes | PUT /mailboxes | Full replacement, not append |
| Enroll contacts | PUT /import-lead | One at a time; linkedinUrl optional |
| Activate campaign | PUT /status | Requires mailboxes assigned |
| Pause campaign | PUT /status | Always works |
| Delete campaign | DELETE /sequences/{id} | Permanent |
| Add to DNC | POST /dnc/bulk | Array of email strings |
| Pull daily metrics | GET /analytics | Requires from_date + to_date |
| Pull aggregate metrics | GET /sequence-metrics | Optional product_id filter |
| List reply threads | GET /threads | List only, content included |
| List mailbox health | GET /mailboxes + GET /mailboxes/{id} | Includes disconnectReason |
| Create webhook listeners | POST /integrations/webhooks | 10 event types |

---

## Part 4 — SQLite Homebase Schema

### Design Principles

1. **SQLite is the source of truth** for planning, targeting, contact enrichment, ICP matching, and engagement history
2. **Salesforge is the sending engine** — we push to it and pull metrics from it, but we don't rely on it to store anything
3. **Every table has timestamps** — created_at and updated_at for auditability
4. **salesforge_id links local records to Salesforge** — nullable (not everything gets pushed)
5. **Soft deletes** — suppressed/archived flags instead of row deletion

### Tables

```sql
-- ═══════════════════════════════════════════
-- CORE ENTITIES
-- ═══════════════════════════════════════════

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
    highest_level_parent      TEXT,     -- FK → accounts.system_name
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

-- All contacts (much richer than Salesforge's 8 fields)
CREATE TABLE contacts (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name              TEXT,
    last_name               TEXT,
    email                   TEXT,
    title                   TEXT,       -- We store this even though SF doesn't
    phone                   TEXT,       -- We store this even though SF doesn't
    company                 TEXT,
    linkedin_url            TEXT,
    account_name            TEXT,       -- FK → accounts.system_name
    facility_definitive_id  TEXT,       -- FK → facilities.definitive_id

    -- ICP matching
    icp_category            TEXT,       -- Decision Maker / Influencer
    icp_intent_score        INTEGER,    -- 50-95
    icp_function_type       TEXT,       -- Clinical / Business
    icp_job_level           TEXT,       -- Executive, Director, Mid-Level, IC
    icp_department          TEXT,       -- From ICP taxonomy
    icp_matched             INTEGER DEFAULT 0,

    -- Data quality
    source                  TEXT,       -- zoominfo, dh, web_scraping, csv_import, manual
    validated               INTEGER DEFAULT 0,   -- Email validated?
    golden_record           INTEGER DEFAULT 0,   -- Survived dedup?
    suppressed              INTEGER DEFAULT 0,
    suppression_reason      TEXT,       -- glytec_client, dnc, opt_out, bounced, stale

    -- Salesforge sync
    salesforge_lead_id      TEXT,       -- lead_xxx from Salesforge (if pushed)
    last_pushed_at          TIMESTAMP,  -- When last sent to Salesforge

    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email)
);

-- ICP title taxonomy (from ICP.json — 66 titles)
CREATE TABLE icp_titles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    department      TEXT,
    title           TEXT,
    category        TEXT,       -- Decision Maker / Influencer
    intent_score    INTEGER,
    function_type   TEXT,       -- Clinical / Business
    job_level       TEXT        -- Executive, Director, Mid-Level, IC, Other
);


-- ═══════════════════════════════════════════
-- CAMPAIGN MANAGEMENT
-- ═══════════════════════════════════════════

-- Campaign ideas / backlog (not yet in Salesforge)
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

-- Active campaigns (maps 1:1 to Salesforge sequences once launched)
CREATE TABLE campaigns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    idea_id         INTEGER REFERENCES campaign_ideas(id),

    -- Salesforge link
    salesforge_seq_id TEXT,    -- seq_xxx (null until pushed)
    salesforge_status TEXT,    -- draft, active, paused, completed, deleted

    -- Targeting metadata (for local analytics rollups)
    target_segment  TEXT,
    target_ehr      TEXT,
    target_geo      TEXT,
    target_tier     TEXT,
    target_persona  TEXT,

    -- Config
    step_count      INTEGER DEFAULT 1,
    mailbox_count   INTEGER DEFAULT 0,
    contact_count   INTEGER DEFAULT 0,

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
    enrolled_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          TEXT DEFAULT 'enrolled',  -- enrolled, contacted, replied, bounced, unsubscribed, completed

    -- Engagement summary (rolled up from events)
    emails_sent     INTEGER DEFAULT 0,
    emails_opened   INTEGER DEFAULT 0,
    emails_clicked  INTEGER DEFAULT 0,
    replied         INTEGER DEFAULT 0,
    reply_type      TEXT,     -- positive, negative, ooo, null
    bounced         INTEGER DEFAULT 0,

    UNIQUE(campaign_id, contact_id)
);

-- Email steps within a campaign (our copy + sync status)
CREATE TABLE campaign_steps (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id         INTEGER NOT NULL REFERENCES campaigns(id),
    step_order          INTEGER NOT NULL,    -- 0-indexed
    step_name           TEXT,                -- "Initial email", "Follow-up 1", etc.
    wait_days           INTEGER DEFAULT 0,

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
    variant_label       TEXT DEFAULT 'A',
    distribution_weight INTEGER DEFAULT 100,

    -- Salesforge sync
    salesforge_step_id    TEXT,    -- stp_xxx
    salesforge_variant_id TEXT,    -- stpv_xxx
    synced_at             TIMESTAMP,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reusable email templates
CREATE TABLE email_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category        TEXT,       -- cold_email, follow_up, case_study, direct_cta
    persona         TEXT,       -- CNO, CFO, CQO, CEO, COO, CMO, general
    ehr_segment     TEXT,       -- epic, cerner, meditech, any
    subject         TEXT,
    body_html       TEXT,
    body_plain      TEXT,
    tags            TEXT,       -- comma-separated
    times_used      INTEGER DEFAULT 0,
    avg_open_rate   REAL,       -- Updated from campaign performance
    avg_reply_rate  REAL,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ═══════════════════════════════════════════
-- ENGAGEMENT TRACKING
-- ═══════════════════════════════════════════

-- Individual engagement events (from webhooks or analytics pulls)
CREATE TABLE engagement_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    contact_id      INTEGER REFERENCES contacts(id),
    contact_email   TEXT,      -- Denormalized for quick lookup
    event_type      TEXT NOT NULL,  -- sent, opened, clicked, replied, bounced, unsubscribed
    event_date      TIMESTAMP,
    metadata        TEXT,      -- JSON: reply content, bounce reason, link clicked, etc.
    source          TEXT DEFAULT 'api_pull',  -- api_pull, webhook, manual
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reply thread mirror (since API is list-only, no detail/update)
CREATE TABLE reply_threads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    salesforge_thread_id TEXT,   -- mth_xxx
    campaign_id         INTEGER REFERENCES campaigns(id),
    contact_id          INTEGER REFERENCES contacts(id),
    contact_email       TEXT,
    contact_first_name  TEXT,
    contact_last_name   TEXT,
    subject             TEXT,
    content             TEXT,       -- Reply content
    reply_type          TEXT,       -- ooo, lead_replied
    sentiment           TEXT,       -- positive, negative, neutral, ooo (classified locally)
    mailbox_id          TEXT,
    event_date          TIMESTAMP,

    -- Our workflow tracking (API can't do this)
    status              TEXT DEFAULT 'new',  -- new, reviewed, needs_follow_up, handled, archived
    handled_by          TEXT,       -- Clayton, Reagan
    handled_at          TIMESTAMP,
    follow_up_notes     TEXT,

    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(salesforge_thread_id)
);


-- ═══════════════════════════════════════════
-- DELIVERABILITY & MAILBOX HEALTH
-- ═══════════════════════════════════════════

-- Mailbox inventory + health (since API is read-only for mailboxes)
CREATE TABLE mailboxes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    salesforge_id       TEXT UNIQUE,    -- mbox_xxx
    address             TEXT NOT NULL,
    first_name          TEXT,
    last_name           TEXT,
    daily_email_limit   INTEGER,
    provider            TEXT,           -- gmail, outlook
    status              TEXT,           -- active, disconnected
    disconnect_reason   TEXT,
    tracking_domain     TEXT,
    last_synced_at      TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily mailbox health snapshots
CREATE TABLE mailbox_health_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mailbox_id      INTEGER REFERENCES mailboxes(id),
    snapshot_date   DATE NOT NULL,
    status          TEXT,
    disconnect_reason TEXT,
    -- Future: warmup stats from Warmforge API
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mailbox_id, snapshot_date)
);

-- Local DNC mirror (API is write-only — can't list or remove)
CREATE TABLE dnc_list (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    reason          TEXT,     -- opt_out, bounce, suppression, manual
    source          TEXT,     -- webhook, manual, csv_import, salesforce
    added_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pushed_to_salesforge INTEGER DEFAULT 0,  -- Have we POST'd to /dnc/bulk?
    pushed_at       TIMESTAMP
);


-- ═══════════════════════════════════════════
-- REPORTING & METRICS
-- ═══════════════════════════════════════════

-- Daily metric snapshots per campaign (from GET /analytics)
CREATE TABLE metric_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    salesforge_seq_id TEXT,
    snapshot_date   DATE NOT NULL,

    -- Counts
    contacted       INTEGER DEFAULT 0,
    sent            INTEGER DEFAULT 0,
    opened          INTEGER DEFAULT 0,
    unique_opened   INTEGER DEFAULT 0,
    clicked         INTEGER DEFAULT 0,
    unique_clicked  INTEGER DEFAULT 0,
    replied         INTEGER DEFAULT 0,
    bounced         INTEGER DEFAULT 0,
    unsubscribed    INTEGER DEFAULT 0,

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
    account_name    TEXT NOT NULL,       -- FK → accounts.system_name
    total_contacts  INTEGER DEFAULT 0,
    contacts_enrolled INTEGER DEFAULT 0,
    contacts_opened INTEGER DEFAULT 0,
    contacts_replied INTEGER DEFAULT 0,
    contacts_bounced INTEGER DEFAULT 0,
    latest_campaign TEXT,
    latest_activity_date TIMESTAMP,
    engagement_tier TEXT,   -- hot (replied), warm (opened), cold (sent, no open), untouched
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_name)
);


-- ═══════════════════════════════════════════
-- OPERATIONS
-- ═══════════════════════════════════════════

-- API call log (every external API call)
CREATE TABLE api_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint        TEXT,
    method          TEXT,
    params          TEXT,       -- JSON
    response_code   INTEGER,
    response_summary TEXT
);

-- Sync state tracking
CREATE TABLE sync_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity          TEXT NOT NULL UNIQUE,   -- contacts, sequences, threads, mailboxes, metrics
    last_synced_at  TIMESTAMP,
    last_offset     INTEGER DEFAULT 0,     -- For paginated full-sync
    total_records   INTEGER,
    notes           TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UI tasks — things that MUST be done in the Salesforge UI
CREATE TABLE ui_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task            TEXT NOT NULL,
    category        TEXT,       -- mailbox, webhook, reply, dnc
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
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_account ON contacts(account_name);
CREATE INDEX idx_contacts_icp ON contacts(icp_category, icp_function_type);
CREATE INDEX idx_contacts_suppressed ON contacts(suppressed);
CREATE INDEX idx_contacts_salesforge ON contacts(salesforge_lead_id);
CREATE INDEX idx_campaigns_sf ON campaigns(salesforge_seq_id);
CREATE INDEX idx_campaign_contacts_cid ON campaign_contacts(campaign_id);
CREATE INDEX idx_campaign_contacts_contact ON campaign_contacts(contact_id);
CREATE INDEX idx_engagement_campaign ON engagement_events(campaign_id);
CREATE INDEX idx_engagement_contact ON engagement_events(contact_id);
CREATE INDEX idx_engagement_type ON engagement_events(event_type);
CREATE INDEX idx_metrics_campaign ON metric_snapshots(campaign_id, snapshot_date);
CREATE INDEX idx_dnc_email ON dnc_list(email);
CREATE INDEX idx_reply_threads_status ON reply_threads(status);
CREATE INDEX idx_account_engagement ON account_engagement(engagement_tier);
```

---

## Part 5 — Sync Strategy

### What to pull from Salesforge and when

| Data | Method | Frequency | SQLite Target |
|------|--------|-----------|---------------|
| Sequence list + stats | GET /sequences | Every 15 min or on-demand | campaigns (update counts + status) |
| Sequence detail | GET /sequences/{id} | On-demand | campaigns + campaign_steps (verify sync) |
| Daily analytics | GET /analytics?from_date&to_date | Daily (cron or manual) | metric_snapshots |
| Aggregate metrics | GET /sequence-metrics | Daily | metric_snapshots (workspace level) |
| Reply threads | GET /threads | Every 15 min | reply_threads (insert new, preserve status) |
| Mailbox health | GET /mailboxes | Daily or on-demand | mailboxes + mailbox_health_log |
| Contact list | GET /contacts (paginate all) | Weekly full sync | contacts (update salesforge_lead_id) |

### What to push to Salesforge and when

| Data | Method | When |
|------|--------|------|
| New sequence | POST /sequences | Campaign launch |
| Email content | PUT /steps | Campaign launch or content update |
| Mailbox assignment | PUT /mailboxes | Campaign launch |
| Contact enrollment | PUT /import-lead | Campaign launch or batch add |
| Activate/pause | PUT /status | On command |
| DNC additions | POST /dnc/bulk | On opt-out, bounce, or manual suppression |
| Delete sequence | DELETE /sequences/{id} | Cleanup |

### Webhook event handling

If webhooks are configured, incoming events should be written to `engagement_events` and used to update `campaign_contacts` rollup fields. Since webhooks can't be deleted via API, only create ones you're sure about.

| Webhook Type | Action |
|-------------|--------|
| email_sent | Insert engagement_event, increment campaign_contacts.emails_sent |
| email_opened | Insert engagement_event, increment campaign_contacts.emails_opened |
| link_clicked | Insert engagement_event, increment campaign_contacts.emails_clicked |
| email_replied | Insert engagement_event, set campaign_contacts.replied=1 |
| email_bounced | Insert engagement_event, set campaign_contacts.bounced=1, consider DNC |
| contact_unsubscribed | Insert engagement_event, add to dnc_list, suppress contact |
| positive_reply | Update reply_threads.sentiment='positive' |
| negative_reply | Update reply_threads.sentiment='negative' |

---

## Part 6 — What We Build vs. What the API Gives Us

### The API gives us a sending engine

```
Create sequence → Load emails → Assign mailboxes → Enroll contacts → Activate → Pull metrics
```

That's it. The entire API is optimized for one workflow: push emails out and read what happened.

### We build everything else

```
Campaign planning    → campaign_ideas, email_templates, email_drafts
Contact management   → contacts (66-field model vs Salesforge's 8)
Contact search       → SQLite FTS or indexed queries (API search is broken)
Contact updates      → Local updates (API has no update endpoint)
ICP matching         → Local fuzzy match against 66 titles
Suppression/DNC      → Local DNC mirror + suppression logic (API is write-only)
Reply workflow       → reply_threads with status tracking (API is list-only)
Segment analytics    → Tag campaigns locally, aggregate by EHR/persona/geo
Account engagement   → Roll up contact events to account level
Historical trends    → Daily metric snapshots in SQLite
Kill-switch logic    → Poll analytics → check thresholds → PUT /status to pause
Pipeline attribution → meetings table (Salesforge has no pipeline concept)
Mailbox monitoring   → Daily health snapshots (API is read-only, can't fix)
```

### The hard truth

Salesforge is 20% of the system. SQLite + our code is 80%. The API is narrow but functional for what it does. The real value is in the orchestration layer we build around it.
