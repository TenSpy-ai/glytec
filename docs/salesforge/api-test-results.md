# Salesforge API — Test Results & Working Reference

**Tested:** 2026-02-19
**API Key env var:** `SALESFORGE_API_KEY` in `.env`

## Auth

- Header: `Authorization: <raw key>` — **no `Bearer` prefix**
- Swagger says `apiKey` type in `Authorization` header
- Wrong key → `{"message":"invalid api key"}`
- Missing key → `{"message":"api key is required"}`

## URL Pattern

All data endpoints are workspace-scoped:
```
https://api.salesforge.ai/public/v2/workspaces/{workspaceID}/...
```
The only non-scoped endpoint is `GET /workspaces` (lists all workspaces).

## Account Inventory

### Workspaces (3)

| ID | Name | Status |
|----|------|--------|
| `wks_05g6m7nsyweyerpgf0wuq` | Glytec | Active (21 mailboxes, 5 sequences, 7,347 contacts) |
| `wks_0mqikf52raioytzkdsm3p` | Reagan | Empty (0 mailboxes, 0 sequences) |
| `wks_qb9pdx34orv9pfv5p4ev4` | Reagan | Empty (0 mailboxes, 0 sequences) |

### Sequences (Glytec workspace)

| ID | Name | Status | Leads | Open% | Reply% | Bounce% |
|----|------|--------|-------|-------|--------|---------|
| `6811` | Untitled sequence | draft | 0 | — | — | — |
| `seq_ja6xyz3i6edirau8ktnt4` | Salesforge_HRSA CEO Sequence_12.8.25 | completed | 336 | 96.27 | 0.62 | 1.19 |
| `seq_zf1rm3h7fegj07bjjoe01` | VA ECQM_CEO_3 Step_1.20.26 | completed | 120 | 73.91 | 0 | 4.17 |
| `seq_dg2e2vaerxei0ieg6eo39` | Quality Acronyms_Manager and Above_3-Step_1.22.26 | completed | 518 | 87.01 | 0.46 | 2.94 |
| `seq_r1lbd61yql3ev57ju7e6i` | Nursing_Manager Plus_2-Step_1.25.26 | **active** | 1,567 | 81.97 | 0.48 | 2.74 |

### Mailboxes (21, all Clayton Maike)

All set to 30 emails/day. Mix of Gmail and Outlook across 7 domains:
- `seeglytec.com`, `runglytec.com`, `joinglytec.com`, `findglytec.com`, `visitglytec.com`, `askglytec.com`
- Address patterns: `clayton@`, `clayton.m@`, `clayton.maike@`, `cmaike@`
- Several have `disconnectReason` errors (invalid credentials, connection interrupted) but `status: "active"`

### Product (1)

| ID | Name |
|----|------|
| `prod_jfxqn21476u6o3m5ocogi` | Glucommander |

Product includes full pain/solution/ICP/proof points/cost-of-inaction fields.

### Contacts: 7,347

Tagged by source batch:
- `Salesforge_HRSA CEO Sequence_12.8.25`
- `Clay Quality Pull_1.22.26`
- `Clay_Quality_1.22.26_Export for Load into Salesforge`
- `Clay_Nursing_1.26.26v2_Export for Load into Salesforge`

Custom vars on contacts: `job_title`, `job_title_level`

### Threads: 48

Mostly OOO auto-replies from the Nursing sequence. A few real replies:
- Opt-out requests
- "Not interested" responses
- Address verification confirmations

## Endpoint Reference (Tested & Verified)

