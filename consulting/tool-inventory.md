# Tool Inventory

Current tools connected via Datagen + tools needed but not yet connected.

_Last updated: 2026-02-13_

---

## Currently Connected Tools

### Apollo.io (via Composio)
Sales engagement platform — contacts, accounts, deals, sequences, enrichment.

| Tool | What It Does |
|------|-------------|
| `APOLLO_SEARCH_CONTACTS` | Search contacts by keyword, stage, sorting (max 50k) |
| `APOLLO_CREATE_CONTACT` | Create a new contact (no auto-dedup) |
| `APOLLO_UPDATE_CONTACT` | Update contact attributes by contact_id |
| `APOLLO_UPDATE_CONTACT_OWNERSHIP` | Reassign contact ownership |
| `APOLLO_UPDATE_CONTACT_STAGE` | Move contacts through sales stages |
| `APOLLO_LIST_CONTACT_STAGES` | List all available contact stages |
| `APOLLO_SEARCH_ACCOUNTS` | Search existing accounts (paid plan, max 50k) |
| `APOLLO_CREATE_ACCOUNT` | Create a new account |
| `APOLLO_UPDATE_ACCOUNT` | Update account attributes |
| `APOLLO_LIST_ACCOUNT_STAGES` | List all account stages |
| `APOLLO_BULK_UPDATE_ACCOUNT_STAGE` | Bulk-update account stages |
| `APOLLO_PEOPLE_ENRICHMENT` | Enrich a person by email, LinkedIn URL, or name+org |
| `APOLLO_BULK_PEOPLE_ENRICHMENT` | Enrich multiple people simultaneously |
| `APOLLO_ORGANIZATION_ENRICHMENT` | Enrich an org by domain |
| `APOLLO_BULK_ORGANIZATION_ENRICHMENT` | Enrich up to 10 orgs by domain |
| `APOLLO_ORGANIZATION_SEARCH` | Search Apollo's org database (consumes credits) |
| `APOLLO_GET_ORGANIZATION_JOB_POSTINGS` | Get job postings for an org |
| `APOLLO_SEARCH_SEQUENCES` | Search email sequences |
| `APOLLO_ADD_CONTACTS_TO_SEQUENCE` | Add contacts to an email sequence |
| `APOLLO_UPDATE_CONTACT_STATUS_IN_SEQUENCE` | Update contact status in a sequence |
| `APOLLO_LIST_DEALS` | List deals/opportunities |
| `APOLLO_CREATE_DEAL` | Create a new deal |
| `APOLLO_UPDATE_DEALS` | Update deal attributes |
| `APOLLO_GET_OPPORTUNITY_STAGES` | List deal/opportunity stages |
| `APOLLO_CREATE_TASK` | Create tasks assigned to contacts |
| `APOLLO_SEARCH_TASKS` | Search tasks by filters |
| `APOLLO_LIST_USERS` | List all team users |
| `APOLLO_LIST_EMAIL_ACCOUNTS` | List connected email accounts |
| `APOLLO_GET_LABELS` | Get all labels for organizing contacts/accounts |
| `APOLLO_GET_TYPED_CUSTOM_FIELDS` | Get custom field definitions |

### LinkedIn (Datagen first-party)
Profile data, company data, social activity — read-only intelligence gathering.

| Tool | What It Does |
|------|-------------|
| `search_linkedin_person` | Search profiles by name, company, title, location (20/page) |
| `search_linkedin_company` | Search company profiles by domain |
| `get_linkedin_person_data` | Full profile: work history, education, skills |
| `get_linkedin_company_data` | Company profile: industry, size, HQ, description |
| `get_linkedin_person_posts` | Recent posts from a person |
| `get_linkedin_person_post` | Single post by activity ID |
| `get_linkedin_person_comments` | Last 50 comments by a person |
| `get_linkedin_person_reactions` | Last 50 reactions by a person |
| `get_linkedin_person_post_comments` | Comments on a person's post (auto-paginate) |
| `get_linkedin_person_post_reactions` | Reactions on a person's post |
| `get_linkedin_person_post_repost` | Reposts of a person's post |
| `get_linkedin_company_posts` | Company page posts |
| `get_linkedin_company_post` | Single company post by activity ID |
| `get_linkedin_company_post_comments` | Comments on a company post |
| `get_linkedin_company_post_reactions` | Reactions on a company post |
| `get_linkedin_company_post_reposts` | Reposts of a company post |

### Notion
Workspace management — search, pages, databases, comments, users.

