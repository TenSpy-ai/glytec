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
| DELETE | `/campaigns/{id}` | Delete campaign |
| POST | `/campaigns/{id}/activate` | Activate (start) or resume a campaign |
| POST | `/campaigns/{id}/pause` | Stop (or pause) a campaign |
| POST | `/campaigns/{id}/duplicate` | Duplicate campaign |
| POST | `/campaigns/{id}/export` | Export campaign to JSON format |
| POST | `/campaigns/{id}/from-export` | Create campaign from shared/exported one |
| POST | `/campaigns/{id}/share` | Share a campaign |
| POST | `/campaigns/{id}/variables` | Add campaign variables |
| GET | `/campaigns/{id}/sending-status` | Get campaign sending status/diagnostics |
| GET | `/campaigns/count-launched` | Get count of launched campaigns |
| GET | `/campaigns/search-by-contact` | Search campaigns by lead email |

**Campaign Schema (38 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| name | string | **required** |
| status | number | **read-only**. 0=Draft, 1=Active, 2=Paused, 3=Completed, 4=Running Subsequences, -99=Account Suspended, -1=Accounts Unhealthy, -2=Bounce Protect |
| campaign_schedule | object | **required**. schedules array with name, timing (from/to HH:MM), days (0-6 booleans), timezone, start_date, end_date |
| sequences | array | Email copy. **Only first element used** — add all steps to that array |
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
| provider_routing_rules | array | ESP routing rules |
| not_sending_status | number | read-only. 1=Outside schedule, 2=Waiting for lead, 3=Campaign daily limit hit, 4=All accounts at limit, 99=Error |
| core_variables | object | read-only. Campaign core variables |
| custom_variables | object | read-only. Campaign custom variables |
| organization | uuid | read-only. Workspace ID |
| ai_sdr_id | uuid | AI SDR that created this campaign |
| owned_by | uuid | Owner user ID |
| timestamp_created | datetime | read-only |
| timestamp_updated | datetime | read-only |

**Request Body — POST `/campaigns` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | **yes** | Campaign name |
| campaign_schedule | object | **yes** | Schedule config: schedules array with name, timing, days, timezone |
| sequences | array | no | Email copy. Only first element used — all steps in that array |
| email_list | array | no | Sending account email addresses |
| email_tag_list | array | no | Tag UUIDs to filter sending accounts |
| daily_limit | number/null | no | Campaign daily send limit |
| daily_max_leads | number/null | no | Max new leads contacted per day |
| email_gap | number/null | no | Minutes between emails |
| random_wait_max | number/null | no | Max random wait (minutes) |
| stop_on_reply | boolean/null | no | Stop for lead on reply |
| stop_on_auto_reply | boolean/null | no | Stop on auto-reply |
| stop_for_company | boolean/null | no | Stop for entire domain on reply |
| link_tracking | boolean/null | no | Track link clicks |
| open_tracking | boolean/null | no | Track opens |
| text_only | boolean/null | no | Send plain text only |
| first_email_text_only | boolean/null | no | First email plain text |
| match_lead_esp | boolean/null | no | Match sending account ESP to lead ESP |
| is_evergreen | boolean/null | no | Evergreen campaign |
| pl_value | number/null | no | Value per positive lead ($) |
| allow_risky_contacts | boolean/null | no | Allow unverified contacts |
| disable_bounce_protect | boolean/null | no | Disable auto-pause on bounces |
| insert_unsubscribe_header | boolean/null | no | Add unsubscribe header |
| prioritize_new_leads | boolean/null | no | Prioritize new leads over follow-ups |
| cc_list | array | no | CC recipients |
| bcc_list | array | no | BCC recipients |
| auto_variant_select | object/null | no | Auto A/B optimization settings |
| limit_emails_per_company_override | object/null | no | Per-campaign company limit override |
| provider_routing_rules | array | no | ESP routing rules |
| owned_by | string/null | no | Owner user ID |
| ai_sdr_id | string/null | no | AI SDR that created this campaign |

**Request Body — PATCH `/campaigns/{id}` (Update):** Same fields as create, but `name` and `campaign_schedule` are optional.

**Request Body — POST `/campaigns/{id}/duplicate`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | no | New name. Defaults to "CAMPAIGN NAME (copy)" |

**Request Body — POST `/campaigns/{id}/variables`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| variables | array | no | Campaign variables to add |

---

### 2. Lead

A lead entity representing an individual contact.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/leads` | Create lead (single) |
| GET | `/leads/{id}` | Get single lead |
| PATCH | `/leads/{id}` | Update lead |
| DELETE | `/leads/{id}` | Delete single lead |
| DELETE | `/leads` | Delete leads in bulk (body: campaign/list + optional lead IDs) |
| POST | `/leads/list` | List leads (with filters, POST body) |
| POST | `/leads/add` | Add leads in bulk to a campaign or list |
| POST | `/leads/move` | Move leads to another campaign or list |
| POST | `/leads/subsequence/move` | Move a lead to a subsequence |
| POST | `/leads/subsequence/remove` | Remove a lead from a subsequence |
| POST | `/leads/merge` | Merge two leads |
| POST | `/leads/bulk-assign` | Bulk assign leads to organization users |
| POST | `/leads/update-interest-status` | Update the interest status of a lead |

**Lead Schema (49 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| email | string | Lead email address |
| first_name | string | |
| last_name | string | |
| company_name | string | |
| company_domain | string | read-only, auto-extracted from email |
| website | string | |
| phone | string | |
| personalization | string | Custom personalization line |
| campaign | uuid | Associated campaign ID |
| list_id | uuid | Associated lead list ID |
| assigned_to | uuid | User ID assigned to this lead |
| status | number | read-only. 1=Active, 2=Paused, 3=Completed, -1=Bounced, -2=Unsubscribed, -3=Skipped |
| lt_interest_status | number | 1=Interested, 2=Meeting Booked, 3=Meeting Completed, 4=Won, 0=Out of Office, -1=Not Interested, -2=Wrong Person, -3=Lost, -4=No Show. Can also be a custom LeadLabel.interest_status value. |
| verification_status | number | read-only. 1=Verified, -1=Invalid, -2=Unknown, -3=Accept-all/Catch-all, -4=Unable to verify, 11=Pending, 12=Skipped |
| enrichment_status | number | read-only. 1=Enriched, -1=Failed, 11=Pending, -2=Not found |
| esp_code | number | read-only. Lead's email provider. 0=Unknown, 1=Google, 2=Microsoft, 3=Yahoo, 8=Zoho, 9=GoDaddy, 10=Rackspace, 12=Web.de, 13=Libero.it, 999=Custom, 1000=Other |
| esg_code | number | read-only. 0=Unknown, 1=US, 2=Italy, 3=Germany, 4=France |
| upload_method | string | read-only. "manual", "api", or "website-visitor" |
| uploaded_by_user | uuid | read-only. User who uploaded this lead |
| is_website_visitor | boolean | read-only |
| pl_value_lead | string | Potential value of the lead |
| payload | object | **read-only in responses**. Custom variables — flat key:value only (string/number/boolean/null, NO objects or arrays). Set via create/update endpoints. |
| organization | uuid | read-only. Workspace ID |
| email_open_count | number | read-only |
| email_reply_count | number | read-only |
| email_click_count | number | read-only |
| status_summary | object | read-only. lastStep info, domain_complete flag |
| status_summary_subseq | object | read-only. Subsequence status |
| last_step_from | string | read-only. "campaign" or "subsequence" |
| last_step_id | uuid | read-only |
| last_step_timestamp_executed | datetime | read-only |
| last_contacted_from | string | read-only. Source of last contact |
| email_opened_step | number | read-only. Last step opened |
| email_opened_variant | number | read-only. Last variant opened |
| email_replied_step | number | read-only. Last step replied to |
| email_replied_variant | number | read-only. Last variant replied to |
| email_clicked_step | number | read-only. Last step clicked |
| email_clicked_variant | number | read-only. Last variant clicked |
| subsequence_id | string | read-only. Current subsequence ID |
| timestamp_created | datetime | read-only |
| timestamp_updated | datetime | read-only |
| timestamp_last_contact | datetime | read-only |
| timestamp_last_touch | datetime | read-only |
| timestamp_last_open | datetime | read-only |
| timestamp_last_reply | datetime | read-only |
| timestamp_last_click | datetime | read-only |
| timestamp_last_interest_change | datetime | read-only |
| timestamp_added_subsequence | datetime | read-only |

**Request Body — POST `/leads` (Create single lead):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string/null | no | Lead email address |
| first_name | string/null | no | |
| last_name | string/null | no | |
| company_name | string/null | no | |
| website | string/null | no | |
| phone | string/null | no | |
| personalization | string/null | no | Custom personalization line |
| campaign | string/null | no | Campaign ID to add lead to |
| list_id | string/null | no | List ID to add lead to |
| assigned_to | string/null | no | User ID to assign lead to |
| lt_interest_status | number | no | Interest status. Enum: 1=Interested, 2=Meeting Booked, 3=Meeting Completed, 4=Won, 0=Out of Office, -1=Not Interested, -2=Wrong Person, -3=Lost, -4=No Show |
| pl_value_lead | string/null | no | Potential value |
| custom_variables | object | no | Flat key:value metadata (string/number/boolean/null only) |
| skip_if_in_campaign | boolean | no | Skip if lead already in the campaign |
| skip_if_in_list | boolean | no | Skip if lead already in the list |
| skip_if_in_workspace | boolean | no | Skip if lead already anywhere in workspace |
| verify_leads_on_import | boolean | no | Verify email on import |
| verify_leads_for_lead_finder | boolean | no | Verify for lead finder |
| blocklist_id | string | no | Blocklist ID to check against |

**Request Body — POST `/leads/add` (Bulk add):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| leads | array | **yes** | Array of lead objects (each must have `email` when using campaign_id) |
| campaign_id | string | no* | Campaign to add leads to. *Use this OR `list_id`, not both |
| list_id | string | no* | List to add leads to. *Use this OR `campaign_id`, not both |
| assigned_to | string | no | User ID to assign all leads to |
| skip_if_in_campaign | boolean | no | Skip if lead already in ANY campaign |
| skip_if_in_list | boolean | no | Skip if lead already in ANY list |
| skip_if_in_workspace | boolean | no | Skip if lead already anywhere in workspace |
| verify_leads_on_import | boolean | no | Creates background job to verify emails |
| blocklist_id | string/null | no | Blocklist to check against (default: workspace blocklist) |

**Request Body — POST `/leads/list` (List/search leads):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| campaign | string | no | Campaign ID filter |
| list_id | string | no | List ID filter |
| search | string | no | Search by first name, last name, or email |
| filter | string | no | Filter criteria. For custom labels, use `interest_status` field |
| contacts | array | no | Array of specific emails to find |
| ids | array | no | Array of specific lead IDs |
| excluded_ids | array | no | Lead IDs to exclude |
| enrichment_status | number | no | Enum: 1=Enriched, -1=Failed, 11=Pending, -2=Not found |
| esg_code | string | no | Enum: "0"=Unknown, "1"=US, "2"=Italy, "3"=Germany, "4"=France, "all", "none" |
| in_campaign | boolean | no | Whether lead is in a campaign |
| in_list | boolean | no | Whether lead is in a list |
| is_website_visitor | boolean | no | Website visitor filter |
| organization_user_ids | array | no | Filter by assigned user IDs |
| smart_view_id | string | no | Smart view (sales flow) filter |
| distinct_contacts | boolean | no | Return distinct contacts |
| queries | array | no | Advanced query filters |
| limit | integer | no | Items to return |
| starting_after | string | no | Cursor for pagination (use `id` from last lead) |

**Request Body — POST `/leads/move` (Move leads):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| to_campaign_id | string | no | Destination campaign ID |
| to_list_id | string | no | Destination list ID |
| campaign | string | no | Source campaign filter |
| list_id | string | no | Source list filter |
| ids | array | no | Specific lead IDs (must also provide `campaign` or `list_id`) |
| contacts | array | no | Array of emails to match |
| excluded_ids | array | no | Lead IDs to exclude |
| filter | string | no | Filter criteria |
| search | string | no | Search string |
| esg_code | string | no | Enum: "0"-"4", "all", "none" |
| esp_code | number | no | Enum: 0=Unknown, 1=Google, 2=Microsoft, 3=Yahoo, 8=Zoho, 9=GoDaddy, 10=Rackspace, 12=Web.de, 13=Libero.it, 999=Custom, 1000=Other |
| in_campaign | boolean | no | Whether in campaign |
| in_list | boolean | no | Whether in list |
| assigned_to | string | no | Reassign to this user |
| copy_leads | boolean | no | Copy instead of move |
| check_duplicates | boolean | no | Check for duplicates |
| check_duplicates_in_campaigns | boolean | no | Check dupes in campaigns |
| reset_interest_status | boolean | no | Reset interest status on move/copy |
| skip_leads_in_verification | boolean | no | Skip leads being verified |
| limit | number | no | Max leads to move |
| queries | array | no | Advanced filters |

**Request Body — POST `/leads/bulk-assign`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| organization_user_ids | array | **yes** | User IDs to assign leads to |
| campaign | string | no | Campaign filter |
| list_id | string | no | List filter |
| ids | array | no | Specific lead IDs |
| filter | string | no | Enum: FILTER_VAL_CONTACTED, FILTER_VAL_NOT_CONTACTED, FILTER_VAL_COMPLETED, FILTER_VAL_UNSUBSCRIBED, FILTER_VAL_ACTIVE, FILTER_LEAD_INTERESTED, FILTER_LEAD_NOT_INTERESTED, FILTER_LEAD_MEETING_BOOKED, FILTER_LEAD_MEETING_COMPLETED, FILTER_LEAD_CLOSED, FILTER_LEAD_OUT_OF_OFFICE, FILTER_LEAD_WRONG_PERSON, FILTER_LEAD_LOST, FILTER_LEAD_NO_SHOW, FILTER_LEAD_CUSTOM_LABEL_POSITIVE, FILTER_LEAD_CUSTOM_LABEL_NEGATIVE, FILTER_VAL_BOUNCED, FILTER_VAL_SKIPPED, FILTER_VAL_RISKY, FILTER_VAL_INVALID, FILTER_VAL_VALID, FILTER_VAL_IN_SUBSEQUENCE, FILTER_VAL_OPENED_NO_REPLY, FILTER_VAL_COMPLETED_NO_REPLY, FILTER_VAL_NO_OPENS, FILTER_VAL_REPLIED, FILTER_VAL_LINK_CLICKED |
| search | string | no | Search string |
| smart_view_id | string | no | Smart view filter |
| in_campaign | boolean | no | Whether in campaign |
| in_list | boolean | no | Whether in list |
| limit | integer | no | Max leads |
| queries | array | no | Advanced filters |

**Request Body — POST `/leads/update-interest-status`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_email | string | **yes** | Email of the lead |
| interest_value | number/null | **yes** | Interest status value, or `null` to reset to "Lead" |
| campaign_id | string | no | Campaign context |
| list_id | string | no | List context |
| ai_interest_value | number | no | AI interest score to set |
| disable_auto_interest | boolean | no | Disable auto interest detection |

**Request Body — POST `/leads/merge`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | string | **yes** | Lead to merge (source) |
| destination_lead_id | string | **yes** | Lead to merge into (target) |

**Request Body — POST `/leads/subsequence/move`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | **yes** | Lead ID |
| subsequence_id | string | **yes** | Target subsequence ID |

**Request Body — POST `/leads/subsequence/remove`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | **yes** | Lead ID to remove from subsequence |

**Request Body — PATCH `/leads/{id}` (Update):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| first_name | string/null | no | |
| last_name | string/null | no | |
| company_name | string/null | no | |
| website | string/null | no | |
| phone | string/null | no | |
| personalization | string/null | no | |
| assigned_to | string/null | no | |
| lt_interest_status | number | no | Same enum as create |
| pl_value_lead | string/null | no | |
| custom_variables | object | no | Flat key:value metadata |

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
| POST | `/accounts/{email}/resume` | Resume a paused account |
| POST | `/accounts/{email}/mark-fixed` | Mark an account as fixed |
| POST | `/accounts/move` | Move accounts between workspaces |
| GET | `/accounts/ctd/status` | Get custom tracking domain status |
| POST | `/accounts/warmup/enable` | Enable warmup (batch — list of emails) |
| POST | `/accounts/warmup/disable` | Disable warmup (batch — returns background job) |

**Account Schema (27 fields):**

| Field | Type | Notes |
|-------|------|-------|
| email | string (email) | **required**, used as identifier |
| first_name | string | **required** |
| last_name | string | **required** |
| organization | uuid | read-only. Workspace ID |
| provider_code | number | **required (read-only after creation)**. 1=Custom IMAP/SMTP, 2=Google, 3=Microsoft, 4=AWS, 8=Other |
| status | number | **read-only**. 1=Active, 2=Paused, 3=Unknown, -1=Connection Error, -2=Soft Bounce Error, -3=Sending Error |
| warmup_status | number | **read-only**. 0=Paused, 1=Active, -1=Banned, -2=Spam Folder Unknown, -3=Permanent Suspension |
| warmup | object | Warmup config: limit, advanced settings, warmup_custom_ftag, increment ("disabled" or config), reply_rate |
| daily_limit | number | Daily email sending limit |
| sending_gap | number | Minutes between emails from this account (min wait time with multiple accounts) |
| enable_slow_ramp | boolean | Gradually increase sending limits |
| tracking_domain_name | string | Custom tracking domain |
| tracking_domain_status | string | Tracking domain status |
| signature | string | Email signature |
| setup_pending | boolean | read-only |
| is_managed_account | boolean | read-only |
| inbox_placement_test_limit | number | |
| stat_warmup_score | number | read-only, e.g. 85 |
| warmup_pool_id | uuid | read-only |
| status_message | object | read-only. Error details: code, command, response, e_message, responseCode |
| added_by | uuid | read-only. User ID who added the account |
| modified_by | uuid | read-only. User ID who last modified |
| dfy_password_changed | boolean | read-only. Whether DFY password has been changed |
| timestamp_created | datetime | read-only |
| timestamp_updated | datetime | read-only |
| timestamp_last_used | datetime | read-only |
| timestamp_warmup_start | datetime | read-only |

**Request Body — POST `/accounts` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | **yes** | Email address |
| first_name | string | **yes** | |
| last_name | string | **yes** | |
| provider_code | number | **yes** | Enum: 1=Custom IMAP/SMTP, 2=Google, 3=Microsoft, 4=AWS, 8=Other |
| imap_host | string | **yes** | IMAP server hostname |
| imap_port | number | **yes** | IMAP port |
| imap_username | string | **yes** | IMAP login |
| imap_password | string | **yes** | IMAP password |
| smtp_host | string | **yes** | SMTP server hostname |
| smtp_port | number | **yes** | SMTP port |
| smtp_username | string | **yes** | SMTP login |
| smtp_password | string | **yes** | SMTP password |
| daily_limit | number/null | no | Daily send limit |
| sending_gap | number | no | Minutes between emails |
| enable_slow_ramp | boolean/null | no | Gradually increase limits |
| signature | string/null | no | Email signature |
| tracking_domain_name | string/null | no | Custom tracking domain |
| tracking_domain_status | string/null | no | Tracking domain status |
| inbox_placement_test_limit | number/null | no | Inbox placement test limit |
| reply_to | string | no | Reply-to address |
| warmup | object | no | Warmup config |
| warmup_custom_ftag | string | no | Custom warmup tag |
| skip_cname_check | boolean | no | Skip CNAME verification |

**Request Body — PATCH `/accounts/{email}` (Update):** Same fields as create minus `email`, `provider_code`, `imap_*`, `smtp_*`. Adds `remove_tracking_domain` (boolean).

**Request Body — POST `/accounts/move`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| emails | array | **yes** | Email addresses to move |
| source_workspace_id | string | **yes** | Source workspace ID |
| destination_workspace_id | string | **yes** | Destination workspace ID |

**Request Body — POST `/accounts/warmup/enable`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| emails | array | no | Specific emails to enable warmup for |
| include_all_emails | boolean | no | Enable warmup for all accounts |
| excluded_emails | array | no | Emails to exclude (when `include_all_emails` is true) |
| filter | object/null | no | Filter (tag_id etc.) when `include_all_emails` is true |
| search | string | no | Search filter when `include_all_emails` is true |

**Request Body — POST `/accounts/warmup/disable`:** Same fields as warmup/enable.

**Request Body — POST `/accounts/warmup-analytics`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| emails | array | **yes** | Account emails to get warmup analytics for |

**Request Body — POST `/accounts/test/vitals`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| accounts | array | no | Accounts to test |

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
| GET | `/lead-lists/{id}/verification-stats` | Get verification statistics for a lead list |

**Lead List Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| name | string | required |
| organization_id | uuid | read-only |
| has_enrichment_task | boolean | Auto-enrich new leads added to list |
| owned_by | uuid | Defaults to creator |

**Request Body — POST `/lead-lists` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | **yes** | List name |
| has_enrichment_task | boolean/null | no | Auto-enrich new leads added to this list |
| owned_by | string/null | no | Owner user ID (defaults to creator) |

**Request Body — PATCH `/lead-lists/{id}` (Update):** Same fields, all optional.

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
| POST | `/lead-labels/ai-reply-label` | Test AI reply label prediction |

**Lead Label Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| label | string | e.g. "Hot Lead" |
| interest_status_label | string | positive / negative / neutral |
| interest_status | number | read-only, auto-generated |
| description | string | Purpose of the label |
| use_with_ai | boolean | Whether AI features should use this label |

**Request Body — POST `/lead-labels` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| label | string | **yes** | Display label, e.g. "Hot Lead" |
| interest_status_label | string | **yes** | Enum: "positive", "negative", "neutral" |
| description | string/null | no | Purpose of the label |
| use_with_ai | boolean/null | no | Whether AI should use this label |

**Request Body — PATCH `/lead-labels/{id}` (Update):** Same fields, all optional.

**Request Body — POST `/lead-labels/ai-reply-label`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reply_text | string | **yes** | Reply text to classify |

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
| conditions | object | **required**. Trigger conditions (see below) |
| conditions.crm_status | array of numbers | 0=Out of Office, 1=Interested, 2=Meeting Booked, 3=Meeting Completed, 4=Won, -1=Not Interested, -2=Wrong Person, -3=Lost, -4=No Show |
| conditions.lead_activity | array of numbers | 2=Email Opened, 4=Link Clicked, 91=Campaign Completed Without Reply |
| conditions.reply_contains | string | Keyword match in reply text |
| subsequence_schedule | object | **required**. Same structure as campaign_schedule |
| sequences | array | **required**. Same as campaign — only first element used, steps array inside |
| workspace | uuid | read-only. Workspace ID |
| timestamp_created | datetime | read-only |
| timestamp_leads_updated | datetime | read-only. When leads were last updated |

**Request Body — POST `/subsequences` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| parent_campaign | string | **yes** | Parent campaign ID |
| name | string | **yes** | Subsequence name |
| conditions | object | **yes** | Trigger conditions (crm_status, lead_activity, reply_contains) |
| subsequence_schedule | object | **yes** | Same structure as campaign_schedule |
| sequences | array | **yes** | Email copy — only first element used, steps array inside |

**Request Body — PATCH `/subsequences/{id}` (Update):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | no | Updated name |

**Request Body — POST `/subsequences/{id}/duplicate`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | **yes** | Name for the duplicate |
| parent_campaign | string | **yes** | Campaign to duplicate into |

---

### 8. Email (Unibox)

Emails visible in the Unibox — campaign sends, replies, manual sends.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/emails` | List emails (filters: campaign, lead, account, etc.) |
| GET | `/emails/{id}` | Get single email |
| PATCH | `/emails/{id}` | Update email |
| DELETE | `/emails/{id}` | Delete email |
| POST | `/emails/reply` | Reply to an email (set reply_to_uuid) |
| POST | `/emails/forward` | Forward an email |
| POST | `/emails/threads/{thread_id}/mark-as-read` | Mark all emails in a thread as read |
| GET | `/emails/unread/count` | Count unread emails |

**Email Schema (34 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| timestamp_email | datetime | **required (read-only)**. Actual email timestamp from mail server |
| timestamp_created | datetime | read-only. When added to Instantly DB (NOT the email timestamp) |
| message_id | string | **required (read-only)**. Unique email ID from mail server |
| subject | string | **required** |
| body | object | read-only. { text: string, html: string } |
| from_address_email | email | read-only, derived from eaccount |
| from_address_json | array | From address details |
| to_address_email_list | string | **required**. Comma-separated recipient emails |
| to_address_json | array | To address details |
| cc_address_email_list | string | Comma-separated CC |
| cc_address_json | array | CC address details |
| bcc_address_email_list | string | Comma-separated BCC |
| reply_to | string | Reply-to email address |
| eaccount | string | **required**. Sending account identifier (must be validated) |
| organization_id | uuid | **required (read-only)**. Workspace ID |
| campaign_id | uuid | null for manual sends |
| subsequence_id | uuid | null for non-subsequence emails |
| list_id | uuid | If lead is part of a list |
| lead | string | Lead email address |
| lead_id | uuid | |
| ue_type | number | 1=Sent from campaign, 2=Received, 3=Sent (manual), 4=Scheduled |
| step | string | Campaign step ID |
| is_unread | number | 0/1 |
| is_auto_reply | number | read-only. 0/1 |
| ai_interest_value | number | AI-scored interest (0.0–1.0) |
| ai_assisted | number | 0/1, whether AI assistance was used |
| is_focused | number | 0/1 (primary tab in Unibox) |
| i_status | number | Interest status |
| thread_id | uuid | Groups emails in same thread |
| content_preview | string | First few lines of email body |
| attachment_json | object | read-only. { files: [{ filename, size, type, url }] }. null when no attachments. |
| reminder_ts | datetime | Timestamp for follow-up reminder |
| ai_agent_id | uuid | If sent by AI agent |

**Request Body — POST `/emails/reply`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reply_to_uuid | string | **yes** | ID of the email to reply to |
| eaccount | string | **yes** | Sending account email (must be connected) |
| subject | string | **yes** | Subject line |
| body | object | **yes** | `{ html: string, text: string }` — specify either or both |
| cc_address_email_list | string | no | Comma-separated CC |
| bcc_address_email_list | string | no | Comma-separated BCC |
| assigned_to | string | no | User ID to assign lead to |
| reminder_ts | string | no | Reminder timestamp (shows in Unibox) |

**Request Body — POST `/emails/forward`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reply_to_uuid | string | **yes** | ID of the email to forward |
| eaccount | string | **yes** | Sending account email |
| subject | string | **yes** | Subject line |
| body | object | **yes** | `{ html: string, text: string }` |
| to_address_email_list | string | **yes** | Comma-separated recipients |
| cc_address_email_list | string | no | Comma-separated CC |
| bcc_address_email_list | string | no | Comma-separated BCC |
| assigned_to | string | no | User ID to assign lead to |

**Request Body — PATCH `/emails/{id}` (Update):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| is_unread | number/null | no | 0=read, 1=unread |
| reminder_ts | string/null | no | Reminder timestamp (null to remove) |

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

**Request Body — POST `/email-verification`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | **yes** | Email address to verify |
| webhook_url | string | no | Webhook URL for async results (if verification takes >10s) |

---

### 10. Inbox Placement Test

Test deliverability across ESPs and geographies.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/inbox-placement-tests` | Create test |
| GET | `/inbox-placement-tests` | List tests |
| GET | `/inbox-placement-tests/{id}` | Get single test |
| PATCH | `/inbox-placement-tests/{id}` | Update test |
| DELETE | `/inbox-placement-tests/{id}` | Delete test |
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

**Request Body — POST `/inbox-placement-tests` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | **yes** | Test name |
| type | number | **yes** | Enum: 1=One-time, 2=Automated |
| sending_method | number | **yes** | Enum: 1=From Instantly, 2=From outside |
| email_subject | string | **yes** | Test email subject |
| email_body | string | **yes** | Test email body |
| emails | array | **yes** | Sending account emails |
| recipients_labels | array | no | ESP + type + geo for recipients (get options via ESP options endpoint) |
| delivery_mode | number/null | no | Enum: 1=One by one, 2=All together |
| schedule | object | no | For automated: days, timing, timezone |
| campaign_id | string/null | no | Link to campaign |
| test_code | string/null | no | ID for tests from outside Instantly |
| text_only | boolean/null | no | Disables open tracking |
| tags | array/null | no | Account tag filters |
| automations | array/null | no | Trigger automations on conditions |
| status | number/null | no | Enum: 1=Active, 2=Paused, 3=Completed |
| not_sending_status | string/null | no | Enum: "daily_limits_hit", "other" |
| run_immediately | boolean | no | Run test immediately + on schedule |
| description | string/null | no | Test description |
| timestamp_next_run | string/null | no | Next automated run |

**Request Body — PATCH `/inbox-placement-tests/{id}` (Update):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | no | Test name |
| schedule | object | no | Schedule config |
| status | number/null | no | Enum: 1=Active, 2=Paused, 3=Completed |
| automations | array/null | no | Trigger automations |

---

### 11. Inbox Placement Analytics

Per-email deliverability results from placement tests.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inbox-placement-analytics` | List analytics for a test |
| GET | `/inbox-placement-analytics/{id}` | Get single analytics record |
| POST | `/inbox-placement-analytics/deliverability-insights` | Retrieve deliverability insights |
| POST | `/inbox-placement-analytics/stats-by-date` | Get stats aggregated by date |
| POST | `/inbox-placement-analytics/stats-by-test-id` | Get stats aggregated by test ID |

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

**Request Body — POST `/inbox-placement-analytics/deliverability-insights`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| test_id | string | **yes** | Test ID |
| date_from | string | no | Start date filter |
| date_to | string | no | End date filter |
| previous_date_from | string | no | Comparison start date |
| previous_date_to | string | no | Comparison end date |
| show_previous | boolean | no | Show comparison data |
| recipient_esp | array | no | Filter by recipient ESP |
| recipient_geo | array | no | Filter by recipient geo |
| recipient_type | array | no | Filter by recipient type |

**Request Body — POST `/inbox-placement-analytics/stats-by-date`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| test_id | string | **yes** | Test ID |
| date_from | string | no | Start date |
| date_to | string | no | End date |
| sender_email | string | no | Filter by sender |
| recipient_esp | array | no | Filter by ESP |
| recipient_geo | array | no | Filter by geo |
| recipient_type | array | no | Filter by type |

**Request Body — POST `/inbox-placement-analytics/stats-by-test-id`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| test_ids | array | **yes** | Test IDs to aggregate |
| date_from | string | no | Start date |
| date_to | string | no | End date |
| sender_email | string | no | Filter by sender |
| recipient_esp | array | no | Filter by ESP |
| recipient_geo | array | no | Filter by geo |
| recipient_type | array | no | Filter by type |

---

### 12. Inbox Placement Blacklist & SpamAssassin Report

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inbox-placement-reports` | List blacklist + SpamAssassin reports for a test |
| GET | `/inbox-placement-reports/{id}` | Get single report |

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

**Webhook Event Types (19):**
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
- `lead_interested`
- `lead_not_interested`
- `lead_meeting_booked`
- `lead_meeting_completed`
- `lead_closed`
- `lead_out_of_office`
- `lead_wrong_person`
- `lead_no_show`
- `supersearch_enrichment_completed`

**Webhook Schema:**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | |
| target_hook_url | string (uri) | Must start with http(s):// |
| event_type | string | One of the 19 event types above, or null for custom label events |
| campaign | uuid | Optional — filter to specific campaign (null = all campaigns) |
| name | string | e.g. "Zapier Positive Replies" |
| custom_interest_value | number | For custom label events, matches LeadLabel.interest_status |
| headers | object | Custom HTTP headers sent with payload (key-value pairs, e.g. auth) |
| organization | uuid | read-only. Workspace ID |
| status | number | read-only. 1=Active, -1=Error (disabled due to delivery failures) |
| timestamp_created | datetime | read-only |
| timestamp_error | datetime | read-only. When disabled due to delivery failures (null if active) |

**Request Body — POST `/webhooks` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target_hook_url | string | **yes** | URL to send payloads (must start with http(s)://) |
| event_type | string/null | no | One of 19 event types (null for custom label events). "all_events" subscribes to everything |
| campaign | string/null | no | Campaign filter (null = all campaigns) |
| name | string/null | no | Webhook name |
| custom_interest_value | number/null | no | For custom label events, matches LeadLabel.interest_status |
| headers | object/null | no | Custom HTTP headers (key-value pairs, e.g. auth tokens) |

**Request Body — PATCH `/webhooks/{id}` (Update):** Same fields, all optional (including `target_hook_url`).

---

### 14. Webhook Event

Delivery log for webhook payloads.

**Webhook Event Schema (16 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| organization_id | uuid | read-only. Workspace ID |
| success | boolean | read-only. Whether delivery succeeded |
| retry_count | number | read-only. Number of retry attempts |
| will_retry | boolean | read-only. Whether the webhook will be retried |
| webhook_url | string | read-only. Target URL |
| payload | object | read-only. JSON payload sent/attempted |
| status_code | number | read-only. HTTP response code from endpoint |
| error_message | string | read-only. e.g. "Connection timeout" |
| timestamp_created | datetime | read-only |
| timestamp_created_date | date | read-only. For partitioning |
| timestamp_next_retry | datetime | read-only. Next retry attempt |
| retry_group_id | uuid | read-only. Groups retry attempts |
| retry_successful | boolean | read-only. Whether a retry succeeded |
| lead_email | string | read-only. Associated lead |
| response_time_ms | number | read-only. Response time in ms |

---

### 15. Block List Entry

Blocked emails and domains.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/block-lists-entries` | Create block list entry |
| GET | `/block-lists-entries` | List entries |
| GET | `/block-lists-entries/{id}` | Get single entry |
| PATCH | `/block-lists-entries/{id}` | Update block list entry |
| DELETE | `/block-lists-entries/{id}` | Delete entry |

**Block List Entry Schema (5 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| bl_value | string | **required**. The email or domain to block |
| is_domain | boolean | read-only. Auto-detected — true if bl_value is a domain |
| organization_id | uuid | read-only |
| timestamp_created | datetime | read-only |

**Request Body — POST `/block-lists-entries` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bl_value | string | **yes** | Email or domain to block |

**Request Body — PATCH `/block-lists-entries/{id}` (Update):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bl_value | string | no | Updated email or domain |

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
| POST | `/custom-tags/toggle-resource` | Assign or unassign tags to resources |

**Request Body — POST `/custom-tags` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| label | string | **yes** | Tag display label |
| description | string/null | no | Tag description |

**Request Body — PATCH `/custom-tags/{id}` (Update):** Same fields, all optional.

**Request Body — POST `/custom-tags/toggle-resource`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| tag_ids | array | **yes** | Tag IDs to assign/unassign |
| resource_ids | array | **yes** | Account or campaign IDs |
| resource_type | number | **yes** | Enum: 1=Account, 2=Campaign |
| assign | boolean | **yes** | true=assign, false=unassign |
| selected_all | boolean | no | Select all resources |
| filter | object | no | Filter when `selected_all` is true |

---

### 17. Custom Tag Mapping

Associates tags with accounts/campaigns.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/custom-tag-mappings` | List mappings |

---

### 18. Audit Log

Track system activities and API usage.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit-logs` | List audit logs (filter by activity_type, search, date range) |

**Activity Types:** 1=User login, 2=Lead deletion, 3=Campaign deletion, 4=Campaign launch, 5=Campaign pause, 6=Account addition, 7=Account deletion, 8=Lead moved, 9=Lead added, 10=Lead merged, 11=Lead exported, 12=Campaign created, 18=Webhook created, 19=Webhook deleted, 20=Subsequence created, 21=Subsequence deleted

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
| model_version | string | "3.5", "gpt-5", "gpt-5-mini", "gpt-5-nano", "4.0", "4.0-Omni", "gpt-4o", "o3", "gpt-4.1", "gpt-4.1-mini", "claude-3.7-sonnet", "claude-3.5-sonnet", "claude-4.5-sonnet", "r1", "grok-4", "gemini-2.0-flash", "gemini-3.0-flash", "gemini-3.0-pro", "instantly-ai-lightspeed-agent", "sonar", "sonar-pro" |
| properties | array | Variable definitions |
| template_type | string | "custom" / "public" |
| like_count | number | read-only |
| execution_count | number | read-only |

**Request Body — POST `/custom-prompt-templates` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | no | Template name |
| category | number | no | Enum: 1=Copywriting, 2=Cleaning, 3=Sales, 4=Marketing, 5=Other, 6=Personalization |
| prompt | string | no | Template with `{{property_1}}` variables |
| model_version | string | no | See full enum in schema above |
| properties | array | no | Variable definitions |
| is_public | boolean | no | |
| template_type | string | no | "custom" or "public" |

**Request Body — PATCH `/custom-prompt-templates/{id}` (Update):** Same fields.

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

Async operations (e.g., disabling warmup, importing/exporting leads, moving leads).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/background-jobs` | List background jobs |
| GET | `/background-jobs/{id}` | Get job status |

**Background Job Schema (11 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | string | read-only |
| workspace_id | uuid | read-only |
| type | string | "move-leads", "import-leads", "export-leads", "update-warmup-accounts", "rename-variable" |
| entity_type | string | "list", "campaign", or "workspace" |
| entity_id | uuid | Related entity ID |
| status | string | "pending", "in-progress", "success", "failed" |
| progress | number | 0–100 percentage |
| data | object | Additional job-specific data |
| user_id | uuid | read-only. User who triggered the job |
| created_at | datetime | |
| updated_at | datetime | |

---

### 24. API Key

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api-keys` | Create API key (with scopes) |
| GET | `/api-keys` | List API keys |
| DELETE | `/api-keys/{id}` | Delete API key |

**API Key Schema:** id, name, scopes (array of scope strings), key (read-only, shown once), organization_id.

**Request Body — POST `/api-keys` (Create):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | **yes** | API key name |
| scopes | array | **yes** | Array of scope strings (e.g. "campaigns:create", "leads:all") |

---

### 25. Workspace

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/current` | Get current workspace |
| PATCH | `/workspaces/current` | Update current workspace |
| POST | `/workspaces/current/change-owner` | Change workspace owner |
| POST | `/workspaces/current/whitelabel-domain` | Set agency domain for workspace |
| GET | `/workspaces/current/whitelabel-domain` | Get verified agency domain info |
| DELETE | `/workspaces/current/whitelabel-domain` | Delete agency domain |

**Workspace Schema (15 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| name | string | **required** |
| owner | uuid | read-only. User ID of workspace owner |
| org_logo_url | string | Workspace logo URL |
| org_client_domain | string | read-only. White-label agency domain |
| add_unsub_to_block | boolean | Whether to add unsubscribes to block list |
| default_opportunity_value | number | Default value for opportunities |
| plan_id | string | read-only. Subscription plan ID |
| plan_id_crm | string | read-only. CRM plan ID |
| plan_id_inbox_placement | string | read-only. Inbox placement plan ID |
| plan_id_leadfinder | string | read-only. Lead finder plan ID |
| plan_id_verification | object | read-only. Verification plan ID |
| plan_id_website_visitor | string | read-only. Website visitor plan ID |
| timestamp_created | datetime | read-only |
| timestamp_updated | datetime | read-only |

**Request Body — PATCH `/workspaces/current` (Update):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | no | Workspace name |
| org_logo_url | string/null | no | Logo URL |

**Request Body — POST `/workspaces/current/change-owner`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | **yes** | New owner email |
| sec | string | **yes** | Security token |

**Request Body — POST `/workspaces/current/whitelabel-domain`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| domain | string | **yes** | Agency domain to set |

---

### 26. Workspace Member

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspace-members` | List workspace members |
| GET | `/workspace-members/{id}` | Get single workspace member |
| POST | `/workspace-members` | Invite workspace member |
| PATCH | `/workspace-members/{id}` | Update member role |
| DELETE | `/workspace-members/{id}` | Remove member |

**Workspace Member Schema (11 fields):**

| Field | Type | Notes |
|-------|------|-------|
| id | uuid | read-only |
| email | string (email) | **required**. Member email |
| user_id | uuid | read-only |
| user_email | string (email) | User's actual email |
| name | object | read-only. Name details |
| role | string | "owner", "admin", "editor", "view", "client". Note: "owner" cannot be created via API — only assigned to workspace creator |
| permissions | array | Restrict access to certain sections |
| accepted | boolean | read-only. Whether invitation was accepted |
| issuer_id | uuid | read-only. User who added this member |
| workspace_id | uuid | read-only |
| timestamp_created | datetime | read-only |

**Request Body — POST `/workspace-members` (Invite):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | **yes** | Member email |
| role | string | **yes** | Enum: "owner", "admin", "editor", "view", "client". Note: "owner" cannot be assigned via API |
| permissions | array/null | no | Restrict access to sections |
| user_email | string/null | no | User's actual email |

**Request Body — PATCH `/workspace-members/{id}` (Update):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role | string | no | Enum: "owner", "admin", "editor", "view", "client" |

---

### 27. Workspace Group Member

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspace-group-members` | List group members |
| GET | `/workspace-group-members/{id}` | Get single group member |
| GET | `/workspace-group-members/admin` | Get current workspace admin |
| POST | `/workspace-group-members` | Add group member |
| DELETE | `/workspace-group-members/{id}` | Remove group member |

**Request Body — POST `/workspace-group-members` (Add):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sub_workspace_id | string | **yes** | Sub-workspace ID to add |

---

### 28. Account Campaign Mapping

Shows which campaigns an account is assigned to.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/account-campaign-mappings/{email}` | Get campaigns associated with an email account |

**Schema:** campaign_id, campaign_name, status, timestamp_created.

---

### 29. Webhook Event

Delivery log for webhook payloads. View delivery status, retries, and response details.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/webhook-events` | List webhook events |
| GET | `/webhook-events/{id}` | Get single webhook event |
| GET | `/webhook-events/summary` | Get overview aggregates for webhook events |
| GET | `/webhook-events/summary-by-date` | Get overview aggregates by date |

---

### 30. DFY Email Account Order

Done-For-You managed email accounts — order, manage, and check domain availability.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/dfy-email-account-orders` | Place a DFY email account order |
| GET | `/dfy-email-account-orders` | List DFY orders |
| GET | `/dfy-email-account-orders/accounts` | List DFY ordered email accounts |
| POST | `/dfy-email-account-orders/accounts/cancel` | Cancel DFY email accounts |
| POST | `/dfy-email-account-orders/domains/check` | Check domain availability |
| POST | `/dfy-email-account-orders/domains/pre-warmed-up-list` | Get pre-warmed-up domains |
| POST | `/dfy-email-account-orders/domains/similar` | Generate similar available domains |

**Request Body — POST `/dfy-email-account-orders` (Place order):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| items | array | **yes** | Domains and accounts to order |
| order_type | string | **yes** | Enum: "dfy", "pre_warmed_up", "extra_accounts" |
| simulation | boolean | no | If true, simulates order — card NOT charged |

**Request Body — POST `/dfy-email-account-orders/accounts/cancel`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| accounts | array | **yes** | Emails to cancel DFY accounts for |

**Request Body — POST `/dfy-email-account-orders/domains/check`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| domains | array | **yes** | Domains to check availability |

**Request Body — POST `/dfy-email-account-orders/domains/pre-warmed-up-list`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| extensions | array | no | Domain extensions to filter (e.g. [".com", ".org"]) |
| search | string | no | Partial or full domain name search |

**Request Body — POST `/dfy-email-account-orders/domains/similar`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| domain | string | **yes** | Base domain for suggestions |
| tlds | array | no | Extensions to use (default: .com and .org) |

---

### 31. SuperSearch Enrichment

Lead discovery and enrichment from Instantly's SuperSearch database.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/supersearch-enrichment` | Create an enrichment |
| POST | `/supersearch-enrichment/ai` | Create AI enrichment |
| GET | `/supersearch-enrichment/ai/{resource_id}/in-progress` | Get AI enrichment status for resource |
| POST | `/supersearch-enrichment/count-leads-from-supersearch` | Count leads from SuperSearch |
| POST | `/supersearch-enrichment/enrich-leads-from-supersearch` | Enrich leads from SuperSearch |
| GET | `/supersearch-enrichment/history/{resource_id}` | Get enrichment history |
| POST | `/supersearch-enrichment/preview-leads-from-supersearch` | Preview leads from SuperSearch |
| POST | `/supersearch-enrichment/run` | Run enrichment for resource |
| GET | `/supersearch-enrichment/{resource_id}` | Get enrichment for resource |
| PATCH | `/supersearch-enrichment/{resource_id}/settings` | Update enrichment settings |

**Request Body — POST `/supersearch-enrichment` (Create enrichment):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| resource_id | string | **yes** | List or campaign ID |
| type | string | **yes** | Enum: "work_email_enrichment", "fully_enriched_profile", "email_verification", "joblisting", "technologies", "news", "funding", "ai_enrichment", "custom_flow" |
| filters | array | no | Filters to apply |
| limit | number | no | Max leads to enrich |
| custom_flow | array | no | Custom enrichment flow |

**Request Body — POST `/supersearch-enrichment/ai` (Create AI enrichment):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| resource_id | string | **yes** | List or campaign ID |
| resource_type | number | **yes** | Enum: 1=List, 2=Campaign |
| model_version | string | **yes** | AI model. Enum: "3.5", "4.0", "gpt-4o", "o3", "gpt-4.1", "gpt-4.1-mini", "gpt-5-mini", "gpt-5-nano", "gpt-5", "claude-3.7-sonnet", "claude-3.5-sonnet", "claude-4.5-sonnet", "r1", "grok-4", "gemini-2.0-flash", "gemini-3.0-flash", "gemini-3.0-pro", "sonar", "sonar-pro", "instantly-ai-lightspeed-agent-for-web-research", "instantly-ai-lightspeed-agent-for-email-generation" |
| output_column | string | **yes** | Column name for results |
| prompt | string | no | Custom prompt with `{{variables}}`. Only used when template_id not provided |
| template_id | number | no | Predefined prompt template ID |
| input_columns | array | no | Lead fields to use as AI input |
| limit | number | no | Max leads to enrich |
| filters | array | no | Filter conditions |
| auto_update | boolean | no | Auto-enrich new leads |
| overwrite | boolean | no | Overwrite existing values |
| skip_leads_without_email | boolean | no | Skip leads without email |
| use_instantly_account | boolean | no | Use Instantly's API keys vs. your own |
| status | number | no | Enum: 1-4 |
| show_state | boolean | no | Send enrichment state |

**Request Body — POST `/supersearch-enrichment/count-leads-from-supersearch`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| search_filters | object | **yes** | Search filters |
| show_one_lead_per_company | boolean | no | One lead per company |
| skip_owned_leads | boolean | no | Skip leads in your workspace |

**Request Body — POST `/supersearch-enrichment/enrich-leads-from-supersearch`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| search_filters | object | **yes** | Search filters |
| limit | number | **yes** | Max leads to import |
| resource_id | string | no | Existing list/campaign ID (or provide `list_name`) |
| resource_type | number | no | Enum: 1=List, 2=Campaign |
| list_name | string | no | Name for new list (if no resource_id) |
| search_name | string | no | Name of the search |
| work_email_enrichment | boolean | no | Enable work email enrichment |
| fully_enriched_profile | boolean | no | Enable LinkedIn profile enrichment |
| custom_flow | array | no | Waterfall enrichment providers |
| auto_update | boolean | no | Auto-update new leads |
| skip_rows_without_email | boolean | no | Skip leads without email |
| evergreen | object | no | Evergreen config |

**Request Body — POST `/supersearch-enrichment/preview-leads-from-supersearch`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| search_filters | object | **yes** | Search filters |
| show_one_lead_per_company | boolean | no | One lead per company |
| skip_owned_leads | boolean | no | Skip workspace leads |

**Request Body — POST `/supersearch-enrichment/run`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| resource_id | string | **yes** | List or campaign ID |
| lead_ids | array | no | Specific lead IDs (optional) |
| limit | integer | no | Max leads to enrich |

**Request Body — PATCH `/supersearch-enrichment/{resource_id}/settings`:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| auto_update | boolean | no | Auto-enrich new leads |
| is_evergreen | boolean | no | Evergreen enrichment |
| skip_rows_without_email | boolean | no | Skip leads without email |

---

### 32. OAuth

Initialize OAuth flows for connecting Google and Microsoft email accounts.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/oauth/google/init` | Initialize Google OAuth |
| POST | `/oauth/microsoft/init` | Initialize Microsoft OAuth |
| GET | `/oauth/session/status/{sessionId}` | Get OAuth session status |

---

### 33. Workspace Billing

Billing and subscription information for the workspace.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspace-billing/plan-details` | Get workspace plan details |
| GET | `/workspace-billing/subscription-details` | Get workspace subscription details |

---

## Endpoint Count Summary

| Category | Endpoints |
|----------|-----------|
| Campaign | 15 |
| Lead | 13 |
| Account | 12 |
| Analytics | 7 |
| Lead List | 6 |
| Lead Label | 6 |
| Campaign Subsequence | 9 |
| Email (Unibox) | 8 |
| Email Verification | 2 |
| Inbox Placement Test | 6 |
| Inbox Placement Analytics | 5 |
| Inbox Placement Reports | 2 |
| Webhook | 8 |
| Webhook Event | 4 |
| Block List Entry | 5 |
| Custom Tag | 6 |
| Custom Tag Mapping | 1 |
| Audit Log | 1 |
| Custom Prompt Template | 5 |
| Sales Flow | 5 |
| Email Template | 5 |
| CRM Actions | 2 |
| Background Job | 2 |
| API Key | 3 |
| Workspace | 6 |
| Workspace Member | 5 |
| Workspace Group Member | 5 |
| Account Campaign Mapping | 1 |
| DFY Email Account Order | 7 |
| SuperSearch Enrichment | 10 |
| OAuth | 3 |
| Workspace Billing | 2 |
| **TOTAL** | **~169** |

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
