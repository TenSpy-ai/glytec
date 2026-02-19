# V1 Tool Stack

How the tools fit together for the v1 pilot. Each layer has a job; tools serve that layer.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     SALESFORCE (CRM)                        │
│              System of record — all roads lead here         │
│                    ↕ push/pull ↕                            │
│               Clay ←──── Datagen                            │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐      ┌──────────────┐     ┌──────────────┐
   │ SIGNALS │      │   CONTACTS   │     │  SEQUENCING  │
   │         │      │              │     │              │
   │ DH API  │      │ Scraping     │     │ SalesForge   │
   │ Company │      │ ZoomInfo     │     │  ├─ Email    │
   │ research│      │ Clay         │     │  └─ LinkedIn │
   │ Clay    │      │ DH           │     │              │
   └─────────┘      └──────────────┘     └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                  ┌─────────────────────┐
                  │    INTELLIGENCE     │
                  │                     │
                  │ Segment ICP by      │
                  │ pain + signals →    │
                  │ develop messaging → │
                  │ find accounts with  │
                  │ that pain           │
                  └─────────────────────┘
```

---

## Layer 1: CRM Backbone

**Salesforce** — system of record (Clayton principle #1)

Everything syncs to and from Salesforce. Two connectors keep it current:

| Connector | Role |
|-----------|------|
| **Clay** | Enrichment workflows push cleaned, deduplicated contact and account data into Salesforce. Pulls account lists and ownership data out. |
| **Datagen** | Orchestrates tool execution programmatically. Reads from and writes to Salesforce via SDK when Clay isn't the right path (e.g., activity logging, opportunity updates, bulk operations). |

Salesforce holds: contacts, accounts, opportunities, campaign membership, activity history, pipeline attribution.

---

## Layer 2: Signals

**Goal:** Know _why now_ for each account. Surface trigger events that make outreach timely instead of random.

| Source | What It Provides |
|--------|-----------------|
| **Definitive Healthcare (HospitalView API)** | EHR migrations, leadership changes, quality improvement initiatives, capital projects, CMS star rating shifts, RFPs. The only source of real-time "why now" triggers. |
| **Company research** (Firecrawl, LinkedIn, Perplexity, web scraping) | Press releases, earnings calls, strategic plans, recent hires, org changes. Fills gaps DH doesn't cover (e.g., IT leadership hires, vendor announcements). |
| **Clay** | Orchestrates signal collection from multiple sources into a normalized feed. Runs enrichment waterfalls and dedup. Routes signals to the right accounts in Salesforce. |

**Signal → action flow:**
1. DH API + research surfaces a trigger (e.g., "Memorial Health announces Epic migration")
2. Clay normalizes the signal and matches it to the Salesforce account
3. Signal triggers the right messaging variant and sequence timing in SalesForge

---

## Layer 3: Title-Fit Contacts

**Goal:** Build a contact list of 15–20 people per account who match the ICP title list, with verified emails and phones.

| Source | What It Covers | Strength |
|--------|---------------|----------|
| **Web scraping** (Firecrawl + manual) | Hospital leadership pages, department directories, "About Us" pages | Often the only source for clinical titles (CDCES, nurse educators, clinical pharmacists). Doesn't scale but necessary for v1. |
| **ZoomInfo** | C-suite, VP, Director-level contacts. Verified emails + direct dials. | Best coverage for Tier 1 + upper Tier 2 ICP titles (70–85% hit rate). Weak on clinical roles. |
| **Clay** | Orchestrates multi-source waterfall: ZoomInfo → scraping → LinkedIn → manual. Dedup, normalize, validate emails, map contact-to-account. | Not a data source itself — the glue that makes the other sources work together. |
| **Definitive Healthcare** | Facility-level contacts, some clinical leadership. | Good for matching contacts to specific facilities by Definitive ID. Email quality is poor (use ZoomInfo for verified emails). |

**Contact build flow:**
1. Start with ICP title list (66 titles, scored by intent)
2. For each target account, run ZoomInfo for Tier 1 + Tier 2 Decision Maker titles
3. Scrape hospital leadership pages for clinical titles ZoomInfo misses
4. Clay deduplicates, validates emails, maps contacts to accounts (via LeanData logic)
5. DH confirms facility-level assignments (which contacts sit at which hospitals in the IDN)
6. Clean contacts push to Salesforce

---

## Layer 4: Sequencing & Sending

**SalesForge** — email infrastructure + multi-channel sending

| Channel | How |
|---------|-----|
| **Email** | SalesForge API (not UI — it's buggy). Dedicated warmed inboxes for Clayton + Reagan. Programmatic sequence creation, send scheduling, deliverability tracking. |
| **LinkedIn** | SalesForge LinkedIn integration (or standalone if SalesForge LinkedIn capabilities are insufficient). Connection requests, InMail, follow-up messages. |

**Pre-send checklist (v1):**
- Email validation via Clay (NeverBounce/ZeroBounce waterfall) before any contact enters a sequence
- Inbox warm-up complete (2-week lead time)
- Bounce rate monitoring — kill sequence if bounce >3%

---

## Layer 5: Intelligence Loop

This is where it all connects. The tool stack isn't a pipeline — it's a feedback loop.

```
Segment ICP by pain + signals
         │
         ▼
