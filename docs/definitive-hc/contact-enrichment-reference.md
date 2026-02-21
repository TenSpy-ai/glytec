# Definitive Healthcare HospitalView API — Contact Discovery & Enrichment Reference

Complete reference for every way to find, enrich, filter, and work with contact and account data through the HospitalView API and Glytec's CSV data files. Covers all endpoints, every field, all gotchas, best practices, and 10 ready-to-use recipes for contact discovery at scale. Derived from live API testing (2026-02-19) and analysis of all four data files (9,774 facilities, 1,683 parent systems, 66 ICP titles).

---

## Table of Contents

1. [API Basics](#1-api-basics)
2. [Finding Hospitals (Account Discovery)](#2-finding-hospitals-account-discovery)
3. [Executive Contact Discovery](#3-executive-contact-discovery)
4. [Physician Contact Discovery](#4-physician-contact-discovery)
5. [RFP Contact Discovery](#5-rfp-contact-discovery)
6. [Enriching Contacts with Account Data](#6-enriching-contacts-with-account-data)
7. [Network & Affiliation Mapping](#7-network--affiliation-mapping)
8. [Trigger Signal Detection](#8-trigger-signal-detection)
9. [Filter System Reference](#9-filter-system-reference)
10. [Data Quality Matrix](#10-data-quality-matrix)
11. [Complete Gotcha Reference](#11-complete-gotcha-reference)
12. [Facility List CSV as Account Source](#12-facility-list-csv-as-account-source)
13. [Supporting Data Files](#13-supporting-data-files)
14. [Recipes & Patterns](#14-recipes--patterns)
15. [Contact Type Summary](#15-contact-type-summary)

---

## 1. API Basics

### Authentication
```
Header: Authorization: ApiKey 76f8374b-8fe7-4ad7-9e8c-757220db34f9
```
- Format is `ApiKey <key>` (not Bearer, not Basic)
- Header values are case-sensitive
- GUID-based keys do not expire

### Base URL
```
https://api-data.defhc.com
```

### Pagination
All endpoints accept:
- `page[size]` — number of records per page (default: 10, no observed hard cap)
- `page[offset]` — page number (default: 1)

### Response Structure
```json
{
  "meta": { "pageSize": 10, "totalRecords": 78, "pageOffset": 1, "totalPages": 8 },
  "data": [ ... ]  // array for all endpoints EXCEPT single hospital GET
}
```

**Gotcha:** `GET /v1/hospitals/{id}` returns `"data": { ... }` (single object), not an array. Every other endpoint returns an array.

### Universe
- **8,557 active hospitals** + 1,448 closed = ~10,005 total
- Always filter `companyStatus Equals "Active"` unless you specifically want closed facilities

---

## 2. Finding Hospitals (Account Discovery)

### 2a. Single Hospital by ID

**Endpoint:** `GET /v1/hospitals/{id}`

Returns full hospital summary. The `definitiveId` is the universal join key across all endpoints.

**Fields returned:**
| Field | Type | Notes |
|-------|------|-------|
| `facilityName` | string | Hospital name |
| `definitiveId` | integer | Universal ID — join key for all sub-endpoints |
| `medicareProviderNumber` | string | CMS provider number |
| `facilityPrimaryNpi` | integer | Primary NPI |
| `facilityNpiList` | integer[] | All NPIs for the facility |
| `firmType` | string | "Hospital", "Ambulatory Surgery Center", etc. |
| `hospitalType` | string | "Short Term Acute Care Hospital", "VA Hospital", etc. |
| `addressLine1`, `addressLine2` | string | Physical address |
| `city`, `state`, `zip` | string | State is 2-letter code |
| `latitude`, `longitude` | string | String representation |
| `latitudeCoordinates`, `longitudeCoordinates` | decimal | Numeric coordinates |
| `county`, `region` | string | "NorthEast", "SouthEast", etc. |
| `geographicClassification` | string | "Urban" or "Rural" |
| `cbsaCode`, `cbsaDescription` | int/string | Metropolitan statistical area |
| `definitiveProfileLink` | string | Link to DH profile page |
| `medicalSchoolAffiliates` | string | Primary affiliation |
| `medicalSchoolAffiliatesList` | string[] | All affiliations |
| `networkId` | integer | Parent health system ID |
| `networkName` | string | Parent health system name |
| `networkParentId` | integer | Holding company ID (null if top-level) |
| `networkParentName` | string | Holding company name (null if top-level) |
| `description` | string | Hospital description text |
| `website` | string | Hospital website |
| `networkOwnership` | string | "Owned", "Leased", etc. |
| `ownership` | string | "Voluntary Nonprofit", "Investor-Owned", "Governmental - Federal" |
| `companyStatus` | string | "Active" or closed with date |
| `phone` | string | Main phone number |
| `fiscalYearEndMonth`, `fiscalYearEndDay` | integer | Fiscal year end |
| `academicMedicalCenter` | boolean | AMC flag |
| `accreditationAgency` | string | "The Joint Commission", etc. |
| `accreditationAgencyList` | string[] | All accreditations |
| `pediatricTraumaCenter` | string | Trauma level or null |
| `traumaCenter` | string | "Level I", "Level II", etc. |
| `IDNIntegrationLevel` | string | "System III (vertical integration)", etc. |
| `facility340BId` | string | 340B program ID |
| `taxId` | string | Tax ID |
| `medicareAdministrativeContract` | string | MAC contractor |
| `marketConcentrationIndex` | decimal | HHI market concentration |
| `payorMixMedicaid` | decimal | Medicaid share (0-1) |
| `payorMixMedicare` | decimal | Medicare share (0-1) |
| `payorMixSelfPay` | decimal | **Misleading** — actually "everything except Medicare/Medicaid" |
| `primaryPhysiciansCount` | integer | Count of primary care physicians |
| `secondaryPhysiciansCount` | integer | Count of specialist physicians |

**Gotchas:**
- **Invalid IDs return 200, not 404.** Response has `definitiveId: 0` and `facilityName: null`. Must check for these values.
- **`payorMixSelfPay`** is NOT just self-pay patients. It includes commercial insurance, self-pay, and all other payors. Medicare + Medicaid + SelfPay = 1.0 exactly. 61% of hospitals have `payorMixSelfPay > 0.5` — it just means more commercial than government. Use `netOperatingMargin` from financials for actual financial health.

### 2b. Bulk Hospital Search

**Endpoint:** `POST /v1/hospitals/search`

Search the entire hospital universe with filters. Returns full hospital objects. **Must provide at least one filter** — empty array returns 400.

**Filterable properties (30 tested, 28 confirmed working):**

| Property | Filterable | Operators That Work | Notes |
|----------|-----------|---------------------|-------|
| `facilityName` | Yes | Contains, Equals, StartsWith, EndsWith | Min 3 chars for wildcard ops |
| `state` | Yes | Equals, In, NotEquals | **No Contains/StartsWith/EndsWith** — 400 error |
| `hospitalType` | Yes | Equals, In, Contains | Use exact strings |
| `ownership` | Yes | Equals, Contains | "Voluntary Nonprofit", "Investor-Owned", etc. |
| `networkName` | Yes | Equals, Contains | Same-level health system name |
| `networkParentName` | Yes | Equals, Contains, IsNull, IsNotNull | Holding company — null for 4,834 hospitals |
| `firmType` | Yes | Equals | "Hospital", etc. |
| `companyStatus` | Yes | Equals, NotEquals | Always use `Equals "Active"` |
| `traumaCenter` | Yes | Equals, IsNotNull | "Level I", "Level II", etc. |
| `geographicClassification` | Yes | Equals | "Urban", "Rural" |
| `region` | Yes | Equals | "NorthEast", "SouthEast", etc. |
| `county` | Yes | Equals, Contains | |
| `cbsaCode` | Yes | Equals | Integer |
| `cbsaDescription` | Yes | Contains | |
| `zip` | Yes | Equals, StartsWith | |
| `city` | Yes | Equals, Contains | |
| `latitude`, `longitude` | Yes | GreaterThan, LessThan | For geo-bounding-box queries |
| `website` | Yes | Contains, IsNotNull | |
| `phone` | Yes | IsNotNull | |
| `payorMixMedicare` | Yes | GreaterThan, LessThan | Decimal 0-1 |
| `payorMixMedicaid` | Yes | GreaterThan, LessThan | Decimal 0-1 |
| `payorMixSelfPay` | Yes | GreaterThan, LessThan | Decimal 0-1 (misleading — see above) |
| `marketConcentrationIndex` | Yes | GreaterThan, LessThan | HHI |
| `IDNIntegrationLevel` | Yes | Equals, Contains | |
| `networkOwnership` | Yes | Equals | |
| `facility340BId` | Yes | IsNotNull, Equals | |
| `taxId` | Yes | Equals | |
| `networkId` | Yes | Equals | Integer |
| `definitiveId` | Yes (limited) | Equals only | **No `In` operator** — 400 error. No batch-fetch. |
| `academicMedicalCenter` | Yes (limited) | True, False | **Not IsNotNull** — it's boolean, use True/False |
| `staffedBeds` | **NO** | — | 400: "invalid property name". Must use financials endpoint. |

**Unsearchable in POST /hospitals/search (documented):**
- `definitiveProfileLink`
- `medicalSchoolAffiliates`
- `accreditationAgency`

**Gotchas:**
- **Multi-filter = AND logic.** No OR within a single request. For OR, make separate requests and merge.
- **`definitiveId` cannot use `In` operator.** To fetch multiple hospitals by ID, you must call `GET /v1/hospitals/{id}` individually per hospital or filter by other properties.
- **`state` cannot use Contains/StartsWith/EndsWith.** Must use `Equals` or `In` with exact 2-letter codes.
- **`In` operator requires a JSON array**, not comma-separated string. `"value": "MN,WI"` silently returns 0. Correct: `"value": ["MN", "WI"]`.
- **Empty filter array returns 400.** You cannot dump the entire universe.
- **1,448 closed hospitals** are in the database. Always include `companyStatus Equals "Active"`.
- **No observed page size cap.** `page[size]=1000` worked and returned all 57 MN acute care hospitals.

---

## 3. Executive Contact Discovery

This is the primary contact discovery mechanism. DH provides facility-level leadership mapped by Definitive ID.

### 3a. All Executives for a Hospital

**Endpoint:** `GET /v1/hospitals/{id}/executives`

Returns all executive contacts at a facility.

**Fields returned per executive:**

| Field | Type | Coverage | Notes |
|-------|------|----------|-------|
| `personId` | integer | 100% | DH person identifier |
| `executiveId` | integer | 100% | DH executive identifier |
| `firstName` | string | 100% | |
| `middleName` | string | ~30% | Often null |
| `lastName` | string | 100% | |
| `prefix` | string | ~20% | "Dr.", etc. |
| `suffix` | string | ~5% | "Jr.", "III", etc. |
| `credentials` | string | ~40% | "MD", "RN", "MBA", etc. |
| `gender` | string | ~95% | "Male", "Female" |
| `department` | string | ~90% | "Board of Directors/Trustees", "Pharmacy", etc. |
| `positionLevel` | string | 100% | See exact values below |
| `standardizedTitle` | string | 100% | Maps directly to ICP titles |
| `title` | string | 100% | Facility-specific title (may differ from standardized) |
| `primaryEmail` | string | **58%** | Corporate emails when present |
| `directEmail` | string | **18%** | **100% personal domains** — Gmail, Yahoo. Never use. |
| `directEmails` | string[] | ~18% | Array of personal emails. Also useless. |
| `directPhone` | string | ~30% | Often null |
| `mobilePhone` | string | ~15% | |
| `mobilePhones` | string[] | ~15% | Array of mobile numbers |
| `locationPhone` | string | ~80% | Facility phone — use as fallback |
| `linkedinProfileURL` | string | **91%** | Primary identifier for cross-referencing |
| `physicianFlag` | boolean | 100% | Whether exec is also a physician |
| `physicianLeader` | boolean | 100% | Physician in leadership role |
| `executiveNPI` | integer | ~10% | NPI if physician |
| `lastUpdatedDate` | string | 100% | `YYYY-MM-DD` format. Filterable — key for freshness. |
| `definitiveId` | integer | 100% | Hospital ID (the facility, not the person) |

### 3b. Filtered Executive Search

**Endpoint:** `POST /v1/hospitals/{id}/executives/search`

Server-side filtering of executives. This is the power tool for ICP matching.

**Filterable properties:**

| Property | Works With | Best Practice |
|----------|-----------|---------------|
| `positionLevel` | Equals, In | Use exact strings (below) |
| `standardizedTitle` | Contains, Equals | **Critical for ICP matching** |
| `department` | Contains, Equals | **Critical for ICP matching** |
| `firstName`, `lastName` | Equals, In, Contains | For known-name lookups |
| `gender` | Equals | "Male", "Female" |
| `primaryEmail` | IsNotNull, IsNull | Filter to execs with emails |
| `linkedinProfileURL` | IsNotNull, IsNull | Filter to execs with LinkedIn |
| `lastUpdatedDate` | GreaterThan, LessThan | **Freshness filter** — date format `YYYY-MM-DD` |
| `physicianFlag` | True, False | Physician executives |
| `physicianLeader` | True, False | Physician leaders specifically |
| `credentials` | Equals, In | **Cannot use Contains/StartsWith/EndsWith** |
| `directPhone` | IsNotNull | Filter to execs with phone numbers |

**`positionLevel` exact values (tested):**

| Value | Typical Count | Use Case |
|-------|--------------|----------|
| `"C-Level"` | ~1-3 per hospital | CEO, CFO, CIO, CMO, CNO |
| `"Vice President"` | ~5-10 per hospital | VP Nursing, VP Operations |
| `"Manager/Director"` | ~50-60 per hospital | Director of Pharmacy, IT Director |
| `"Other"` | ~10-15 per hospital | **Noise** — EP techs, chaplains, billing officers. Filter out. |
| `"Board of Directors"` | varies | Board members — not operational contacts |

**"VP" returns 0. "Director" returns 0.** Must use the exact strings above.

### 3c. Executive Discovery Strategies

#### Strategy 1: ICP Title Match (Most Precise)
```json
// Find nursing leadership
[{"propertyName": "standardizedTitle", "operatorType": "Contains", "value": "Nursing"}]
// Returns: CNO, Director of Nursing

// Find pharmacy contacts
[{"propertyName": "department", "operatorType": "Contains", "value": "Pharmacy"}]
// Returns: Pharmacy Manager, VP of Pharmacy

// Find IT decision-makers
[{"propertyName": "department", "operatorType": "Contains", "value": "Information"}]

// Find C-suite only
[{"propertyName": "positionLevel", "operatorType": "Equals", "value": "C-Level"}]
```

#### Strategy 2: Leadership Changes (Freshness-Based)
```json
// Executives updated in the last 60 days — catches new hires before news breaks
[{"propertyName": "lastUpdatedDate", "operatorType": "GreaterThan", "value": "2026-01-01"}]
```
This is **faster than the news endpoint** for detecting leadership changes. The executive record updates before the corresponding "People on the Move" news article appears.

#### Strategy 3: Executives with Contact Info
```json
// Only executives who have corporate email
[{"propertyName": "primaryEmail", "operatorType": "IsNotNull"}]

// Only executives with LinkedIn profiles
[{"propertyName": "linkedinProfileURL", "operatorType": "IsNotNull"}]

// Combine: C-Level with LinkedIn (AND logic)
[
  {"propertyName": "positionLevel", "operatorType": "Equals", "value": "C-Level"},
  {"propertyName": "linkedinProfileURL", "operatorType": "IsNotNull"}
]
```

#### Strategy 4: Physician Leaders
```json
// Physicians in leadership roles — CMOs, medical directors, etc.
[{"propertyName": "physicianLeader", "operatorType": "True"}]
```

#### Strategy 5: Multi-Hospital Executive Search
There is **no cross-hospital executive search endpoint**. You must:
1. Build your target hospital list (via `POST /v1/hospitals/search`)
2. Loop through each hospital calling `POST /v1/hospitals/{id}/executives/search`
3. Merge results client-side

This is the fundamental architectural limitation — all sub-resource endpoints are hospital-scoped.

### 3d. Executive Contact Data Quality Summary

| Field | Coverage | Quality | Use in Pipeline |
|-------|----------|---------|-----------------|
| `standardizedTitle` | 100% | High | ICP matching. Primary filter. |
| `linkedinProfileURL` | 91% | High | Primary cross-reference for ZoomInfo/Apollo enrichment |
| `positionLevel` | 100% | High | Tier filtering. Skip "Other". |
| `department` | ~90% | High | ICP matching. Secondary filter. |
| `primaryEmail` | 58% | Medium | Corporate emails when present. Needs ZoomInfo overwrite. |
| `lastUpdatedDate` | 100% | High | Freshness tracking. Leadership change detection. |
| `directEmail` | 18% | **Useless** | 100% personal domains (Gmail/Yahoo). Never use for outbound. |
| `directPhone` | ~30% | Low | Use `locationPhone` as fallback |
| `mobilePhone` | ~15% | Low | Sparse |

---

## 4. Physician Contact Discovery

Physicians are a secondary contact source. Richer per-person data than executives but less relevant for GTM unless targeting physician leaders (endocrinologists, hospitalists).

### 4a. All Physicians at a Hospital

**Endpoint:** `GET /v1/hospitals/{id}/physicians/affiliated`

**Fields returned per physician:**

| Field | Type | Notes |
|-------|------|-------|
| `personId` | integer | DH person ID |
| `npi` | integer | National Provider Identifier — universal physician key |
| `firstName`, `middleName`, `lastName` | string | |
| `prefix` | string | "Dr." |
| `suffix` | string | |
| `credentials` | string | "MD", "DO", etc. |
| `role` | string | "Physician & Medical Director", etc. |
| `gender` | string | |
| `primaryPracticeCity`, `primaryPracticeState` | string | Practice location |
| `primaryPracticeLocationPhone` | string | Practice phone |
| `primarySpecialty` | string | Full specialty name (see gotcha below) |
| `primaryHospitalAffiliation` | string | Primary hospital name |
| `primaryHospitalAffiliationDefinitiveID` | string | Primary hospital DH ID |
| `secondaryHospitalAffiliation` | string | Secondary hospital name |
| `secondaryHospitalAffiliationDefinitiveID` | string | Secondary hospital DH ID |
| `medicarePayments` | string | Medicare payment amount (string representation) |
| `medicareClaimPayments` | decimal | Medicare payments (numeric) |
| `medicareCharges` | string | Medicare charges (string) |
| `medicareClaimCharges` | decimal | Medicare charges (numeric) |
| `medicareUniquePatients` | integer | Number of unique Medicare patients |
| `numberOfMedicalProcedures` | integer | Total procedure count |
| `definitiveId` | integer | Hospital ID |

### 4b. Filtered Physician Search

**Endpoint:** `POST /v1/hospitals/{id}/physicians/affiliated/search`

**Filterable properties:**
| Property | Works With | Notes |
|----------|-----------|-------|
| `primarySpecialty` | Equals, Contains | Specialty names are long and specific |
| `primaryPracticeState` | Equals, In | **Cannot use Contains/StartsWith/EndsWith** |
| `credentials` | Equals, In | **Cannot use Contains/StartsWith/EndsWith** |
| `firstName`, `lastName` | Equals, In, Contains | Name search |
| `npi` | Equals | NPI lookup |
| `role` | Equals, Contains | |
| `gender` | Equals | |
| `medicareClaimPayments` | GreaterThan, LessThan | High-volume physicians |
| `medicareUniquePatients` | GreaterThan, LessThan | Patient volume |

### 4c. Physician Specialty Gotcha

Specialty names are full formal names, NOT abbreviations:
```
"Surgery - Orthopedic Surgery"  ← not "Orthopedics"
"Internal Medicine - Endocrinology, Diabetes & Metabolism"  ← not "Endocrinology"
```

Use `Contains` to avoid exact-match failures:
```json
[{"propertyName": "primarySpecialty", "operatorType": "Contains", "value": "Endocrinology"}]
```

Even with `Contains`, some specialties may return 0 results at a given hospital — this means the hospital genuinely has no affiliated physicians in that specialty, not necessarily a name mismatch.

### 4d. Physician Cross-Referencing

Physicians have two key cross-reference fields:
- **`npi`** — NPI number. Use to cross-reference with NPPES, CMS data, ZoomInfo
- **`primaryHospitalAffiliationDefinitiveID`** + **`secondaryHospitalAffiliationDefinitiveID`** — discover which other hospitals a physician is affiliated with

**Pattern:** Find all endocrinologists at a hospital → get their NPIs → use NPI to look up detailed contact info in ZoomInfo/Apollo.

---

## 5. RFP Contact Discovery

RFPs occasionally include direct procurement contacts — buyer names, emails, and phone numbers embedded in the RFP record.

### 5a. All RFPs for a Hospital

**Endpoint:** `GET /v1/hospitals/{id}/requests`

### 5b. Filtered RFP Search

**Endpoint:** `POST /v1/hospitals/{id}/requests/search`

**Fields returned:**
| Field | Type | Notes |
|-------|------|-------|
| `definitiveId` | integer | Hospital ID |
| `facilityName` | string | |
| `type` | string | "Request for Proposal", "Certificate of Need" |
| `datePosted` | string | `YYYY-MM-DD` |
| `dateModified` | string | `YYYY-MM-DD` |
| `dateDue` | string | `YYYY-MM-DD` |
| `postingLink` | string | URL to the RFP |
| `category` | string | "Technology Services", "Medical/Surgical Equipment", etc. |
| `contact.name` | string | **Buyer contact name** |
| `contact.email` | string | **Buyer email** |
| `contact.phone` | string | **Buyer phone** |
| `contact.title` | string | "Contracting Officer", etc. |
| `definitiveRfpId` | integer | DH RFP ID |
| `description` | string | RFP description |
| `classification` | string | "Combined Synopsis/Solicitation", "Definitive Healthcare Conversation" |

**Gotcha:** The `contact` object can only be filtered with `IsNull`/`IsNotNull` operators — you cannot search by contact name or email.

**Gotcha:** `classification` includes "Definitive Healthcare Conversation" — these are DH's own intelligence, not public RFPs. Filter with `classification NotEquals "Definitive Healthcare Conversation"` for real RFPs only.

### 5c. RFP Data Quality

- **Most hospitals have 0 RFPs.** Mass General had 3; Abbott NW had 0.
- Useful **only when present** — cannot be a primary contact source
- Technology Services RFPs are the highest-value category for Glytec
- When an RFP does exist, the `contact` object provides a named procurement buyer with direct email/phone — extremely high value

**RFP categories observed:**
- "Technology Services"
- "Radiology/Medical Imaging"
- "Medical/Surgical Equipment or Supplies"
- "Real Estate"
- "Construction - New Building/Renovations/Design"

---

## 6. Enriching Contacts with Account Data

Once you have contacts, enrich them with account-level data from these endpoints.

### 6a. Technology Install (EHR Detection)

**GET:** `GET /v1/hospitals/{id}/technologies/currentimplementations`
**Search:** `POST /v1/hospitals/{id}/technologies/currentimplementations/search`

**Fields:**
| Field | Coverage | Notes |
|-------|----------|-------|
| `category` | ~100% | "Electronic Medical Records", "Clinical Systems", etc. |
| `technology` | ~100% | "Electronic Health/Medical Record - Inpatient", etc. |
| `vendor` | ~100% | **Full legal names** — see below |
| `product` | ~80% | Specific product name |
| `vendorStatus` | **0%** | Always null. Dead field. Do not use. |
| `implementationYear` | ~17% | Mostly null. Unreliable. |
| `unitsInstalled` | sparse | Often null |

**Vendor Name Gotcha — Must Use Full Legal Names:**
| Common Name | API Value(s) |
|-------------|-------------|
| Epic | `"Epic Systems Corporation"` |
| Cerner | `"Oracle Cerner"`, `"Oracle Cerner - Oracle Cerner-Millennium"`, `"Oracle Cerner - MHS GENESIS"` |
| MEDITECH | `"MEDITECH"` |

`vendor Equals "Epic"` returns 0 results. Use `vendor Contains "Epic"` instead.

**Best practice:** Always use `Contains` for vendor searches unless you need the exact product variant.

### 6b. Quality Metrics (CMS Data)

**GET:** `GET /v1/hospitals/{id}/quality`
**Search:** `POST /v1/hospitals/{id}/quality/search`

**Fields:** `name`, `description`, `dataType`, `numericValue`, `value`, `year`, `definitiveId`

**Key metrics for enrichment:**
| Metric `name` | Description | Use Case |
|---------------|-------------|----------|
| `hacPenalty` | HAC Rate Penalty | Active penalty = urgency trigger |
| `hacPenaltyAdjustment` | Revenue Loss Due to HAC Penalty | Dollar impact messaging |
| `readmissionPenalty` | Readmission penalty rate | Quality messaging |
| `vbpAdjustment` | Value-Based Purchasing Adjustment | Incentive alignment |
| CMS stars (various) | Overall rating, safety, etc. | Quality positioning |
| HCAHPS (various) | Patient satisfaction scores | Patient experience angle |

**Gotchas:**
- Property name is `name`, NOT `metric`. `metric` returns 400.
- `year` filter requires integer, not string. `"2024"` → 400. `2024` → works.
- `numericValue` is filterable — can query `numericValue GreaterThan 0` for active penalties.
- Multi-year data available (2023-2025).

### 6c. Financial Metrics

**GET:** `GET /v1/hospitals/{id}/financials`
**Search:** `POST /v1/hospitals/{id}/financials/search`

**Fields:** Same structure as quality — `name`, `description`, `dataType`, `numericValue`, `value`, `year`, `definitiveId`

**141 unique metrics.** Key ones for contact enrichment and messaging:

| Metric `name` | Description | Enrichment Use |
|---------------|-------------|----------------|
| `netOperatingMargin` | Net operating margin | Financial health → message tone |
| `staffedBeds` | Staffed bed count | Size indicator (not filterable in bulk search!) |
| `discharges` | Number of discharges | Volume indicator |
| `employees` | Number of employees | Size indicator |
| `avgLengthOfStay` | Average length of stay | Clinical efficiency |
| `caseMixIndex` | Case mix index | Acuity indicator |
| `bedUtilization` | Bed utilization rate | Capacity pressure |
| `budgetOperatingIT` | Estimated Operating IT Budget | IT spend capacity ($53.6M for Abbott NW) |
| `budgetCapitalIT` | Estimated Capital IT Budget | IT investment capacity |
| `incomeOperating` | Operating income | Negative = financial distress |
| `cashOnHandDays` | Cash on hand (days) | Liquidity |
| `badDebtArRatio` | Bad debt ratio | Financial stress |
| `assets` | Total assets | Size indicator |
| `revenues` | Total revenues | Size indicator |
| `visitsEmergencyRoom` | ER visits | Volume |
| `visitsOutpatient` | Outpatient visits | Volume |
| `surgeries` | Surgical volume | Volume |
| `expensesOperating` | Total operating expenses | Cost structure |

**Gotchas:**
- Same as quality: property is `name`, not `metric`. `year` must be integer.
- `numericValue` is filterable for server-side financial filtering.
- `payorMixPrivate` (from financials) = "Payor Mix: Private/Self-Pay/Other Days" — more accurate than summary-level `payorMixSelfPay`.
- Some metrics are estimates (e.g., "Estimated Operating IT Budget").

### 6d. Memberships (GPO, ACO)

**GET:** `GET /v1/hospitals/{id}/memberships`
**Search:** `POST /v1/hospitals/{id}/memberships/search`

**Fields:** `membershipDefinitiveId`, `type`, `name`, `subType`, `definitiveId`

**Types observed:**
- `"Group Purchasing Organization"` — Vizient, Premier, HPG, etc.
- `"Accountable Care Organization"` — with `subType` like "Commercial ACO", "Medicare Shared Savings ACO"
- `"Clinically Integrated Network"` — CIN affiliations
- `"Health Information Exchange"` — HIE participation

**Enrichment use:** GPO membership indicates purchasing channel. If a hospital uses Vizient GPO, Glucommander may need to go through Vizient's contract vehicle.

---

## 7. Network & Affiliation Mapping

### 7a. Understanding the 2-Tier Hierarchy

```
networkParentName → networkName → individual hospital

Example (3-tier):
  "Tenet Healthcare" (parent) → "Abrazo Health" (network) → "Abrazo Arizona Heart Hospital"
  networkParentName = "Tenet Healthcare"
  networkName = "Abrazo Health"

Example (2-tier — no parent):
  null (parent) → "Allina Health" (network) → "Abbott Northwestern Hospital"
  networkParentName = null
  networkName = "Allina Health"
```

- **5,171 hospitals** have a `networkParentName`
- **4,834 hospitals** have null `networkParentName` (top-level or independent)

### 7b. Finding All Facilities in a Health System

**Method 1: Bulk search by networkName**
```json
POST /v1/hospitals/search
[{"propertyName": "networkName", "operatorType": "Equals", "value": "Allina Health"}]
// Returns all 14 Allina Health facilities
```

**Method 2: Bulk search by networkParentName**
```json
POST /v1/hospitals/search
[{"propertyName": "networkParentName", "operatorType": "Equals", "value": "Defense Health Agency"}]
// Returns all 49 DHA facilities
```

**Method 3: Per-hospital affiliations endpoint**

**GET:** `GET /v1/hospitals/{id}/affiliations`
**Search:** `POST /v1/hospitals/{id}/affiliations/search`

Returns all affiliated facilities including non-hospitals (ASCs, SNFs, rural health clinics). More detailed than bulk search.

**Fields:** `affiliatedFacilityDefinitiveId`, `facilityName`, `firmType`, `address fields`, `subNetwork`, `subNetworkDefinitiveId`, `definitiveId`

**Gotcha:** The affiliations `state` field cannot use Contains/StartsWith/EndsWith — Equals and In only.

### 7c. Network Mapping for Contact Discovery

**Pattern:** When you find a champion at one facility, use network mapping to discover all sibling facilities where the same IDN-level decision might apply.

1. Get hospital → find `networkId` and `networkName`
2. Search `POST /v1/hospitals/search` with `networkName Equals "{name}"`
3. Get all facility IDs in the network
4. Pull executives from each facility to build the full org map

---

## 8. Trigger Signal Detection

### 8a. News & Intelligence

**GET:** `GET /v1/hospitals/{id}/newsandintelligence`
**Search:** `POST /v1/hospitals/{id}/newsandintelligence/search`

**Fields:** `publicationDate`, `intelligenceType`, `newsEventTitle`, `bodyOfArticle`, `publicationId`, `definitiveId`

**Intelligence Types by Trigger Value:**

| Type | Volume | Trigger Value | Filter |
|------|--------|---------------|--------|
| `"People on the Move"` | High | **Critical** — leadership changes | `Contains "People"` |
| `"Information Technology"` | Rare | **Critical** — EHR migration signals | `Contains "Information Technology"` |
| `"Merger/Acquisition"` | Rare | **Critical** — M&A activity | `Contains "Merger"` |
| `"Affiliation/Partnership"` | Low | **High** — IDN changes | `Contains "Affiliation"` |
| `"Bankruptcy"` | Rare | **High** — financial distress | `Contains "Bankruptcy"` |
| `"New Facility/Company"` | Low | **Moderate** — new deployment opportunity | `Contains "New Facility"` |
| `"Finances/Funding"` | Low | **Moderate** — funding announcements | `Contains "Finances"` |
| `"Labor/Staffing"` | Low | **Moderate** — staffing changes | `Contains "Labor"` |
| `"New Capabilities"` | Moderate | **Moderate** — service line expansions | `Contains "New Capabilities"` |
| `"Clinical Trials/Research"` | **Dominant** (48% of volume) | Low — mostly noise for GTM | Skip |
| `"Awards/Recognitions"` | Low | Low — PR fluff | Skip |
| `"Legal/Regulatory"` | Low | Low — usually not actionable | Skip |

**Date filtering:** `publicationDate GreaterThan "2025-06-01"` — pull only recent signals.

**Pro tip:** Mass General had 626 news records spanning 2024-2026. Always date-filter to avoid pulling years of noise.

### 8b. Leadership Change Detection (Faster Than News)

**The executive `lastUpdatedDate` filter detects leadership changes BEFORE the news article appears.**

```json
POST /v1/hospitals/{id}/executives/search
[{"propertyName": "lastUpdatedDate", "operatorType": "GreaterThan", "value": "2026-01-01"}]
// Returns executives whose records were updated in 2026 → new hires, promotions, departures
```

Compare this against the previous executive pull to detect:
- New entries = new hires
- Changed `standardizedTitle` = promotions
- Missing entries = departures

### 8c. RFPs as Trigger Signals

**Endpoint:** `GET /v1/hospitals/{id}/requests` (no date filter needed — most hospitals have 0-3)

**High-value RFP categories for Glytec:**
- `"Technology Services"` — active IT procurement
- `"Construction - New Building/Renovations/Design"` — new units = new deployment opportunities

**RFP classifications:**
- `"Solicitation"` — real procurement
- `"Combined Synopsis/Solicitation"` — real procurement
- `"Certificate of Need"` — regulatory filing (new service lines)
- `"Definitive Healthcare Conversation"` — DH's own intelligence, NOT a public RFP

---

## 9. Filter System Reference

### 9a. Operator Types

| Operator | Value Required | Works On | Notes |
|----------|---------------|----------|-------|
| `Equals` | Yes | numeric, string, date | Exact match |
| `NotEquals` | Yes | numeric, string, date | |
| `GreaterThan` | Yes | numeric, date | Exclusive |
| `LessThan` | Yes | numeric, date | Exclusive |
| `GreaterThanOrEqual` | Yes | numeric, date | Inclusive |
| `LessThanOrEqual` | Yes | numeric, date | Inclusive |
| `In` | Yes (array) | numeric, string, date | **Must be JSON array** |
| `NotIn` | Yes (array) | numeric, string, date | |
| `StartsWith` | Yes (string 3+ chars) | string | Min 3 characters |
| `EndsWith` | Yes (string 3+ chars) | string | Min 3 characters |
| `Contains` | Yes (string 3+ chars) | string | Min 3 characters, **case-insensitive** |
| `IsNull` | No | any nullable | |
| `IsNotNull` | No | any nullable | |
| `True` | No | boolean | Use instead of `Equals true` |
| `False` | No | boolean | Use instead of `Equals false` |

### 9b. Critical Filter Rules

1. **`Contains` is case-insensitive.** `"epic"` = `"Epic"` = `"EPIC"`. No need to worry about casing.
2. **Min 3 characters** for Contains/StartsWith/EndsWith. `"VA"` → 400 error.
3. **`In` requires JSON array.** `"value": "MN,WI"` silently returns 0. Correct: `"value": ["MN", "WI"]`.
4. **`year` must be integer.** `"value": "2024"` → 400. Correct: `"value": 2024`.
5. **Multiple filters = AND logic.** No OR support. Make separate requests for OR.
6. **`state` field** — Equals/In only. No Contains/StartsWith/EndsWith on any endpoint.
7. **`credentials` field** (executives, physicians) — Equals/In only. No wildcard operators.
8. **`primaryPracticeState` field** (physicians) — Equals/In only. No wildcard operators.
9. **`contact` object** (RFPs) — IsNull/IsNotNull only. Cannot filter by contact name/email.
10. **Empty filter array → 400.** At least one filter required on all POST search endpoints.
11. **`definitiveId`** — Equals only in bulk search. No `In` operator (400 error).
12. **`academicMedicalCenter`** — Use `True`/`False` operators, not `IsNotNull`.

### 9c. Date Format

All dates use `YYYY-MM-DD` format:
```json
{"propertyName": "lastUpdatedDate", "operatorType": "GreaterThan", "value": "2026-01-01"}
{"propertyName": "publicationDate", "operatorType": "GreaterThan", "value": "2025-06-01"}
```

---

## 10. Data Quality Matrix

### Contact Fields by Reliability

| Data Point | Source | Coverage | Reliability | Pipeline Use |
|------------|--------|----------|-------------|-------------|
| **Executive standardizedTitle** | Executives endpoint | 100% | High | ICP matching — primary filter |
| **Executive linkedinProfileURL** | Executives endpoint | 91% | High | Cross-reference key for ZoomInfo/Apollo |
| **Executive positionLevel** | Executives endpoint | 100% | High | Tier filtering |
| **Executive department** | Executives endpoint | ~90% | High | ICP matching — secondary filter |
| **Executive lastUpdatedDate** | Executives endpoint | 100% | High | Freshness tracking, change detection |
| **Executive primaryEmail** | Executives endpoint | 58% | Medium | Corporate email — needs enrichment |
| **Physician NPI** | Physicians endpoint | ~100% | High | Universal cross-reference |
| **Physician primarySpecialty** | Physicians endpoint | ~100% | High | Specialty filtering |
| **RFP contact info** | Requests endpoint | When present | High | Direct buyer contact |
| **Executive directEmail** | Executives endpoint | 18% | **Useless** | 100% personal (Gmail/Yahoo). Never use. |
| **Executive directPhone** | Executives endpoint | ~30% | Low | Sparse. Use locationPhone. |
| **Executive mobilePhone** | Executives endpoint | ~15% | Low | Very sparse |

### Account Fields by Reliability

| Data Point | Source | Coverage | Reliability | Notes |
|------------|--------|----------|-------------|-------|
| Hospital demographics | Hospital summary | ~100% | High | networkId, ownership, type all present |
| EHR vendor | Technologies | ~100% | High | `vendorStatus` is dead (0%). Use `vendor` + `product`. |
| Quality metrics | Quality | ~100% | High | Multi-year, numericValue filterable |
| Financial metrics | Financials | ~100% | High | 141 metrics. Some are estimates. |
| Affiliations | Affiliations | ~100% | High | Complete network mapping |
| Memberships | Memberships | ~95% | High | GPO, ACO, CIN, HIE |
| News/Intelligence | News | Varies | Medium | 12 types. Date range varies by hospital. |
| RFPs | Requests | **Sparse** | Medium | Most hospitals have 0 |
| Technology `vendorStatus` | Technologies | **0%** | Dead | Always null. Do not use. |
| Technology `implementationYear` | Technologies | ~17% | Low | Mostly null |

---

## 11. Complete Gotcha Reference

All 27 gotchas discovered during testing, organized by category.

### Response Format Gotchas

| # | Gotcha | Impact | Mitigation |
|---|--------|--------|------------|
| 1 | Invalid hospital ID returns 200 with null object, not 404 | Silent failure | Check `definitiveId == 0` or `facilityName == null` |
| 9 | Single hospital GET returns object, not array | Parse error if expecting array | Check `data` type before iterating |

### Filter System Gotchas

| # | Gotcha | Impact | Mitigation |
|---|--------|--------|------------|
| 3 | `staffedBeds` is NOT filterable in bulk search | Cannot filter by size server-side | Use financials endpoint or client-side filter |
| 5 | Quality/Financial property is `name`, not `metric` | 400 error | Always use `name` |
| 6 | `year` filter requires integer, not string | 400 error | `"value": 2024` not `"value": "2024"` |
| 7 | `In` operator takes array, not comma-separated string | Silent 0 results | `"value": ["MN","WI"]` not `"value": "MN,WI"` |
| 8 | `definitiveId` — Equals works, `In` does not | No batch-fetch by ID | Individual GET calls per hospital |
| 14 | Multi-filter is AND logic only | No server-side OR | Separate requests + merge |
| 17 | `state` cannot use Contains/StartsWith/EndsWith | 400 error | Equals or In with exact 2-letter codes |
| 18 | Contains/StartsWith/EndsWith require min 3 characters | 400 error | Pad search terms |
| 19 | Empty filter array → 400 | Cannot dump full universe | Always include at least one filter |
| 25 | Only 2 properties unfilterable: `staffedBeds`, `academicMedicalCenter` (with IsNotNull) | | `academicMedicalCenter` uses True/False |

### Data Quality Gotchas

| # | Gotcha | Impact | Mitigation |
|---|--------|--------|------------|
| 2 | Vendor names are full legal names | 0 results with shorthand | Use Contains: `"Epic"` matches `"Epic Systems Corporation"` |
| 10 | `vendorStatus` is ALWAYS null | Cannot track install status | Rely on `vendor` + `product` only |
| 11 | `primaryEmail` 58%, `directEmail` 100% personal | Email quality poor | Use LinkedIn for cross-ref, ZoomInfo for email overwrite |
| 12 | `positionLevel` "Other" is noise | EP techs, chaplains in results | Filter: `positionLevel NotEquals "Other"` |
| 13 | RFPs are sparse | Most hospitals have 0 | Supplementary signal only |
| 20 | 1,448 closed hospitals in database | Closed facilities in results | Always filter `companyStatus Equals "Active"` |
| 21 | `payorMixSelfPay` includes commercial insurance | Misleading financial indicator | Use `netOperatingMargin` for financial health |

### Network & Hierarchy Gotchas

| # | Gotcha | Impact | Mitigation |
|---|--------|--------|------------|
| 4 | `networkParentName` is null for 4,834 hospitals | Queries on parent return 0 for many | Use both `networkName` and `networkParentName` |

### Operator Behavior Gotchas

| # | Gotcha | Impact | Mitigation |
|---|--------|--------|------------|
| 15 | No observed page size cap | Memory risk on large pulls | Use reasonable sizes (100-500) |
| 16 | `Contains` is case-insensitive | — | Actually helpful — no casing worry |

### Domain-Specific Gotchas

| # | Gotcha | Impact | Mitigation |
|---|--------|--------|------------|
| 22 | `standardizedTitle` and `department` are filterable | — | **Use this** — critical for ICP matching |
| 23 | `lastUpdatedDate` is filterable | — | **Use this** — leadership change detection |
| 24 | `numericValue` is filterable on quality/financials | — | **Use this** — server-side metric filtering |
| 26 | 12 distinct news intelligence types | Volume skew | Filter for high-value types only |
| 27 | 141 unique financial metrics | Overwhelming | Focus on key metrics listed in section 6c |

---

## 12. Facility List CSV as Account Source

### 12a. What the CSV Is (and Isn't)

`AI SDR_Facility List_1.23.26.csv` — **9,774 rows (8,458 active)** of pre-qualified hospital accounts. This file has **zero contact data** — no names, emails, phones, or LinkedIn URLs. Its value is as the **master account targeting list** that feeds Definitive IDs into the DH API for contact discovery.

### 12b. CSV Column Reference

| Column | Type | Coverage | Contact Discovery Use |
|--------|------|----------|----------------------|
| `Definitive ID` | integer | 100% | **Join key** — feeds into every DH API endpoint |
| `Hospital Name` | string | 100% | Display name, dedup check |
| `Highest Level Parent` | string | 100% | Parent system grouping (2,574 unique) |
| `Highest Level Parent Type` | enum | 100% | `IDN Parent` (4,458), `IDN` (2,571), `Non IDN` (1,429) |
| `Highest Level Parent Header/Line` | enum | 100% | `Header` = parent record (2,063), `Line` = child facility (6,395) |
| `IDN` | string | 83% | Intermediate network name (e.g., "HCA Mountain Division") |
| `Definitive IDN ID` | integer | 83% | DH ID for intermediate network |
| `IDN Parent` | string | 53% | Top-level parent (e.g., "Defense Health Agency") |
| `Definitive IDN Parent ID` | integer | 53% | DH ID for top-level parent |
| `Hospital Type` | string | 100% | Segmentation — see distribution below |
| `Electronic Health/Medical Record - Inpatient` | string | 97% | EHR vendor+product (pre-populated, saves API calls) |
| `# of Staffed Beds` | integer | 92% | Size indicator (NOT filterable in bulk DH API search) |
| `Net Operating Profit Margin` | decimal | 80% | Financial health indicator |
| `Net Patient Revenue` | currency | 80% | Revenue size |
| `ICU Inpatient Charges` / `ICU Total Charges` | currency | varies | ICU activity — Glucommander relevance signal |
| `Intensive Care Unit Beds` / `Days` | integer | 42% / varies | ICU capacity |
| `All Cause Hospital-Wide Readmission Rate` | decimal | 50% | Quality signal |
| `Patient Survey (HCAHPS) Summary Star Rating` | integer | 37% | Quality signal |
| `Hospital Compare Overall Rating` | integer | varies | CMS star rating |
| `Computerized Physician Order Entry (CPOE)` | string | 86% | CPOE vendor — IT maturity signal |
| `State`, `City`, `Zip Code`, `County`, `Region` | string | 100% | Geography |
| `Geographic Classification` | enum | 100% | Urban (5,935) / Rural (2,523) |
| `Hospital ownership` | string | 93% | Ownership type |
| `Closed` | boolean | 100% | TRUE = closed. Always filter to FALSE. |
| `Company Status` | string | 100% | "Active" or "Closed" |
| `DHC Profile Link` | URL | 100% | Link to DH profile |

### 12c. Hospital Type Distribution (Active Only)

| Hospital Type | Count | Contact Discovery Notes |
|---------------|-------|------------------------|
| Short Term Acute Care Hospital | 4,479 | **Primary target.** Highest executive density. |
| Critical Access Hospital | 1,440 | Small rural hospitals. Fewer executives, limited ICU. |
| Health System | 1,157 | System-level records. May have system-level execs. |
| Psychiatric Hospital | 994 | Different ICP — less Glucommander-relevant. |
| Long Term Acute Care Hospital | 582 | Insulin management relevant. Smaller exec teams. |
| Rehabilitation Hospital | 560 | Some insulin relevance. Smaller teams. |
| Children's Hospital | 298 | Pediatric insulin — different buyer persona. |
| VA Hospital | 168 | Government procurement. Different sales motion. |
| Department of Defense Hospital | 44 | Government. Oracle Cerner/MHS GENESIS dominant. |
| Rural Emergency Hospital | 32 | New category. Minimal staffing. |
| Religious Non-Medical Health Care Institution | 20 | Not relevant. |

### 12d. Parent Structure (Who Owns What)

The CSV encodes a 3-tier hierarchy:

```
IDN Parent (top)  →  IDN (middle)  →  Facility (bottom)

Example:
  HCA Healthcare (IDN Parent, 249 facilities)
    → HCA Mountain Division (IDN)
      → Alaska Regional Hospital (Line, Def ID 122)
    → HCA North Carolina Division (IDN)
      → Angel Medical Center (Line, Def ID 2999)
```

**Top 10 parents by facility count:**

| Parent | Facilities | Type |
|--------|-----------|------|
| HCA Healthcare | 249 | IDN Parent |
| Universal Health Services | 201 | IDN Parent |
| Department of Veterans Affairs | 180 | IDN Parent |
| Encompass Health | 175 | IDN Parent |
| CommonSpirit Health | 170 | IDN Parent |
| Select Medical | 121 | IDN Parent |
| Trinity Health | 106 | IDN Parent |
| Ascension Health | 106 | IDN Parent |
| LifePoint Health | 105 | IDN Parent |
| ScionHealth | 93 | IDN Parent |

### 12e. What's NOT in This CSV

- No executive names, titles, emails, phones, or LinkedIn URLs
- No physician data
- No news/trigger signals
- No RFP/procurement contacts
- No GPO/ACO membership data
- No technology vendor detail beyond the single EHR field

**The CSV provides the "where to look" — the DH API provides the "who to contact."**

---

## 13. Supporting Data Files

### 13a. Supplemental Data (`AI SDR_Facility List_Supplemental Data_1.23.26.csv`)

5,475 rows — a subset of the facility list with rep assignments. Same facility columns plus:

| Column | Notes |
|--------|-------|
| `Assigned Rep` | Rep territory assignment |

**Rep distribution:** Non Team Maike (3,995), Khirstyn (445), Reagan (426), Ian (381), Victoria (228)

**Use:** Filter contact discovery to specific rep territories. When pulling contacts for a rep's accounts, filter the facility list by `Assigned Rep` first, then run DH API calls only for those Definitive IDs.

### 13b. Parent Account List (`AI SDR_Parent Account List_1.23.26.csv`)

1,683 parent systems. Key columns not in the facility list:

| Column | Coverage | Notes |
|--------|----------|-------|
| `Rank` | 100% | System priority ranking |
| `SFDC Account ID` | 100% | Salesforce account ID — CRM join key |
| `Segment` | 100% | Commercial (1,329), Enterprise/Strategic (296), Partner Growth (54), Government (4) |
| `Total $ Opp` / `Adj Total $ Opp` | varies | Dollar opportunity estimate |
| `Glytec Client - 8.31.25` | 100% | 54 current clients (exclude from outbound) |
| `GC $ Opp` / `CC $ Opp` | varies | GluCommander vs ClearConnect opportunity |

**Gotcha:** The `Definitive ID (validate!!)` column is **100% empty** in this file. The "validate!!" in the column name is a flag that this data was never populated. You must join parent accounts to facilities via `System Name` ↔ `Highest Level Parent` (string match), NOT by Definitive ID.

**Use:** Prioritize contact discovery by segment (Enterprise/Strategic first), exclude current clients, use SFDC Account ID to push contacts back to Salesforce.

### 13c. ICP Titles (`AI SDR_ICP Titles_2.12.26.csv`)

66 target titles across 18 departments. This is the **ICP matching key** that maps to DH API `standardizedTitle` and `department` fields.

**Department distribution:**

| Department | # Titles | DH API Filter |
|------------|---------|---------------|
| Surgery | 10 | `department Contains "Surg"` |
| Hospital Medicine | 8 | `standardizedTitle Contains "Hospital"` or `"Medicine"` |
| Nursing | 8 | `department Contains "Nurs"` |
| Pharmacy | 6 | `department Contains "Pharm"` |
| Critical Care | 5 | `department Contains "Critical"` or `"ICU"` |
| Endocrinology | 5 | `standardizedTitle Contains "Endocrin"` |
| Clinical Informatics | 4 | `department Contains "Informati"` |
| Quality Improvement | 4 | `department Contains "Quality"` |
| Diabetes Services | 3 | `standardizedTitle Contains "Diabetes"` |
| Patient Safety | 3 | `department Contains "Safety"` |
| Executive Leadership | 2 | `positionLevel Equals "C-Level"` |
| Nursing Informatics | 2 | `standardizedTitle Contains "Nursing Informati"` |
| Others (7 depts) | 1 each | Compliance, Data, Diversity, Finance, Innovation, Strategy |

**Intent Score tiers:**
- **90-95 (7 titles):** CEO, CNO, CMIO, COO, CFO, CQO, Chief of Endocrinology
- **80-85 (23 titles):** Directors and department heads
- **60-75 (36 titles):** Influencers, coordinators, individual contributors

---

## 14. Recipes & Patterns

### Recipe 1: Full Contact Extraction for a Single Hospital

Given a `Definitive ID` from the CSV, pull every conceivable contact.

```
INPUT: Definitive ID 2151 (Abbott Northwestern Hospital)

═══ EXECUTIVES (primary contact source) ═══

Call 1: All executives (no filter) — gets the full picture
  GET /v1/hospitals/2151/executives?page[size]=500
  → ~78 executives at this hospital

Call 2 (optional): ICP-filtered executives only
  POST /v1/hospitals/2151/executives/search
  [{"propertyName": "positionLevel", "operatorType": "In",
    "value": ["C-Level", "Vice President", "Manager/Director"]}]
  → Drops ~14 "Other" noise contacts (EP techs, chaplains)

OUTPUT per executive:
  - firstName, lastName (name)
  - standardizedTitle (for ICP matching)
  - department (for ICP matching)
  - positionLevel (C-Level / VP / Director)
  - primaryEmail (58% coverage — corporate email)
  - linkedinProfileURL (91% — cross-reference key)
  - directPhone / locationPhone (sparse)
  - lastUpdatedDate (freshness)
  - executiveId, personId (dedup keys)

═══ PHYSICIANS (secondary contact source) ═══

Call 3: All affiliated physicians
  GET /v1/hospitals/2151/physicians/affiliated?page[size]=500
  → 100+ physicians

Call 4 (targeted): Endocrinology/diabetes-relevant specialties
  POST /v1/hospitals/2151/physicians/affiliated/search
  [{"propertyName": "primarySpecialty", "operatorType": "Contains",
    "value": "Endocrinology"}]

  Also try:
  [{"propertyName": "primarySpecialty", "operatorType": "Contains",
    "value": "Internal Medicine"}]
  [{"propertyName": "role", "operatorType": "Contains",
    "value": "Medical Director"}]

OUTPUT per physician:
  - firstName, lastName
  - npi (universal cross-reference → ZoomInfo, NPPES, CMS)
  - primarySpecialty
  - role
  - primaryPracticeLocationPhone
  - primaryHospitalAffiliationDefinitiveID (their "home" hospital)
  - secondaryHospitalAffiliationDefinitiveID (multi-hospital influence)
  - medicareClaimPayments, medicareUniquePatients (volume/influence indicators)

═══ RFP CONTACTS (rare but high-value) ═══

Call 5: RFPs
  GET /v1/hospitals/2151/requests?page[size]=100
  → Usually 0. When present: named buyer with email and phone.

OUTPUT per RFP (when it exists):
  - contact.name
  - contact.email
  - contact.phone
  - contact.title (e.g., "Contracting Officer")
  - category (filter for "Technology Services")

═══ NEWS-DERIVED CONTACTS ═══

Call 6: Leadership change news
  POST /v1/hospitals/2151/newsandintelligence/search
  [{"propertyName": "intelligenceType", "operatorType": "Contains",
    "value": "People"},
   {"propertyName": "publicationDate", "operatorType": "GreaterThan",
    "value": "2025-06-01"}]

OUTPUT: bodyOfArticle often names the person, their new title, and where
they came from. Parse article text to extract:
  - Person name
  - New title/role
  - Previous organization (referral source)
  - Date of change

TOTAL CONTACTS PER HOSPITAL: Typically 80-200
  ~78 executives + 100+ physicians + 0-3 RFP contacts + news-derived names
```

### Recipe 2: ICP-Matched Contact Discovery (Using ICP Titles CSV)

Map the 66 ICP titles to DH API filters. Because DH uses `standardizedTitle` (not identical to ICP titles), you need fuzzy matching via `Contains`.

```
INPUT: ICP Titles CSV + Definitive ID

═══ STEP 1: Build DH API filter queries from ICP departments ═══

The 66 ICP titles span 18 departments. Group into DH API search batches:

Batch A — Executive Leadership (Intent 90-95)
  [{"propertyName": "positionLevel", "operatorType": "Equals", "value": "C-Level"}]
  Catches: CEO, CNO, COO, CFO, CQO, CMIO, Chief Compliance Officer, etc.

Batch B — Pharmacy (Intent 60-85)
  [{"propertyName": "department", "operatorType": "Contains", "value": "Pharm"}]
  Catches: Chief Pharmacy Officer, Director of Clinical Pharmacy,
           Pharmacy Clinical Coordinator, Clinical Pharmacist

Batch C — Nursing (Intent 50-95)
  [{"propertyName": "department", "operatorType": "Contains", "value": "Nurs"}]
  Catches: CNO, Director of Inpatient Nursing, Nurse Educator,
           Clinical Nurse Specialist, Nursing Informatics

Batch D — Quality/Safety (Intent 60-90)
  [{"propertyName": "department", "operatorType": "Contains", "value": "Quality"}]
  +
  [{"propertyName": "department", "operatorType": "Contains", "value": "Safety"}]
  Catches: CQO, Director of Quality Improvement, Patient Safety Officer,
           Quality Coordinator, Risk Manager

Batch E — Clinical Informatics (Intent 70-90)
  [{"propertyName": "department", "operatorType": "Contains", "value": "Informati"}]
  Catches: CMIO, Director of Clinical Informatics, Clinical Informaticist,
           Nursing Informatics

Batch F — Critical Care / ICU (Intent 60-80)
  [{"propertyName": "department", "operatorType": "Contains", "value": "Critical"}]
  +
  [{"propertyName": "standardizedTitle", "operatorType": "Contains", "value": "ICU"}]
  Catches: Chief of Critical Care, Medical Director ICU,
           ICU Clinical Nurse Specialist, ICU Quality Coordinator

Batch G — Surgery (Intent 65-85)
  [{"propertyName": "department", "operatorType": "Contains", "value": "Surg"}]
  Catches: Surgical ICU Director, Chief of Cardiothoracic/Vascular/General
           Surgery, Perioperative Medical Director

Batch H — Endocrinology/Diabetes (Intent 60-90)
  [{"propertyName": "standardizedTitle", "operatorType": "Contains",
    "value": "Endocrin"}]
  +
  [{"propertyName": "standardizedTitle", "operatorType": "Contains",
    "value": "Diabetes"}]
  Catches: Chief of Endocrinology, Medical Director Diabetes Services,
           Diabetes Program Coordinator, CDCES

Batch I — Hospital Medicine (Intent 65-85)
  [{"propertyName": "standardizedTitle", "operatorType": "Contains",
    "value": "Hospital"}]
  +
  [{"propertyName": "standardizedTitle", "operatorType": "Contains",
    "value": "Medicine"}]
  Catches: Medical Director of Hospital Medicine, Hospitalist,
           Clinical Operations Lead, Chair of Medicine

═══ STEP 2: Execute batches per hospital ═══

For each Definitive ID:
  - Run 9-12 POST searches (batches A through I, some have 2 queries)
  - Merge results, deduplicate by executiveId
  - Match each executive against ICP title list for Intent Score assignment

═══ STEP 3: Score and rank contacts ═══

For each matched contact:
  intent_score = ICP title match score (50-95)
  has_email = 1 if primaryEmail is not null, 0 otherwise
  has_linkedin = 1 if linkedinProfileURL is not null, 0 otherwise
  freshness = 1 if lastUpdatedDate > 6 months ago, 0 otherwise

  contact_priority = intent_score + (has_email * 5) + (has_linkedin * 5) + (freshness * 5)

  Sort by contact_priority descending.
```

### Recipe 3: Full Network Contact Map (All Contacts at Every Facility in a System)

When targeting an IDN, you need contacts across ALL their facilities, not just one.

```
INPUT: "CommonSpirit Health" (170 facilities in CSV)

═══ STEP 1: Get all facility Definitive IDs from CSV ═══

  Filter CSV: Highest Level Parent = "CommonSpirit Health" AND Closed = FALSE
  → Returns ~170 rows with Definitive IDs

  Alternatively (from DH API — may catch facilities not in CSV):
  POST /v1/hospitals/search
  [{"propertyName": "networkName", "operatorType": "Contains",
    "value": "CommonSpirit"}]

  AND also check the parent level:
  POST /v1/hospitals/search
  [{"propertyName": "networkParentName", "operatorType": "Contains",
    "value": "CommonSpirit"}]

  Merge both result sets (some facilities only match one).

═══ STEP 2: Pull executives from EVERY facility ═══

  For each Definitive ID (parallelize 5-10 at a time):
    GET /v1/hospitals/{id}/executives?page[size]=500

  Total across 170 facilities: likely 5,000-15,000 executive records

═══ STEP 3: Deduplicate across facilities ═══

  Same person may appear at multiple facilities in the system.
  Dedup key: executiveId (or personId)

  For each unique person, record ALL their facility affiliations:
    {
      personId: 12345,
      name: "Jane Smith",
      title: "VP of Nursing",
      facilities: [
        {definitiveId: 2151, name: "Abbott Northwestern"},
        {definitiveId: 2119, name: "Mercy Hospital"}
      ],
      linkedinProfileURL: "...",
      primaryEmail: "..."
    }

  People appearing at multiple facilities = system-level decision makers.
  Prioritize them.

═══ STEP 4: ICP filter the deduped contacts ═══

  Apply Recipe 2's ICP matching to the deduped list.
  Tag each contact with:
    - ICP match (which title/department)
    - Intent score
    - Facility count (how many facilities they span)
    - Position level

═══ STEP 5: Identify system-level vs. facility-level contacts ═══

  System-level contacts (appear at 3+ facilities or have system-wide titles):
    → Target for IDN-level conversations
    → Likely have "System" or "Corporate" in their title

  Facility-level contacts (appear at 1 facility):
    → Target for facility-level pilot conversations
    → May be the champion who opens the door for the system deal

═══ STEP 6: Supplement with physicians ═══

  For the top-priority facilities (by bed count, ICU beds from CSV):
    POST /v1/hospitals/{id}/physicians/affiliated/search
    [{"propertyName": "primarySpecialty", "operatorType": "Contains",
      "value": "Endocrinology"}]

  Extract NPIs for external enrichment.

EXPECTED OUTPUT: 1,000-3,000 unique contacts across the system
  with ICP scores, facility mappings, and contact info coverage.
```

### Recipe 4: Tiered Contact Discovery Using All CSV Data Sources

Use the Parent Account List for prioritization, Facility List for account details, and ICP Titles for filtering.

```
INPUT: All three CSVs + DH API

═══ TIER 1: Enterprise/Strategic accounts (296 parent systems) ═══

  Filter Parent Account List: Segment = "Enterprise/Strategic"
  Exclude: Glytec Client = "Current Client" (54 systems)
  Sort by: Adj Total $ Opp descending
  → ~242 target parent systems

  For each parent system:
    1. Match to Facility List via System Name ↔ Highest Level Parent
       (string match — Parent Account List has NO Definitive IDs)
    2. Get all child facility Definitive IDs (Lines under this Header)
    3. Run Recipe 3 (full network contact map) for each system

  API calls: ~242 systems × ~15 facilities avg × 2 calls = ~7,260 calls
  Expected contacts: ~50,000-75,000 across all Enterprise accounts

═══ TIER 2: Commercial accounts with ICU activity (high Glucommander fit) ═══

  Filter Parent Account List: Segment = "Commercial"
  Filter Facility List:
    - Intensive Care Unit Beds > 0 (3,590 facilities, 42% of active)
    - OR ICU Inpatient Charges > 0
    - Hospital Type IN ("Short Term Acute Care Hospital", "Critical Access Hospital")
  Sort by: ICU beds × readmission rate (proxy for insulin management need)

  For each facility:
    Run Recipe 1 (full contact extraction), focusing on:
    - Batch F (Critical Care contacts)
    - Batch H (Endocrinology/Diabetes contacts)
    - Batch B (Pharmacy contacts)
    - Batch A (C-suite)

═══ TIER 3: Trigger-activated accounts ═══

  For all active facilities in CSV:
    Check for recent trigger signals:
    POST /v1/hospitals/{id}/newsandintelligence/search
    [{"propertyName": "publicationDate", "operatorType": "GreaterThan",
      "value": "2025-12-01"}]

    Also check for recently updated executives:
    POST /v1/hospitals/{id}/executives/search
    [{"propertyName": "lastUpdatedDate", "operatorType": "GreaterThan",
      "value": "2025-12-01"}]

  Hospitals with trigger signals get promoted regardless of tier.
  Pull full contacts (Recipe 1) for any triggered hospital.

═══ TIER 4: Rep-territory contact extraction ═══

  Filter Supplemental Data by Assigned Rep (e.g., "Khirstyn" = 445 facilities)
  For each rep's territory:
    Run Recipe 1 for each facility
    Output contact list grouped by rep territory
```

### Recipe 5: EHR-Segmented Contact Discovery (Using CSV EHR Data)

The CSV already has EHR populated for 97% of facilities — no need to call the technologies API for most hospitals.

```
INPUT: Facility List CSV (EHR column pre-populated)

═══ STEP 1: Segment by EHR from CSV (skip API for this) ═══

  Epic shops (3,332 facilities):
    CSV column contains "Epic Systems Corporation"
    Variants: ClinDoc (2,032), base (950), Hyperdrive (178), MyChart (172)

  Oracle Cerner shops (1,534 facilities):
    CSV column contains "Oracle Cerner"
    Variants: Millennium (572), base (524), PowerChart (438)

  MEDITECH shops (831 facilities):
    CSV column contains "MEDITECH"
    Variants: base (379), Expanse (251), Magic (120), Client Server (81)

  Other EHR (2,508 facilities):
    WellSky (204), Vista (155), Netsmart (152), MEDHOST (202),
    TruBridge (308), Altera (86), others

  No EHR data (253 facilities):
    Fall back to DH API technologies endpoint for these only.

═══ STEP 2: Pull contacts with EHR-specific ICP weighting ═══

  For Epic hospitals — prioritize IT/Informatics contacts:
    POST /v1/hospitals/{id}/executives/search
    [{"propertyName": "department", "operatorType": "Contains",
      "value": "Informati"}]
    → These are the people managing Epic customizations and
      "DIY insulin calculators" you're replacing.

  For Oracle Cerner hospitals — prioritize operational leadership:
    POST /v1/hospitals/{id}/executives/search
    [{"propertyName": "positionLevel", "operatorType": "In",
      "value": ["C-Level", "Vice President"]}]
    → Oracle transition creates urgency at the leadership level.

  For MEDITECH hospitals — prioritize quality/safety contacts:
    POST /v1/hospitals/{id}/executives/search
    [{"propertyName": "department", "operatorType": "Contains",
      "value": "Quality"}]
    → Modernization angle resonates with quality teams.

  For ALL hospitals — always pull endocrinology and pharmacy:
    POST /v1/hospitals/{id}/executives/search
    [{"propertyName": "department", "operatorType": "Contains",
      "value": "Pharm"}]
    +
    POST /v1/hospitals/{id}/executives/search
    [{"propertyName": "standardizedTitle", "operatorType": "Contains",
      "value": "Endocrin"}]

═══ STEP 3: Tag each contact with their hospital's EHR ═══

  This enrichment data (from CSV) attaches to every contact pulled:
    contact.ehr_vendor = "Epic Systems Corporation"
    contact.ehr_product = "ClinDoc"
    contact.message_angle = "DIY calculator liability"
```

### Recipe 6: Financial Distress + Quality Penalty Contact Discovery

Use CSV financial data to pre-filter, then enrich from API.

```
INPUT: Facility List CSV (Net Operating Profit Margin column)

═══ STEP 1: Pre-filter from CSV ═══

  Financially distressed facilities:
    Filter: Net Operating Profit Margin < 0 (negative margin)
    → ~4,700 facilities (55.9% of active — this is why it's a huge market)

  Further narrow to ICU-active:
    Filter: Intensive Care Unit Beds > 0
    → ~2,100 facilities (distressed AND have ICU)

═══ STEP 2: Enrich with quality penalties from API ═══

  For each of the ~2,100 facilities:
    POST /v1/hospitals/{id}/quality/search
    [{"propertyName": "name", "operatorType": "Contains", "value": "HAC"},
     {"propertyName": "numericValue", "operatorType": "GreaterThan", "value": 0}]

  Hospitals with negative margin + active HAC penalty = **highest urgency**.

═══ STEP 3: Pull contacts at highest-urgency hospitals ═══

  For hospitals with both distress signals:
    Run Recipe 1 (full contact extraction)
    Prioritize:
    - CFO (financial pain point owner)
    - CQO / Quality Director (quality penalty owner)
    - CNO (nursing operations owner)
    - CMO (clinical outcomes owner)

  For each contact, attach enrichment:
    contact.hospital_margin = -0.12
    contact.hac_penalty = true
    contact.hac_score = 10.83
    contact.message = "ROI: $20K/bed savings + CMS penalty mitigation"
```

### Recipe 7: Contact Discovery by Geography and Rep Territory

```
INPUT: Supplemental Data CSV (Assigned Rep) + Facility List CSV

═══ STEP 1: Build rep territory account lists ═══

  For each assigned rep:
    Khirstyn: 445 facilities → get all Definitive IDs
    Reagan: 426 facilities → get all Definitive IDs
    Ian: 381 facilities → get all Definitive IDs
    Victoria: 228 facilities → get all Definitive IDs
    Non Team Maike: 3,995 → lower priority (unassigned)

═══ STEP 2: Priority-order facilities within each territory ═══

  Sort by:
    1. Hospital Type (SAC > CAH > LTAC > Rehab > Psych)
    2. # of Staffed Beds (descending)
    3. ICU Beds > 0 (boolean boost)
    4. Net Operating Profit Margin (negative gets priority)

═══ STEP 3: Pull contacts for each rep's top facilities ═══

  For each rep, process their facilities in priority order:
    Run Recipe 2 (ICP-matched contact discovery) per facility
    Stop after reaching target contact count per rep (e.g., 500 contacts)

═══ STEP 4: Geographic clustering (for non-assigned facilities) ═══

  For the 3,995 "Non Team Maike" facilities:
    Group by state → region → CBSA area
    Process densest geographic clusters first
    (More facilities in an area = more efficient outreach)
```

### Recipe 8: Physician Champion Discovery Pipeline

Physicians are harder to contact but carry clinical authority. This recipe finds the endocrinologists and hospitalists who would champion Glucommander internally.

```
INPUT: Facility List CSV (Definitive IDs for hospitals with ICU activity)

═══ STEP 1: Filter to high-value facilities from CSV ═══

  Filter: Intensive Care Unit Beds > 10 AND Hospital Type = "Short Term Acute Care Hospital"
  → ~2,500 facilities

═══ STEP 2: Pull endocrinology physicians at each facility ═══

  POST /v1/hospitals/{id}/physicians/affiliated/search
  [{"propertyName": "primarySpecialty", "operatorType": "Contains",
    "value": "Endocrinology"}]

  If 0 results (common — many hospitals have no endocrinologist on staff):
    Try broader:
    [{"propertyName": "primarySpecialty", "operatorType": "Contains",
      "value": "Internal Medicine"}]
    Then filter client-side for diabetes/endocrine relevance.

    Also try:
    [{"propertyName": "role", "operatorType": "Contains",
      "value": "Medical Director"}]
    → Medical Directors who oversee insulin protocols.

═══ STEP 3: Pull hospitalist physicians ═══

  [{"propertyName": "primarySpecialty", "operatorType": "Contains",
    "value": "Hospital Medicine"}]
  +
  [{"propertyName": "primarySpecialty", "operatorType": "Contains",
    "value": "Internal Medicine"}]

  Filter client-side for those with:
    - medicareUniquePatients > 200 (high-volume physicians)
    - role Contains "Director" or "Chief" (leadership physicians)

═══ STEP 4: Discover multi-hospital influence ═══

  For each physician found:
    Check primaryHospitalAffiliationDefinitiveID
    Check secondaryHospitalAffiliationDefinitiveID

    If physician is affiliated with MULTIPLE hospitals in the CSV:
      → This physician has cross-facility influence
      → Prioritize them as a network-level champion

═══ STEP 5: Cross-reference for contact info ═══

  Physician records lack email. For contact info:
    1. NPI → NPPES (National Plan and Provider Enumeration System)
       → Practice address, phone, specialty verification
    2. NPI → ZoomInfo/Apollo → email, social profiles
    3. Name + hospital → LinkedIn search
    4. Check if they also appear in executives endpoint
       (some physician leaders are in both — they'll have LinkedIn URL there)

  POST /v1/hospitals/{id}/executives/search
  [{"propertyName": "physicianLeader", "operatorType": "True"}]
  → Physician leaders who appear as executives have richer contact data
     (LinkedIn 91%, primaryEmail 58%)
```

### Recipe 9: Comprehensive Account Enrichment Bundle (CSV + API Combined)

For each target hospital, combine CSV data (already have) with API data (need to fetch).

```
INPUT: Single Definitive ID + its CSV row

═══ DATA ALREADY IN CSV (no API calls needed) ═══

  From facility row:
    - Hospital Name, Address, City, State, Zip
    - Highest Level Parent (→ link to Parent Account List for segment, $ opp, SFDC ID)
    - Hospital Type, Firm Type
    - EHR vendor+product (97% populated)
    - # of Staffed Beds (92%)
    - Net Operating Profit Margin (80%)
    - ICU Beds, ICU Charges
    - Readmission Rate, HCAHPS Rating
    - Geographic Classification, Region
    - Ownership, 340B Classification
    - CPOE vendor

  From parent account list (join via Highest Level Parent ↔ System Name):
    - Segment (Enterprise/Strategic, Commercial, etc.)
    - SFDC Account ID (for CRM push)
    - Total $ Opportunity
    - Glytec Client status (exclude if current client)
    - Rank

═══ DATA FROM API (6-10 calls per hospital) ═══

  CONTACTS (the main goal):
    1. GET /v1/hospitals/{id}/executives?page[size]=500       → all executives
    2. POST /v1/hospitals/{id}/physicians/affiliated/search   → ICP-relevant physicians
    3. GET /v1/hospitals/{id}/requests                        → RFP buyer contacts

  ENRICHMENT (attach to each contact):
    4. GET /v1/hospitals/{id}/quality                         → CMS penalties
    5. GET /v1/hospitals/{id}/memberships                     → GPO/ACO
    6. GET /v1/hospitals/{id}/newsandintelligence              → trigger signals
    7. GET /v1/hospitals/{id}/affiliations                    → sibling facilities

  ONLY IF CSV DATA IS MISSING:
    8. GET /v1/hospitals/{id}                                 → demographics (CSV has most of this)
    9. GET /v1/hospitals/{id}/technologies/currentimplementations → EHR (CSV has this for 97%)
    10. GET /v1/hospitals/{id}/financials                     → financial detail (CSV has margin)

═══ OUTPUT: Enriched contact record ═══

  {
    // Person
    "name": "Jane Smith",
    "title": "Chief Nursing Officer",
    "department": "Nursing",
    "positionLevel": "C-Level",
    "primaryEmail": "jsmith@allinahealth.org",
    "linkedinProfileURL": "https://linkedin.com/in/...",
    "lastUpdatedDate": "2026-01-15",
    "icpMatch": "Chief Nursing Officer (CNO)",
    "intentScore": 95,

    // Hospital (from CSV)
    "hospital": "Abbott Northwestern Hospital",
    "definitiveId": 2151,
    "state": "MN",
    "staffedBeds": 627,
    "icuBeds": 92,
    "ehrVendor": "Epic Systems Corporation - ClinDoc",
    "operatingMargin": -0.03,
    "hospitalType": "Short Term Acute Care Hospital",

    // System (from Parent Account List)
    "parentSystem": "Allina Health",
    "segment": "Enterprise/Strategic",
    "sfdcAccountId": "001Nt00000...",
    "totalOpportunity": "$2,400,000",
    "glytecClient": false,

    // Enrichment (from API)
    "hacPenalty": true,
    "hacScore": 10.83,
    "gpo": "Vizient",
    "recentTrigger": "New CNO appointed Sep 2025",
    "messageAngle": "DIY calculator liability + ROI ($20K/bed)",
    "networkFacilityCount": 14,

    // Rep assignment (from Supplemental Data)
    "assignedRep": "Khirstyn"
  }
```

### Recipe 10: The "Get Every Contact at This Company" Approach

When you want to be exhaustive — every possible contact at a parent system.

```
INPUT: Parent system name (e.g., "Tenet Healthcare")

═══ STEP 1: Identify all facilities ═══

  Source A — CSV:
    Filter: Highest Level Parent = "Tenet Healthcare" AND Closed = FALSE
    → 92 facilities with Definitive IDs

  Source B — DH API (catches facilities not in CSV):
    POST /v1/hospitals/search
    [{"propertyName": "networkParentName", "operatorType": "Equals",
      "value": "Tenet Healthcare"},
     {"propertyName": "companyStatus", "operatorType": "Equals",
      "value": "Active"}]

    POST /v1/hospitals/search
    [{"propertyName": "networkName", "operatorType": "Contains",
      "value": "Tenet"},
     {"propertyName": "companyStatus", "operatorType": "Equals",
      "value": "Active"}]

  Source C — Affiliations (catches non-hospital affiliates):
    For each facility from Sources A/B:
      GET /v1/hospitals/{id}/affiliations?page[size]=500
    → Includes ASCs, SNFs, Rural Health Clinics not in the hospital universe

  Merge all three sources. Deduplicate by Definitive ID.

═══ STEP 2: Pull EVERY executive at EVERY facility ═══

  For each Definitive ID (parallelize 5-10):
    GET /v1/hospitals/{id}/executives?page[size]=500

  Estimated total: 92 facilities × 50-80 execs = 4,600-7,360 records

═══ STEP 3: Pull physicians at high-priority facilities ═══

  Filter to facilities with ICU Beds > 0 (from CSV):
    For each:
      GET /v1/hospitals/{id}/physicians/affiliated?page[size]=500

  Focus on: endocrinology, hospitalists, medical directors

═══ STEP 4: Check every facility for RFPs ═══

  For each facility:
    GET /v1/hospitals/{id}/requests
  → Most return 0. When they don't, the contact is gold.

═══ STEP 5: Pull news for leadership-change-derived contacts ═══

  For each facility:
    POST /v1/hospitals/{id}/newsandintelligence/search
    [{"propertyName": "intelligenceType", "operatorType": "Contains",
      "value": "People"},
     {"propertyName": "publicationDate", "operatorType": "GreaterThan",
      "value": "2025-01-01"}]

  Parse article bodies for names not in the executives list
  (people who left, people in transition, people from other orgs mentioned).

═══ STEP 6: Deduplicate and enrich ═══

  Dedup executives by executiveId across all facilities.
  Dedup physicians by npi across all facilities.
  Flag multi-facility people as system-level contacts.
  Apply ICP matching (Recipe 2).
  Attach hospital enrichment (Recipe 9).

═══ CONTACT TYPES DISCOVERED ═══

  1. Executives (from executives endpoint) — ~2,000-4,000 unique after dedup
  2. Physicians (from physicians endpoint) — ~500-2,000 unique
  3. RFP buyers (from requests endpoint) — 0-10 (rare but valuable)
  4. News-mentioned people (from news endpoint) — 10-50 (parse article text)

  TOTAL: 2,500-6,000+ unique contacts per large health system

═══ API CALL BUDGET ═══

  92 facilities × (1 exec + 1 physician + 1 RFP + 1 news) = ~368 calls
  + facility discovery calls = ~375 total
  At 5 concurrent: ~75 batches × ~1 sec = ~75 seconds
```

---

## 15. Contact Type Summary

Every conceivable contact type available through the DH API + CSV pipeline:

| Contact Type | Source | How to Find | Coverage | Quality |
|-------------|--------|------------|----------|---------|
| **C-Suite executives** (CEO, CNO, CFO, CMO, CIO, CQO) | Executives endpoint | `positionLevel Equals "C-Level"` | ~1-5 per hospital | High — 91% LinkedIn |
| **VP-level** | Executives endpoint | `positionLevel Equals "Vice President"` | ~5-10 per hospital | High |
| **Directors** | Executives endpoint | `positionLevel Equals "Manager/Director"` | ~50-60 per hospital | High |
| **Department-specific contacts** | Executives endpoint | `department Contains "{dept}"` | Varies | High |
| **ICP-matched contacts** | Executives endpoint | `standardizedTitle Contains "{keyword}"` | Varies | High |
| **Recently changed contacts** | Executives endpoint | `lastUpdatedDate GreaterThan "{date}"` | ~2-5% of execs | High |
| **Physician leaders** | Executives endpoint | `physicianLeader True` | ~5-10 per hospital | High (91% LinkedIn) |
| **Endocrinologists** | Physicians endpoint | `primarySpecialty Contains "Endocrinology"` | 0-5 per hospital | Medium (NPI only) |
| **Hospitalists** | Physicians endpoint | `primarySpecialty Contains "Hospital Medicine"` | 10-50 per hospital | Medium (NPI only) |
| **Medical directors** | Physicians endpoint | `role Contains "Medical Director"` | 5-15 per hospital | Medium |
| **High-volume physicians** | Physicians endpoint | `medicareUniquePatients GreaterThan 500` | Varies | Medium |
| **RFP procurement contacts** | Requests endpoint | Check `contact` object | 0-3 per hospital | Very high when present |
| **News-mentioned people** | News endpoint | `intelligenceType Contains "People"` | Varies | Must parse article text |
| **Multi-facility executives** | Cross-facility dedup | Appear at 2+ facilities | Rare but very valuable | System-level influence |

---

## Appendix: Field-to-Endpoint Quick Reference

| I Need... | Endpoint | Key Filter |
|-----------|----------|------------|
| Hospital demographics | `GET /v1/hospitals/{id}` or **CSV** (faster) | — |
| Hospitals by state/type/network | `POST /v1/hospitals/search` or **CSV** (pre-filtered) | See section 2b |
| Executive contacts | `GET/POST .../executives` | `standardizedTitle`, `positionLevel`, `department` |
| Executive emails | `GET .../executives` | `primaryEmail` (58%). Never use `directEmail`. |
| Executive LinkedIn | `GET .../executives` | `linkedinProfileURL` (91%) |
| Recently changed executives | `POST .../executives/search` | `lastUpdatedDate GreaterThan "{date}"` |
| Physician contacts | `GET/POST .../physicians/affiliated` | `primarySpecialty`, `npi` |
| EHR vendor | **CSV** (97% populated) or `GET/POST .../technologies/...` | `vendor Contains "{name}"` |
| Financial health | **CSV** (80% have margin) or `POST .../financials/search` | `name Contains "netOperatingMargin"` |
| Bed count | **CSV** (92% populated) | `# of Staffed Beds` column |
| ICU activity | **CSV** | `Intensive Care Unit Beds`, `ICU Inpatient Charges` |
| IT budget | `POST .../financials/search` (not in CSV) | `name Contains "budgetOperatingIT"` |
| CMS penalties | `POST .../quality/search` (not in CSV) | `name Contains "HAC"` or `"readmission"` |
| Leadership changes | `POST .../newsandintelligence/search` | `intelligenceType Contains "People"` |
| M&A activity | `POST .../newsandintelligence/search` | `intelligenceType Contains "Merger"` |
| EHR migration signals | `POST .../newsandintelligence/search` | `intelligenceType Contains "Information Technology"` |
| RFP buyer contacts | `GET .../requests` | Check `contact` object |
| Network siblings | `POST /v1/hospitals/search` or **CSV** (`Highest Level Parent`) | `networkName Equals "{name}"` |
| Affiliated facilities | `GET/POST .../affiliations` | Includes non-hospitals (ASCs, SNFs) |
| GPO membership | `POST .../memberships/search` (not in CSV) | `type Equals "Group Purchasing Organization"` |
| All facilities in holding company | **CSV** (`Highest Level Parent`) or `POST /v1/hospitals/search` | `networkParentName Equals "{name}"` |
| Parent system segment | **Parent Account List CSV** | `Segment` column |
| SFDC Account ID | **Parent Account List CSV** | `SFDC Account ID` column |
| Dollar opportunity | **Parent Account List CSV** | `Total $ Opp` column |
| Glytec client status | **Parent Account List CSV** | `Glytec Client - 8.31.25` column |
| Rep territory | **Supplemental Data CSV** | `Assigned Rep` column |
| ICP title matching criteria | **ICP Titles CSV** | 66 titles, 18 departments, intent scores 50-95 |
