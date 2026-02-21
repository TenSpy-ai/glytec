# Instantly API & MCP — Verified Test Results

**Date:** 2026-02-21
**Test suite:** `gtm-hello-world/tests/` — 186 tests across 12 files
**Coverage:** 38 MCP tools, 5 REST endpoints, 9 ops scripts, sync pipeline, config server

---

## 1. MCP Protocol — Verified Behavior

### Authentication & Session
- MCP URL template: `https://mcp.instantly.ai/sse?api_key={api_key}`
- Protocol: JSON-RPC 2.0 over Streamable HTTP
- Response format: SSE (Server-Sent Events) — last `data:` line contains JSON-RPC result
- Session handshake: `initialize` → `notifications/initialized` → ready
- Session ID returned in `Mcp-Session-Id` response header, must be sent on subsequent requests
- Each `InstantlyMCP()` instance gets its own session (safe for parallel use)

### Critical: Argument Wrapping
**All Instantly MCP tools expect arguments nested under a `params` key:**
```json
{
  "name": "list_campaigns",
  "arguments": {
    "params": {
      "limit": 5,
      "search": "test"
    }
  }
}
```

Without the `params` wrapper, tools return string error messages instead of structured data.

### Response Shapes
MCP tool responses come as content blocks:
```json
{"result": {"content": [{"type": "text", "text": "{...json...}"}]}}
```

The `text` field contains the actual data as a JSON string. When the workspace is empty or the tool has no data to return, the text may be a plain string like `"No campaigns found"` instead of JSON.

**Type checking must accept `str`, `dict`, and `list`:**
```python
VALID_RESPONSE = (dict, list, str)
```

### Pagination
- Cursor-based: `starting_after` parameter, `next_starting_after` in response
- Response structure: `{"items": [...], "next_starting_after": "cursor_id"}`
- Key is `items` (not `data`) for most list endpoints
- Empty workspace: returns `{"items": []}` when `params` wrapper is correct, returns string when it's not

---

## 2. create_campaign — Actual MCP Schema

**The REST API schema and the MCP tool schema diverge.** The MCP `create_campaign` tool does NOT accept:
- `campaign_schedule` (not a valid parameter)
- `sequences` (not a valid parameter)

**Actual required parameters:**
| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `name` | string | YES | Campaign name |
| `subject` | string | YES | First email subject line |
| `body` | string | YES | First email body (HTML) |

**Actual optional parameters:**
| Parameter | Type | Notes |
|-----------|------|-------|
| `email_list` | array[string] | Sender account emails |
| `timing_from` | string | e.g., "08:00" |
| `timing_to` | string | e.g., "17:00" |
| `timezone` | string | e.g., "America/New_York" |
| `daily_limit` | integer | Per-account daily send limit |
| `email_gap` | integer | Minutes between sends |
| `stop_on_reply` | boolean | Stop sequence on reply |
| `sequence_steps` | integer | Number of follow-up steps |
| `step_delay_days` | array[int] | Days between steps |
| `sequence_subjects` | array[string] | Follow-up subjects |
| `sequence_bodies` | array[string] | Follow-up bodies |

**Critical constraint:** Campaign creation fails with `{"success": false, "stage": "no_accounts"}` if the workspace has zero sending accounts connected.

---

## 3. Workspace State (as of 2026-02-21)

- **Sending accounts:** 0 (none connected)
- **Campaigns:** 0
- **Leads:** 0 (after test cleanup)
- **Lead lists:** 0 (after test cleanup)
- **Emails/threads:** 0
- **Block list writes:** HTTP 403 (API plan restriction — read-only access)

---

## 4. REST API — Block List Endpoints

Base URL: `https://api.instantly.ai/api/v2`
Auth: `Bearer {api_key}` in Authorization header

| Method | Endpoint | Status | Notes |
|--------|----------|--------|-------|
| GET | `/block-lists-entries` | 200 | Works. Note hyphens not underscores |
| POST | `/block-lists-entries` | **403** | Plan restriction — write access denied |
| GET | `/block-lists-entries/{id}` | **403** | Plan restriction |
| PATCH | `/block-lists-entries/{id}` | **403** | Plan restriction |
| DELETE | `/block-lists-entries/{id}` | **403** | Plan restriction |

All block list write operations return HTTP 403. This is a plan-level restriction, not an auth error. The `ops/block_list.py` script handles this by always writing to the local `block_list` table and attempting the API call as a best-effort operation.

---

