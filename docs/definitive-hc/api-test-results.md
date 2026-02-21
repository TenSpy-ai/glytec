# HospitalView API — Test Results & Gotchas

Comprehensive endpoint testing against live Definitive Healthcare HospitalView API.
Tested 2026-02-19.

---

## Test Configuration

| Item | Value |
|------|-------|
| API Key | `76f8374b-8fe7-4ad7-9e8c-757220db34f9` |
| Auth Header | `Authorization: ApiKey <key>` |
| Base URL | `https://api-data.defhc.com` |
| Primary Test Hospital | Abbott Northwestern Hospital (ID: 2151, Allina Health, Minneapolis MN, Epic shop) |
| Secondary Test Hospital | Massachusetts General Hospital (ID: 1973, Mass General Brigham, Boston MA) |
| Pagination | `page[size]` and `page[offset]` query params |

---

## Endpoint Test Summary

All 20 endpoints tested. 20/20 returned HTTP 200 (when called correctly).

### GET Endpoints (10/10 pass)

| Endpoint | HTTP | Records | Notes |
|----------|------|---------|-------|
| `GET /v1/hospitals/{id}` | 200 | 1 (object) | Full hospital summary. Returns single object in `data`, not array. |
| `GET .../technologies/currentimplementations` | 200 | 184 | EHR/tech installs. Epic Systems Corporation is primary vendor. |
| `GET .../newsandintelligence` | 200 | 20+ | News articles with full `bodyOfArticle` text. Types: People on the Move, Awards/Recognitions, M&A. |
| `GET .../executives` | 200 | 78 | Leadership contacts. LinkedIn coverage 91%, primaryEmail 58%, directEmail 9%. |
| `GET .../physicians/affiliated` | 200 | 100+ | Rich data: NPI, specialty, medicare payments, hospital affiliations. |
| `GET .../quality` | 200 | 48 | CMS quality metrics: HAC scores, HCAHPS ratings, readmission, stars. Years 2023-2025. |
| `GET .../financials` | 200 | 141 | Very detailed: total assets, operating margin, revenue, IT budget estimates. |
| `GET .../affiliations` | 200 | 12+ | Full IDN facility network with `subNetwork` and `subNetworkDefinitiveId`. |
| `GET .../memberships` | 200 | 6 | GPO (Vizient), ACO, Clinically Integrated Network. |
| `GET .../requests` | 200 | 0 (2151), 3 (1973) | RFPs/CONs. Sparse — most hospitals have 0. Mass General had 3. |

### POST/Search Endpoints (10/10 pass)

| Endpoint | HTTP | Test Filter | Records | Notes |
|----------|------|-------------|---------|-------|
| `POST .../technologies/.../search` | 200 | `vendor Contains "Epic"` | 58 | Exact match ("Equals") on "Epic" returns 0 — must use "Epic Systems Corporation". |
| `POST .../newsandintelligence/search` | 200 | `intelligenceType Contains "Merger"` | 8 (1973) | Returns M&A articles with full text. "Leadership Changes" = 0 for 2151. |
| `POST .../executives/search` | 200 | `positionLevel Equals "C-Level"` | 1 | Only 1 C-Level at hospital 2151. VP = 7, Director = 56. |
| `POST .../physicians/affiliated/search` | 200 | `primarySpecialty Equals "Endocrinology..."` | 0 | No endocrinologists at this facility (or exact name mismatch). |
| `POST .../quality/search` | 200 | `name Contains "HAC"` | 9 | Property is `name` not `metric`. `year` requires integer type not string. |
| `POST .../financials/search` | 200 | `name Contains "Operating"` | 7 | Property is `name` not `metric`. Operating income: -$313M, IT budget: $53.6M. |
| `POST .../affiliations/search` | 200 | `firmType Equals "Hospital"` | 12 | Full Allina Health hospital network. |
| `POST .../memberships/search` | 200 | `type Equals "Group Purchasing Organization"` | 1 | Vizient GPO. |
| `POST .../requests/search` | 200 | `type Equals "Request for Proposal"` | 0 (2151) | Endpoint works, hospital just has no RFPs. |
| `POST /v1/hospitals/search` | 200 | `state Equals "MN"` + `hospitalType Equals "Short Term Acute Care Hospital"` | 57 | Bulk search. Full hospital objects returned. Multi-filter = AND logic. |

