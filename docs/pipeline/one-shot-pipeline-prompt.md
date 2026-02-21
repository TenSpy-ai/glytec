# Glytec AI SDR — V1 Pipeline Build Prompt

You are building a **working local pipeline** for Glytec's AI-powered Sales Development Representative system. The pipeline takes hospital facility data from CSVs, scores and enriches accounts, washes contacts, composes personalized outbound emails, and pushes them to Salesforge for sequenced delivery.

Everything goes in a `pipeline/` folder. SQLite is the local data store (replacing Clay/Salesforce for the demo). The Salesforge API is real — you have a live API key and verified endpoint patterns.

---

## What Glytec Sells

Glytec sells **Glucommander**, an FDA-cleared insulin management system for hospitals. Their pitch varies by persona:
- **CNO/Nursing:** 99.8% hypoglycemia reduction, nurse workflow improvement, patient safety
- **CFO/Finance:** $20K savings per patient stay, 3.18-day LOS reduction, margin recovery
- **CQO/Quality:** CMS eCQM compliance, Hospital Compare rating improvement, readmission reduction
- **CEO/Strategy:** Board-level glycemic governance, competitive differentiation, regulatory readiness
- **CMO/Clinical:** Clinical outcomes, evidence-based dosing, reduced adverse events

Their competitive angle depends on the hospital's EHR vendor:
- **Epic hospitals:** "Your unvalidated in-house insulin calculator is a liability"
- **Cerner/Oracle hospitals:** "Your Oracle Health migration is disrupting insulin protocols"
- **MEDITECH hospitals:** "Leapfrog to a modern solution — no technical debt"

---

## Environment & Credentials

```python
# .env file
SALESFORGE_API_KEY=<key>
```

- Python 3.11, virtualenv at `.venv/`
- Salesforge base URL: `https://api.salesforge.ai/public/v2`
- Glytec workspace ID: `wks_05g6m7nsyweyerpgf0wuq`
- Glucommander product ID: `prod_jfxqn21476u6o3m5ocogi`

---

## Data Files (in `data/`)

### 1. `AI SDR_Parent Account List_1.23.26.csv` — 1,683 parent health systems

Key columns:
```
Rank, System Name, Definitive ID (validate!!), SFDC Account ID, City, State,
Segment, Facilities, Beds, Avg. Beds/Facility,
Glytec Client - 8.31.25, Glytec ARR - 8.31.25,
GC $ Opp, CC $ Opp, Total $ Opp, Adj Total $ Opp
```
- `Segment`: "Enterprise / Strategic", "Enterprise / Not Strategic", "Commercial", "Partner Growth"
- `Glytec Client - 8.31.25`: "Y" or blank — used for suppression
- `Beds`: total bed count across all facilities
- Currency columns need parsing (`$19,851,766` → float)

### 2. `AI SDR_Facility List_1.23.26.csv` — 9,774 facilities (filter out Closed=TRUE → ~8,458 active)

Key columns:
```
Highest Level Parent, Hospital Name, Definitive ID, Closed,
Electronic Health/Medical Record - Inpatient, Hospital Compare Overall Rating,
# of Staffed Beds, Net Operating Profit Margin, Net Patient Revenue,
All Cause Hospital-Wide Readmission Rate, Intensive Care Unit Beds,
Average Length of Stay, Hospital ownership, Firm Type, Hospital Type,
State, City, Zip Code
```
- `Highest Level Parent` joins to `System Name` in the parent account list
- `Definitive ID` is the universal join key across all CSVs and the DH API

### 3. `AI SDR_Facility List_Supplemental Data_1.23.26.csv` — 5,475 assigned facilities

Same facility columns plus `Assigned Rep`. Join to facility list on `Definitive ID`.

### 4. `AI SDR_ICP Titles_2.12.26.csv` — 66 ICP titles (also available as `outbound/ICP.json`)

```
Department, Title, Category, Intent Score, Function Type, Job Level
```
- Category: "Decision Maker" or "Influencer"
- Intent Score: 50–95 (CEO=95, CNO=95, CFO=90, inpatient RN=50)
- Function Type: "Clinical" or "Business"
- Job Level: "Executive", "Director", "Mid-Level", "Individual Contributor"

---

## Pipeline Architecture

