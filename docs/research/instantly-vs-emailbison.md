# Instantly vs Email Bison — Deep API Comparison

*Compiled 2026-02-20*

---

## At a Glance

| Dimension | **Instantly** | **Email Bison** |
|-----------|--------------|-----------------|
| Base URL | `https://api.instantly.ai/api/v2` | `https://dedi.emailbison.com` |
| Auth | Bearer token | Bearer token |
| API Version | V2 (V1 deprecated 2025) | v1 + v1.1 (v1 workspaces deprecated) |
| OpenAPI spec | No public spec (docs at developer.instantly.ai) | Full OpenAPI 3.0.3 spec |
| Endpoint count | **~118** | **~140** (excluding deprecated v1 dupes) |
| IDs | UUIDs everywhere | Integer IDs everywhere |
| Pagination | Cursor-based (`starting_after`) | Page-based (`links`/`meta` with `current_page`, `per_page`, `total`) |
| Rate limiting | Workspace-wide, 429 on exceed (Growth+ plan) | Not documented in spec |
| Naming | snake_case | snake_case |
| Scoping | API key scopes (168+ granular `resource:action`) | Token per workspace, no granular scopes |

---

## 1. Campaign Management

### Lifecycle

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Statuses | Draft(0), Active(1), Paused(2), Completed(3), Running Subsequences(4), Account Suspended(-99), Accounts Unhealthy(-1), Bounce Protect(-2) | Draft, Launching, Active, Stopped, Completed, Paused, Failed, Queued, Archived, Pending Deletion, Deleted |
| Create | `POST /campaigns` | `POST /api/campaigns` |
| Update | `PATCH /campaigns/{id}` | `PATCH /api/campaigns/{id}/update` |
| Launch | `POST /campaigns/{id}/launch` | `PATCH /api/campaigns/{id}/resume` (from draft → queued → active) |
| Pause | `POST /campaigns/{id}/pause` | `PATCH /api/campaigns/{id}/pause` |
| Archive | — (no archive concept) | `PATCH /api/campaigns/{id}/archive` |
| Duplicate | — | `POST /api/campaigns/{id}/duplicate` |
| Delete | — (no delete endpoint) | `DELETE /api/campaigns/{id}` + bulk delete |
| Types | Single type (campaign) | `outbound` + `reply_followup` (auto follow-up in same thread) |

**Key differences:**
- **Email Bison has more lifecycle states** — Launching, Queued, Failed, Archived, Pending Deletion give finer operational visibility
- **Email Bison supports campaign deletion** — Instantly has no campaign delete endpoint
- **Email Bison has a `reply_followup` campaign type** — a dedicated campaign type for automated follow-up in existing email threads (Instantly uses subsequences for this)
- **Email Bison has campaign duplication** — Instantly does not
- **Instantly has `not_sending_status`** — explains *why* a campaign isn't sending (outside schedule, waiting for lead, daily limit hit, all accounts at limit, error)

### Campaign Configuration

| Setting | **Instantly** | **Email Bison** |
|---------|--------------|-----------------|
| Daily send limit | `daily_limit` | `max_emails_per_day` |
| Daily new leads limit | `daily_max_leads` | `max_new_leads_per_day` |
| Email gap | `email_gap` (minutes between emails) | — (not exposed) |
| Random wait | `random_wait_max` | — |
| Stop on reply | `stop_on_reply` | — (implied; leads get "sequence_stopped") |
| Stop on auto-reply | `stop_on_auto_reply` | `include_auto_replies_in_stats` (different angle) |
| Stop for company | `stop_for_company` (entire domain) | — |
| Link tracking | `link_tracking` | — (not per-campaign) |
| Open tracking | `open_tracking` | `open_tracking` |
| Text only | `text_only`, `first_email_text_only` | `plain_text` |
| Unsubscribe header | `insert_unsubscribe_header` | `can_unsubscribe` |
| Match lead ESP | `match_lead_esp` | — |
| Evergreen | `is_evergreen` | — |
| Prioritize new leads | `prioritize_new_leads` | `sequence_prioritization` (enum: followups/new_leads) |
| CC/BCC | `cc_list`, `bcc_list` | — (per-campaign; available on individual sends) |
| Company limit override | `limit_emails_per_company_override` | — |
| Reputation building | — | `reputation_building` (spam protection) |
| A/B optimization | `auto_variant_select` (AI-driven) | — |
| Provider routing | `provider_routing_rules` | — |
| Bounce protection | `disable_bounce_protect` | — |
| Allow risky contacts | `allow_risky_contacts` | — |
| PL value | `pl_value` ($ per positive lead) | — |