Develop messaging for each segment
         │
         ▼
Intel finds accounts showing that pain
         │
         ▼
Run sequences against those accounts
         │
         ▼
Measure response → refine segments + messaging
         │
         └──────────→ (back to top)
```

**How it works in practice:**

1. **Segment by pain:** Use the messaging framework pain points (safety liability, revenue leakage, regulatory risk, EHR frustration) crossed with DH signals (EHR vendor, financial health, CMS quality scores) to create target segments.

2. **Develop messaging:** Each segment gets tailored messaging per the Magnetic Messaging Framework — different hooks, proof points, and CTAs based on what pain the account is most likely feeling.

3. **Intel finds the accounts:** DH API + Clay enrichment surfaces accounts currently exhibiting that pain signal. Example: hospitals with below-average CMS star ratings + recent quality improvement press releases = "regulatory risk" segment, triggered for the compliance-focused messaging variant.

4. **Execute + learn:** SalesForge runs the sequences. Response data flows back to Salesforce. Open rates, reply rates, and meeting conversions by segment feed back into the model — which segments convert, which messages resonate, which signals predict receptivity.

---

## Operational Rules

The layers above describe _what_ tools do. This section describes the rules that govern _how_ they behave together — suppression, routing, compliance, prioritization, dedup, content generation, and handoff.

### Suppression & Do-Not-Contact

Before any contact enters a sequence, they must clear a suppression check. One email to an existing customer's C-suite from an AI SDR is a relationship risk.

**Suppression lists (maintained in Salesforce, enforced via Clay):**

| List | Source | Match Key |
|------|--------|-----------|
| Current customers | Salesforce account status = Active | Account Definitive ID or domain |
| Active opportunities | Salesforce open opps | Account ID |
| Competitors | Manual list maintained by Clayton | Domain |
| Off-limits contacts | Salesforce contact flag or tag | Email or contact ID |
| Prior opt-outs | SalesForge unsubscribe events synced to Salesforce | Email |

**Enforcement point:** Clay enrichment workflow checks every contact against all suppression lists _before_ pushing to SalesForge. No exceptions. A contact that matches any list is flagged in Salesforce (not deleted — audit trail matters) but never enters a sequence.

### Reply Handling & Routing

The doc covers outbound. This is the inbound path.

**Reply classification:**

| Reply Type | Example | Action | Owner | SLA |
|------------|---------|--------|-------|-----|
| Interested | "Tell me more," "Can we set up a call?" | Create Salesforce task for AE. Pause sequence. | Clayton / Reagan | Respond within 4 hours |
| Referral | "Talk to [name] instead" | Add referred contact to enrichment pipeline. Pause sequence for original contact. | Jeremy (enrichment) → Clayton (outreach) | Enrich within 24 hours |
| Not now | "Bad timing, reach out in Q3" | Tag in Salesforce with snooze date. Remove from active sequence. Re-enter drip in Q3. | Automated | — |
| Remove me | "Unsubscribe," "Stop emailing me" | Add to suppression list. Remove from all active sequences. | Automated | Immediate |
| Wrong person | "I don't handle this" | Remove from sequence. Flag title mismatch for enrichment QA. | Automated | — |
| Negative | "Not interested," "We already have a solution" | Log disposition in Salesforce. Remove from sequence. Do not re-enter for 12 months. | Automated | — |
| Bounce | Hard bounce returned | Add to suppression list. Flag email as invalid in Clay. | Automated | Immediate |

**Where replies land:** SalesForge captures reply events → syncs to Salesforce as activity → classification logic (AI or rule-based) routes to the right action. For v1, Clayton and Reagan manually classify; v2+ automates with AI triage.

### Personalization & Content Generation

The Magnetic Messaging Framework defines the message architecture. The tool stack needs to show _what writes the actual emails_.

**V1 content generation flow:**

1. **Segment determines the messaging variant.** Pain point (safety, revenue, regulatory, EHR) × persona tier (C-suite, VP/Director, clinical) = one of ~12 messaging templates from the framework.

2. **AI generates the personalized layer.** For each contact, Datagen `ai_writer` or Claude produces:
   - A personalized opening line referencing a signal (e.g., "Saw Memorial Health's recent Epic migration announcement...")
   - Account-specific proof points (bed count, patient volume, peer comparisons from DH data)
   - Title-specific pain framing (CFO gets revenue language, CNO gets patient safety language)

3. **Human reviews before send (v1).** Clayton or Reagan approves personalized drafts before they enter SalesForge sequences. At v1 scale (100 contacts, 10 accounts), this is manageable. At v2+ scale, review shifts to spot-checking.

**Content inputs per email:**

| Input | Source |
|-------|--------|
| Messaging template | Magnetic Messaging Framework (static) |
| Signal/trigger hook | DH API + company research via Clay (dynamic) |
| Account data (beds, EHR, financials) | DH + Salesforce (dynamic) |
| Contact title and department | ZoomInfo + Clay enrichment (dynamic) |
| Personalized opening line | AI-generated from above inputs |

### Account Scoring & Prioritization

Signals and contacts exist for hundreds of accounts. Scoring determines _which accounts get worked first_.

**V1 scoring model (computed in Clay, stored in Salesforce):**

| Factor | Weight | Source |
|--------|--------|--------|
| Bed count (≥300 = high) | 20% | DH API |
| Operating margin (below median = higher score — financial pressure) | 15% | DH API |
| EHR vendor (non-Epic = higher score — DIY insulin calc risk) | 20% | DH API |
| CMS quality signals (below-average stars, high readmission rates) | 15% | DH API |
| Active trigger signal in last 90 days | 20% | DH API (news/RFP) + company research |
| Contact coverage (≥10 title-fit contacts found) | 10% | Clay enrichment output |

**Score → action mapping:**

| Score | Tier | Action |
|-------|------|--------|
| 80–100 | Priority | Immediate sequence entry. Full personalization. Clayton reviews. |
| 60–79 | Active | Sequence entry within 1 week. Standard personalization. |
| 40–59 | Nurture | Lower-touch drip sequence. Revisit when new signal fires. |
| <40 | Monitor | No outreach. Re-score monthly. |

### CAN-SPAM & Opt-Out Compliance

Programmatic sending at scale requires compliance infrastructure, not just good intentions.

**Requirements:**

- Every outbound email includes a functioning unsubscribe mechanism (SalesForge handles this natively)
- Opt-out requests honored within 10 business days (CAN-SPAM requirement) — v1 targets same-day
- Suppression list syncs bidirectionally between SalesForge and Salesforce at least daily
- Physical mailing address included in email footer (Glytec HQ)
- "From" name and email accurately represent the sender (Clayton Maike / Reagan — no spoofing)
- Purchased/scraped contact lists validated before first send (email validation via Clay)

**Opt-out flow:**
1. Recipient clicks unsubscribe → SalesForge records opt-out
2. SalesForge syncs opt-out to Salesforce (contact field: `Email Opt-Out = true`)
3. Clay enrichment workflow checks `Email Opt-Out` before any future sequence entry
4. Contact never re-enters an outbound sequence unless they explicitly re-opt-in

### Sales Handoff

The AI SDR generates pipeline. A human closes it. The handoff must be clean.

**When a handoff triggers:**
- Positive reply classified as "Interested" or "Referral"
- Meeting booked (if self-scheduling is implemented)
- Inbound call or LinkedIn response to outreach

**What travels with the handoff (Salesforce task + record):**

| Field | Content |
|-------|---------|
| Account summary | Bed count, EHR, parent system, segment, score |
| Signal that triggered outreach | The specific "why now" (e.g., "Epic migration announced Jan 2026") |
| Contact context | Title, department, how they were sourced, LinkedIn profile |
| Conversation history | Full email thread from SalesForge, synced to Salesforce activity |
| Recommended next step | AI-suggested talk track based on pain segment and signal |
| Other contacts at account | List of other enriched contacts — who else to loop in |

**Handoff owner:** Clayton for Enterprise/Strategic accounts. Reagan for Partner Growth/Commercial. Assignment based on Salesforce account ownership.

### Dedup & Golden Record Strategy

Multiple sources will return the same person with slightly different data. Without explicit match logic, you either spam someone twice or lose a valid contact.

**Match keys (evaluated in order):**

| Priority | Match Key | Logic |
|----------|-----------|-------|
| 1 | Email address | Exact match. If two records share an email, they're the same person. |
| 2 | LinkedIn URL | Exact match. Normalized (strip tracking params, trailing slashes). |
| 3 | Name + Definitive ID | First name + last name (fuzzy, handles initials) at the same facility Definitive ID. |
| 4 | Name + domain | First name + last name (fuzzy) at the same email domain. Catches cases where Definitive ID isn't present. |

**Merge rules (Clay enforces):**

| Field | Winning Source |
|-------|---------------|
| Email | ZoomInfo (highest verification rate) > Clay validation > DH > scraping |
| Phone | ZoomInfo > DH |
| Title | Most specific (e.g., "VP, Clinical Informatics" wins over "VP") |
| Facility assignment | DH Definitive ID (authoritative for facility-level mapping) |
| LinkedIn URL | Whichever source provides it first |

**Golden record destination:** Salesforce. One contact record per person. Clay handles merge before push — duplicates never reach Salesforce.

---

## V1 Tool Summary

| Tool | Layer | Status |
|------|-------|--------|
| Salesforce | CRM backbone | NOT CONNECTED — Tier 1 priority |
| Clay | Orchestrator (all layers) | NOT CONNECTED — Tier 1 priority |
| Datagen | SDK/MCP execution layer | CONNECTED |
| Definitive Healthcare API | Signals + contacts | NOT CONNECTED — integration specialist assigned |
| ZoomInfo | Contacts | NOT CONNECTED — Tier 2 priority |
| SalesForge | Sequencing | NOT CONNECTED — Tier 1 priority |
| Firecrawl | Scraping / research | CONNECTED |
| LinkedIn | Research / signals | CONNECTED |
| LeanData | Contact-to-account mapping | NOT CONNECTED — Tier 2 priority |
| Email validation (via Clay) | Pre-send hygiene | NOT CONNECTED — required before launch |

---

## Integration Specs

### Salesforce Field Mapping

Every tool in the stack reads from or writes to Salesforce. This is the schema.

**Account Object:**

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `Name` | Text | DH / Manual | Parent system name |
| `Definitive_ID__c` | Text (ext ID) | DH | Primary cross-system join key. Links to DH API and facility CSVs. |
| `SFDC_Account_ID` | Text | Salesforce native | Already exists in parent account list (`SFDC Account ID` column) |
| `Segment__c` | Picklist | Scoring model | Enterprise/Strategic, Commercial, Partner Growth, Government |
| `Account_Score__c` | Number | Clay → SF | Composite score from scoring model (0–100) |
| `Score_Tier__c` | Picklist | Derived from score | Priority, Active, Nurture, Monitor |
| `EHR_Vendor__c` | Text | DH API | Epic, Oracle Cerner, MEDITECH, Vista, Other |
| `Bed_Count__c` | Number | DH API | Total staffed beds across all facilities in system |
| `Facility_Count__c` | Number | DH API | Number of hospitals under this parent |
| `Operating_Margin__c` | Percent | DH API | Net operating profit margin |
| `CMS_Star_Rating__c` | Number | DH API | Hospital Compare overall rating (1–5) |
| `Readmission_Rate__c` | Percent | DH API | All-cause hospital-wide readmission rate |
| `Glytec_Client_Status__c` | Picklist | Manual / existing | Current Client, Former Client, Prospect, Off-Limits |
| `Assigned_Rep__c` | Lookup (User) | Manual / existing | Clayton, Reagan, Khirstyn, Ian, Victoria, or Unassigned |
| `Latest_Signal__c` | Text (long) | Clay | Most recent trigger signal (e.g., "Epic migration announced Jan 2026") |
| `Signal_Date__c` | Date | Clay | When the latest signal was detected |
| `Last_Scored_Date__c` | Date | Clay | When the account was last re-scored |
| `Do_Not_Contact__c` | Checkbox | Manual | Account-level suppression flag |
| `Owner` | Lookup (User) | Salesforce native | Handoff routing — Clayton (Enterprise/Strategic) or Reagan (Partner Growth/Commercial) |

**Contact Object:**

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `FirstName` / `LastName` | Text | ZoomInfo / Clay / scraping | Standard fields |
| `Email` | Email | ZoomInfo (preferred) > Clay > DH > scraping | Golden record per merge rules |
| `Phone` | Phone | ZoomInfo > DH | Direct dial preferred |
| `Title` | Text | Most specific source wins | Per dedup merge rules |
| `Department__c` | Text | ICP title list mapping | Maps to one of the ICP departments |
| `ICP_Tier__c` | Picklist | ICP title list | Tier 1 (90–95), Tier 2 (75–89), Tier 3 (50–74) |
| `Intent_Score__c` | Number | ICP title list | 50–95 based on title match |
| `ICP_Category__c` | Picklist | ICP title list | Decision Maker or Influencer |
| `Function_Type__c` | Picklist | ICP title list | Clinical or Business |
| `Job_Level__c` | Picklist | ICP title list | Executive, Director, Mid-Level, Individual Contributor |
| `AccountId` | Lookup (Account) | Clay / LeanData | Contact-to-account mapping |
| `Facility_Definitive_ID__c` | Text | DH | Which specific facility this contact sits at (vs. parent system) |
| `LinkedIn_URL__c` | URL | LinkedIn / Clay | Profile link |
| `Enrichment_Source__c` | Picklist | Clay | ZoomInfo, DH, Scraping, LinkedIn, Manual |
| `Email_Validated__c` | Checkbox | Clay (NeverBounce/ZeroBounce) | True = passed validation |
| `Email_Opt_Out` | Checkbox | SalesForge sync | Standard SF field. Suppresses from all sequences. |
| `Do_Not_Contact__c` | Checkbox | Manual / suppression rules | Contact-level suppression |
| `Snooze_Until__c` | Date | Reply handling | "Not now" replies — re-enter drip after this date |

**Opportunity Object (created at handoff):**

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `Name` | Text | Auto-generated | `{Account Name} - AI SDR {Date}` |
| `AccountId` | Lookup | From contact's account | |
| `StageName` | Picklist | Default | "Meeting Booked" or "Qualified Lead" |
| `AI_SDR_Sourced__c` | Checkbox | Automated | True = originated from AI SDR outreach |
| `Signal_That_Triggered__c` | Text | From account record | The "why now" that initiated outreach |
| `Source_Campaign__c` | Lookup (Campaign) | SalesForge sync | Which sequence/campaign generated this opp |

**Campaign / Activity:**

| Object | Purpose |
|--------|---------|
| `Campaign` | One per SalesForge sequence. Tracks members, status, response rates. |
| `CampaignMember` | Links contacts to campaigns. Status: Sent, Opened, Replied, Meeting Booked, Opted Out. |
| `Task` | Logged per handoff. Contains account summary, signal, conversation history, recommended next step. |
| `EmailMessage` / `Activity` | SalesForge email threads synced as activities on the contact record. |

---

### Clay Workflow Specs

Clay is the orchestrator. These are the workflows that need to be built.

**Workflow 1: Account Enrichment & Scoring**

```
Trigger: New account added to target list (or monthly re-score cycle)
    │
    ├─ Step 1: Pull current data from DH API
    │    → Bed count, EHR vendor, operating margin, CMS stars, readmission rate
    │    → Match by Definitive ID
    │
    ├─ Step 2: Pull trigger signals from DH API
    │    → News articles, RFPs for this account in last 90 days
    │    → Also run Firecrawl/Perplexity for supplemental company research
    │
    ├─ Step 3: Compute account score
    │    → Apply 6-factor weighted model (see Account Scoring section)
    │    → Assign tier: Priority / Active / Nurture / Monitor
    │
    ├─ Step 4: Check suppression
    │    → Is this a current Glytec client? (Glytec_Client_Status__c)
    │    → Is this account flagged Do_Not_Contact__c?
    │    → If suppressed → flag, do not proceed to sequencing
    │
    └─ Step 5: Push to Salesforce
         → Update account fields: score, tier, EHR, latest signal, signal date, last scored date
         → If Priority or Active tier → trigger Workflow 2
