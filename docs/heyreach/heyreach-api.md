# HeyReach API — Comprehensive Reference

Last compiled: 2026-02-19
Sources: n8n community node endpoint map, MCP server source, Make/Zapier integrations, HeyReach help center, Cotera/Clay/Cargo docs

---

## Overview

HeyReach is a LinkedIn automation platform. The API exposes campaign management, lead management, list management, inbox/conversations, LinkedIn account management, analytics, webhooks, and network queries.

**Not email.** HeyReach is purely LinkedIn automation — connection requests, messages, InMails, profile views, follows, post likes. It's the LinkedIn counterpart to email platforms like Instantly, Smartlead, or Salesforge.

---

## Auth & Base

| Property | Value |
|----------|-------|
| Base URL | `https://api.heyreach.io/api/public` |
| Auth | `X-API-KEY` header (API key from Settings → Integrations) |
| Rate limit | 300 requests/minute (429 on excess) |
| Content-Type | `application/json` (POST/PUT/PATCH) |
| Accept | `text/plain` |
| Retry policy (webhooks) | 5 retries over 24 hours on delivery failure |

---

## Pricing (affects API access)

All plans include API + webhooks access.

| Plan | Price | LinkedIn Senders | Email Credits |
|------|-------|-----------------|---------------|
| Growth | $79/seat/mo ($59 annual) | 1–10 | 100–300 |
| Agency | $999/mo ($749 annual) | 50 | 900 |
| Unlimited | $1,999/mo ($1,499 annual) | Unlimited (500 fair-use cap) | 1,500–6,000 |

All plans: unlimited campaigns, all LinkedIn actions, unified inbox, multichannel integrations, MCP server, workspaces.

---

## Full Endpoint Reference

### Authentication

| Method | Path | Body / Notes |
|--------|------|-------------|
| GET | `/auth/CheckApiKey` | No body. Returns 200 if key is valid. |

---

### Campaigns (8 endpoints)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/campaign/GetAll` | `{offset, limit}` — paginated list of all campaigns |
| GET | `/campaign/GetById?campaignId={id}` | Single campaign with full detail (steps, senders, settings) |
| POST | `/campaign/Resume` | `{campaignId}` — resume a paused campaign |
| POST | `/campaign/Pause` | `{campaignId}` — pause an active campaign |
| POST | `/campaign/AddLeadsToCampaign` | `{campaignId, accountLeadPairs[]}` — add leads with sender assignment |
| POST | `/campaign/AddLeadsToCampaignV2` | Enhanced version with improved validation |
| POST | `/campaign/StopLeadInCampaign` | `{campaignId, leadMemberId, leadUrl}` — halt all future actions for a lead |
| POST | `/campaign/GetLeadsFromCampaign` | `{campaignId, offset, limit, timeFrom, timeTo, timeFilter}` — paginated leads with status |
| POST | `/campaign/GetCampaignsForLead` | `{email?, linkedinId?, profileUrl?, offset, limit}` — reverse lookup |

**Campaign creation is UI-only.** The public API does not expose a campaign create endpoint — campaigns must be created in the HeyReach UI, then the API is used for lead enrollment, pause/resume, and monitoring.

#### Add Leads Request Body (V1)

```json
{
  "campaignId": 123456,
  "accountLeadPairs": [
    {
      "linkedInAccountId": 789,
      "lead": {
        "firstName": "Sarah",
        "lastName": "Chen",
        "profileUrl": "https://www.linkedin.com/in/sarahchen",
        "location": "Minneapolis, MN",
        "summary": "VP of Clinical Informatics",
        "companyName": "Memorial Health System",
        "position": "VP Clinical Informatics",
        "about": "20+ years in healthcare IT",
        "emailAddress": "s.chen@memorialhealth.org",
        "customUserFields": [
          {"name": "source", "value": "definitive_hc"},
          {"name": "account_tier", "value": "Priority"}
        ]
      }
    }
  ]
}
```

#### Add Leads Response

```json
{
  "addedLeadsCount": 1,
  "updatedLeadsCount": 0,
  "failedLeadsCount": 0
}
```

#### Lead Status Enum (in GetLeadsFromCampaign response)