**Verdict: Instantly has significantly more campaign-level knobs** — company controls, ESP matching, bounce protection, AI variant selection, provider routing, evergreen mode. Email Bison is simpler.

### Sequence Steps / Email Copy

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Where steps live | `sequences[0].steps[]` inside campaign object | Separate endpoints: `/campaigns/{id}/sequence-steps` |
| Step fields | type, subject, body (HTML), delay (days), variants[] | email_subject, email_body, wait_in_days, order, variant, variant_from_step_id, thread_reply, attachments |
| A/B variants | `variants[]` array on each step | `variant: true` + `variant_from_step_id` linking to parent step |
| Variant activation | — (part of campaign update) | `PATCH .../activate-or-deactivate` per variant |
| Thread reply | — (implied by step order) | Explicit `thread_reply` boolean per step |
| Attachments | — (not on steps) | Supported per step |
| Test email | — | `POST .../test-email` per step |
| API versioning | Single V2 | v1 (deprecated) + v1.1 (uses ID-based variant linking) |

**Key difference: Email Bison supports attachments on sequence steps and per-step test emails.** Instantly does not expose these via API.

### Schedules

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Where | `campaign_schedule` object on campaign | Separate `/schedule` sub-resource |
| Format | Multiple named schedules, each with `timing.from/to`, `days` (0-6 booleans), timezone, start/end dates | Day booleans (monday-sunday) + start_time/end_time + timezone |
| Templates | — | Schedule templates (save, list, create-from-template) |
| Sending forecast | — | `GET /sending-schedules` + `GET /sending-schedule` (today/tomorrow/day_after_tomorrow) |
| Timezones | Freeform string | Must use value from `GET /available-timezones` |

**Email Bison wins on schedule management** — templates, sending forecasts, and validated timezone lists. Instantly supports multiple named schedules per campaign with date ranges.

---

## 2. Lead / Contact Management

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Create | `POST /leads` (single) | `POST /api/leads` (single) |
| Bulk create | `POST /leads/bulk` (to campaign or list) | `POST /api/leads/multiple` (max 500), `POST /api/leads/bulk/csv` |
| Get | `POST /leads/list` (POST with filters) | `GET /api/leads` (GET with query filters) |
| Update | `PATCH /leads/{id}` | `PUT /api/leads/{id}` (full replace) + `PATCH /api/leads/{id}` (partial) |
| Upsert | — | `POST /api/leads/create-or-update/{id}` + bulk upsert with `existing_lead_behavior` (put/patch/skip) |
| Delete | `DELETE /leads/{id}` + bulk delete | `DELETE /api/leads/{id}` + bulk delete |
| Move | `POST /leads/move` | `POST /campaigns/{id}/leads/move-to-another-campaign` |
| Unsubscribe | — (status change) | `PATCH /api/leads/{id}/unsubscribe` (dedicated endpoint) |
| Blacklist | — (block list entries) | `POST /api/leads/{id}/blacklist` (direct from lead) |
| Status update | Via PATCH | `PATCH /api/leads/{id}/update-status` + bulk status update |
| CSV import | Via bulk endpoint | `POST /api/leads/bulk/csv` with column mapping |
| Sent emails | — | `GET /api/leads/{id}/sent-emails` |
| Scheduled emails | — | `GET /api/leads/{id}/scheduled-emails` |

### Lead Schema

| Field | **Instantly** | **Email Bison** |
|-------|--------------|-----------------|
| ID type | UUID | Integer |
| Core fields | email, first_name, last_name, company_name, website, phone | email, first_name, last_name, title, company, notes |
| Custom data | `payload` (flat key:value, no nested objects) | `custom_variables[]` (array of `{name, value}`) |
| Personalization | `personalization` field | — (use custom_variables) |
| Engagement stats | email_open_count, reply_count, click_count + detailed step-level tracking | `overall_stats` {emails_sent, opens, replies, unique_replies, unique_opens} |
| Status model | Numeric (1=Active, 2=Paused, 3=Completed, -1=Bounced, -2=Unsub, -3=Skipped) | String enum (verified, unverified, risky, unknown, inactive, bounced, unsubscribed) |
| Campaign status | `status` + `status_summary` + `last_step_*` fields | `lead_campaign_data` nested object per campaign |
| Interest | `lt_interest_status` (numeric) | — (on replies, not leads) |
| company_domain | Auto-extracted (read-only) | — |

