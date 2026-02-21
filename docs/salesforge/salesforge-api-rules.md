# Salesforge API — Field-Level Rules Reference

**Tested:** 2026-02-19
**Base URL:** `https://api.salesforge.ai/public/v2`
**Auth:** Raw API key in `Authorization` header — NO `Bearer` prefix
**Scoping:** All data endpoints require `/workspaces/{workspaceID}/...` except `GET /workspaces`

---

## POST /sequences — Create Sequence

**Required fields:**
| Field | Type | Rules |
|-------|------|-------|
| `name` | string | Required. Duplicates allowed — no uniqueness constraint. |
| `productId` | string | Required. Must be a valid product ID. |
| `language` | string | Required. Must be one of: `american_english`, `british_english`, `dutch`, `italian`, `czech`, `hungarian`, `swedish`, `ukrainian`, `german`, `danish`, `romanian`, `french`, `russian`, `estonian`, `finnish`, `latvian`, `japanese`, `brazilian_portugese`, `norwegian`, `spanish`, `polish`, `lithuanian`. **`"en"` does NOT work.** |
| `timezone` | string | Required. Must be a valid timezone (e.g., `America/New_York`). |

**Optional fields:**
| Field | Persists? | Notes |
|-------|-----------|-------|
| `openTrackingEnabled` | Yes | Boolean. Defaults to `true`. |
| `clickTrackingEnabled` | Yes | Boolean. Defaults to `true`. |

**Auto-created:** One empty step named "Initial email" with one variant (`label="Initial email"`, `status="active"`).

**Response keys:** `id`, `workspaceId`, `productId`, `name`, `status`, `leadCount`, `contactedCount`, `openedCount`, `openedPercent`, `repliedCount`, `repliedPercent`, `repliedPositiveCount`, `repliedPositivePercent`, `bouncedCount`, `bouncedPercent`, `clickedCount`, `clickedPercent`, `completedCount`, `completedPercent`, `companyOutreachLimitCount`, `companyOutreachLimitEnabled`, `localizedOptOutEnabled`, `sequentialCompanySendingEnabled`, `openTrackingEnabled`, `clickTrackingEnabled`, `steps`, `mailboxes`

---

## DELETE /sequences/{id} — Delete Sequence

Returns **204** — sequence permanently deleted. This is the **only destructive DELETE** that works in the entire API.

---

## GET /sequences — List Sequences

**Response shape:** `{data: [...], limit, offset, total}`

**Pagination:** `limit` and `offset` params work correctly.

**Filters DO NOT WORK:**
- `status` param is accepted but **does not filter** — always returns all sequences
- `product_id` param is accepted but **does not filter**
- `search` param is accepted but **does not filter**
- `sort` / `order` params are accepted but **do not sort**

To filter by status, you must do it client-side.

---

## GET /sequences/{id} — Sequence Detail

Returns the same keys as POST response. Includes full `steps` array with variants, and `mailboxes` array.

**Fields NOT in response:** `language`, `timezone` — these are set at creation but never returned.

**Step keys:** `id`, `order`, `name`, `waitDays`, `distributionStrategy`, `variants`

**Variant keys:** `id`, `order`, `label`, `status`, `emailSubject`, `emailContent`, `distributionWeight`, `isGenerated`, `dynamicLanguageEnabled`, `overdriveEnabled`, `contactInformationSource`, `tonality`

---

## PUT /sequences/{id} — Update Sequence

| Field | Persists? | Notes |
|-------|-----------|-------|
| `name` | **Yes** | |
| `openTrackingEnabled` | **Yes** | |
| `clickTrackingEnabled` | **Yes** | |
| `language` | **No** | Returns 200 but value doesn't change |
| `timezone` | **No** | Returns 200 but value doesn't change |
| `productId` | **500 ERROR** | Crashes the API — never send this |
| `steps` | **No** | Silently ignored — use `PUT /steps` |
| `mailboxes` | **No** | Silently ignored — use `PUT /mailboxes` |

---

## PUT /sequences/{id}/steps — Update Email Content

**Replaces ALL steps.** Omitted steps will be deleted. **Minimum 1 step required** — empty array `{"steps": []}` → 400 ("steps must contain at least 1 item").

**No standalone GET** — `GET /sequences/{id}/steps` → 404. Steps are only accessible via GET on the parent sequence detail.