## 5. MCP Tools — Full Behavior Matrix (38 tools)

### Accounts (6 tools)
| Tool | Dry-run behavior | Live behavior | Notes |
|------|-----------------|---------------|-------|
| `list_accounts` | Always live | Returns `{"items": []}` | 0 accounts in workspace |
| `get_account` | Always live | Returns account or error | Needs valid email |
| `create_account` | Mock return | Needs IMAP/SMTP creds | Never tested live |
| `update_account` | Mock return | — | Never tested live |
| `manage_account_state` | Mock (except test_vitals) | Pause/resume/warmup | test_vitals always live |
| `delete_account` | Mock return | — | Never tested live |

### Campaigns (8 tools)
| Tool | Dry-run behavior | Live behavior | Notes |
|------|-----------------|---------------|-------|
| `create_campaign` | Mock `dry_run_{name}` | Fails: no_accounts | Needs `subject`+`body`, NOT `campaign_schedule` |
| `list_campaigns` | Always live | `{"items": []}` | `search` param accepted but doesn't filter |
| `get_campaign` | Always live | Returns campaign dict | — |
| `update_campaign` | Mock return | Untested (no campaigns) | — |
| `activate_campaign` | Mock `True` | Untested | Needs senders+leads+sequences+schedule |
| `pause_campaign` | Mock `True` | Untested | — |
| `delete_campaign` | Mock `True` | Untested | — |
| `search_campaigns_by_contact` | Always live | Returns list or str | Bug: calls `.get()` on str response |

### Leads (12 tools)
| Tool | Dry-run behavior | Live behavior | Notes |
|------|-----------------|---------------|-------|
| `list_leads` | Always live | Uses POST body, not GET | `{"items": [...]}` |
| `get_lead` | Always live | Returns lead dict | — |
| `create_lead` | Mock return | Creates lead (verified) | Doesn't require campaign |
| `update_lead` | Mock return | Updates lead (verified) | `custom_variables` REPLACES |
| `add_leads_bulk` | Mock return | Adds leads (verified) | Max 1000/call |
| `list_lead_lists` | Always live | `{"items": [...]}` | — |
| `create_lead_list` | Mock return | Creates list (verified) | — |
| `update_lead_list` | Mock return | Updates list (verified) | — |
| `get_verification_stats` | Always live | Returns stats dict | — |
| `delete_lead` | Mock return | Deletes lead (verified) | — |
| `delete_lead_list` | Mock return | Deletes list (verified) | — |
| `move_leads` | Mock return | Returns dict or error | — |

### Emails/Unibox (6 tools)
| Tool | Dry-run behavior | Live behavior | Notes |
|------|-----------------|---------------|-------|
| `list_emails` | Always live | `{"items": []}` | Empty workspace |
| `get_email` | Always live | Returns email or error | — |
| `count_unread_emails` | Always live | Returns `0` | — |
| `verify_email` | Always live | 5-45s per call | Returns verification result |
| `reply_to_email` | Mock return | SENDS REAL EMAIL | Never tested live |
| `mark_thread_as_read` | Mock return | Marks as read | — |

### Analytics (3 tools)
| Tool | Dry-run behavior | Live behavior | Notes |
|------|-----------------|---------------|-------|
| `get_campaign_analytics` | Always live | Returns aggregate dict | Optional campaign_id filter |
| `get_daily_campaign_analytics` | Always live | Returns daily breakdown | — |
| `get_warmup_analytics` | Always live | Returns warmup stats | — |

### Background Jobs (1 tool)
| Tool | Dry-run behavior | Live behavior | Notes |
|------|-----------------|---------------|-------|
| `list_background_jobs` | Always live | `{"items": []}` | — |

---

## 6. Known Bugs in mcp.py

1. **search_campaigns_by_contact** (line ~364): Calls `.get()` on result that can be a `str` when workspace is empty. Raises `AttributeError`. Test catches this with `except AttributeError`.

2. **_call_tool wrapper**: Fixed. Previously didn't wrap arguments in `params` key, causing all tools to return string errors instead of structured data.

3. **create_campaign schema**: Fixed. Previously accepted `campaign_schedule` and `sequences` parameters that the MCP tool doesn't understand. Now accepts `subject`/`body` with backward-compatible translation from legacy params.

---

## 7. DB Schema — Verified Column Names

Tables with non-obvious column names (verified by INSERT/SELECT during testing):