```
pipeline/
├── config.py                  # Constants, API keys, scoring weights, paths
├── db.py                      # SQLite schema (6 tables)
├── step1_load_data.py         # CSV → SQLite
├── step2_score_accounts.py    # 6-factor scoring → tier assignment
├── step3_enrich_contacts.py   # Pre-filled contacts + simulated Firecrawl
├── step4_wash_contacts.py     # 6-step contact washing machine
├── step5_compose_messages.py  # 3-layer personalized message composition
├── step6_push_to_salesforge.py # Create sequences + enroll contacts (dry-run default)
├── step7_pull_metrics.py      # Pull live Salesforge analytics + threads
├── run_pipeline.py            # Orchestrator (--live, --steps, --top-n)
└── api_call_log.md            # Auto-generated API call audit trail
```

---

## SQLite Schema (6 tables)

### `accounts`
```sql
system_name TEXT UNIQUE, definitive_id TEXT, sfdc_account_id TEXT,
segment TEXT, total_beds INTEGER, glytec_client TEXT, glytec_arr TEXT,
gc_opp REAL, cc_opp REAL, total_opp REAL, adj_total_opp REAL,
rank INTEGER, score REAL, tier TEXT
```

### `facilities`
```sql
hospital_name TEXT, definitive_id TEXT UNIQUE, highest_level_parent TEXT,
ehr_inpatient TEXT, staffed_beds INTEGER, net_operating_profit_margin REAL,
cms_overall_rating REAL, readmission_rate REAL, icu_beds INTEGER,
net_patient_revenue REAL, assigned_rep TEXT
```

### `contacts`
```sql
first_name TEXT, last_name TEXT, email TEXT, title TEXT, company TEXT,
icp_category TEXT, icp_intent_score INTEGER, icp_function_type TEXT,
icp_job_level TEXT, facility_definitive_id TEXT, account_name TEXT,
linkedin_url TEXT, source TEXT, validated INTEGER DEFAULT 1,
suppressed INTEGER DEFAULT 0, suppression_reason TEXT,
icp_matched INTEGER DEFAULT 0, golden_record INTEGER DEFAULT 1
```

### `sequences`
```sql
name TEXT, salesforge_id TEXT, status TEXT, account_segment TEXT, contact_count INTEGER
```

### `messages`
```sql
contact_id INTEGER REFERENCES contacts(id), subject TEXT, body TEXT,
layer1_persona TEXT, layer2_ehr TEXT, layer3_financial TEXT, signal_hook TEXT
```

### `api_log`
```sql
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, endpoint TEXT, method TEXT,
params TEXT, response_code INTEGER, response_summary TEXT
```

---

## Step 1: Load Data

- Read all 3 CSVs with pandas
- Parse messy values: currency strings (`$19,851,766` → float), integer strings with commas (`38,726` → int), percentage strings
- Join facility list + supplemental data on `Definitive ID` (left join — supplemental adds `Assigned Rep`)
- Filter out closed facilities (`Closed` column)
- Insert into `accounts` (from parent list) and `facilities` (from joined facility data)
- Use `INSERT OR IGNORE` for idempotent re-runs

---

## Step 2: Score Accounts — 6-Factor Weighted Model

| Factor | Weight | Scoring Logic |
|--------|--------|---------------|
| Bed count | 20% | ≥600=100, 400-599=80, 200-399=60, 100-199=40, <100=20 |
| Operating margin | 15% | Median across child facilities. Negative=100, 0-5%=70, 5-10%=40, >10%=20 |
| EHR vendor | 20% | Primary EHR of child facilities. MEDITECH=100, Cerner/Oracle=90, Other=80, Epic=40 |
| CMS quality | 15% | Avg star rating across facilities. ≤1=100, ≤2=80, ≤3=60, ≤4=40, 5=20. Bonus +10 if avg readmission >15.5% |
| Trigger signal | 20% | Pre-filled signals for ~15 top accounts (EHR migration, new CNO, RFP, etc.). Signal=100, none=20 |
| Contact coverage | 10% | Contacts in DB: ≥15=100, 10-14=70, 5-9=40, <5=20. If no contacts, use facility count as proxy: ≥50=100, ≥20=70, ≥5=40 |

**Tier thresholds:** Priority 80-100, Active 60-79, Nurture 40-59, Monitor <40

Pre-fill ~15 realistic trigger signals for the largest health systems. Examples:
- "Oracle Cerner → Oracle Health migration in progress across 191 facilities"
- "New Chief Nursing Officer appointed Q4 2025; systemwide quality initiative announced"
- "Launched enterprise glycemic management RFP Dec 2025"
- "Epic rollout complete but insulin calculator validation flagged by Joint Commission"
- "Operating margin dropped to -2.3%; board approved cost-reduction initiative"
- "CMS readmission penalty applied to 12 facilities Q1 2026"

**Important:** Use exact `System Name` values from the parent account CSV as dict keys — these contain parenthetical aliases like "Trinity Health (FKA CHE Trinity Health)".