| Tool | What It Does |
|------|-------------|
| `notion_search` | Semantic search across workspace + connected sources |
| `notion_fetch` | Get page/database details by URL or ID |
| `notion_create_pages` | Create pages (standalone or in databases) |
| `notion_update_page` | Update page properties or content |
| `notion_move_pages` | Move pages to a new parent |
| `notion_duplicate_page` | Duplicate a page |
| `notion_create_database` | Create a new database with schema |
| `notion_update_database` | Update database properties/schema |
| `notion_get_comments` | Get all comments on a page |
| `notion_create_comment` | Add a comment to a page |
| `notion_get_self` | Get bot user info |
| `notion_get_user` | Get a specific user |
| `notion_get_users` | List all users |
| `notion_get_teams` | List teams/teamspaces |
| `notion_list_agents` | List custom Notion agents/workflows |

### Firecrawl
Web scraping, crawling, search, and structured extraction.

| Tool | What It Does |
|------|-------------|
| `firecrawl_scrape` | Scrape a single URL (markdown, HTML, branding) |
| `firecrawl_crawl` | Crawl a website and extract from all pages |
| `firecrawl_search` | Web search with optional content extraction |
| `firecrawl_map` | Discover all URLs on a website |
| `firecrawl_extract` | Extract structured data from pages via LLM |

### Cloudflare
Workers, D1 databases, KV storage, R2 object storage, Hyperdrive.

| Tool | What It Does |
|------|-------------|
| `accounts_list` | List Cloudflare accounts |
| `workers_list` / `workers_get_worker` / `workers_get_worker_code` | Manage Workers |
| `d1_databases_list` / `d1_database_create` / `d1_database_get` / `d1_database_query` / `d1_database_delete` | D1 SQL databases |
| `kv_namespaces_list` / `kv_namespace_create` / `kv_namespace_get` / `kv_namespace_update` / `kv_namespace_delete` | KV key-value storage |
| `r2_buckets_list` / `r2_bucket_create` / `r2_bucket_get` / `r2_bucket_delete` | R2 object storage |
| `hyperdrive_configs_list` / `hyperdrive_config_get` / `hyperdrive_config_edit` / `hyperdrive_config_delete` | Hyperdrive DB caching |
| `search_cloudflare_documentation` | Search CF docs |

### AI & Utility (Datagen first-party)
Built-in AI processing, research, and file handling tools.

| Tool | What It Does |
|------|-------------|
| `ai_writer` | Generate content from a prompt (emails, summaries) |
| `extract_structured_output` | Extract structured data from content via JSON schema |
| `doc_understanding_tool` | Parse and extract from HTML/PDF/text documents |
| `image_understanding_tool` | OCR, object detection, image classification |
| `audio_understanding_tool` | Transcription, speaker ID, audio analysis |
| `video_understanding_tool` | Video/YouTube content analysis |
| `chatgpt_webresearch` | Web research with synthesized answer + citations |
| `perplexity_search` | Web search via Perplexity answer engine |
| `parallel_findall` / `parallel_findall_result` | Discover entities matching criteria (Parallel AI) |
| `write_file_to_local` | Write data to file (CSV, JSON, PDF, images, etc.) |

---

## NOT Connected — Needed for GTM Infrastructure

These are required by Clayton's infrastructure principles and the tool stack design (see [project-context.md](project-context.md) and [likely-gtm-needs.md](likely-gtm-needs.md)).

### Tier 1: Critical Path (blocks v1 launch)