### clay_push_log
- `contact_first_name` (NOT `first_name`)
- `contact_last_name` (NOT `last_name`)
- `payload_json` (NOT `request_payload`)
- `pushed_at` (NOT `created_at`)
- `salesforce_sync_status` (default: 'pending')

### metric_snapshots
- `snapshot_date` — TEXT, ISO format (YYYY-MM-DD)
- `open_rate`, `reply_rate`, `bounce_rate` — REAL, stored as decimals (0.05 = 5%)
- Uses `INSERT OR REPLACE` keyed on `(campaign_id, snapshot_date)`

### email_threads
- `ue_type` — 1=sent, 2=received/reply
- `status` — 'new' → 'reviewed'/'needs_follow_up'/'handled'
- `sentiment` — set by store_reply()
- `ai_interest_value` — REAL, 0.0-1.0 from Instantly AI

### block_list
- `is_domain` — INTEGER (0=email, 1=domain)
- `instantly_id` — may be NULL if API returned 403

---

## 8. Kill Switch Thresholds

Defined in `config.py`, verified in tests:

| Threshold | Default | Used in | Notes |
|-----------|---------|---------|-------|
| `BOUNCE_RATE_LIMIT` | 0.05 (5%) | `check_kill_switches()` | ACTIVE — triggers WARNING |
| `SPAM_RATE_LIMIT` | 0.003 (0.3%) | Defined but NOT checked | Code exists but no condition |
| `UNSUBSCRIBE_RATE_LIMIT` | — | Defined but NOT checked | Code exists but no condition |
| `POSITIVE_THRESHOLD` | 0.7 | `classify_sentiment()` | AI score > 0.7 = positive |
| `NEGATIVE_THRESHOLD` | 0.3 | `classify_sentiment()` | AI score < 0.3 = negative |

---

## 9. Sentiment Classification — Decision Tree

```
Input: body_text + ai_interest_value

1. OOO keywords in body? → ("ooo", 0.95, "keyword")
2. Negative keywords in body? → ("negative", 0.90, "keyword")
3. Positive keywords in body? → ("positive", 0.85, "keyword")
4. AI score > 0.7? → ("positive", ai_score, "ai")
5. AI score < 0.3? → ("negative", 1-ai_score, "ai")
6. AI score 0.3-0.7? → ("neutral", 0.5, "ai")
7. No AI score? → ("neutral", 0.5, "ai")
```

Keywords override AI scores. OOO overrides negative which overrides positive.

---

## 10. Test Suite Summary

| Test File | Tests | What it covers |
|-----------|-------|----------------|
| test_00_db | 22 | Schema, seed data, FK integrity, WAL mode, idempotent seed |
| test_01_mcp_read | 14 | All read-only MCP tools against live Instantly |
| test_02_api_blocklist | 10 | REST API block list CRUD (handles 403 plan restriction) |
| test_03_campaign_lifecycle | 14 | Campaign CRUD lifecycle (handles no_accounts) |
| test_04_lead_management | 12 | Lead + lead list full CRUD lifecycle |
| test_05_email_tools | 10 | Email listing, verification, dry-run reply/mark-read |
| test_06_ops_scripts | 18 | All 9 ops scripts called programmatically |
| test_07_sync | 8 | Sync pipeline (5 jobs + paginate_all helper) |
| test_08_replies_clay | 19 | Sentiment classification + Clay push pipeline |
| test_09_config_server | 12 | Config server HTTP API on port 8199 |
| test_10_e2e | 17 | Full GTM flow with 17 sequential checkpoints |
| test_11_monitoring | 30 | All 7 reports, metrics, kill switches, DB persistence |
| **TOTAL** | **186** | **38 MCP tools, 5 REST endpoints, 9 ops scripts, sync, config server** |

### Running Tests

```bash
cd gtm-hello-world

# Full parallel run (4 phases)
python -m tests.run_all

# Skip e2e
python -m tests.run_all --quick

# Single file
python -m tests.run_all test_00_db

# Force sequential (debugging)
python -m tests.run_all --serial
```

---

## 11. Environment Constraints

- **No sending accounts** → Campaign creation fails. Tests skip gracefully.
- **Block list writes 403** → API plan restriction. Tests skip gracefully.
- **Empty workspace** → MCP read tools return strings instead of dicts. Tests accept both.
- **verify_email slow** → 5-45 seconds per call. Only 2 calls in test suite.
- **No pytest** → All tests use stdlib `assert` + custom `TestResult` collector.
- **Parallel safe** → 4-phase runner, unique names with `QA_TEST_` prefix + timestamps.