| Status | Meaning |
|--------|---------|
| Pending | Queued, not yet processed |
| InSequence | Actively being worked through steps |
| Finished | Completed all sequence steps |
| Paused | Manually paused |
| Failed | Action failed (account issue, LinkedIn limit, etc.) |

---

### Leads (4 endpoints)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/lead/GetLead` | `{profileUrl}` — full lead profile |
| POST | `/lead/AddTags` | `{leadProfileUrl?, leadLinkedInId?, tags[], createTagIfNotExisting}` — additive |
| POST | `/lead/GetTags` | `{profileUrl}` — returns alphabetically sorted tags |
| POST | `/lead/ReplaceTags` | `{leadProfileUrl?, leadLinkedInId?, tags[], createTagIfNotExisting}` — destructive replace |

#### Lead Object (from GetLead)

```json
{
  "linkedin_id": "abc123",
  "imageUrl": "https://...",
  "firstName": "Sarah",
  "lastName": "Chen",
  "fullName": "Sarah Chen",
  "location": "Minneapolis, MN",
  "companyName": "Memorial Health System",
  "position": "VP Clinical Informatics",
  "emailAddress": "s.chen@memorialhealth.org",
  "enrichedEmailAddress": "sarah.chen@memorialhealth.org",
  "emailEnrichments": []
}
```

---

### Lists (10 endpoints)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/list/GetAll` | `{offset, limit}` — paginated list of all lists |
| GET | `/list/GetById?listId={id}` | Single list detail |
| POST | `/list/CreateEmptyList` | `{name, type}` — type: `COMPANY_LIST` or `USER_LIST` |
| POST | `/list/AddLeadsToList` | Add leads to existing list |
| POST | `/list/AddLeadsToListV2` | Enhanced version |
| DELETE | `/list/DeleteLeadsFromList` | `{listId, leadMemberIds[]}` — remove by LinkedIn IDs |
| DELETE | `/list/DeleteLeadsFromListByProfileUrl` | Remove by profile URLs |
| POST | `/list/GetLeadsFromList` | `{listId, offset, limit}` — paginated leads |
| POST | `/list/GetCompaniesFromList` | Returns companies from company-type lists |
| POST | `/list/GetListsForLead` | Reverse lookup — which lists contain this lead |

#### Create List Response

```json
{
  "id": "list_abc123",
  "name": "Priority Accounts Q1",
  "count": 0,
  "listType": "USER_LIST",
  "creationTime": "2026-02-19T10:00:00Z",
  "isDeleted": false,
  "campaigns": [],
  "search": null,
  "status": "ACTIVE"
}
```

---

### Inbox / Conversations (4 endpoints)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/inbox/GetConversations` | `{offset, limit, filters}` — up to 100 conversations |
| POST | `/inbox/GetConversationsV2` | Enhanced filtering and sorting |
| GET | `/inbox/GetChatroom?chatroomId={id}` | Single conversation detail |
| POST | `/inbox/SendMessage` | `{linkedInAccountId, recipientProfileUrl, message}` |

#### Conversation Filters

```json
{
  "offset": 0,
  "limit": 50,
  "filters": {
    "linkedInAccountIds": ["acc_123"],
    "campaignIds": ["camp_456"],
    "searchString": "glycemic",
    "seen": false
  }
}
```

---

### LinkedIn Accounts / Senders (2 endpoints)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/linkedinaccount/GetAll` | `{offset, limit}` — all connected LinkedIn accounts |
| GET | `/linkedinaccount/GetById?accountId={id}` | Single account detail |

---

### My Network (2 endpoints)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/MyNetwork/GetMyNetworkForSender` | `{pageNumber, pageSize, senderId}` — browse a sender's network |
| POST | `/MyNetwork/IsConnection` | `{senderAccountId, leadProfileUrl?, leadLinkedInId?}` — check connection status |

#### Network Profile Object

```json
{
  "linkedin_id": "abc123",
  "profileUrl": "https://www.linkedin.com/in/...",
  "firstName": "John",
  "lastName": "Smith",
  "headline": "Chief Nursing Officer at Abbott Northwestern",
  "imageUrl": "https://...",
  "location": "Minneapolis, MN",
  "companyName": "Allina Health",
  "position": "Chief Nursing Officer",
  "about": "...",
  "connections": 500,
  "followers": 1200,
  "emailAddress": "john.smith@allina.org"
}
```