### Working Endpoints

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/workspaces` | GET | Lists all workspaces. No workspace scope needed. |
| `/workspaces/{id}/sequences` | GET | Paginated. `limit`, `offset` params. |
| `/workspaces/{id}/sequences` | POST | Requires `productId`, `language` (`american_english`, not `en`), `timezone`. Creates in `draft` status with one empty step auto-generated. |
| `/workspaces/{id}/sequences/{id}` | GET | Returns full sequence with steps, variants, mailboxes, stats. |
| `/workspaces/{id}/sequences/{id}` | PUT | Updates top-level fields only: `name`, `openTrackingEnabled`, `clickTrackingEnabled`. Does **NOT** update `steps` or `mailboxes` (silently ignored). |
| `/workspaces/{id}/sequences/{id}/steps` | PUT | **Separate endpoint for email content.** Body: `{"steps": [{id, order, name, waitDays, distributionStrategy, variants: [{id, order, label, status, emailSubject, emailContent, distributionWeight}]}]}`. Required variant fields: `distributionStrategy` (equal\|custom), `label`, `status` (active\|paused). Supports multi-step creation. |
| `/workspaces/{id}/sequences/{id}/mailboxes` | PUT | Body: `{"mailboxIds": ["mbox_...", ...]}`. `mailboxIds` is a required field. POST returns 404 — must use PUT. |
| `/workspaces/{id}/sequences/{id}/contacts` | PUT | **Enroll existing contacts.** Body: `{"contactIds": ["lead_...", ...]}`. `contactIds` is required, minimum 1. Returns 204. |
| `/workspaces/{id}/sequences/{id}/import-lead` | PUT | **Create + enroll in one call.** Body: `{firstName, lastName, email, company}`. Optional: `linkedinUrl` (valid URL or **omit entirely** — empty string `""` fails validation), `tags` (array), `customVars` (object — key/value pairs persist on contact). `jobTitle` is accepted but **does not persist** (use `customVars` instead). Returns 204. Note: enrolled contacts show in sequence `leadCount` but `/contacts/count` may return 0. |
| `/workspaces/{id}/sequences/{id}/contacts/count` | GET | Returns `{"count": N}`. **Note:** May return 0 for contacts enrolled via `import-lead` — use sequence detail `leadCount` field instead for accurate count. |
| `/workspaces/{id}/sequences/{id}/status` | PUT | Body: `{"status": "active"|"paused"}`. Cannot set back to `draft`. Returns 204. |
| `/workspaces/{id}/sequences/{id}/analytics` | GET | **Requires** `from_date` and `to_date` query params (YYYY-MM-DD). Returns daily breakdown. |
| `/workspaces/{id}/sequence-metrics` | GET | Workspace-level aggregate metrics. Optional `product_id` and `sequence_ids[]` query params. Returns contacted, opened, replied, bounced counts and percents. |
| `/workspaces/{id}/mailboxes` | GET | Paginated. Returns status, provider, signature, disconnect reasons. |
| `/workspaces/{id}/contacts` | GET | Paginated. 50 per page default. Returns tags, customVars. |
| `/workspaces/{id}/contacts` | POST | Single contact only: `{firstName, lastName, email, company}`. Auto-tags with `pa-YYYYMMDD`. Returns 201 with lead ID. **Array body returns 400.** |
| `/workspaces/{id}/contacts/{id}` | GET | Returns full contact detail with tags, customVars. |
| `/workspaces/{id}/contacts/bulk` | POST | Body: `{"contacts": [{firstName, lastName, email, company, tags: [...]}]}`. **`tags` is required** on each contact. Returns 201 with array of created contacts. |
| `/workspaces/{id}/dnc/bulk` | POST | Body: `{"dncs": ["email1@x.com", "email2@x.com"]}` — array of **strings**, not objects. |
| `/workspaces/{id}/threads` | GET | Paginated. Returns subject, content preview, replyType (`ooo`, `lead_replied`), labelId. |
| `/workspaces/{id}/integrations/webhooks` | GET | Lists registered webhooks. |
| `/workspaces/{id}/integrations/webhooks` | POST | Requires `name`, `type`, `url`. |
| `/workspaces/{id}/products` | GET | Returns product with full translations (pain, solution, ICP, proof points). |

### Endpoints Not Found / Not Working

| Endpoint | Issue |
|----------|-------|
| `POST /sequences/{id}/mailboxes` | 404 — must use **PUT** not POST |
| `POST /sequences/{id}/contacts` | 404 — must use **PUT** not POST |
| `/sequences/{id}/metrics` | 404 — use `/sequence-metrics` (workspace-level) or `/sequences/{id}/analytics` instead |
| `/sequences/{id}/steps` (GET) | 404 — steps only accessible via GET on sequence detail or PUT to update |
| `/sequences/{id}/steps/{id}/variants/{id}` | 404 — no sub-resource endpoints for steps/variants; use PUT /steps with full array |
| `/webhooks` (non-scoped) | 404 — must use `/integrations/webhooks` under workspace |
| `/custom-variables` | 404 |
| `/auth` (without Bearer) | 404 — only works with `Bearer` prefix oddly, but returns "invalid api key" with Bearer |

### Sequence Lifecycle (Verified Flow)

```
1. POST /sequences                    → creates draft with 1 empty step
2. PUT  /sequences/{id}/steps         → populate email subject + content
3. PUT  /sequences/{id}/mailboxes     → assign sending mailboxes
4. PUT  /sequences/{id}/import-lead   → create + enroll contacts (one at a time, linkedinUrl optional — just omit the field)
   — OR —
   POST /contacts + PUT /sequences/{id}/contacts → bulk create then assign by ID