---

## Gotchas & Undocumented Behavior

### 1. Invalid Hospital ID Returns 200 with Null Object (Not 404)
```
GET /v1/hospitals/9999999 → 200
{
  "meta": { "pageSize": 0, "totalRecords": 0 },
  "data": { "facilityName": null, "definitiveId": 0, ... }
}
```
**Impact:** Must check `definitiveId == 0` or `facilityName == null` to detect invalid IDs. Don't rely on HTTP status.

### 2. Vendor Names Are Full Legal Names
`vendor` = `"Epic Systems Corporation"`, not `"Epic"`. Use `Contains` operator if unsure of exact name.
- Epic → "Epic Systems Corporation"
- Cerner → "Oracle Cerner" or "Oracle Cerner - Oracle Cerner-Millennium" or "Oracle Cerner - MHS GENESIS"
- MEDITECH → "MEDITECH" (check — may vary)

### 3. `staffedBeds` Is NOT Filterable in Bulk Search
`POST /v1/hospitals/search` with `propertyName: "staffedBeds"` returns 400:
> "Request body contains an invalid property name: 'staffedBeds'"

**Impact:** Cannot filter hospitals by bed count server-side. Must pull all hospitals and filter client-side.

### 4. `networkParentName` — Understand the 2-Tier Network Hierarchy

`networkParentName` IS filterable — but it's **null for 4,834 hospitals** (the majority). The original test returned 0 because Allina Health is already the top-level network (no parent above it).

**How the hierarchy works:**
```
networkParentName → networkName → individual hospital

Example 1 (3-tier):
  "Defense Health Agency" (parent) → "US Air Force Medical Service" (network) → "60th Medical Group - Travis AFB" (facility)
  networkParentName = "Defense Health Agency"
  networkName = "US Air Force Medical Service"

Example 2 (3-tier):
  "Tenet Healthcare" (parent) → "Abrazo Health" (network) → "Abrazo Arizona Heart Hospital" (facility)
  networkParentName = "Tenet Healthcare"
  networkName = "Abrazo Health"

Example 3 (2-tier — no parent):
  null (parent) → "Allina Health" (network) → "Abbott Northwestern Hospital" (facility)
  networkParentName = null
  networkName = "Allina Health"
```