**PATCH not supported** — 404. Only PUT works.

**Required on each step:**
| Field | Type | Rules |
|-------|------|-------|
| `order` | integer | Position in sequence (0-indexed) |
| `name` | string | Display name |
| `waitDays` | integer | Days to wait after previous step (0 for first step) |
| `distributionStrategy` | string | `"equal"` or `"custom"`. **Required.** |

**Required on each variant:**
| Field | Type | Rules |
|-------|------|-------|
| `label` | string | **Required.** Display name. |
| `status` | string | **Required.** `"active"` or `"paused"`. |
| `distributionWeight` | integer | Weight (usually 100 for single variant). |
| `emailSubject` | string | Email subject line. |
| `emailContent` | string | HTML email body. |

**Optional on step/variant:** `id` (omit for new steps/variants — Salesforge generates IDs). Include `id` to update existing ones.

**Multi-step:** Works. Include multiple objects in the `steps` array with incrementing `order` values.

**A/B testing:** Works. Include multiple variants in one step with `distributionStrategy: "custom"` and split `distributionWeight` (e.g., 50/50).

---

## PUT /sequences/{id}/mailboxes — Assign Mailboxes

**Body:** `{"mailboxIds": ["mbox_...", ...]}`

| Input | Result |
|-------|--------|
| Valid IDs | **204** — assigns mailboxes |
| Empty array `[]` | **204** — **clears all mailbox assignments** |
| Invalid ID | **500** — server crash, not a clean error |

**Replaces all mailboxes** — this is a full replacement, not an append. Sending `["A", "B"]` then `["C"]` results in only "C" assigned.

Must use **PUT**, not POST (POST → 404). **No standalone GET** — `GET /sequences/{id}/mailboxes` → 404. See assigned mailboxes via GET sequence detail. **No DELETE** — to clear, PUT with empty array `[]`. **No PATCH** — 404.

---

## PUT /sequences/{id}/contacts — Enroll Existing Contacts

**Body:** `{"contactIds": ["lead_...", ...]}`

| Input | Result |
|-------|--------|
| Valid IDs | **204** — enrolls contacts |
| Empty array `[]` | **400** — "contactIds must contain at least 1 item" |
| Invalid ID | **204** — silently accepted (no error) |
| Duplicate enrollment | **204** — leadCount **increments again** (same contact counted twice) |
| Multiple IDs | **204** — bulk enrollment works |

Must use **PUT**, not POST (POST → 404).

---

## PUT /sequences/{id}/import-lead — Create + Enroll in One Call

**Required fields:**
| Field | Type | Rules |
|-------|------|-------|
| `firstName` | string | Required |
| `lastName` | string | Required |
| `email` | string | Required |
| `company` | string | Required |

**Optional fields:**
| Field | Persists? | Notes |
|-------|-----------|-------|
| `linkedinUrl` | Yes | **Omit the field or pass `null`** — both work. **Empty string `""` → 400** ("must be a valid linkedin url"). |
| `tags` | Yes | Array of strings. |
| `customVars` | Yes | Object of key-value pairs. All values are strings. **This is the primary way to pass dynamic data.** |
| `jobTitle` | **NO** | Accepted (204) but **does not persist** on the contact. Use `customVars` instead. |

**Notes:**
- Creates the contact AND enrolls in the sequence in one call
- One contact per call (not bulk)
- Contacts show up in sequence `leadCount` on the detail endpoint
- `/contacts/count` may return 0 for import-lead contacts — use `leadCount` from GET sequence detail instead

---

## PUT /sequences/{id}/contacts — List/Count Enrolled Contacts

**No GET /sequences/{id}/contacts** — 404. Cannot list enrolled contacts.

**GET /sequences/{id}/contacts/count** — **200** — returns `{"count": N}`. May return 0 for import-lead contacts; use sequence detail `leadCount` instead.

---

## PUT /sequences/{id}/status — Activate / Pause

**Body:** `{"status": "active"|"paused"}`

| Transition | Result |
|-----------|--------|
| `draft → active` | **Requires mailboxes.** 400 "sequence without mailboxes" if none assigned. |
| `active → paused` | **204** — always works |
| `paused → active` | **Requires mailboxes.** Same error as above if mailboxes were cleared. |
| `paused → draft` | **400** — "status must be one of [active paused]" |
| `any → completed` | **400** — cannot manually set to completed |
| `any → archived` | **400** — "archived" is not a valid status |