---

## Step 3: Enrich Contacts

Pre-fill ~20 realistic C-suite contacts for 5-7 top accounts:
- Roles: CEO, CFO, CNO, COO, CMO, CQO
- Fields: first_name, last_name, title, company, account_name (must match CSV system_name exactly), email, linkedin_url, source="web_scraping"
- Some contacts should have empty `linkedin_url` to test both enrollment paths in step 6

Simulate Firecrawl enrichment:
- For each top Priority account, log what `firecrawl_map` and `firecrawl_scrape` calls would be made
- Pre-fill enrichment signals per account: ehr_migration, leadership_change, glycemic_initiative, financial_note

---

## Step 4: Contact Washing Machine (6 Steps)

### 4.1 Dedup & Merge
Match keys in priority order: email → LinkedIn URL → name+account_name → name+email_domain. Delete duplicates, keep golden record.

### 4.2 Email Validation
- Regex format check
- Flag known bad domains (example.com, test.com, etc.)
- Flag catch-all personal domains (gmail.com, yahoo.com)
- In production: NeverBounce/ZeroBounce waterfall

### 4.3 Suppression Check
- Load `Glytec Client - 8.31.25 = "Y"` accounts from parent CSV
- Suppress any contact at a Glytec client account: `suppressed=1, suppression_reason='glytec_client'`
- In production: also check Salesforge DNC list and completed sequences

### 4.4 LinkedIn Cross-Reference
- Contacts without LinkedIn URL → `validated=0` (unverified flag)
- In production: check if LinkedIn title matches, flag stale contacts

### 4.5 ICP Title Match
Fuzzy-match contact titles against 66 ICP titles:
1. Exact match (case-insensitive)
2. `difflib.get_close_matches` (cutoff ~0.6)
3. Keyword overlap (≥50% of words in ICP title appear in contact title)

On match: set `icp_matched=1`, copy `icp_category`, `icp_intent_score`, `icp_function_type`, `icp_job_level` from the matched ICP entry.

### 4.6 Account Mapping
Verify each contact's `account_name` exists in the `accounts` table.

---

## Step 5: Compose Messages — 3-Layer Model

Target: clean contacts (`golden_record=1, suppressed=0, icp_matched=1`) at Priority or Active accounts.

### Layer 1 — Persona Frame (from contact title)
Map ICP category to messaging frame:
- CNO/nursing titles → `safety_workflow`: patient safety + nurse workflow framing
- CFO/finance titles → `roi_los`: ROI + length-of-stay reduction framing
- CQO/quality titles → `cms_compliance`: CMS eCQM + compliance framing
- CEO titles → `strategic_board`: board-level governance + strategic risk framing
- COO titles → `operational_efficiency`: throughput + operational excellence framing
- CMO titles → `clinical_outcomes`: clinical evidence + outcomes framing
- Director/other → `department_impact`: department-specific impact framing

Each frame has a subject template and body template with `{company}` and `{beds}` substitutions.

### Layer 2 — EHR Angle (from facility's primary EHR)
- EPIC: "unvalidated in-house insulin calculator = liability exposure"
- CERNER/ORACLE: "Oracle Health migration disrupting insulin protocols"
- MEDITECH: "leapfrog to modern solution, no technical debt"
- Default: "platform-agnostic clinical risk"

### Layer 3 — Financial Urgency (from facility operating margin)
- Negative margin: "$20K savings per patient stay, 3.18-day LOS reduction"
- 0-5%: "measurable ROI, margin recovery"
- 5-10%: "quality leadership + competitive differentiation"
- >10%: "CMS leadership positioning, early-adopter advantage"

### Signal Hook
If the account has a trigger signal from step 2, inject it as a personalized opening line.

Store each message with its layer attribution for analysis.

---

## Step 6: Push to Salesforge

**CRITICAL: These are the VERIFIED API patterns. Do not guess or use swagger docs — they are wrong in several places.**

### Auth
```python
headers = {"Authorization": SALESFORGE_API_KEY}  # Raw key, NO "Bearer" prefix
```

### All endpoints are workspace-scoped
```
https://api.salesforge.ai/public/v2/workspaces/{WORKSPACE_ID}/...
```

### Contact Data Model (CRITICAL — only 8 fields)
The Salesforge contact model has ONLY these fields:
```
id, firstName, lastName, email, company, linkedinUrl, tags, customVars
```
- `jobTitle` and `phone` are ACCEPTED by create endpoints (201/204) but do NOT persist
- `customVars` is the ONLY extensibility mechanism — use it for job_title, phone, icp_category, ehr_vendor, etc.
- `customVars` is an object of string key-value pairs: `{"job_title": "CNO", "ehr": "Epic"}`
- `tags` is an array of strings — contacts auto-tagged `pa-YYYYMMDD` on creation
- Duplicate email on POST /contacts → same lead ID returned, existing record updated (upsert behavior)

