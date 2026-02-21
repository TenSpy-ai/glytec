# Warmforge Public API Reference

**Swagger source:** https://api.warmforge.ai/public/swagger/doc.json
**Base URL:** `https://api.warmforge.ai/public/v1`
**Auth:** API key via `Authorization` header (ApiKeyAuth) or Bearer token

## Endpoints

### Mailboxes

- `GET /mailboxes` — List mailboxes (paginated; filter by search, external reference, status)
  - Status values: `warm`, `pending`, `disconnected`, `suspended`, `all`
- `POST /mailboxes/connect-oauth2` — Connect Gmail or Outlook via OAuth2
- `POST /mailboxes/connect-smtp` — Connect SMTP mailbox (host/port/username/password)
- `GET /mailboxes/{address}` — Get single mailbox info
- `PATCH /mailboxes/{address}` — Update mailbox settings (warmup config, email rates, signature, display name)
- `DELETE /mailboxes/{address}` — Remove mailbox (202 accepted)
- `POST /mailboxes/bulk-update` — Bulk update mailboxes with filters
- `GET /mailboxes/{address}/warmup/stats` — Warmup statistics within date range

### Placement Tests

- `GET /placement-tests` — List placement tests (paginated, searchable)
- `POST /placement-tests` — Create placement test (subject, body, target mailboxes)
- `GET /placement-tests/{placementTestID}` — Get test details and results
- `DELETE /placement-tests/{placementTestID}` — Remove test (202 accepted)

## Key Data Models

### MailboxResponse
- address, status, provider type
- warmup metrics, DNS health data, reputation scores

### PlacementTestResponse
- inbox/spam counts by provider
- pending/missing statuses
- individual test results

### WarmupStatsResponse
- Daily metrics: sent/reply/spam counts
- Provider-specific breakdowns

## Notes
- Pagination via `limit` and `offset`
- Error responses: 401 (Unauthorized), 404 (Not Found), 500 (Internal Server Error)