**The split:** 5,171 hospitals have a networkParentName. 4,834 have null (they're already at the top of their hierarchy, or independent).

**Impact for IDN queries:**
- To find all facilities in a **top-level health system** (like Allina Health), use `networkName`
- To find all facilities under a **holding company/parent org** (like CHS, Tenet, DHA), use `networkParentName`
- Both are filterable. Both support Equals, Contains, IsNull, IsNotNull.
- To get the complete picture for a given system, you may need to query BOTH fields

### 5. Quality/Financial Property Is `name`, Not `metric`
The quality and financials schemas use `name` for the metric identifier. Filtering by `metric` returns 400: "invalid property name."

### 6. Quality/Financial `year` Filter — Must Pass Integer, Not String
`"value": "2024"` (string) → 400 error. `"value": 2024` (integer) → 200, returns 13 quality records.
```json
// WRONG
{"propertyName":"year","operatorType":"Equals","value":"2024"}

// CORRECT
{"propertyName":"year","operatorType":"Equals","value":2024}
```
**Impact:** JSON type matters. The schema says `value` is `{...} nullable: true` — it accepts mixed types, but year must be numeric.

### 7. `In` Operator Takes Array, Not Comma-Separated String
```json
// WRONG — returns 0 results silently
{"propertyName":"state","operatorType":"In","value":"MN,WI"}

// CORRECT — returns 419 results
{"propertyName":"state","operatorType":"In","value":["MN","WI"]}
```
**Impact:** Comma-separated strings silently return 0 results. No error. Must use JSON array for `In` operator.

### 8. `definitiveId` — Equals Works, `In` Does Not, AND Logic Blocks Multi-ID
- `Equals` with single integer value → works (`definitiveId Equals 2151` → 1 result)
- `In` with array → 400 error ("value not valid for property name 'definitiveId'")
- Two Equals filters on same field → AND logic → 0 results (`id = 2151 AND id = 1973` is impossible)

**Impact:** No batch-fetch by ID via POST search. Must call `GET /v1/hospitals/{id}` individually per hospital. For bulk operations, filter by other properties (state, networkName, hospitalType, etc.).

### 9. Hospital Summary Returns Object, Not Array
`GET /v1/hospitals/{id}` returns `"data": { ... }` (single object). All other endpoints return `"data": [ ... ]` (array).

### 10. `vendorStatus` Is ALWAYS Null — Not Just Sometimes
Tested across 3 hospitals (Abbott NW: 0/184, Mass General: 0/100, Abbeville: 0/50). Zero populated values found. The field exists in the schema but appears to be deprecated or unpopulated across the entire database.

`implementationYear` is slightly better at 17% (17/100 at Mass General) but still unreliable.

**Impact:** Cannot use `vendorStatus` for anything. Do not build pipeline logic around it. For EHR detection, rely on `vendor` + `product` fields only.

### 11. `primaryEmail` Coverage Is Low (~58%), LinkedIn Is High (~91%), `directEmail` Is All Gmail/Yahoo
For hospital 2151 (78 executives):
- `primaryEmail`: 45/78 (58%) — corporate emails when present
- `directEmail`: 14 total emails found, **100% personal domains** (12 Gmail, 2 Yahoo, 0 corporate)
- `linkedinProfileURL`: 71/78 (91%)

**Impact:** LinkedIn is the reliable identifier for executive contacts. `directEmail` is useless for outbound — it's exclusively personal email addresses. Email quality confirms the "email quality poor, ZoomInfo overwrites" assumption. Never use `directEmail` in a sequence.

### 12. `positionLevel` Values Are Specific Strings — "Other" Is Noise
Tested values: `"C-Level"`, `"Vice President"`, `"Manager/Director"`, `"Other"`. "VP" and "Director" (shorthand) return 0 results — must use exact values.

**"Other" category (14 at Abbott NW) is noise:** Infection Prevention Strategist, Clinical Specialist, Electrophysiology Techs (4x), Billing Officer, ED Huc/Tech, Contract Consultant, Palliative Care Chaplain, Recruiter. These are not ICP targets. Filter them out.

**Distribution at Abbott NW:** Manager/Director: 56 (72%), Other: 14 (18%), VP: 7 (9%), C-Level: 1 (1%)

### 13. RFPs Are Sparse
Most hospitals have 0 RFPs/CONs. Only 3 found at Mass General. The `classification` field includes "Definitive Healthcare Conversation" (their own intelligence) alongside traditional RFPs.

### 14. Multi-Filter is AND Logic
Multiple filter parameters in the array are combined with AND. No OR logic available within a single request.

### 15. Pagination Caps at Requested Size (No Server Max Observed)
Requested `page[size]=1000` → returned all 57 MN acute care hospitals. No observed hard cap on page size. However, for large result sets, use reasonable page sizes to avoid timeouts.

### 16. `Contains` Is Case-Insensitive
`vendor Contains "epic"` (lowercase) returns the same 58 records as `vendor Contains "Epic"`. All string filter operators (Contains, StartsWith, EndsWith) are case-insensitive.

**Impact:** No need to worry about casing when building filters. This is actually helpful for pipeline automation.

### 17. `state` Cannot Use Contains/StartsWith/EndsWith
Confirmed: `state Contains "MN"` → 400 error. The API explicitly blocks wildcard operators on the `state` field. Must use `Equals` or `In` with exact 2-letter state codes.

### 18. `Contains`/`StartsWith`/`EndsWith` Require Minimum 3 Characters
`facilityName Contains "VA"` → 400: "Value... is too short. Enter a value with at least 3 characters." Documented behavior, confirmed enforced.

### 19. Empty Filter Array → 400 (Enforced)
`POST /v1/hospitals/search` with `[]` body → 400: "Request isn't complete. Review format or check for missing syntax." The docs say "must provide at least one field parameter" — confirmed enforced. You cannot dump the entire universe in one call.

### 20. 1,448 Closed Hospitals in the Database — Filter Them Out
`companyStatus NotEquals "Active"` returns 1,448 records. These are closed hospitals with dates in the name (e.g., "Chilton Medical Center (Closed 2012-10-01)"). If you're building target lists, **always include** `companyStatus Equals "Active"` as a filter.

**Universe:** 8,557 active + 1,448 closed = ~10,005 total hospitals in the API.

### 21. `payorMixSelfPay` Is Actually "Everything Except Medicare and Medicaid"
The three payor mix fields sum to exactly 1.0:
```
Abbott NW: Medicare 0.2243 + Medicaid 0.0905 + SelfPay 0.6852 = 1.0000
```
`payorMixSelfPay` includes commercial insurance, self-pay, and all other payors. It's NOT just uninsured/self-pay patients. The financials endpoint has the more accurate breakdown: `payorMixPrivate` = "Payor Mix: Private/Self-Pay/Other Days", `payorMixGovernment` = "Payor Mix: Government Days".

**Impact:** Don't use `payorMixSelfPay > 0.5` as an indicator of financial distress — 5,234 hospitals (61% of the universe) meet that threshold. It just means they have more commercial than government business. Use `netOperatingMargin` from the financials endpoint for actual financial health.

### 22. `standardizedTitle` and `department` Are Filterable — Critical for ICP Matching
Both fields work with `Contains`:
- `standardizedTitle Contains "Nursing"` → 2 results (CNO + Director of Nursing)
- `department Contains "Pharmacy"` → 2 results (Pharmacy Manager + VP of Pharmacy)

**Impact:** Can pre-filter executives server-side before pulling them into the pipeline. Reduces noise significantly vs pulling all 78 execs and filtering client-side.

### 23. `lastUpdatedDate` Is Filterable — Executive Data Freshness Is Trackable
`lastUpdatedDate GreaterThan "2026-01-01"` → 4 execs updated in 2026 at Abbott NW. Date format is `YYYY-MM-DD`.

**Impact:** Can build a "recently updated executives" query to detect leadership changes before they appear in news articles. This is a faster trigger signal than the news endpoint.

### 24. `numericValue` Is Filterable on Quality and Financials
`numericValue GreaterThan 0` on quality → 39 records. Enables server-side filtering for hospitals with active penalties, positive HAC scores, etc.

**Impact:** Can query "hospitals where HAC penalty > 0" directly rather than pulling all quality data and filtering. Powerful for building targeted lists.

### 25. Only 2 Properties Are NOT Filterable in Bulk Hospital Search
Tested 30 properties. Only these 2 returned 400:
- `staffedBeds` — confirmed unfilterable
- `academicMedicalCenter` — only fails with `IsNotNull` (it's boolean — use `True`/`False` operator instead)

Everything else works: facilityName, state, hospitalType, ownership, networkName, networkParentName, firmType, companyStatus, traumaCenter, geographicClassification, region, county, cbsaCode, cbsaDescription, zip, city, latitude, website, phone, payorMixMedicare, payorMixMedicaid, payorMixSelfPay, marketConcentrationIndex, IDNIntegrationLevel, networkOwnership, facility340BId, taxId, networkId, definitiveId.

### 26. News Intelligence Types — 12 Distinct Categories
Across 4 test hospitals, these are the intelligence types observed:
```
75x Clinical Trials/Research     ← high volume, low trigger value
35x People on the Move           ← LEADERSHIP CHANGES — high trigger value
10x New Capabilities             ← moderate trigger value
 9x Awards/Recognitions          ← low trigger value
 9x Finances/Funding             ← moderate trigger value
 5x Labor/Staffing               ← moderate trigger value
 4x Affiliation/Partnership      ← HIGH trigger value (IDN changes)
 4x Legal/Regulatory             ← low trigger value
 2x Information Technology       ← HIGH trigger value (EHR migration signals)
 2x New Facility/Company         ← moderate trigger value
 1x Merger/Acquisition           ← HIGH trigger value
 1x Bankruptcy                   ← HIGH trigger value (financial distress)
```
**For the pipeline:** Filter on `intelligenceType Contains "People"`, `"Information Technology"`, `"Merger"`, `"Affiliation"`, `"Bankruptcy"` for the highest-value trigger signals. "Clinical Trials/Research" dominates volume but is mostly noise for GTM purposes.

### 27. Financial Endpoint Has 141 Unique Metrics
Key metrics for the pipeline (with API `name` values):
- **Scoring:** `netOperatingMargin`, `staffedBeds`, `discharges`, `employees`
- **ROI messaging:** `averageLengthOfStay`, `caseMixIndex`, `bedUtilization`
- **IT spend capacity:** `budgetOperatingIT` ($53.6M for Abbott NW), `budgetCapitalIT`
- **Financial distress signals:** `incomeOperating` (negative = distressed), `cashOnHandDays`, `badDebtArRatio`
- **Size indicators:** `assets`, `revenues`, `visitsEmergencyRoom`, `visitsOutpatient`, `surgeries`

Full list of 141 metric names documented for reference.

---

## Data Quality Assessment by Endpoint

### High Quality (reliable for pipeline use)
- **Hospital Summary** — Core demographics near-100% populated. networkId, networkName, ownership, hospitalType all present. 8,557 active hospitals. **But watch out:** 1,448 closed hospitals also in the database — always filter by `companyStatus Equals "Active"`.
- **Technologies** — Category and vendor reliably populated. Product names ~80% present. `vendorStatus` is dead (0% populated across all tested hospitals). `implementationYear` at ~17%.
- **Quality** — HAC, HCAHPS, readmission penalty all present with numeric values. Multi-year data (2023-2025). `numericValue` is filterable — can query "hospitals with HAC penalty > 0" server-side.
- **Affiliations** — Complete network facility mapping. subNetwork + subNetworkDefinitiveId = parent/child mapping.
- **Memberships** — Type, name, subType well-populated.

### Medium Quality (useful but gaps)
- **Executives** — LinkedIn 91% (good), primaryEmail 58% (poor), `directEmail` 100% personal Gmail/Yahoo (useless). `standardizedTitle` and `department` are searchable — critical for ICP filtering server-side. `lastUpdatedDate` enables freshness tracking. Position level "Other" is noise (EP techs, chaplains) — filter it out.
- **Financials** — 141 unique metrics per hospital. Some are estimates (e.g., "Estimated Operating IT Budget"). `numericValue` is filterable. Key gotcha: `payorMixSelfPay` = "everything except Medicare/Medicaid" (includes commercial) — use `netOperatingMargin` for financial health.
- **News/Intelligence** — 12 distinct intelligence types. "Clinical Trials/Research" dominates volume but is low trigger value. High-value types: "People on the Move" (leadership changes), "Information Technology" (EHR migrations), "Merger/Acquisition", "Affiliation/Partnership". `publicationDate` is filterable — can query for recent signals only. Mass General had 626 news records; date range 2024–2026.

### Low Quality (supplementary only)
- **RFPs/Requests** — Most hospitals have 0 records. Mass General had 3 (one was a "Definitive Healthcare Conversation" — their own intelligence, not a public RFP). Useful when present but cannot be a primary trigger source.
- **Physicians** — Rich per-physician data but endocrinology specialty search returned 0 for Abbott NW. May need exact specialty name matching. Supplementary to executive contacts.

---

## Infrastructure Mapping

How each endpoint maps to our pipeline stages and goals:

### Account Scoring (Step 2)

| Score Factor | Weight | API Source | Endpoint | Filter Strategy |
|---|---|---|---|---|
| Bed count / facility type | 20% | staffedBeds, hospitalType | `GET /hospitals/{id}` | Single-hospital GET (not bulk-filterable) |
| EHR vendor | 20% | vendor, product | `GET .../technologies` | Bulk: `POST .../technologies/search` with `vendor Contains` |
| Operating margin | 15% | netOperatingMargin | `POST .../financials/search` with `name Contains "Operating"` | Returns numericValue |
| CMS quality | 15% | HAC rates, HCAHPS, readmission | `POST .../quality/search` with `name Contains "HAC"` etc. | Multi-year data available |
| Trigger signals | 20% | news + RFPs | `GET .../newsandintelligence` + `GET .../requests` | RFPs sparse; news is primary source |
| Contact coverage | 10% | — | Not from DH | ZoomInfo/Apollo enrichment |

### EHR-Segmented Messaging (Layer 2)

| EHR Vendor (API value) | Message Angle | Filter |
|---|---|---|
| `Epic Systems Corporation` | "DIY calculator liability" | `vendor Contains "Epic"` |
| `Oracle Cerner` / `Oracle Cerner - Oracle Cerner-Millennium` / `Oracle Cerner - MHS GENESIS` | "Oracle transition risk" | `vendor Contains "Oracle Cerner"` |
| `MEDITECH` | "Modernization" | `vendor Contains "MEDITECH"` |

### Financial Health Matrix (Layer 3)

Key metrics from `POST .../financials/search`:
- `netOperatingMargin` — negative = unprofitable → ROI messaging ($20K/bed)
- `netOperatingMargin%` — percentile ranking vs peers
- `budgetOperatingIT` — estimated IT spend capacity
- `expensesOperating` — total operating expenses
- `incomeOperating` — operating income

### Trigger Signals

**News/Intelligence** (`POST .../newsandintelligence/search`):

High-value triggers (filter for these):
- `intelligenceType Contains "People"` — "People on the Move" = leadership changes. Most valuable. Example: "Allina Health names Steven Dickson as Abbott Northwestern Hospital Chi[ef Nursing Officer]" (Sep 2025)
- `intelligenceType Contains "Information Technology"` — EHR migration signals. Rare but extremely high value.
- `intelligenceType Contains "Merger"` — M&A activity. Example: "Mass General Eyes Acquisition of Exeter Hospital"
- `intelligenceType Contains "Affiliation"` — Partnership/IDN changes
- `intelligenceType Contains "Bankruptcy"` — Financial distress
- `intelligenceType Contains "New Facility"` — New unit = new deployment opportunity

Moderate value:
- `intelligenceType Contains "Finances"` — Funding announcements
- `intelligenceType Contains "Labor"` — Staffing changes
- `intelligenceType Contains "New Capabilities"` — Service line expansions

Skip (noise):
- `intelligenceType Contains "Clinical Trials"` — Dominates volume (75/157 in sample) but low GTM value
- `intelligenceType Contains "Awards"` — PR fluff
- `intelligenceType Contains "Legal"` — Usually not actionable

**Date filtering:** `publicationDate GreaterThan "2025-06-01"` works — use this to pull only recent signals. Date format: `YYYY-MM-DD`.

**Leadership change detection shortcut:** `POST .../executives/search` with `lastUpdatedDate GreaterThan "2026-01-01"` is **faster than the news endpoint** for detecting leadership changes. It catches the executive record update before the news article appears.

**RFPs** (`GET .../requests`):
- `type = "Request for Proposal"` — Active procurement
- `category` includes "Technology Services", "Radiology/Medical Imaging"
- `classification` includes "Definitive Healthcare Conversation" (DH's own intelligence, not public RFPs)
- Sparse data — most hospitals have 0. Supplementary trigger only.

### IDN/Network Hierarchy

**Bulk facility search** (`POST /v1/hospitals/search`):
- `networkName Equals "Allina Health"` → Returns all 14 facilities in the network
- `networkParentName Equals "Defense Health Agency"` → Returns all 49 DHA facilities
- Each facility has `networkId`, `networkName`, `networkParentId`, `networkParentName`
- Use `networkName` for same-level health systems (Allina Health, Mayo Clinic). Use `networkParentName` for holding companies (CHS, Tenet, DHA). See gotcha #4 for the full hierarchy explanation.

**Per-hospital affiliations** (`GET .../affiliations`):
- Returns all affiliated facilities with `subNetwork` and `subNetworkDefinitiveId`
- More detailed than bulk search — includes non-hospital affiliates (ASCs, etc.)

### Executive Contact Enrichment

**Search** (`POST .../executives/search`):
- `positionLevel Equals "C-Level"` — CNO, CEO, CFO, CIO, CMO (1 at Abbott NW)
- `positionLevel Equals "Vice President"` — VP of Nursing, VP of Operations, etc. (7)
- `positionLevel Equals "Manager/Director"` — Director of Pharmacy, IT Director, etc. (56)
- Skip `positionLevel Equals "Other"` — EP techs, billing, chaplains (14 — noise)
- `standardizedTitle Contains "Nursing"` — 2 results (ICP-targeted search)
- `department Contains "Pharmacy"` — 2 results (ICP-targeted search)
- `lastUpdatedDate GreaterThan "2026-01-01"` — 4 recently-updated execs (freshness filter)

**Coverage (hospital 2151 sample, 78 executives):**
- `standardizedTitle`: 100% populated — maps directly to ICP title matching
- `linkedinProfileURL`: 91% (71/78) — primary identifier for cross-referencing
- `primaryEmail`: 58% (45/78) — corporate emails, needs ZoomInfo/Apollo overwrite
- `directEmail`: 18% (14/78) — **100% personal domains** (12 Gmail, 2 Yahoo). Never use for outbound.
- `directPhone`: varies — often null, use `locationPhone` as fallback

### DoD/DHA Hospitals

44 Department of Defense hospitals confirmed accessible via API:
- `hospitalType Equals "Department of Defense Hospital"` + `ownership Equals "Governmental - Federal"`
- Network hierarchy: Individual service networks (e.g., "US Air Force Medical Service") under parent "Defense Health Agency"
- Travis AFB (ID: 551551) confirmed present: 60th Medical Group, Oracle Cerner + CliniComp stack
- EHR mix: primarily Oracle Cerner and Oracle Cerner - MHS GENESIS

---

## Test Artifacts

All test responses saved to `/tmp/dh_*.json` (ephemeral).

### Key Hospital IDs Used
- 2151 — Abbott Northwestern Hospital (Allina Health, MN)
- 1973 — Massachusetts General Hospital (Mass General Brigham, MA)
- 551551 — 60th Medical Group, Travis AFB (DHA, CA)
- 2119 — Mercy Hospital (Allina Health, MN)

### API Inventory Observed
- 57 Short Term Acute Care Hospitals in MN
- 419 hospitals in MN + WI combined
- 14 facilities in Allina Health network
- 44 DoD hospitals
- 116 MN hospitals with trauma center designation
- 3 academic medical centers in MN