```

**Workflow 2: Contact Enrichment Waterfall**

```
Trigger: Account scores Priority or Active AND contact coverage < 15
    │
    ├─ Step 1: ZoomInfo bulk enrichment
    │    → Search by account domain + ICP title keywords
    │    → Pull: name, email, phone, title, LinkedIn URL
    │    → Expected yield: 70–85% for Tier 1, 50–65% for Tier 2 DMs
    │
    ├─ Step 2: DH facility contacts
    │    → Pull executive contacts by Definitive ID
    │    → Cross-reference with ZoomInfo results (dedup by email)
    │
    ├─ Step 3: Web scraping (Firecrawl)
    │    → Scrape hospital leadership page for this account
    │    → Extract names + titles for clinical roles ZoomInfo missed
    │    → Especially: CDCES, nurse educators, pharmacy leads, hospitalists
    │
    ├─ Step 4: LinkedIn verification
    │    → For contacts without verified email, search LinkedIn by name + org
    │    → Pull LinkedIn URL for all contacts (used in multi-channel sequences)
    │
    ├─ Step 5: Dedup & merge
    │    → Apply match keys (email → LinkedIn URL → name+DefID → name+domain)
    │    → Apply merge rules (ZoomInfo email wins, most specific title wins, DH DefID for facility)
    │    → One golden record per person
    │
    ├─ Step 6: Email validation
    │    → Run all emails through NeverBounce or ZeroBounce
    │    → Mark Email_Validated__c = true/false
    │    → Invalid emails → do not enter sequence (LinkedIn-only outreach if URL exists)
    │
    ├─ Step 7: ICP title matching
    │    → Match contact title against 66 ICP titles (fuzzy match — handles "VP of" vs "Vice President,")
    │    → Assign: ICP_Tier__c, Intent_Score__c, ICP_Category__c, Function_Type__c, Job_Level__c
    │    → Non-matching titles → flag for manual review, do not auto-sequence
    │
    ├─ Step 8: Suppression check (contact-level)
    │    → Check Email_Opt_Out, Do_Not_Contact__c, existing active sequence membership
    │    → Check against competitor domain list
    │
    └─ Step 9: Push to Salesforce
         → Create or update Contact records
         → Link to Account via AccountId
         → Set Facility_Definitive_ID__c, Enrichment_Source__c
         → If account is Priority tier → notify Clayton/Reagan for sequence approval