| Tool | Why Needed | Status | Notes |
|------|-----------|--------|-------|
| **Salesforce** | System of record (Clayton principle #1). All contacts, accounts, opportunities, campaign tracking live here. | NOT CONNECTED | Must be the CRM backbone. Apollo may sync to SF but direct access needed for reporting, attribution, and data integrity. |
| **Clay** | Orchestrator (Clayton principle #5). Multi-source enrichment workflows, dedup, contact-to-account normalization, email validation waterfall. | NOT CONNECTED | Central to the entire data pipeline. Without Clay, enrichment is manual and fragmented. |
| **SalesForge** (or sequencer) | Outbound email + LinkedIn sequences. API-over-UI decision already made. | NOT CONNECTED | Tool choice is flexible per Clayton principle #2. Apollo sequences are connected and could substitute for v1 pilot if SalesForge API proves difficult. |
| **Definitive Healthcare (HospitalView API)** | Live hospital data — bed counts, EHR, financials, CMS quality, news/RFP trigger signals. Only source of "why now" signals. | NOT CONNECTED | #1 implementation priority per likely-gtm-needs.md. Integration specialist assigned (Ryan McDonald). Static CSVs in `data/` are already stale. |

### Tier 2: Important (needed for scale / v2+)

| Tool | Why Needed | Status | Notes |
|------|-----------|--------|-------|
| **ZoomInfo** | Primary source for verified business emails and phone numbers (Clayton principle #8). DH email quality is poor. | NOT CONNECTED | Covers Tier 1 + upper Tier 2 ICP titles well. Weak on clinical titles. |
| **LeanData** | Contact-to-account mapping (Clayton principle #9). Parent/child account hierarchy handling (principle #10). | NOT CONNECTED | Available per Clayton; needs configuration. |
| **Email validation** (NeverBounce, ZeroBounce, or via Clay) | Deliverability check before any sends. High bounce rates = sender reputation damage. | NOT CONNECTED | Critical before v1 launch — programmatic sends at scale amplify deliverability problems. |
| **Gmail** | Direct email sending for Clayton/Reagan profiles. LinkedIn warm-up inboxes. | NOT CONNECTED | Apollo has email account access but unclear if it covers the dedicated SDR inboxes. |

### Tier 3: Evaluate / Defer

| Tool | Why Needed | Status | Notes |
|------|-----------|--------|-------|
| **PhysicianView API** (Definitive HC) | Clinical contact discovery — endocrinologists, hospitalists, pharmacy leaders. Maps to 33/66 ICP titles. | NOT AVAILABLE | Requires separate module purchase. Run v1 pilot without; evaluate based on Tier 3 hit rates. |
| **Monocl Expert Insight** | KOL/thought leader identification — conference speakers, publication authors, advisory boards. | NOT AVAILABLE | Manual KOL research viable at small scale for top 20 accounts. Ask Clayton for existing KOL relationships first. |
| **Reporting/Dashboard tool** | Campaign metrics, enrichment coverage, pipeline attribution (Clayton principle #7). | TBD | Could be Salesforce reports, standalone BI, or Notion dashboards. |

---

## Coverage Gap Analysis

Mapping Clayton's principles to current tool availability:

| Principle | Tool Needed | Have It? |
|-----------|------------|----------|
| 1. Salesforce as system of record | Salesforce | NO |
| 2. Sequencer is tool-agnostic | SalesForge / Apollo sequences | PARTIAL (Apollo sequences connected) |
| 3. All programmatic | Datagen SDK + MCP tools | YES |
| 4. Lean into AI/agents | Datagen AI tools + Claude | YES |
| 5. Clay as orchestrator | Clay | NO |
| 6. Learning/feedback loop | Reporting + iteration workflow | NO (tooling gap) |
| 7. Reporting/dashboard | Salesforce reports / BI tool | NO |
| 8. ZoomInfo + contact data | ZoomInfo | NO (Apollo enrichment is partial substitute) |
| 9. LeanData mapping | LeanData | NO |
| 10. Parent/child account mapping | LeanData + Salesforce hierarchy | NO |
| 11. Ongoing hygiene/validation | Email validation + Clay workflows | NO |

---

## What Apollo Can Cover (Partial Substitutes)

Apollo is the only sales tool currently connected. Here's what it can partially cover while other integrations are pending:

| Gap | Apollo Workaround | Limitation |
|-----|------------------|------------|
| Contact enrichment (ZoomInfo) | `APOLLO_PEOPLE_ENRICHMENT`, `APOLLO_BULK_PEOPLE_ENRICHMENT` | Apollo's database is smaller than ZoomInfo. Clinical titles will have lower hit rates. |
| Org enrichment | `APOLLO_ORGANIZATION_ENRICHMENT` | Covers business data; no hospital-specific fields (beds, EHR, CMS data). |
| Email sequences (SalesForge) | `APOLLO_SEARCH_SEQUENCES`, `APOLLO_ADD_CONTACTS_TO_SEQUENCE` | Viable for v1 pilot. Flexibility preserved per principle #2. |
| CRM (Salesforce) | `APOLLO_SEARCH_CONTACTS/ACCOUNTS`, `APOLLO_CREATE_*`, `APOLLO_UPDATE_*` | NOT a substitute for Salesforce as system of record. Data lives in Apollo silo. |
| Contact-to-account mapping (LeanData) | Manual via `APOLLO_CREATE_CONTACT` with `account_id` | No automated routing or dedup logic. |

---

## Recommended Connection Priority

1. **Salesforce** — unblocks reporting, attribution, and system-of-record requirement
2. **Clay** — unblocks enrichment orchestration, dedup, email validation workflows
3. **Definitive Healthcare API** — unblocks live data, trigger signals, and account scoring
4. **ZoomInfo** — unblocks verified email/phone enrichment at scale
5. **SalesForge** (if not using Apollo sequences) — unblocks dedicated outbound sequencing
6. **LeanData** — unblocks automated contact-to-account mapping
7. **Email validation tool** — unblocks deliverability safety before launch