### Sequence Lifecycle (verified 5-step flow)

```
1. POST /workspaces/{id}/sequences
   Body: {"name": "...", "productId": "prod_jfxqn21476u6o3m5ocogi", "language": "american_english", "timezone": "America/New_York"}
   IMPORTANT: language must be "american_english" — "en" returns 400.
   Valid languages: american_english, british_english, dutch, italian, czech, hungarian, swedish, ukrainian,
     german, danish, romanian, french, russian, estonian, finnish, latvian, japanese, brazilian_portugese,
     norwegian, spanish, polish, lithuanian
   Returns: sequence object with id, plus one auto-generated empty step (with step id + variant id)
   Response includes: id, workspaceId, productId, name, status, steps[], mailboxes[], stats
   NOTE: language and timezone are NOT returned in the response — set at creation only

2. PUT /workspaces/{id}/sequences/{seq_id}/steps
   Body: {"steps": [{
     "id": step_id, "order": 0, "name": "Initial email", "waitDays": 0,
     "distributionStrategy": "equal",
     "variants": [{
       "id": variant_id, "order": 0, "label": "Initial email",
       "status": "active",
       "emailSubject": "...",
       "emailContent": "<p>HTML content</p>",
       "distributionWeight": 100
     }]
   }]}
   IMPORTANT: distributionStrategy, label, and status are REQUIRED on variants or you get 400.
   IMPORTANT: This REPLACES ALL steps — omitted steps will be deleted. Send the full array.
   Multi-step: works — include multiple objects with incrementing order values.
   A/B testing: works — multiple variants in one step with distributionStrategy: "custom" and split weights.

3. PUT /workspaces/{id}/sequences/{seq_id}/mailboxes
   Body: {"mailboxIds": ["mbox_...", "mbox_..."]}
   IMPORTANT: Must use PUT, not POST (POST returns 404).
   IMPORTANT: This is a full replacement — sending ["A","B"] then ["C"] results in only "C".
   IMPORTANT: Empty array [] clears ALL mailbox assignments.
   IMPORTANT: Invalid mailbox ID → 500 server crash (not a clean error).
   Fetch mailbox IDs first via GET /workspaces/{id}/mailboxes

4. Enroll contacts — use import-lead for all contacts:
   PUT /workspaces/{id}/sequences/{seq_id}/import-lead
   Body: {"firstName": "...", "lastName": "...", "email": "...", "company": "..."}
   Optional: linkedinUrl (omit field or null — both work. Empty string "" → 400)
   Optional: tags (array of strings)
   Optional: customVars (object of string key-value pairs — PERSISTS on the contact)
   IMPORTANT: jobTitle is accepted but does NOT persist — pass via customVars instead
   Creates the contact AND enrolls in the sequence in one call. One contact at a time.
   Returns: 204

   Alternative path (bulk create then assign):
   POST /workspaces/{id}/contacts → single object, returns 201 with lead_id
   POST /workspaces/{id}/contacts/bulk → {"contacts": [...]} where each has "tags": [...]
   PUT /workspaces/{id}/sequences/{seq_id}/contacts → {"contactIds": ["lead_..."]}
   WARNING: Same contact can be enrolled twice — leadCount increments again (no dedup protection)

5. PUT /workspaces/{id}/sequences/{seq_id}/status
   Body: {"status": "active"}
   Requires mailboxes assigned — 400 "sequence without mailboxes" if none.
   Status transitions: draft → active ↔ paused. Cannot go back to draft. Cannot set to completed.
```

### PUT /sequences/{id} — Update Sequence (limited)
```
Only these fields persist:   name, openTrackingEnabled, clickTrackingEnabled
Silently ignored:            language, timezone (returns 200 but doesn't change)
500 CRASH:                   productId (never send this)
Silently ignored:            steps, mailboxes (use dedicated sub-resource endpoints)
```