```

**Workflow 3: Suppression Sync**

```
Trigger: Daily (and on-demand after SalesForge sync)
    │
    ├─ Step 1: Pull SalesForge unsubscribes from last 24 hours
    │    → Match by email to Salesforce contacts
    │    → Set Email_Opt_Out = true
    │
    ├─ Step 2: Pull hard bounces from SalesForge
    │    → Set Email_Validated__c = false
    │    → Add to suppression list
    │
    ├─ Step 3: Pull Salesforce account status changes
    │    → New clients (Glytec_Client_Status__c changed to "Current Client")
    │    → Remove all contacts at that account from active SalesForge sequences
    │
    └─ Step 4: Pull new Salesforce opportunities
         → If opp created on an account with active sequences → pause sequences
         → Avoid sending cold outreach to accounts with live deals
```

**Workflow 4: Signal-Triggered Re-scoring**

```
Trigger: DH API news/RFP feed returns new signal for a monitored account
    │
    ├─ Step 1: Log signal to account record (Latest_Signal__c, Signal_Date__c)
    │
    ├─ Step 2: Re-run scoring model
    │    → Signal recency boosts the "active trigger" factor
    │    → Account may jump tiers (e.g., Nurture → Active)
    │
    └─ Step 3: If tier upgraded → trigger Workflow 2 (contact enrichment)
         → And notify Clayton/Reagan: "HCA Healthcare just announced an EHR migration. Score moved from 55 to 82. 12 contacts enriched. Ready to sequence?"