**Key differences:**
- **Email Bison has proper upsert** with configurable behavior (put/patch/skip) — Instantly lacks upsert
- **Email Bison separates lead verification status from campaign status** — cleaner model
- **Instantly tracks engagement at the step+variant level** — more granular
- **Instantly auto-extracts company_domain** from email
- **Email Bison has per-lead sent-emails and scheduled-emails views** — Instantly doesn't expose this per-lead

### Lead Filtering

| Filter | **Instantly** | **Email Bison** |
|--------|--------------|-----------------|
| Campaign status | Via campaign filter | `lead_campaign_status` (in_sequence, finished, stopped, never_contacted, replied) |
| Email stats | — | `emails_sent`, `opens`, `replies` with comparison operators (=, >=, >, <=, <) |
| Verification | — | `verification_statuses[]` (verifying, verified, risky, unknown, unverified, inactive, bounced, unsub) |
| Tags | — | `tag_ids[]`, `excluded_tag_ids[]`, `without_tags` |
| Date range | — | `created_at`, `updated_at` with criteria/value |

**Email Bison has significantly richer lead filtering** with comparison operators and multi-dimensional filters. Instantly's lead list endpoint is less documented for filters.

---

## 3. Email Accounts (Sender Emails)

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Create | `POST /accounts` | `POST /api/sender-emails/imap-smtp` |
| Bulk create | — | `POST /api/sender-emails/bulk` (CSV upload) |
| List | `GET /accounts` (filter by tags) | `GET /api/sender-emails` (filter by tags, status, search) |
| Get | `GET /accounts/{email}` | `GET /api/sender-emails/{id}` |
| Update | `PATCH /accounts/{email}` | `PATCH /api/sender-emails/{id}` |
| Delete | `DELETE /accounts/{email}` | `DELETE /api/sender-emails/{id}` |
| Pause | `POST /accounts/{email}/pause` | — (no pause, just campaign-level) |
| Bulk signatures | — | `PATCH /api/sender-emails/signatures/bulk` |
| Bulk daily limits | — | `PATCH /api/sender-emails/daily-limits/bulk` |
| OAuth token | — | `GET /api/sender-emails/{id}/oauth-access-token` |
| MX records | — | `POST /api/sender-emails/{id}/check-mx-records` + bulk check |
| Account campaigns | — (see campaign mapping) | `GET /api/sender-emails/{id}/campaigns` |
| Account replies | — | `GET /api/sender-emails/{id}/replies` |
| ID scheme | Email address as ID | Integer ID (also accepts email address) |

### Account Schema

| Field | **Instantly** | **Email Bison** |
|-------|--------------|-----------------|
| Provider | `provider_code` (1=Custom IMAP, 2=Google, 3=Microsoft, 4=AWS) | `type` ("Inbox") |
| Status | Numeric (1=Active, 2=Paused, -1=Connection Error, -2=Soft Bounce, -3=Sending Error) | String (Connected, Not Connected, Pending Move, Pending Deletion) |
| Warmup status | `warmup_status` (0=Paused, 1=Active, -1=Banned, -2=Spam Unknown, -3=Permanent Suspension) | `warmup_enabled` (boolean) |
| Warmup score | `stat_warmup_score` | Via warmup endpoints |
| Daily limit | `daily_limit` | `daily_limit` |
| Sending gap | `sending_gap` [0-1440] minutes | — |
| Slow ramp | `enable_slow_ramp` | — |
| Tracking domain | `tracking_domain_name` + `tracking_domain_status` | Via custom tracking domain endpoints |
| Signature | `signature` | `email_signature` (HTML) |
| Connection details | — (provider-managed) | `imap_server`, `imap_port`, `smtp_server`, `smtp_port` |
| Engagement stats | — | `emails_sent_count`, `total_replied_count`, `total_opened_count`, etc. |
| Error details | `status_message` (code, command, response, e_message, responseCode) | — |

