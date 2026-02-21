# Glytec AI SDR — Instantly GTM System Summary

*2026-02-20 · For full technical detail see `gtm-operations-design-instantly.md`*

---

## What We're Doing

Glytec sells Glucommander (insulin management software) to hospitals. The AI SDR system sends cold emails to hospital executives — CNOs, CFOs, CMOs — trying to book meetings. Everything in this system exists to support one goal: **send the right email to the right person at the right hospital at the right time, and handle whatever comes back.**

---

## The 5 User Flows

**1. "Who should we email?"**
Pick a segment (e.g. Epic hospitals, 500+ beds, Southeast). Know which accounts are high-value, which contacts match the ICP, who hasn't been contacted yet.

**2. "Write and launch a campaign"**
Draft email copy, pick mailboxes, load contacts, hit go. The system sends on a schedule, spacing across mailboxes.

**3. "What's happening?"**
Daily check: sends, opens, replies, bounces. If bounce rate spikes, auto-pause to protect domain reputation.

**4. "Someone replied"**
Read the reply, classify it (interested / not interested / out-of-office). If positive, respond. If opt-out, block them.

**5. "Is this working?"**
Weekly reports: which campaigns performed best, which segments respond most, did we book meetings.

---

## The 3 Tools

### 1. Instantly MCP (38 tools) — the sending engine you talk to

The email platform. Holds mailboxes, sends campaigns, tracks opens/replies/bounces. "MCP" means the AI agent operates it directly as tool calls — no code, no scripts.

| Flow | What MCP does |
|------|---------------|
| Launch a campaign | `create_campaign` → `add_leads_to_campaign_or_list_bulk` → `activate_campaign` |
| Pause if something's wrong | `pause_campaign` |
| Check performance | `get_campaign_analytics`, `get_daily_campaign_analytics` |
| Read replies | `list_emails`, `get_email` |
| Respond to a reply | `reply_to_email` |
| Mark handled | `mark_thread_as_read` |
| Check mailbox health | `list_accounts`, `get_account`, `manage_account_state` (test_vitals) |
| Manage warmup | `manage_account_state` (enable/disable_warmup), `get_warmup_analytics` |
| Search for a contact | `list_leads` with search/filter, `search_campaigns_by_contact` |
| Update a contact | `update_lead` |
| Verify an email | `verify_email` |
| Bulk load contacts | `add_leads_to_campaign_or_list_bulk` (up to 1,000/call) |
| Delete test data | `delete_campaign`, `delete_lead` |

**MCP = the robot arm that does things in the email platform.**

### 2. Instantly REST API (~80 more endpoints) — setup and advanced features

Same platform, but not available as MCP tools. Things you configure once or rarely touch. HTTP calls to `api.instantly.ai`.

| What | When you use it |
|------|-----------------|
| **Webhooks** (8 endpoints) | Once: set up event listeners so opens/replies/bounces push to us in real-time |
| **Subsequences** (9 endpoints) | Campaign setup: auto-follow-up if someone opens but doesn't reply |
| **Inbox placement tests** (9 endpoints) | Pre-launch: check if emails land in inbox vs spam across Gmail, Outlook, etc. |
| **Block list** (4 endpoints) | Ongoing: block an email/domain permanently |
| **Lead labels** (5 endpoints) | Setup: define categories like "Hot Lead" for AI classification |
| **Custom tags** (8 endpoints) | Setup: tag accounts/campaigns for filtering (e.g. "Epic", "Southeast") |
| **Audit log** (1 endpoint) | Investigation: who did what, when, API or UI |
| **Email templates** (5 endpoints) | Ongoing: save/reuse email copy in Instantly |
| **Sales flows** (5 endpoints) | Setup: smart views for filtering leads by engagement |
| **AI prompt templates** (5 endpoints) | Setup: custom prompts for personalization with model selection |

Full field-level schemas for all API-only endpoints: [`docs/instantly/instantly-api.md`](instantly/instantly-api.md) sections 4–28.

**REST API = the settings panel you configure before the robot arm starts working.**

### 3. SQLite Database — the brain

