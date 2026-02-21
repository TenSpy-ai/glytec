# Instantly.ai API V2 — Comprehensive Reference

Compiled from developer.instantly.ai, help.instantly.ai, and tested raw dump (Jan 2026).

---

## Overview

- **Base URL:** `https://api.instantly.ai/api/v2`
- **Auth:** Bearer token in `Authorization: Bearer <token>` header
- **API Keys:** Create via developer.instantly.ai; supports multiple keys per workspace with granular scopes
- **Rate Limit:** Workspace-wide (shared across all API keys and v1/v2); exceeding → 429 status. Available on Growth plan and above.
- **Pagination:** Cursor-based via `starting_after` param + `next_starting_after` in response
- **Naming:** snake_case for all entities and fields
- **V1 Deprecated:** 2025. V2 is NOT compatible with V1 — new keys required.

### API Scopes

168+ granular scope values. Pattern: `{resource}:{action}` where action = `all|create|read|update|delete`.

Examples: `campaigns:create`, `leads:all`, `accounts:read`, `webhooks:delete`, `all:all` (full access).

Resource prefixes include: `campaigns`, `leads`, `accounts`, `webhooks`, `lead_labels`, `lead_lists`, `emails`, `email_verification`, `inbox_placement_tests`, `inbox_placement_analytics`, `block_list_entries`, `audit_logs`, `custom_tags`, `custom_tag_mappings`, `crm_actions`, `background_jobs`, `api_keys`, `workspaces`, `workspace_members`, `ai_agents`, `subsequences`, `custom_prompt_templates`, `sales_flows`, `email_templates`.

---

## Resource Categories & Endpoints

### 1. Campaign

A campaign that can be sent to a list of recipients.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/campaigns` | Create campaign |
| GET | `/campaigns` | List campaigns (filter by status, name) |
| GET | `/campaigns/{id}` | Get single campaign |
| PATCH | `/campaigns/{id}` | Update campaign |
| POST | `/campaigns/{id}/launch` | Launch campaign |
| POST | `/campaigns/{id}/pause` | Pause campaign |
| POST | `/campaigns/{id}/activate-all-sending-accounts` | Activate all sending accounts |
| POST | `/campaigns/search-by-contact` | Search campaigns by contact email |

**Campaign Schema (key fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| name | string | required |
| status | number | 0=Draft, 1=Active, 2=Paused, 3=Completed, 4=Running Subsequences, -99=Account Suspended, -1=Accounts Unhealthy, -2=Bounce Protect |
| campaign_schedule | object | schedules array with name, timing (from/to HH:MM), days (0-6 booleans), timezone, start_date, end_date |
| sequences | array | Email copy. Only first element used — add all steps to that array |
| sequences[].steps[].type | string | Always "email" |
| sequences[].steps[].subject | string | Email subject (supports {{variables}}) |
| sequences[].steps[].body | string | Email body HTML |
| sequences[].steps[].delay | number | Days to wait before sending |
| sequences[].steps[].variants | array | A/B test variants |
| email_list | array of strings | Sending accounts (email addresses) |
| email_tag_list | array of uuids | Tags to filter sending accounts |
| daily_limit | number | Campaign daily send limit |
| daily_max_leads | number | Max new leads contacted per day |
| email_gap | number | Minutes between emails |
| random_wait_max | number | Max random wait (minutes) |
| stop_on_reply | boolean | Stop for lead on reply |
| stop_on_auto_reply | boolean | Stop on auto-reply |
| stop_for_company | boolean | Stop for entire domain on reply |
| link_tracking | boolean | Track link clicks |
| open_tracking | boolean | Track opens |
| text_only | boolean | Send plain text only |
| first_email_text_only | boolean | First email plain text |
| match_lead_esp | boolean | Match sending account ESP to lead ESP |
| is_evergreen | boolean | Evergreen campaign |
| pl_value | number | Value per positive lead ($) |
| allow_risky_contacts | boolean | Allow unverified contacts |
| disable_bounce_protect | boolean | Disable auto-pause on bounces |
| insert_unsubscribe_header | boolean | Add unsubscribe header |
| prioritize_new_leads | boolean | Prioritize new leads over follow-ups |
| cc_list | array of emails | CC recipients |
| bcc_list | array of emails | BCC recipients |
| auto_variant_select | object | Auto A/B optimization settings |
| limit_emails_per_company_override | object | Per-campaign company limit override |
| not_sending_status | number | 1=Outside schedule, 2=Waiting for lead, 3=Campaign daily limit hit, 4=All accounts at limit, 99=Error |
| provider_routing_rules | array | ESP routing rules |
| ai_sdr_id | uuid | AI SDR that created this campaign |
| owned_by | uuid | Owner user ID |

---

### 2. Lead

A lead entity representing an individual contact.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/leads` | Create lead (single) |
| POST | `/leads/list` | List leads (with filters, POST body) |
| PATCH | `/leads/{id}` | Update lead |
| DELETE | `/leads/{id}` | Delete single lead |
| DELETE | `/leads` | Delete leads in bulk (body: campaign/list + optional lead IDs) |
| POST | `/leads/move` | Move leads to another campaign or list |
| POST | `/leads/move-to-subsequence` | Move lead to a subsequence |
| POST | `/leads/remove-from-subsequence` | Remove lead from subsequence |
| POST | `/leads/bulk` | Add leads in bulk to campaign or list |