```

---

### SalesForge API Integration

SalesForge is the sending layer. API over UI (the UI is buggy). These are the integration points.

**Authentication:**
- API key-based auth (SalesForge REST API)
- Base URL: `https://api.salesforge.ai/v1/` (confirm with SalesForge docs)
- Key stored in `.env` as `SALESFORGE_API_KEY`
- Rate limits: TBD — confirm with SalesForge before v1 launch

**Core API operations needed for v1:**

| Operation | Endpoint (logical) | When Used |
|-----------|-------------------|-----------|
| Create sequence | `POST /sequences` | When a new campaign launches for a segment |
| Add contacts to sequence | `POST /sequences/{id}/contacts` | After Clay pushes validated contacts |
| Pause/resume contact in sequence | `PATCH /sequences/{id}/contacts/{id}` | Reply handling ("Not now", "Interested") |
| Remove contact from sequence | `DELETE /sequences/{id}/contacts/{id}` | Opt-out, bounce, wrong person, negative reply |
| Get sequence stats | `GET /sequences/{id}/stats` | Daily reporting — opens, clicks, replies, bounces |
| Get reply events | `GET /sequences/{id}/replies` | Feed into reply classification (manual v1, AI v2) |
| Get bounce events | `GET /sequences/{id}/bounces` | Feed into suppression sync (Workflow 3) |
| Get unsubscribe events | `GET /sequences/{id}/unsubscribes` | Feed into suppression sync (Workflow 3) |
| List email accounts | `GET /email-accounts` | Verify Clayton + Reagan inboxes are connected and warm |
| Send test email | `POST /email-accounts/{id}/test` | Pre-launch validation |