**Key differences:**
- **Email Bison has bulk operations** for signatures and daily limits — great for managing many accounts
- **Email Bison exposes OAuth tokens** — lets you use the connected account for external integrations
- **Email Bison has MX record checking** — built-in deliverability validation
- **Instantly has richer provider/status model** — tracks provider type, error details, warmup pool, sending gap, slow ramp
- **Instantly uses email as ID** — Email Bison uses integer IDs

---

## 4. Warmup

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Enable | `POST /accounts/warmup/enable` (batch) | `PATCH /api/warmup/sender-emails/enable` |
| Disable | `POST /accounts/warmup/disable` (batch, returns background job) | `PATCH /api/warmup/sender-emails/disable` |
| Analytics | `POST /accounts/warmup-analytics` | `GET /api/warmup/sender-emails` (with date range) |
| Per-account | Via account `warmup_status`, `stat_warmup_score`, `warmup` config object | `GET /api/warmup/sender-emails/{id}` |
| Daily limits | Via account `warmup.limit` | `PATCH /api/warmup/sender-emails/update-daily-warmup-limits` |
| Reply rate | `warmup.reply_rate` config | `daily_reply_limit` (int or "auto") |
| Warmup score | `stat_warmup_score` on account | `warmup_score` on warmup endpoint |
| Warmup pool | `warmup_pool_id` | — |
| Ignore phrases | — | `GET/POST/DELETE /api/ignore-phrases` (filter warmup noise) |
| Bounce tracking | — | `warmup_bounces_received_count`, `warmup_bounces_caused_count`, `warmup_disabled_for_bouncing_count` |
| MX filter | — | `mx_records_status` filter on warmup list |