---

### Stats / Analytics (1 endpoint)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/stats/GetOverallStats` | `{accountIds[], campaignIds[], startDate, endDate}` — ISO datetime, UTC |

#### Stats Response

```json
{
  "byDayStats": {
    "2026-02-18": { "profileViews": 12, "messagesSent": 5, "connectionsSent": 8, "connectionsAccepted": 3 }
  },
  "overallStats": {
    "profileViews": 120,
    "postLikes": 45,
    "follows": 30,
    "messagesSent": 89,
    "totalMessageStarted": 89,
    "totalMessageReplies": 23,
    "connectionsSent": 156,
    "connectionsAccepted": 67,
    "responseRate": 0.258,
    "connectionRate": 0.429
  }
}
```

---

### Webhooks (5 endpoints — full CRUD)

| Method | Path | Body / Notes |
|--------|------|-------------|
| POST | `/webhooks/GetAllWebhooks` | `{offset, limit}` |
| POST | `/webhooks/CreateWebhook` | `{webhookName, webhookUrl, eventType, campaignIds[], isActive}` |
| GET | `/webhooks/GetWebhookById?webhookId={id}` | Single webhook detail |
| PATCH | `/webhooks/UpdateWebhook?webhookId={id}` | Partial update — null fields retain original values |
| DELETE | `/webhooks/DeleteWebhook?webhookId={id}` | Permanently deletes webhook |

**HeyReach has full webhook CRUD** — create, read, update, delete. This is better than Salesforge (create+read only) and comparable to Instantly.

#### Webhook Event Types (11)

| Event Type | Description |
|------------|-------------|
| `CONNECTION_REQUEST_SENT` | Connection request dispatched |
| `CONNECTION_REQUEST_ACCEPTED` | Prospect accepted connection |
| `MESSAGE_SENT` | LinkedIn message sent from campaign |
| `MESSAGE_REPLY_RECEIVED` | Prospect replied to message |
| `INMAIL_SENT` | InMail dispatched |
| `INMAIL_REPLY_RECEIVED` | Prospect replied to InMail |
| `FOLLOW_SENT` | Follow action completed |
| `LIKED_POST` | Post like action completed |
| `VIEWED_PROFILE` | Profile view action completed |
| `CAMPAIGN_COMPLETED` | Campaign finished all leads |
| `LEAD_TAG_UPDATED` | Lead tag was changed |

**Cross-campaign events:** `MESSAGE_REPLY_RECEIVED` and `LEAD_TAG_UPDATED` trigger regardless of campaign (even for messages sent outside campaigns), provided tracking and conversation importing are enabled.

#### Webhook Object

```json
{
  "id": "wh_abc123",
  "webhookName": "Replies to CRM",
  "webhookUrl": "https://hooks.zapier.com/...",
  "eventType": "MESSAGE_REPLY_RECEIVED",
  "campaignIds": ["camp_456", "camp_789"],
  "isActive": true
}
```

---

## Campaign Sequence Step Types

Campaigns are built in the HeyReach UI with multi-step sequences. These are the available action types:

| Step Type | Description | Requirements |
|-----------|-------------|-------------|
| **Connection Request** | Send connection request with optional personalized message | 2nd/3rd degree connections only |
| **Message** | Send LinkedIn message | 1st degree connections only |
| **InMail** | Send InMail with subject line | Sales Navigator or Recruiter account; InMail credits for closed profiles |
| **View Profile** | View prospect's profile (triggers notification) | Any connection degree |
| **Follow** | Follow prospect | Cannot follow after sending connection request |
| **Like Post** | Like a prospect's post with configurable reaction type | Reaction types: Like, Celebrate, Support, Funny, Love, Insightful; timeframe: 24h–3mo |
| **If Connected** | Branch based on connection status | Splits into two paths (connected vs not) |

**Timing rules:**
- Minimum 3-hour delay between actions
- "If Connected" can run with no delay as first step
- A/B testing supported on Connection Request, Message, and InMail steps
- Custom variables supported: `{{firstName}}`, `{{lastName}}`, `{{companyName}}`, etc.

---

## Key API Characteristics

