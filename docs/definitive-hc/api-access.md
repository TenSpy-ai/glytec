# Definitive Healthcare — API Access & Reference

Details provided by the Definitive Healthcare customer care team. Integration specialist: **Ryan McDonald** (rmcdonald@definitivehc.com).

---

## API Key

```
76f8374b-8fe7-4ad7-9e8c-757220db34f9
```

**Authentication format:** `ApiKey 76f8374b-8fe7-4ad7-9e8c-757220db34f9`

---

## Swagger / API Documentation

**URL:** https://api-data.defhc.com/docs/swagger/index.html

- Requires a Definitive Healthcare user login to view
- "Try it out" requests require the API key, formatted as `ApiKey 76f8374b-8fe7-4ad7-9e8c-757220db34f9`
- Covers specifications, schemas, errors, versioning, and sample requests

---

## What's Available

The Commercial API currently exposes data points within:

1. **HospitalView** — facility demographics, EHR/technology, financials, quality, executives, news, RFPs, memberships

---

## Commercial API Properties File Structure

The properties file (provided by DH support) is organized by tabs, each sharing the same column headers:

| Column | Description |
|---|---|
| **ENDPOINT** | URL for the request |
| **GET** | "Y" if the property is available in a GET request |
| **POST** | "Y" if the property is available in a POST request |
| **PROPERTY NAME** | Name of the available API property within the request URL |
| **DATA TYPE** | Data type of the property's return |
| **NULLABLE** | "Y" if nullable |
| **SAMPLE** | Sample of return data |

---

## HospitalView Supplementary Tabs

These tabs list the specific property values that can be queried within each endpoint:

### Executive Titles
Standardized titles used in executive contact data.
- Examples: "Chief Executive Officer", "Director of Marketing", "Chief Nursing Officer"

### Firm & Hospital Types
Firm types for affiliations and hospital types within HospitalView.
- Firm types: "Ambulatory Surgery Center", etc.
- Hospital types: "Short Term Acute Care", etc.

### Memberships
Types and subtypes of organizational memberships.
- Types: "Group Purchasing Organization", "Accountable Care Organization"

### News & Intelligence
Article types related to hospitals.
- Types: "Affiliation/Partnership", "Merger/Acquisition", "Clinical Trials", "Leadership Changes"

### Tech
Technology categories and specific products.
- Categories: "Electronic Medical Records"
- Specifics: "Electronic Health/Medical Record - Inpatient"

### Quality
Quality metrics exposed in the API.
- Metrics: "VBP Adjustment", "HAC Rate Penalty", "Readmission Penalty", CMS stars

### Financials
Financial metrics for facilities.
- Metrics: "Staffed Beds", "Number of Discharges", "Operating Margin", "Number of Employees"

### RFPs
Request for Proposal and Certificate of Need data.
- Classifications: "Solicitation", "Certificate of Need"
- Categories: "Real Estate", "Construction - New Building/Renovations/Design", "Technology Services"