**Key differences:**
- **Email Bison has "ignore phrases"** — filter out warmup noise from inbox (Instantly doesn't have this)
- **Email Bison tracks warmup bounce metrics** separately (received, caused, auto-disabled count)
- **Instantly has warmup pools** and more granular warmup configuration (increment settings, custom ftag)
- Both have built-in warmup as a first-class feature

---

## 5. Reply / Email Management

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| List emails | `GET /emails` | `GET /api/replies` |
| Get single | `GET /emails/{id}` | `GET /api/replies/{id}` |
| Reply | `POST /emails/reply` | `POST /api/replies/{id}/reply` |
| Forward | `POST /emails/forward` | `POST /api/replies/{id}/forward` |
| Compose new | — | `POST /api/replies/new` (one-off email, new thread) |
| Mark read | `POST /emails/threads/{id}/mark-as-read` | `PATCH /api/replies/{id}/mark-as-read-or-unread` |
| Delete | `DELETE /emails/{id}` | `DELETE /api/replies/{id}` |
| Unread count | `GET /emails/unread/count` | — |
| Thread view | Via `thread_id` field | `GET /api/replies/{id}/conversation-thread` (full thread expansion) |
| Mark interested | — (via lead label) | `PATCH /api/replies/{id}/mark-as-interested` |
| Mark not interested | — (via lead label) | `PATCH /api/replies/{id}/mark-as-not-interested` |
| Mark automated | — (field on email) | `PATCH /api/replies/{id}/mark-as-automated-or-not-automated` |
| Unsubscribe | — | `PATCH /api/replies/{id}/unsubscribe` (from reply context) |
| Attach to scheduled | — | `POST /api/replies/{id}/attach-scheduled-email-to-reply` |
| Push to followup | — | `POST /api/replies/{id}/followup-campaign/push` |
| Reply templates | — | Full CRUD: `GET/POST/PUT/DELETE /api/reply-templates` with attachments |

### Email/Reply Schema

| Field | **Instantly** | **Email Bison** |
|-------|--------------|-----------------|
| Body | `body.text` + `body.html` | `html_body` + `text_body` + `raw_body` |
| AI interest | `ai_interest_value` (0.0-1.0) | — (auto-interested via master inbox GPT-4o-mini) |
| AI assisted | `ai_assisted` flag | — |
| Auto-reply detection | `is_auto_reply` (read-only) | `automated_reply` (read + write) |
| Focused | `is_focused` (primary tab) | — |
| Attachments | `attachment_json` (files array) | `attachments[]` (id, uuid, file_name, download_url) |
| Type classification | `ue_type` (1=Campaign sent, 2=Received, 3=Manual sent, 4=Scheduled) | `type` ("Untracked Reply", etc.) + `tracked_reply` boolean |
| Headers | — | `headers` (raw email headers) |
| Folder | — | `folder` (inbox/sent/spam/bounced/all) |

**Key differences:**
- **Email Bison has richer reply management** — compose new emails, reply templates with attachments, mark interested/not-interested, push to followup campaigns, attach untracked replies
- **Email Bison exposes raw email headers** — useful for deliverability debugging
- **Instantly has AI interest scoring** on every email (0.0-1.0 float) — Email Bison has workspace-level auto-categorization via GPT-4o-mini
- **Email Bison has folder-based organization** (inbox/sent/spam/bounced) — Instantly uses `is_focused` for primary tab
- **Instantly has unread count endpoint** — Email Bison doesn't

---

## 6. Analytics & Stats

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Campaign analytics | `GET /campaigns/analytics` | `POST /api/campaigns/{id}/stats` (date-ranged) |
| Campaign overview | `GET /campaigns/analytics/overview` | Stats inline on campaign object |
| Daily analytics | `GET /campaigns/analytics/daily` | `GET /api/campaigns/{id}/line-area-chart-stats` |
| Step analytics | `GET /campaigns/analytics/steps` | `sequence_step_stats[]` in stats response |
| Account analytics | `GET /accounts/analytics/daily` | Stats inline on sender email object |
| Account vitals | `POST /accounts/test/vitals` | `POST /api/sender-emails/{id}/check-mx-records` |
| Cross-campaign | — | `GET /api/campaign-events/stats` (filter by campaigns + sender emails) |
| Workspace stats | — | `GET /api/workspaces/v1.1/stats` + `line-area-chart-stats` |
| Warmup analytics | `POST /accounts/warmup-analytics` | Via warmup endpoints with date range |

**Key differences:**
- **Email Bison has workspace-level stats** — aggregate view across all campaigns
- **Email Bison has cross-campaign event drill-down** with sender email filtering
- **Instantly has dedicated step-level analytics** endpoint
- **Instantly has account vitals testing** (deliverability check) — Email Bison has MX record checking

---

## 7. Blocklist / DNC

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| Email blocklist | `POST/GET/DELETE /block-list-entries` | `POST/GET/DELETE /api/blacklisted-emails` + bulk CSV |
| Domain blocklist | Same endpoint (block list entries) | Separate: `POST/GET/DELETE /api/blacklisted-domains` + bulk CSV |
| Bulk import | — | CSV upload for both email and domain blacklists |
| From lead | — | `POST /api/leads/{id}/blacklist` |

**Email Bison has separate email and domain blacklists** with bulk CSV import and direct lead-to-blacklist. Instantly combines them in one endpoint.

---

## 8. Webhooks

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| CRUD | Full (GET/POST/PATCH/DELETE) | Full (GET/POST/PUT/DELETE) |
| Event types | 19+ (email_sent, opened, clicked, reply, bounce, unsub, campaign_completed, account_error, custom label events, etc.) | 17 (email_sent, lead_first_contacted, lead_replied, lead_interested, email_opened, email_bounced, lead_unsubscribed, account add/remove/disconnect/reconnect, manual_email_sent, untracked_reply, tag_attached/removed, warmup_disabled events) |
| Test webhook | `POST /webhooks/{id}/test` | `POST /api/webhook-events/test-event` (to any URL) |
| Sample payloads | — | `GET /api/webhook-events/sample-payload` |
| Resume disabled | `POST /webhooks/{id}/resume` | — |
| Event types list | `GET /webhooks/event-types` | `GET /api/webhook-events/event-types` |
| Custom headers | `headers` object on webhook | — |
| Campaign filter | `campaign` field on webhook | — |
| Custom label events | `custom_interest_value` for label-triggered events | — |
| Delivery log | Full webhook event schema with retry tracking | — |
| Webhook status | `status` (1=Active, -1=Error) + `timestamp_error` | — |

**Key differences:**
- **Instantly has custom headers on webhooks** — auth tokens for target systems
- **Instantly has webhook delivery logs** with retry tracking and response time
- **Instantly has webhook resume** for re-enabling disabled webhooks
- **Email Bison has sample payloads** — preview what a webhook will look like
- **Email Bison has warmup-specific webhook events** (disabled_receiving/causing_bounces)
- **Email Bison has tag-related events** (tag_attached, tag_removed)

---

## 9. Tags

| | **Instantly** | **Email Bison** |
|--|--------------|-----------------|
| CRUD | `POST/GET/PATCH/DELETE /custom-tags` | `POST/GET/DELETE /api/tags` |
| Attach to | Campaigns + Accounts (via tag mappings) | Campaigns + Leads + Email Accounts (direct endpoints) |
| Tag mappings | Separate `custom-tag-mappings` resource | Direct `attach-to-*` and `remove-from-*` endpoints |
| Skip webhooks | — | `skip_webhooks` param on attach/remove |

**Email Bison's tag system is simpler and more flexible** — direct attach/detach endpoints for campaigns, leads, and sender emails with webhook control. Instantly uses a separate mapping resource.

---

## 10. Features Only in Instantly

| Feature | Notes |
|---------|-------|
| **Campaign Subsequences** | Behavior-triggered follow-up sequences (CRM status, opens, clicks, reply content, campaign completion). Full CRUD + pause/resume + sending diagnostics. |
| **Lead Lists** | Standalone lists for organizing leads (CRUD). |
| **Lead Labels** | Custom labels with AI integration (`use_with_ai`), interest status mapping. |
| **Inbox Placement Testing** | One-time + automated recurring tests. Per-ESP per-geography deliverability. SPF/DKIM/DMARC validation. SpamAssassin scoring. IP blacklist monitoring. |
| **Inbox Placement Analytics** | Detailed per-email deliverability results from placement tests. |
| **Email Verification** | Verify single emails, poll for async results. |
| **Custom Prompt Templates** | AI prompt templates with GPT model selection (3.5 through GPT-5, o3). |
| **Sales Flows** | Smart views with engagement-based lead filtering (reply, open, click, status change). |
| **Email Templates** | Reusable templates (CRUD). |
| **CRM Actions / Phone** | Twilio phone number management. |
| **Audit Log** | Full activity tracking (16+ activity types, IP logging, API vs UI distinction). |
| **Background Jobs** | Async operation tracking. |
| **API Key Management** | Create keys with granular scopes (168+ scope values). |
| **Workspace Members** | Member management with role-based groups. |
| **Company-Level Controls** | Stop for company, per-company email limits, ESP matching. |
| **AI Interest Scoring** | Per-email `ai_interest_value` (0.0-1.0 float). |
| **AI SDR Integration** | `ai_sdr_id` on campaigns, `ai_agent_id` on emails. |

---

## 11. Features Only in Email Bison

| Feature | Notes |
|---------|-------|
| **Reply Followup Campaigns** | Dedicated campaign type (`reply_followup`) for automated follow-up in existing threads. Push replies into followup campaigns via API. |
| **Reply Templates** | Full CRUD with attachment support (max 25MB combined). |
| **Compose New Emails** | `POST /api/replies/new` — send one-off emails outside campaigns. |
| **Ignore Phrases** | Filter warmup/noise emails from inbox. |
| **Domain Blacklist** | Separate from email blacklist, with bulk CSV import. |
| **Custom Tracking Domains** | Dedicated CRUD endpoints with status tracking. |
| **Custom Lead Variables** | Workspace-level variable definitions (then set per-lead). |
| **Sending Schedule Forecasts** | Preview what will be sent today/tomorrow/day_after_tomorrow. |
| **Schedule Templates** | Save and reuse sending schedules. |
| **OAuth Token Access** | Get OAuth tokens for connected Google/Microsoft accounts. |
| **MX Record Checking** | Per-account and bulk MX validation. |
| **Bulk Operations** | Bulk signature update, bulk daily limit update, bulk CSV imports for accounts/leads/blacklists. |
| **Headless UI Token** | Embed Email Bison UI in partner apps. |
| **Per-Step Test Emails** | Send test emails from any sequence step. |
| **Step Attachments** | Attach files to sequence step emails. |
| **Master Inbox Settings** | `sync_all_emails`, `smart_warmup_filter`, `auto_interested_categorization` (GPT-4o-mini). |
| **Campaign Stats by Date** | Time-series stats with chart-ready format (`{label, color, dates}`). |
| **Workspace Stats** | Aggregate stats across all campaigns. |
| **Super Admin API** | Create users, create API tokens, delete workspaces. |
| **Warmup Bounce Tracking** | Track bounces received, caused, and auto-disable counts. |
| **Conversation Threading** | `GET /replies/{id}/conversation-thread` expands full thread. |
| **Attach Untracked Replies** | Link untracked replies to scheduled emails for stat correction. |

---

## 12. Comparison Summary for Glytec

### Where Instantly Wins
1. **Deliverability infrastructure** — inbox placement testing, SpamAssassin scoring, IP blacklist monitoring, email verification
2. **AI features** — per-email interest scoring, AI SDR integration, AI-driven A/B variant optimization, custom prompt templates
3. **Subsequences** — behavior-triggered follow-up sequences with complex conditions (CRM status, reply content, engagement)
4. **Audit trail** — full activity logging with 16+ types, IP tracking, API vs UI distinction
5. **Company-level controls** — stop-for-company, per-company limits, ESP matching
6. **API maturity** — granular scopes (168+), documented rate limits, cursor-based pagination
7. **Lead labels** — AI-integrated categorization system

### Where Email Bison Wins
1. **Reply management** — compose new emails, reply templates with attachments, push-to-followup, mark interested/not-interested, conversation threading
2. **Bulk operations** — CSV imports for accounts/leads/blacklists, bulk signature/limit updates
3. **Operational visibility** — sending schedule forecasts, campaign states (Launching/Queued/Failed), per-step test emails
4. **Flexibility** — separate email + domain blacklists, custom tracking domains, custom lead variables with explicit definitions
5. **Admin capabilities** — create users, create API tokens, headless UI embedding
6. **Campaign lifecycle** — duplicate, archive, delete, reply-followup campaign type
7. **Full OpenAPI spec** — machine-readable, no guessing

### For Glytec's Use Case (AI SDR for Hospital Systems)

| Need | Better Fit | Why |
|------|-----------|-----|
| Automated outbound sequencing | **Tie** | Both handle multi-step campaigns with A/B variants |
| Deliverability monitoring | **Instantly** | Inbox placement testing, SpamAssassin, IP blacklist monitoring |
| AI interest scoring | **Instantly** | Per-email AI scoring (0.0-1.0), AI SDR integration |
| Reply handling at scale | **Email Bison** | Reply templates, followup campaigns, conversation threading, compose new |
| Bulk operations | **Email Bison** | CSV imports, bulk updates for signatures/limits |
| Mailbox management | **Email Bison** | OAuth tokens, MX checking, bulk creation, per-account stats |
| API automation reliability | **Instantly** | Granular scopes, documented rate limits, webhook delivery logs |
| Cost of migration from SalesForge | **Email Bison** | More similar API patterns (integer IDs, PATCH support, explicit lifecycle states) |
| Subsequence/trigger automation | **Instantly** | Full subsequence system vs Email Bison's reply_followup campaigns |

### Integration Effort Estimate

**From SalesForge → Instantly:**
- Different auth (Bearer vs raw key)
- UUID IDs vs SalesForge's string IDs
- Different sequence step model (inline vs sub-resources)
- Cursor pagination vs offset pagination
- No PATCH on SalesForge; Instantly uses PATCH everywhere
- Campaign launch is explicit endpoint vs status change

**From SalesForge → Email Bison:**
- Same auth pattern (Bearer token)
- Integer IDs (simpler than SalesForge's string IDs)
- Similar sub-resource pattern for sequence steps
- Page-based pagination (more standard)
- Both PUT and PATCH available
- More lifecycle states to map
- Reply followup campaign type maps well to SalesForge's simpler model

---

## 13. API Quality & DX Comparison

| Dimension | **Instantly** | **Email Bison** |
|-----------|--------------|-----------------|
| Documentation | Developer portal + help docs (no OpenAPI spec) | Full OpenAPI 3.0.3 spec |
| Error responses | Not well-documented | 422 validation errors with field-level messages |
| Pagination | Cursor-based (scalable) | Page-based (simpler but less scalable) |
| Consistency | Very consistent snake_case, UUIDs | Consistent snake_case, integer IDs |
| Versioning | V2 only (V1 sunset) | v1 (deprecated) + v1.1 coexist |
| Deprecation | Clean V1→V2 migration | Deprecated endpoints still present alongside v1.1 |
| Bulk operations | Limited (leads bulk, warmup batch) | Extensive (CSV imports, bulk updates) |
| Webhook DX | Custom headers, delivery logs, retry tracking, resume | Sample payloads, test events |
| Response envelope | Varies | Consistent `{data: ...}` envelope |

---

*End of comparison. Saved to `docs/instantly-vs-emailbison.md`*