**Sequence structure (v1):**

```
Sequence = 1 campaign segment (e.g., "Epic + Enterprise + Unprofitable + CNO")
    │
    ├─ Step 1: Email 1 (Day 0)
    │    → Personalized cold email (AI-generated, Clayton-approved)
    │
    ├─ Step 2: Email 2 (Day 3)
    │    → Follow-up with different angle (same pain, new proof point)
    │
    ├─ Step 3: LinkedIn connection request (Day 5)
    │    → If LinkedIn URL exists on contact record
    │
    ├─ Step 4: Email 3 (Day 7)
    │    → Final email — direct CTA, case study link
    │
    └─ Step 5: LinkedIn message (Day 10)
         → If connection accepted — brief, conversational follow-up
```

**Salesforce sync requirements:**
- Every email sent → logged as Activity on Contact record in Salesforce
- Every reply received → logged as Activity with reply body
- Sequence membership → mapped to CampaignMember status in Salesforce
- Unsubscribes → trigger Email_Opt_Out field update (via Clay Workflow 3)
- Bounces → trigger Email_Validated__c = false (via Clay Workflow 3)

**Error handling:**
- 401/403 → API key invalid or expired. Alert Jeremy immediately.
- 429 → Rate limit hit. Back off and retry with exponential delay.
- 400/422 → Bad request. Log full payload for debugging. Likely a field mismatch between Clay output and SalesForge expected schema.
- 5xx → SalesForge outage. Queue sends and retry when API recovers. Do not drop contacts from sequences.

