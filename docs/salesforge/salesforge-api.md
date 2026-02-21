# SalesForge Public API Reference

**Swagger source:** https://api.salesforge.ai/public/v2/swagger/doc.json
**Base URL:** `https://api.salesforge.ai/public/v2`
**Auth:** API key via `ApiKeyAuth` header

## Endpoints

### Authentication
- `GET /auth` — Validate API key, retrieve account info

### Workspaces
- `POST /workspaces` — Create workspace
- `GET /workspaces` — List workspaces

### Contacts
- `POST /contacts` — Create contact
- `GET /contacts` — List contacts (filter by tags, validation status; paginated)
- `POST /contacts/bulk` — Bulk create/manage contacts

### Custom Variables
- `GET /custom-variables` — Get workspace-specific custom variable definitions

### DNC (Do Not Contact)
- `POST /dnc/bulk` — Bulk create DNC entries

### Webhooks
- `POST /webhooks` — Register webhook
- `GET /webhooks` — List webhooks
- `DELETE /webhooks/{id}` — Remove webhook

### Mailboxes
- `GET /mailboxes` — List mailboxes (extensive filtering: status, tags, address)

### Email
- `POST /emails/{id}/reply` — Reply to a specific email within a thread

### Threads
- `GET /threads` — List email conversation threads (filterable)

### Products
- `POST /products` — Create product
- `GET /products` — List products

### Sequences
- `POST /sequences` — Create sequence
- `GET /sequences` — List sequences (filter by status, product, type)
- `GET /sequences/{id}` — Get sequence detail
- `PUT /sequences/{id}` — Update sequence
- `DELETE /sequences/{id}` — Delete sequence
- `GET /sequences/{id}/analytics` — Sequence analytics
- `POST /sequences/{id}/contacts/validate` — Validate contacts in sequence
- `POST /sequences/{id}/mailboxes` — Assign mailboxes to sequence

### Sequence Metrics
- `GET /sequences/{id}/metrics` — Performance data for a sequence

## Notes
- Pagination via `limit` and `offset` on list endpoints
- Responses use `ListResponse` wrappers with paginated `data` arrays