**PATCH not supported** — 404. Only PUT works.

**Cannot go back to draft.** Cannot manually complete a sequence. Only `active` and `paused` are valid.

---

## GET /sequences/{id}/analytics — Daily Breakdown

**Required query params:** `from_date` and `to_date` (format: `YYYY-MM-DD`). Without them → 400.

**Response shape:**
```json
{
  "days": {
    "2026-01-15": {
      "replied": 0,
      "sent": 45,
      "totalClicked": 0,
      "totalOpened": 38,
      "uniqueClicked": 0,
      "uniqueOpened": 35
    }
  },
  "stats": {
    "clicked": 0,
    "clickedPercent": 0,
    "contacted": 1578,
    "opened": 1256,
    "openedPercent": 81.92
  }
}
```

---

## GET /sequence-metrics — Workspace Aggregates

**Optional filters:** `product_id`, `sequence_ids[]` (use `sequence_ids[]=seq_xxx` for each ID)

**Response keys:** `bounced`, `bouncedPercent`, `clicked`, `clickedPercent`, `contacted`, `opened`, `openedPercent`, `replied`, `repliedPercent`, `repliedPositive`, `repliedPositivePercent`

---

## POST /contacts — Create Single Contact

**Required:** `firstName`, `lastName`, `email`

**NOT required:** `company` (accepted but can be empty string)

**Field persistence:**
| Field | Persists? | Notes |
|-------|-----------|-------|
| `firstName` | Yes | |
| `lastName` | Yes | |
| `email` | Yes | |
| `company` | Yes | Not required — defaults to empty string |
| `linkedinUrl` | Yes | |
| `tags` | Yes | Merged with auto-tag `pa-YYYYMMDD` |
| `customVars` | Yes | Object of key-value string pairs |
| `jobTitle` | **NO** | Accepted (201) but not on the contact model |
| `phone` | **NO** | Accepted (201) but not on the contact model |

**Auto-tagging:** Every contact gets a `pa-YYYYMMDD` tag automatically.

**Duplicate email:** Returns **201 with the same lead ID** — does not create a new contact. Updates firstName, lastName, company on the existing record.

**Array body → 400** — must send a single object, not an array.

---

## POST /contacts/bulk — Bulk Create

**Body:** `{"contacts": [{...}, {...}]}`

**Required on each contact:** `firstName`, `lastName`, `email`, `tags` (array, at least one tag)

**Same persistence rules as single POST** — `jobTitle` and `phone` don't persist, `customVars` and `linkedinUrl` do.

---

## Contacts — CRUD Limitations

**Contacts are CREATE + READ only.** No update, no delete.

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/contacts` | 201 | Create single contact |
| POST | `/contacts/bulk` | 201 | Create multiple contacts |
| GET | `/contacts` | 200 | List contacts (paginated) |
| GET | `/contacts/{id}` | 200 | Single contact detail |
| PUT | `/contacts/{id}` | **404** | No update endpoint |
| PATCH | `/contacts/{id}` | **404** | No PATCH support |
| DELETE | `/contacts/{id}` | **404** | No delete endpoint |
| PUT | `/contacts/bulk` | **404** | No bulk update |
| DELETE | `/contacts/bulk` | **404** | No bulk delete |
| GET | `/contacts/count` | **404** | Treats "count" as a contact ID. Use `total` field from GET /contacts response instead. |

**To update a contact:** Re-POST with the same email → returns 201 with the same lead ID, updates firstName, lastName, company on the existing record. **customVars and tags cannot be updated this way** — only through a new import-lead enrollment.

---

## GET /contacts — List Contacts

**Response shape:** `{data: [...], limit, offset, total}`

**Contact object keys (only 8):** `id`, `firstName`, `lastName`, `email`, `company`, `linkedinUrl`, `tags`, `customVars`

**NO `jobTitle`, `phone`, `title`, `status`** — these fields do not exist on the Salesforge contact model.

**Filters DO NOT WORK:**
- `tags` param accepted but does not filter results
- `validation_status` param accepted but does not filter results
- `email` param accepted but does not filter results
- `search` param accepted but does not filter results
- `firstName` param accepted but does not filter results

To filter, you must paginate through all contacts and filter client-side. Use `total` field from response for workspace-level count.

---

## GET /contacts/{id} — Contact Detail

Returns the **same 8 keys** as the list endpoint. No additional fields in detail view.

---

## Mailboxes — Read-Only via API

**Mailboxes are managed through the UI only.** The API provides read access but no create, update, or delete.

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/mailboxes` | 200 | List all mailboxes (paginated) |
| GET | `/mailboxes/{id}` | 200 | Single mailbox detail |
| POST | `/mailboxes` | **404** | Cannot create mailboxes via API |
| PUT | `/mailboxes/{id}` | **404** | Cannot update (e.g., dailyEmailLimit) |
| PATCH | `/mailboxes/{id}` | **404** | No PATCH support |
| DELETE | `/mailboxes/{id}` | **404** | Cannot delete mailboxes via API |