---

### Email Deliverability Pre-Launch Checklist

Every item must be complete before the first programmatic send. One bad launch can damage sender reputation for months.

**Domain & DNS setup:**

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Dedicated sending subdomain (e.g., `outreach.glytec.com`) | TBD | Clayton's IT | Isolates AI SDR sends from corporate email reputation |
| SPF record includes SalesForge sending IPs | TBD | Clayton's IT | Required for deliverability |
| DKIM signing configured for sending subdomain | TBD | Clayton's IT | SalesForge provides the DKIM key; IT adds the DNS record |
| DMARC policy set (start with `p=none` for monitoring) | TBD | Clayton's IT | Monitor first, enforce later. Prevents spoofing. |
| Reverse DNS (PTR record) for sending IPs | TBD | SalesForge | Usually handled by SalesForge automatically |

**Inbox warm-up:**

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Clayton inbox created on sending subdomain | TBD | Clayton's IT | e.g., `clayton@outreach.glytec.com` |
| Reagan inbox created on sending subdomain | TBD | Clayton's IT | e.g., `reagan@outreach.glytec.com` |
| Warm-up started (SalesForge or Instantly) | TBD | Jeremy | 2-week minimum before first real send |
| Warm-up volume ramp: 5/day → 10 → 20 → 40 → target | TBD | Jeremy | Gradual ramp over 14 days |
| Warm-up engagement rate monitored (>30% open rate target) | TBD | Jeremy | If warm-up engagement is low, investigate before launching |