**Lead Schema (key fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| email | string | Lead email address |
| first_name | string | |
| last_name | string | |
| company_name | string | |
| company_domain | string | read-only, auto-extracted |
| website | string | |
| phone | string | |
| personalization | string | Custom personalization line |
| campaign | uuid | Associated campaign |
| status | number | 1=Active, 2=Paused, 3=Completed, -1=Bounced, -2=Unsubscribed, -3=Skipped |
| email_open_count | number | read-only |
| email_reply_count | number | read-only |
| email_click_count | number | read-only |
| status_summary | object | lastStep info, domain_complete flag |
| status_summary_subseq | object | Subsequence status |
| last_step_from | string | "campaign" or "subsequence" |
| last_step_id | uuid | |
| last_step_timestamp_executed | datetime | |
| email_opened_step | number | Last step opened |
| email_opened_variant | number | Last variant opened |
| email_replied_step | number | Last step replied to |
| email_replied_variant | number | Last variant replied to |
| email_clicked_step | number | Last step clicked |
| email_clicked_variant | number | Last variant clicked |
| lt_interest_status | number | Interest status (custom or standard) |
| payload | object | Custom variables — flat key:value only (string/number/boolean/null, NO objects or arrays) |

---

### 3. Account (Email Account)

An email account that can be used to send campaigns.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accounts` | Create account |
| GET | `/accounts` | List accounts (filter by tags) |
| GET | `/accounts/{email}` | Get single account |
| PATCH | `/accounts/{email}` | Update account |
| DELETE | `/accounts/{email}` | Delete account |
| POST | `/accounts/{email}/pause` | Pause account |
| POST | `/accounts/warmup/enable` | Enable warmup (batch — list of emails) |
| POST | `/accounts/warmup/disable` | Disable warmup (batch — returns background job) |

**Account Schema (key fields):**

| Field | Type | Notes |
|-------|------|-------|
| email | string (email) | required, used as identifier |
| first_name | string | required |
| last_name | string | required |
| provider_code | number | 1=Custom IMAP/SMTP, 2=Google, 3=Microsoft, 4=AWS |
| status | number | 1=Active, 2=Paused, -1=Connection Error, -2=Soft Bounce Error, -3=Sending Error |
| warmup_status | number | 0=Paused, 1=Active, -1=Banned, -2=Spam Folder Unknown, -3=Permanent Suspension |
| warmup | object | limit, advanced settings, warmup_custom_ftag, increment ("disabled" or config), reply_rate |
| daily_limit | number | Daily email sending limit |
| sending_gap | number [0-1440] | Minutes between emails from this account |
| enable_slow_ramp | boolean | Gradually increase sending limits |
| tracking_domain_name | string | Custom tracking domain |
| tracking_domain_status | string | "active" etc. |
| signature | string | Email signature |
| setup_pending | boolean | read-only |
| is_managed_account | boolean | read-only |
| inbox_placement_test_limit | number | |
| stat_warmup_score | number | read-only, e.g. 85 |
| warmup_pool_id | uuid | read-only |
| status_message | object | Error details: code, command, response, e_message, responseCode |
| timestamp_last_used | datetime | read-only |
| timestamp_warmup_start | datetime | read-only |

---

### 4. Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/campaigns/analytics` | Campaign analytics (filter by campaign_id or all) |
| GET | `/campaigns/analytics/overview` | Campaign analytics overview |
| GET | `/campaigns/analytics/daily` | Campaign daily analytics |
| GET | `/campaigns/analytics/steps` | Per-step analytics |
| POST | `/accounts/warmup-analytics` | Warmup analytics (batch — list of emails) |
| GET | `/accounts/analytics/daily` | Account daily sending analytics |
| POST | `/accounts/test/vitals` | Test account vitals (deliverability check) |

---

### 5. Lead List

A list used to store and organize leads.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/lead-lists` | Create lead list |
| GET | `/lead-lists` | List lead lists |
| GET | `/lead-lists/{id}` | Get single lead list |
| PATCH | `/lead-lists/{id}` | Update lead list |
| DELETE | `/lead-lists/{id}` | Delete lead list |

**Lead List Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| name | string | required |
| organization_id | uuid | read-only |
| has_enrichment_task | boolean | Auto-enrich new leads added to list |
| owned_by | uuid | Defaults to creator |

---

### 6. Lead Label

Custom labels for categorizing leads (integrates with AI features).

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/lead-labels` | Create label |
| GET | `/lead-labels` | List labels |
| GET | `/lead-labels/{id}` | Get single label |
| PATCH | `/lead-labels/{id}` | Update label |
| DELETE | `/lead-labels/{id}` | Delete label |

**Lead Label Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| label | string | e.g. "Hot Lead" |
| interest_status_label | string | positive / negative / neutral |
| interest_status | number | read-only, auto-generated |
| description | string | Purpose of the label |
| use_with_ai | boolean | Whether AI features should use this label |

---

### 7. Campaign Subsequence

Follow-up sequences triggered by lead behavior (reply content, CRM status, engagement activity).

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/subsequences` | Create subsequence |
| GET | `/subsequences` | List subsequences |
| POST | `/subsequences/{id}/duplicate` | Duplicate subsequence |
| POST | `/subsequences/{id}/pause` | Pause subsequence |
| POST | `/subsequences/{id}/resume` | Resume subsequence |
| GET | `/subsequences/{id}` | Get single subsequence |
| PATCH | `/subsequences/{id}` | Update subsequence |
| DELETE | `/subsequences/{id}` | Delete subsequence |
| GET | `/subsequences/{id}/sending-status` | Get sending diagnostics |

**Subsequence Schema (key fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| parent_campaign | uuid | required |
| name | string | required |
| status | number | 0=Draft, 1=Active, 2=Paused, 3=Completed, 4=Running Subsequences, -99=Account Suspended, -1=Accounts Unhealthy, -2=Bounce Protection |
| conditions | object | Trigger conditions (see below) |
| conditions.crm_status | array of numbers | 0=Out of Office, 1=Interested, 2=Meeting Booked, 3=Meeting Completed, 4=Won, -1=Not Interested, -2=Wrong Person, -3=Lost, -4=No Show |
| conditions.lead_activity | array of numbers | 2=Email Opened, 4=Link Clicked, 91=Campaign Completed Without Reply |
| conditions.reply_contains | string | Keyword match in reply text |
| subsequence_schedule | object | Same structure as campaign_schedule |
| sequences | array | Same as campaign — only first element used, steps array inside |

---

### 8. Email (Unibox)

Emails visible in the Unibox — campaign sends, replies, manual sends.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/emails` | List emails (filters: campaign, lead, account, etc.) |
| GET | `/emails/{id}` | Get single email |
| POST | `/emails/reply` | Reply to an email (set reply_to_uuid) |
| POST | `/emails/forward` | Forward an email |
| POST | `/emails/threads/{id}/mark-as-read` | Mark thread as read |
| DELETE | `/emails/{id}` | Delete email |
| GET | `/emails/unread/count` | Get unread email count |

**Email Schema (key fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| timestamp_email | datetime | Actual email timestamp (from mail server) |
| timestamp_created | datetime | When added to Instantly DB |
| message_id | string | Server-assigned message ID |
| subject | string | |
| body | object | { text: string, html: string } |
| from_address_email | email | read-only, derived from eaccount |
| to_address_email_list | string | Comma-separated |
| cc_address_email_list | string | |
| bcc_address_email_list | string | |
| reply_to | string | |
| eaccount | string | Sending account identifier |
| campaign_id | uuid | null for manual sends |
| subsequence_id | uuid | |
| list_id | uuid | |
| lead | string | Lead email |
| lead_id | uuid | |
| ue_type | number | 1=Sent from campaign, 2=Received, 3=Sent (manual), 4=Scheduled |
| step | string | Campaign step ID |
| is_unread | number | 0/1 |
| is_auto_reply | number | read-only, 0/1 |
| ai_interest_value | number | AI-scored interest (0.0–1.0) |
| ai_assisted | number | 0/1 |
| is_focused | number | 0/1 (primary tab in Unibox) |
| i_status | number | Interest status |
| thread_id | uuid | Groups emails in same thread |
| content_preview | string | First few lines |
| attachment_json | object | { files: [{ filename, size, type, url }] } |
| ai_agent_id | uuid | If sent by AI agent |

---

### 9. Email Verification

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/email-verification` | Verify a single email |
| GET | `/email-verification/{email}` | Check verification status |

**Email Verification Schema:**

| Field | Type | Notes |
|-------|------|-------|
| email | string | required |
| verification_status | string | pending / verified / invalid |
| status | string | success / error (request status, NOT verification result) |
| catch_all | boolean or "pending" | Whether domain is catch-all |
| credits | number | Remaining verification credits |
| credits_used | number | Credits consumed |

Note: If verification takes >10 seconds, returns `pending`. Poll the GET endpoint to check result.

---

### 10. Inbox Placement Test

Test deliverability across ESPs and geographies.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/inbox-placement-tests` | Create test |
| GET | `/inbox-placement-tests` | List tests |
| GET | `/inbox-placement-tests/{id}` | Get single test |
| PATCH | `/inbox-placement-tests/{id}` | Update test |
| POST | `/inbox-placement-tests/{id}/pause` | Pause automated test |
| POST | `/inbox-placement-tests/{id}/resume` | Resume automated test |
| GET | `/inbox-placement-tests/email-service-provider-options` | Get available ESP options |

**Inbox Placement Test Schema (key fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| name | string | required |
| type | number | 1=One-time, 2=Automated (recurring) |
| sending_method | number | 1=From Instantly, 2=From outside Instantly |
| email_subject | string | Test email subject |
| email_body | string | Test email body |
| emails | array of strings | Sending accounts |
| recipients | array of strings | read-only, Instantly test addresses |
| recipients_labels | array | ESP + type + geo for recipients |
| delivery_mode | number | 1=One by one, 2=All together |
| schedule | object | For automated: days, timing, timezone |
| campaign_id | uuid | Link to campaign |
| test_code | string | Identifier for tests from outside Instantly |
| text_only | boolean | Disables open tracking |
| tags | array of uuids | Account tag filters |
| automations | array | Trigger automations on conditions |
| status | number | 1=Active, 2=Paused, 3=Completed |
| not_sending_status | string | "daily_limits_hit" / "other" / "" |
| timestamp_next_run | datetime | Next automated run |

---

### 11. Inbox Placement Analytics

Per-email deliverability results from placement tests.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inbox-placement-analytics` | List analytics for a test |

**Inbox Placement Analytics Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | |
| test_id | uuid | Parent test |
| is_spam | boolean | Landed in spam? (only on record_type=2/received) |
| has_category | boolean | Categorized (promotions, social)? |
| sender_email | string | |
| sender_esp | number | 1=Google, 2=Microsoft, 12=Web.de, 13=Libero.it |
| recipient_email | string | |
| recipient_esp | number | Same enum as sender_esp |
| recipient_geo | number | 1=US, 2=Italy, 3=Germany, 4=France |
| recipient_type | number | 1=Professional, 2=Personal |
| spf_pass | boolean | SPF validation |
| dkim_pass | boolean | DKIM validation |
| dmarc_pass | boolean | DMARC validation |
| smtp_ip_blacklist_report | object | IP blacklist details |
| authentication_failure_results | object | SPF/DKIM/DMARC failure details |
| record_type | number | 1=Sent, 2=Received |

---

### 12. Inbox Placement Blacklist & SpamAssassin Report

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inbox-placement-reports` | Get blacklist + SpamAssassin report for a test |

**Report Schema:**

| Field | Type | Notes |
|-------|------|-------|
| domain | string | e.g. "growinstantly.com" |
| domain_ip | string | IP address |
| spam_assassin_score | number | e.g. 2.5 |
| domain_blacklist_count | number | |
| domain_ip_blacklist_count | number | |
| spam_assassin_report | object | { is_spam, report[], spam_score } |
| blacklist_report | object | { address, blacklisted_count, details[], ip, is_blacklisted, is_domain } |

---

### 13. Webhook

Event notification subscriptions.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/webhooks` | List webhooks (filter by campaign, event_type) |
| POST | `/webhooks` | Create webhook |
| GET | `/webhooks/{id}` | Get single webhook |
| PATCH | `/webhooks/{id}` | Update webhook |
| DELETE | `/webhooks/{id}` | Delete webhook |
| GET | `/webhooks/event-types` | List available event types |
| POST | `/webhooks/{id}/test` | Send test webhook |
| POST | `/webhooks/{id}/resume` | Resume disabled webhook |

**Webhook Event Types (19+):**
- `all_events` — subscribe to everything including custom label events
- `email_sent`
- `email_opened`
- `email_link_clicked`
- `reply_received`
- `email_bounced`
- `lead_unsubscribed`
- `campaign_completed`
- `account_error`
- `lead_neutral`
- Plus 9+ more including custom label-triggered events

**Webhook Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | |
| target_hook_url | string (uri) | Must start with http(s):// |
| event_type | string | One of the event types above, or null for custom label events |
| campaign | uuid | Optional — filter to specific campaign |
| name | string | e.g. "Zapier Positive Replies" |
| custom_interest_value | number | For custom label events, matches LeadLabel.interest_status |
| headers | object | Custom HTTP headers sent with payload (e.g. auth) |
| status | number | 1=Active, -1=Error (disabled due to delivery failures) |
| timestamp_error | datetime | When disabled (null if active) |

---

### 14. Webhook Event

Delivery log for webhook payloads.

**Webhook Event Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | |
| success | boolean | Whether delivery succeeded |
| retry_count | number | Retry attempts |
| will_retry | boolean | |
| webhook_url | string | Target URL |
| payload | object | JSON payload sent |
| status_code | number | HTTP response code |
| error_message | string | e.g. "Connection timeout" |
| timestamp_next_retry | datetime | |
| retry_group_id | uuid | Groups retry attempts |
| retry_successful | boolean | |
| lead_email | string | Associated lead |
| response_time_ms | number | Response time in ms |

---

### 15. Block List Entry

Blocked emails and domains.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/block-list-entries` | Create block list entry |
| GET | `/block-list-entries` | List entries |
| GET | `/block-list-entries/{id}` | Get single entry |
| DELETE | `/block-list-entries/{id}` | Delete entry |

---

### 16. Custom Tag

Tags for organizing accounts and campaigns. Can be used as filters in list APIs.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/custom-tags` | Create tag |
| GET | `/custom-tags` | List tags |
| GET | `/custom-tags/{id}` | Get single tag |
| PATCH | `/custom-tags/{id}` | Update tag |
| DELETE | `/custom-tags/{id}` | Delete tag |

---

### 17. Custom Tag Mapping

Associates tags with accounts/campaigns.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/custom-tag-mappings` | Create mapping |
| GET | `/custom-tag-mappings` | List mappings |
| DELETE | `/custom-tag-mappings/{id}` | Delete mapping |

---

### 18. Audit Log

Track system activities and API usage.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit-logs` | List audit logs (filter by activity_type, search, date range) |

**Activity Types:** 1=User login, 2=Lead deletion, 3=Campaign deletion, 4=Campaign launch, 5=Campaign pause, 6=Account addition, 7=Account deletion, 8=Lead moved, 9=Lead added, 10=Lead merged, + 6 more

**Audit Log Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | |
| timestamp | datetime | When activity occurred |
| activity_type | number | See enum above |
| ip_address | string | |
| from_api | boolean | Whether via API |
| user_agent | string | |
| user_id | uuid | |
| user_name | string | |
| affected_count | number | Items affected |
| campaign_id | uuid | If applicable |
| webhook_id | uuid | If applicable |
| subsequence_id | uuid | If applicable |
| list_id | uuid | If applicable |

---

### 19. Custom Prompt Template

AI prompt templates for copywriting, cleaning, sales, marketing, personalization.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/custom-prompt-templates` | Create template |
| GET | `/custom-prompt-templates` | List templates |
| GET | `/custom-prompt-templates/{id}` | Get single template |
| PATCH | `/custom-prompt-templates/{id}` | Update template |
| DELETE | `/custom-prompt-templates/{id}` | Delete template |

**Template Schema:**

| Field | Type | Notes |
|-------|------|-------|
| name | string | |
| category | number | 1=Copywriting, 2=Cleaning, 3=Sales, 4=Marketing, 5=Other, 6=Personalization |
| prompt | string | Template with `{{property_1}}` variables |
| is_public | boolean | |
| model_version | string | "3.5", "gpt-5", "gpt-5-mini", "gpt-5-nano", "4.0", "4.0-Omni", "gpt-4o", "o3", "gpt-4.1", "gpt-4.1-mini", +13 more |
| properties | array | Variable definitions |
| template_type | string | "custom" / "public" |
| like_count | number | read-only |
| execution_count | number | read-only |

---

### 20. Sales Flow

Smart views for filtering leads by engagement behavior.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sales-flows` | Create sales flow |
| GET | `/sales-flows` | List sales flows |
| GET | `/sales-flows/{id}` | Get single |
| PATCH | `/sales-flows/{id}` | Update |
| DELETE | `/sales-flows/{id}` | Delete |

**Sales Flow Schema:**

| Field | Type | Notes |
|-------|------|-------|
| name | string | e.g. "Smart view name" |
| queries | array | Filter conditions |
| queries[].actionType | string | "reply", "email-open", "last-contacted", "link-click", "lead-status", "lead-status-change" |
| queries[].values | object | occurrence-days, occurrence-count, lead-status filters |
| is_default | boolean | Default view for user |
| list_id | string | "all-lists" or specific UUID |
| campaign_id | string | null when "all-campaigns" |

---

### 21. Email Template

Reusable email templates for campaigns.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/email-templates` | Create template |
| GET | `/email-templates` | List templates |
| GET | `/email-templates/{id}` | Get single |
| PATCH | `/email-templates/{id}` | Update |
| DELETE | `/email-templates/{id}` | Delete |

**Schema:** id, name, subject, body (HTML or text), organization.

---

### 22. CRM Actions

Phone number management (Twilio integration).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/crm-actions/phone-numbers` | List phone numbers |
| DELETE | `/crm-actions/phone-numbers/{id}` | Delete phone number |

**Phone Number Schema:** id, phone_number (E.164), country, locality, subscription_id, twilio_sid, renewal_date, price.

---

### 23. Background Job

Async operations (e.g., disabling warmup for many accounts).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/background-jobs` | List background jobs |
| GET | `/background-jobs/{id}` | Get job status |

---

### 24. API Key

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api-keys` | Create API key (with scopes) |

**API Key Schema:** id, name, scopes (array of scope strings), key (read-only, shown once), organization_id.

---

### 25. Workspace

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces` | List workspaces |

---

### 26. Workspace Member

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspace-members` | List workspace members |
| POST | `/workspace-members` | Invite workspace member |
| PATCH | `/workspace-members/{id}` | Update member role |
| DELETE | `/workspace-members/{id}` | Remove member |

Note: "owner" role exists in enum but cannot be created via API — only assigned to workspace creator.

---

### 27. Workspace Group Member

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspace-group-members` | List group members |
| POST | `/workspace-group-members` | Add group member |
| DELETE | `/workspace-group-members/{id}` | Remove group member |

---

### 28. Account Campaign Mapping

Shows which campaigns an account is assigned to.

**Schema:** campaign_id, campaign_name, status, timestamp_created.

---

## Endpoint Count Summary

| Category | Endpoints |
|----------|-----------|
| Campaign | 8 |
| Lead | 9 |
| Account | 8 |
| Analytics | 7 |
| Lead List | 5 |
| Lead Label | 5 |
| Campaign Subsequence | 9 |
| Email (Unibox) | 7 |
| Email Verification | 2 |
| Inbox Placement Test | 7 |
| Inbox Placement Analytics | 1 |
| Inbox Placement Reports | 1 |
| Webhook | 8 |
| Block List Entry | 4 |
| Custom Tag | 5 |
| Custom Tag Mapping | 3 |
| Audit Log | 1 |
| Custom Prompt Template | 5 |
| Sales Flow | 5 |
| Email Template | 5 |
| CRM Actions | 2 |
| Background Job | 2 |
| API Key | 1 |
| Workspace | 1 |
| Workspace Member | 4 |
| Workspace Group Member | 3 |
| **TOTAL** | **~118** |

---

## Notable Features (vs competitors)

### Built-in Warmup
Accounts have native warmup with warmup_status, warmup_score, warmup pool, and configurable reply_rate. Enable/disable warmup in bulk via dedicated endpoints. Warmup analytics available per-account.

### Inbox Placement Testing
One-time and automated (recurring) placement tests. Per-ESP and per-geography deliverability results. SPF/DKIM/DMARC validation, SpamAssassin scoring, IP blacklist monitoring. Automations can trigger on placement results.

### AI Features
- `ai_interest_value` on emails — AI-scored reply interest
- `use_with_ai` on lead labels — AI uses labels for classification
- `ai_assisted` flag on emails
- `ai_agent_id` on emails — AI-generated sends
- `ai_sdr_id` on campaigns — AI SDR campaign creation
- Custom prompt templates with GPT model selection (3.5 through GPT-5, o3)
- `auto_variant_select` — AI optimizes A/B test variants

### Campaign Subsequences
Behavior-triggered follow-up sequences: CRM status changes, email opens, link clicks, campaign completion without reply, reply content matching. Each subsequence has its own schedule and email steps.

### Company-Level Controls
- `stop_for_company` — stop for entire domain when one lead replies
- `limit_emails_per_company_override` — cap outreach per domain
- `match_lead_esp` — match sending account provider to lead's provider

### Unibox
Unified inbox across all accounts/campaigns. Threading, AI interest scoring, auto-reply detection, focused view, reminders, attachment support.

### Block List
Domain and email-level blocking across the workspace.

### Audit Log
Full activity tracking with API vs UI distinction, IP logging, and user attribution.