---

## GET /mailboxes — List Mailboxes

**Response shape:** `{data: [...], limit, offset, total}`

**Mailbox keys:** `id`, `address`, `firstName`, `lastName`, `dailyEmailLimit`, `disconnectReason`, `mailboxProvider`, `signature`, `status`, `trackingDomain`

**Status filter does not work** — returns all mailboxes regardless of filter value.

---

## GET /mailboxes/{id} — Mailbox Detail

Returns the same keys as the list endpoint for a single mailbox. Includes full `signature` HTML, `disconnectReason`, and `trackingDomain`.

---

## DNC — Write-Only

**DNC is add-only.** You can add emails to the DNC list but cannot list, search, or remove them.

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/dnc/bulk` | 200 | Add emails to DNC |
| GET | `/dnc` | **404** | Cannot list DNC entries |
| GET | `/dnc/bulk` | **404** | Cannot list via bulk endpoint |
| DELETE | `/dnc/bulk` | **404** | Cannot remove from DNC |
| PUT | `/dnc/bulk` | **404** | Only POST works |

---

## POST /dnc/bulk — Add to Do Not Contact

**Body:** `{"dncs": ["email1@x.com", "email2@x.com"]}`

- Array of **strings** — objects → 400
- Empty array → 400 ("must contain at least 1 item")
- Returns: `{"created": N}`

---

## Threads — List-Only

**Threads are list-only.** No detail view, no update (can't mark read), no reply via API.

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/threads` | 200 | List all threads (paginated) |
| GET | `/threads/{id}` | **404** | No single-thread detail |
| PUT | `/threads/{id}` | **404** | Cannot mark read/unread |
| POST | `/threads/{id}/reply` | **404** | Cannot reply via API |

---

## GET /threads — Reply Threads

**Response shape:** `{data: [...], limit, offset, total}`

**Thread keys:** `id`, `contactEmail`, `contactFirstName`, `contactLastName`, `content`, `date`, `subject`, `isUnread`, `labelId`, `mailboxId`, `replyType`

**replyType values observed:** `ooo`, `lead_replied`

**reply_type filter does not work** — returns all threads regardless.

---

## Products — Read-Only

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/products` | 200 | List all products |
| GET | `/products/{id}` | 200 | Single product detail |
| PUT | `/products/{id}` | **404** | Cannot update products via API |

---

## GET /products

**Product keys:** `id`, `internalName`, `translations`

- **`name` is null** — use `internalName` for the product name
- `translations` is an array containing localized versions with: name, pain, solution, ICP, proof points, etc.
- `GET /products/{id}` returns the same data for a single product

---

## Webhooks — Create + Read Only

**Path:** `/integrations/webhooks` — NOT `/webhooks` (that returns 404)

**Webhooks cannot be updated or deleted via the API.**

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/integrations/webhooks` | 200 | List all webhooks (paginated) |
| GET | `/integrations/webhooks/{id}` | 200 | Single webhook detail |
| POST | `/integrations/webhooks` | 201 | Create new webhook |
| PUT | `/integrations/webhooks/{id}` | **404** | Cannot update webhooks |
| PATCH | `/integrations/webhooks/{id}` | **404** | No PATCH support |
| DELETE | `/integrations/webhooks/{id}` | **404** | Cannot delete webhooks |

**POST required fields:** `name` (string), `type` (string), `url` (string, valid URL)

**Valid webhook types (10):**
```
email_sent, email_opened, link_clicked, email_replied,
linkedin_replied, contact_unsubscribed, email_bounced,
positive_reply, negative_reply, label_changed
```