**Validation & hygiene:**

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| All v1 contact emails validated (NeverBounce/ZeroBounce via Clay) | TBD | Jeremy | Zero tolerance for invalid emails in first send |
| Catch-all domain detection | TBD | Jeremy (via Clay) | Catch-all domains accept all emails — can't distinguish valid from invalid. Flag but don't exclude. |
| Role-based email filtering (info@, admin@, hr@) | TBD | Jeremy (via Clay) | Remove role-based addresses — they rarely reach a person |
| Suppression lists loaded (customers, opt-outs, competitors) | TBD | Jeremy | Must be in place before any send |

**Content & compliance:**

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Unsubscribe link functional in all templates | TBD | Jeremy | Test manually before launch |
| Physical mailing address in footer | TBD | Jeremy | Glytec HQ address |
| "From" name matches real sender identity | TBD | Jeremy | Clayton Maike / Reagan — no aliases |
| Subject lines reviewed (no spam trigger words) | TBD | Clayton | Avoid: "free", "act now", "limited time", excessive caps/punctuation |
| Test emails sent to seed list (Gmail, Outlook, Yahoo) | TBD | Jeremy | Confirm inbox placement across providers before real send |
| Link tracking configured (but not excessive) | TBD | Jeremy | 1–2 tracked links max per email. Excessive tracking triggers spam filters. |

**Monitoring (ongoing after launch):**

| Metric | Threshold | Action If Breached |
|--------|-----------|-------------------|
| Bounce rate | >3% | Pause all sequences. Audit contact list. Re-validate emails. |
| Spam complaint rate | >0.1% | Pause all sequences. Review content. Check suppression lists. |
| Open rate | <15% | Investigate deliverability. Check if landing in spam. Adjust subject lines. |
| Unsubscribe rate | >1% per send | Review targeting. Are we hitting the wrong personas? |
| Blacklist check | Any listing | Immediate pause. Investigate root cause. Contact blacklist for delisting. |

**Kill switch:** If bounce rate exceeds 5% or spam complaints exceed 0.3% in any 24-hour period, all SalesForge sequences auto-pause. Jeremy investigates before resuming. This protects the sending domain from permanent reputation damage.

---

## What's Explicitly NOT in V1

- PhysicianView API (clinical contact discovery) — evaluate after pilot hit rate data
- Monocl / KOL intelligence — manual research for top 20 accounts
- Advanced reporting/BI — Salesforce native reports for v1
- Full sales team LinkedIn profiles — Clayton + Reagan only
- Apollo — connected but not part of v1 architecture (potential fallback for sequences if SalesForge fails)