5. PUT  /sequences/{id}/status        → {"status": "active"} to start sending
```

## Gotchas vs Swagger Docs

1. **No `Bearer` prefix** on auth — raw key in `Authorization` header
2. **All endpoints workspace-scoped** — swagger shows flat paths but real API needs `/workspaces/{id}/` prefix
3. **Webhooks path** is `/integrations/webhooks`, not `/webhooks`
4. **DNC body** is `{"dncs": ["email"]}` — array of strings, not objects
5. **Sequence creation** auto-generates one empty "Initial email" step
6. **Analytics endpoint** requires date params or returns 422
7. **Contacts auto-tagged** with `pa-YYYYMMDD` on creation
8. **PUT sequence ignores steps/mailboxes** — these have dedicated sub-resource endpoints (`PUT /steps`, `PUT /mailboxes`)
9. **POST on sub-resources is 404** — mailboxes and contacts assignment use **PUT**, not POST
10. **Bulk contacts require tags** — `POST /contacts/bulk` requires `tags` array on each contact; single `POST /contacts` does not
11. **import-lead: linkedinUrl is optional** — **omit the field** or pass `null` and it works (204). **Empty string `""` returns 400** (validation error). `jobTitle` is accepted but doesn't persist — use `customVars` for title data instead
12. **import-lead supports customVars** — `customVars: {"key": "value"}` persists on the contact. Also supports `tags: [...]`. Useful for passing persona, EHR, signal, etc.
13. **Sequence creation language changed** — `"en"` no longer accepted; use `"american_english"`
14. **contacts/count may undercount** — `/contacts/count` returns 0 for import-lead enrolled contacts; check sequence detail `leadCount` instead
15. **Status cannot go back to draft** — only `active` ↔ `paused` transitions allowed
16. **PUT /steps replaces all steps** — sending the full steps array; omitted steps may be deleted

## Webhook Event Types

Available types for webhook registration:
- `email_sent`
- `email_opened`
- `link_clicked`
- `email_replied`
- `linkedin_replied`
- `contact_unsubscribed`
- `email_bounced`
- `positive_reply`
- `negative_reply`
- `label_changed`
- `dnc_added`

## Test Artifacts (safe to delete)

| Type | Name/ID | Notes |
|------|---------|-------|
| Sequence | `seq_dos5fqukuxnk0xniluihe` (API_Test_Sequence_DELETE_ME) | Paused, 2 steps, 2 mailboxes, ~4 test leads |
| Contact | `lead_zdn90lfd0dlnxebgt1jdj` (test.apitest.deleteme@example.com) | Fake |
| Contact | `lead_0ic2s3shaeejitgts3sew` (test3.pipeline.deleteme@example.com) | Pipeline test |
| Contact | `lead_dm21560e15283y7o9fg9k` (test5.pipeline.deleteme@example.com) | Pipeline test (bulk) |
| Contact | `lead_pym3lz11lhc5ajks4e4fm` (test4.pipeline.deleteme@example.com) | Pipeline test (bulk) |
| Contact | `lead_9t36keu644a5y15ifl2hs` (test8.pipeline.deleteme@example.com) | Pipeline test |
| Contact | `lead_iaz123s73l1790qoemn1n` (test9.pipeline.deleteme@example.com) | Pipeline test (bulk) |
| Contact | (testimport.pipeline.deleteme@example.com) | Imported via import-lead |
| Contact | (testimport4.pipeline.deleteme@example.com) | Imported via import-lead with full fields |
| Contact | (nolinkedin.pipeline.deleteme@example.com) | Imported via import-lead with placeholder LinkedIn |
| Sequence | `seq_9fcn86zyi19v3tvqucpvz` (ImportLead_Test_DELETE_ME) | Draft, 3 test leads via import-lead |
| Contact | `lead_wy8fxjv2y6ef42xkkl8ta` (nolinkedin.test.deleteme@example.com) | import-lead without linkedinUrl |
| Contact | `lead_k7qp5k355u19rg5zjzdtd` (nulllinkedin.test.deleteme@example.com) | import-lead with linkedinUrl=null |
| Contact | `lead_2xjof7c4yblsmuicbnez0` (customvar.test.deleteme@example.com) | import-lead with customVars + tags |
| Contact | `lead_9q392ahzyxxrqswr046na` (nullurl.noli.deleteme@example.com) | import-lead without linkedinUrl (draft seq) |
| Contact | `lead_xmlkkmyx2xtv1duxtuxfl` (emailonly.noli.deleteme@example.com) | import-lead email-only (draft seq) |
| Contact | `lead_myf74al42a8zzg171ze5g` (fullfields.custom.deleteme@example.com) | import-lead with all custom fields |
| DNC | `test.apitest.deleteme@example.com` | Fake email |
| Webhook | `rwh_wd7tas4vf5u0egnda9c8u` (API_Test_Webhook_DELETE_ME) | Points to example.com |