**`dnc_added` is NOT a valid type** — the API rejects it despite some docs listing it.

**Response:** `{id, name, url, sentCount, type}`

---

## Workspaces — Read-Only

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/workspaces` (no workspace scope) | 200 | List all workspaces |
| GET | `/workspaces/{id}` (no workspace scope) | 200 | Returns `{id, accountId, name, slug}` |
| PUT | `/workspaces/{id}` | **404** | Cannot update workspace |

The workspace root (`GET /workspaces/{id}/`) also returns workspace metadata.

---

## Universal Rules

### PATCH is never supported
The API does not support PATCH on any endpoint. Every PATCH attempt returns 404. Only GET, POST, PUT, and DELETE are used, and DELETE only works on sequences.

### HTTP method support by resource
| Resource | GET | POST | PUT | DELETE |
|----------|-----|------|-----|--------|
| Sequences | list + detail | create | update (limited) | **delete** |
| Steps | via parent | — | replace all | — |
| Mailboxes (on seq) | via parent | — | replace all | — |
| Contacts (on seq) | count only | — | enroll | — |
| import-lead | — | — | create+enroll | — |
| Status | — | — | set | — |
| Analytics | query | — | — | — |
| Sequence-metrics | query | — | — | — |
| Contacts | list + detail | create (single/bulk) | — | — |
| Mailboxes | list + detail | — | — | — |
| Threads | list only | — | — | — |
| Webhooks | list + detail | create | — | — |
| DNC | — | add (bulk) | — | — |
| Products | list + detail | — | — | — |
| Workspaces | list + detail | — | — | — |

### Filters are broken
Most list-endpoint filters **accept the parameter but do not actually filter**. Always returns the full unfiltered dataset. **You must filter client-side.**

| Endpoint | Broken filters |
|----------|---------------|
| GET /sequences | `status`, `product_id`, `search`, `sort`, `order` |
| GET /contacts | `tags`, `validation_status`, `email`, `search`, `firstName` |
| GET /mailboxes | `status` |
| GET /threads | `reply_type` |

### Fields that never persist
`jobTitle` and `phone` are accepted by contact creation endpoints (201/204) but **are not part of the contact data model**. The only way to store title/phone is via `customVars`.

### customVars is the extensibility mechanism
All key-value pairs in `customVars` persist and are returned on every GET. Use this for: job title, phone, EHR vendor, persona frame, trigger signal, bed count, or any other dynamic data.

### Duplicate behavior
- **Contacts:** Duplicate email → same lead ID returned, existing record updated (firstName, lastName, company only)
- **Sequences:** Duplicate names allowed — no constraint
- **Enrollment:** Same contact can be enrolled twice → leadCount increments (possible bug)

### Error patterns
| HTTP Code | Meaning |
|-----------|---------|
| 200/201/204 | Success |
| 400 | Validation error — check `data.validations` array for specific field errors |
| 404 | Endpoint doesn't exist or wrong HTTP method |
| 500 | Server error — often caused by invalid reference IDs (e.g., fake mailbox ID, trying to change productId) |

### No spam word / content analysis
The API provides **zero content analysis**. No spam score, no spam word detection, no content quality check. Tested with maximally spammy subject + body ("FREE OFFER!!!", "ACT NOW", "BUY NOW", "GUARANTEED") — accepted 200 with no warnings, no flagged fields, no additional response keys. No `/spam-check`, `/spam-score`, `/spam-words`, `/content-check`, or `/analyze` endpoints exist (all 404). Swagger only mentions "spam" in email validation context (spamtrap addresses), not content analysis. **Spam word checking must be built client-side** or use a third-party tool before pushing content.

### Endpoints that DO NOT EXIST
These were all tested and returned 404:
```
/settings, /billing, /users, /labels, /tags, /custom-fields,
/email-accounts, /campaigns, /templates, /contacts/validate,
/custom-variables, /webhooks (without /integrations/)
```

### What you can't change after creation
- `productId` on a sequence (500 if attempted)
- `language` on a sequence (silently ignored)
- `timezone` on a sequence (silently ignored)
- Sequence status back to `draft` (400)
- Sequence status to `completed` (400)
- Contact fields via PUT/PATCH (no update endpoint exists)
- Webhook URL/type (no update endpoint exists)
- DNC entries (no remove endpoint exists)
- Mailbox settings like dailyEmailLimit (no update endpoint exists)