### Other verified endpoints
```
GET  /workspaces                                    # List all workspaces (not workspace-scoped)
GET  /workspaces/{id}/sequences                     # Paginated: limit, offset. Status filter DOESN'T WORK — filter client-side.
GET  /workspaces/{id}/sequences/{id}                # Full detail with steps, variants, stats. No language/timezone in response.
GET  /workspaces/{id}/sequences/{id}/contacts/count # Returns {"count": N} — may return 0 for import-lead contacts. Use sequence leadCount instead.
GET  /workspaces/{id}/sequences/{id}/analytics      # REQUIRES from_date + to_date (YYYY-MM-DD). Returns {days: {...}, stats: {...}}
GET  /workspaces/{id}/sequence-metrics              # Workspace aggregates. Optional: product_id, sequence_ids[] filters
GET  /workspaces/{id}/mailboxes                     # Paginated. Status filter DOESN'T WORK.
GET  /workspaces/{id}/contacts                      # Paginated, 50/page. Tags filter DOESN'T WORK. Returns only 8 fields.
GET  /workspaces/{id}/contacts/{id}                 # Same 8 fields as list. No additional fields in detail view.
POST /workspaces/{id}/dnc/bulk                      # Body: {"dncs": ["email@..."]} — array of STRINGS, not objects. Min 1 item.
GET  /workspaces/{id}/threads                       # Paginated. replyType: ooo, lead_replied. reply_type filter DOESN'T WORK.
GET  /workspaces/{id}/integrations/webhooks         # List webhooks (NOT /webhooks — that's 404)
POST /workspaces/{id}/integrations/webhooks         # {"name", "type", "url"} — type must be one of the 10 valid types below
GET  /workspaces/{id}/products                      # name is null — use internalName for the product name
```

### BROKEN FILTERS (accept param but return all data — must filter client-side)
- `status` on GET /sequences
- `product_id` on GET /sequences
- `tags` on GET /contacts
- `validation_status` on GET /contacts
- `status` on GET /mailboxes
- `reply_type` on GET /threads

### Webhook event types (10 valid types)
```
email_sent, email_opened, link_clicked, email_replied, linkedin_replied,
contact_unsubscribed, email_bounced, positive_reply, negative_reply, label_changed
```
**`dnc_added` is NOT a valid type** — the API rejects it despite appearing in some docs.

### Endpoints that DO NOT EXIST (will return 404)
```
POST /sequences/{id}/mailboxes          → use PUT
POST /sequences/{id}/contacts           → use PUT
GET  /sequences/{id}/steps              → steps only via GET sequence detail or PUT /steps
/sequences/{id}/steps/{id}/variants/{id} → no sub-resource endpoints
/sequences/{id}/metrics                 → use /sequence-metrics or /sequences/{id}/analytics
/contacts/validate                      → doesn't exist
/custom-variables                       → doesn't exist
/webhooks (without /integrations/)      → doesn't exist
```

### Fields that CANNOT be changed after creation
- `productId` on a sequence (500 crash if attempted)
- `language` on a sequence (silently ignored)
- `timezone` on a sequence (silently ignored)
- Sequence status back to `draft` (400)
- Sequence status to `completed` (400)

### Implementation

- `DRY_RUN = True` by default — log what would happen without calling the API
- `--live` flag enables real API calls
- Group contacts by tier+segment → one sequence per group
- Naming convention: `Glucommander_Q1_2026_{tier}_{segment}`
- Convert plain text bodies to HTML (`<p>` tags) before sending to Salesforge
- Log every API call to both SQLite `api_log` table and `api_call_log.md`
- Use `import-lead` for ALL contacts (linkedinUrl is optional — omit the field if not available)
- Pass job title, ICP category, function type via `customVars` (jobTitle doesn't persist on the model)
- Omit `linkedinUrl` field entirely when not available (empty string "" causes 400)

---

## Step 7: Pull Metrics

- `GET /sequences` — list all sequences with stats
- `GET /sequences/{id}/analytics?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` — 90-day window
- `GET /threads` — recent reply threads
- Print formatted report: open rates, reply rates, bounce rates per sequence
- Check kill-switch thresholds: bounce >5% or spam >0.3% → alert

---

## Run Pipeline (Orchestrator)

```
python run_pipeline.py              # dry-run, all steps
python run_pipeline.py --live       # real API calls
python run_pipeline.py --steps 1,2  # specific steps only
```

- Run steps 1-7 sequentially
- Catch exceptions per step (don't abort the whole run)
- Print timing per step
- Print final database stats: accounts scored, facilities, contacts (total + clean), messages, sequences, API calls

---

## Mailbox Inventory (for reference)

21 mailboxes in the Glytec workspace, all Clayton Maike:
- Domains: seeglytec.com, runglytec.com, joinglytec.com, findglytec.com, visitglytec.com, askglytec.com
- Patterns: clayton@, clayton.m@, clayton.maike@, cmaike@
- All set to 30 emails/day
- Several have disconnect errors but still show status: "active"