### What the API CAN do
- **Enroll leads into campaigns** — the primary API use case
- **Pause/resume campaigns** — operational control
- **Monitor campaign performance** — stats by date range, by campaign, by sender
- **Manage lead lists** — full CRUD including company lists
- **Send messages** — direct messaging outside of campaigns
- **Manage tags** — add, replace, get tags on leads
- **Full webhook lifecycle** — create, read, update, delete webhooks
- **Query network** — check if a lead is a connection, browse a sender's network
- **Get conversations** — filter by campaign, sender, read status

### What the API CANNOT do
- **Create campaigns** — UI only (Clay docs confirm: "new campaigns cannot be created directly")
- **Edit sequences** — steps/actions must be configured in the UI
- **Manage LinkedIn accounts** — connect/disconnect/configure accounts is UI only
- **Create/manage workspaces** — administrative operations are UI only
- **Email enrichment** — credits consumed via UI enrichment features, not API

---

## Endpoint Count Summary

| Category | Endpoints |
|----------|-----------|
| Auth | 1 |
| Campaigns | 9 |
| Leads | 4 |
| Lists | 10 |
| Inbox | 4 |
| LinkedIn Accounts | 2 |
| My Network | 2 |
| Stats | 1 |
| Webhooks | 5 |
| **Total** | **38** |

---

## Integration Ecosystem

### Native Integrations
- **Instantly** — bidirectional lead movement, cross-platform pause
- **Smartlead** — same pattern as Instantly
- **HubSpot** — CRM sync
- **Clay** — enrichment + lead push
- **RB2B** — website visitor identification
- **Trigify** — LinkedIn signal monitoring

### Automation Platforms
- **Make** — 30+ modules (campaigns, messages, senders, lists, leads, stats + webhook triggers)
- **Zapier** — 11 triggers + 8 actions + 14 searches
- **n8n** — community node with full endpoint coverage
- **Pabbly** — basic integration
- **Albato** — basic integration

### AI/MCP
- **MCP Server** — `heyreach-mcp-server` npm package, 18 tools, works with Claude Desktop, Cursor, VS Code
- **Claude integration** — via MCP
- **ChatGPT integration** — via MCP

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (invalid params) |
| 401 | Unauthorized (bad/missing API key) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Rate Limited (>300 req/min) |
| 500 | Server Error |
| 503 | Service Unavailable |

---

## Comparison Notes (vs Email Platforms)

| Feature | HeyReach | Instantly | Salesforge |
|---------|----------|-----------|------------|
| Channel | LinkedIn only | Email only | Email only |
| Campaign create via API | No (UI only) | Yes | Yes |
| Webhook CRUD | Full (create/read/update/delete) | Full | Create+read only |
| Webhook events | 11 LinkedIn events | 20+ email events | 10 email events |
| Rate limit | 300/min | Not published | Not published |
| Lead delete | Yes (from lists) | Yes | No |
| Conversation access | Yes (filter, read, reply) | Yes (Unibox) | List only (no reply) |
| Analytics | 1 flexible endpoint | 6+ endpoints | 2 endpoints |
| Auth | X-API-KEY header | Bearer token | Raw key (no Bearer) |
| Total endpoints | ~38 | ~118 | ~30 working |

---

## Gotchas

1. **Campaign creation is UI-only** — cannot create or edit campaigns/sequences via API
2. **Most endpoints are POST** — even read operations (GetAll, GetLeadsFromList) use POST with body, not GET with query params
3. **Pagination is offset-based** — `{offset, limit}` pattern, not cursor-based
4. **LinkedIn account assignment matters** — when adding leads to campaigns, you can specify which LinkedIn sender handles each lead via `linkedInAccountId`
5. **V1 vs V2 endpoints** — AddLeadsToCampaign and AddLeadsToList have V2 versions with improved validation; prefer V2
6. **Minimum 3-hour delay** between campaign sequence steps
7. **InMail requires Sales Navigator** — if the sender doesn't have SN/Recruiter, InMail steps fail silently
8. **Cross-campaign webhooks** — MESSAGE_REPLY_RECEIVED and LEAD_TAG_UPDATED fire for all conversations, not just campaign-initiated ones
9. **Tag operations** — AddTags is additive (safe), ReplaceTags is destructive (replaces all existing tags)
10. **No email operations** — HeyReach is LinkedIn-only; email is handled by partner integrations (Instantly, Smartlead, Salesforge)