Instantly sends emails and tracks engagement. It knows nothing about business strategy. SQLite is where all the thinking happens.

| What SQLite knows | Why Instantly can't |
|-------------------|-------------------|
| 1,683 parent health systems and how they rank | No concept of "accounts" or hospital hierarchy |
| 8,458 facilities grouped under those systems | Doesn't group contacts by organization |
| Account scoring (beds, EHR, margin, CMS rating, readmission, opportunity $) | Has leads and campaigns, not scoring models |
| ICP matching (66 title patterns — is "VP of Patient Safety" a decision maker?) | Stores contacts but doesn't classify them |
| Suppression logic (existing client, opted out, bounced, stale) | Has a block list but not suppression rules |
| Campaign planning (ideas backlog, draft copy, untouched segments) | Tracks active campaigns, not your planning pipeline |
| Segment analytics (reply rate by EHR: Epic vs Cerner vs MEDITECH) | Reports per-campaign, not per-business-segment |
| Account-level engagement (has *anyone* at Memorial Health opened *anything*?) | Tracks per-lead, not rolled up to organization |
| Historical trends (30/60/90 day, week-over-week) | Current stats only, no time-series |
| Pipeline attribution (which campaign → which meeting) | Zero CRM/pipeline concept |
| Reply workflow (new → reviewed → needs follow-up → handled) | Shows the reply, doesn't track your process on it |

**SQLite = the strategist that decides *what* to do. Instantly *does* it.**

---

## How They Work Together

```
                    ┌─────────────────────────┐
                    │      SQLite (Brain)      │
                    │                          │
                    │  Accounts, scoring, ICP  │
                    │  Campaign planning       │
                    │  Segment analytics       │
                    │  Reply workflow           │
                    │  Historical trends        │
                    └────────┬───────┬─────────┘
                             │       │
                    decide   │       │  store results
                    what     │       │
                    to do    │       │
                             ▼       │
               ┌─────────────────────┴──────┐
               │     AI Agent (Operator)     │
               │                             │
               │  Reads SQLite → picks       │
               │  targets → calls tools      │
               │  → writes results back      │
               └──────┬──────────────┬───────┘
                      │              │
             MCP tools│              │REST API
            (38 tools)│              │(~80 endpoints)
                      ▼              ▼
             ┌──────────────┐  ┌──────────────────┐
             │  Instantly    │  │  Instantly API   │
             │  MCP Server   │  │  (setup/admin)   │
             │               │  │                  │
             │  Send emails  │  │  Webhooks        │
             │  Read replies │  │  Subsequences    │
             │  Manage accts │  │  Placement tests │
             │  Analytics    │  │  Block list      │
             │  Lead CRUD    │  │  Tags, labels    │
             └──────────────┘  └──────────────────┘
```

## A Typical Day

1. **Morning** — Agent pulls analytics via MCP, stores snapshots in SQLite, checks bounce rates. Any campaign >5% bounce → auto-pause via MCP
2. **Morning** — Agent checks mailbox health via MCP, flags disconnects. Reconnecting OAuth mailboxes is the one thing still requiring the Instantly UI
3. **Midday** — Agent pulls new replies via MCP, stores in SQLite with status "new". Reagan reviews, marks as handled
4. **Ongoing** — Webhooks (configured once via API) push real-time events into SQLite for live dashboards
5. **Campaign launch** — Agent queries SQLite for untouched Priority accounts → ICP-matched contacts → creates campaign via MCP → loads contacts → activates
6. **Weekly** — Pat pulls reports from SQLite: segment breakdowns, account engagement, pipeline attribution

---

## The Bottom Line

**Instantly handles 60%** of the system — email sending, contact management, mailbox operations, reply handling, analytics.

**SQLite + custom code handles 40%** — the strategic intelligence that makes this an AI SDR instead of a mass emailer: which hospitals to target, which people to contact, what to say, how to score engagement, and whether it's working.

The MCP layer is what makes the 60% feel like 90%. Instead of writing Python scripts to call REST endpoints, the AI agent just says `create_campaign` and it happens.
