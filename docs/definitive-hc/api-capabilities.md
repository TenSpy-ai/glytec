# HospitalView Commercial API — Capabilities & Infrastructure Mapping

What the API delivers and what each capability powers in the Glytec AI SDR infrastructure.

All data exposed via GET and POST endpoints, keyed by **Definitive ID**.

---

## Enterprise Account Segmentation

**Fields:** staffedBeds, hospitalType (Short Term Acute Care, etc.), ownership (Voluntary Nonprofit, Investor-Owned), academicMedicalCenter, traumaCenter level, firmType

**Powers:** Segment assignment (Enterprise/Strategic vs Commercial), bed-weighted scoring (20% of account score), and facility-level targeting.

---

## Network / IDN Hierarchy

**Fields:** networkId, networkName, networkParentId, networkParentName, networkOwnership, affiliated facilities

**Powers:** Parent/child account mapping. One API call returns every facility under a health system — critical for IDN-level selling where a champion at one hospital opens doors across the network.

---

## Technology Install (EHR)

**Fields:** vendor, product, vendorStatus (Installed Vendor), implementationYear, technology category

**Powers:** EHR-segmented messaging. Epic shops get the "DIY calculator liability" angle. Cerner shops get the "Oracle transition risk" angle. MEDITECH shops get the "modernization" angle. This is Layer 2 of the 3-layer message composition.

---

## Executive Contacts

**Fields:** standardizedTitle, positionLevel (C-Level, VP, Director), department, primaryEmail, directPhone, linkedinProfileURL, executiveId

**Powers:** Feeds the contact enrichment pipeline. DH provides facility-level leadership mapped by Definitive ID. Email quality is poor (ZoomInfo overwrites), but titles, departments, and LinkedIn URLs are high-value for ICP matching.

---

## Quality & Hospital Compare Signals

**Fields:** readmissionPenalty, VBP Adjustment, HAC Rate Penalty, CMS star ratings

**Powers:** CMS quality scoring (15% of account score) and the "CMS is publicly reporting your glycemic harm outcomes" messaging angle. Hospitals with active penalties are higher-urgency targets. These are the Hospital Compare-related objects exposed in the API.

---

## Financials

**Fields:** staffedBeds, numEmployees, number of discharges, operating margin

**Powers:** The financial health matrix. Unprofitable facilities (55.9% of universe) get ROI-led messaging ($20K/bed savings). Profitable facilities get CMS quality-led messaging. This is Layer 3 of the 3-layer message composition.

---

## News & Intelligence

**Fields:** intelligenceType (M&A, Affiliations/Partnerships, Clinical Trials/Research, Leadership Changes), publicationDate, newsEventTitle, bodyOfArticle

**Powers:** Trigger-based outbound timing. An EHR migration announcement = receptive moment for the "don't build a DIY calculator" message. A new CNO = new evaluation cycle = buying window. These signals feed into Clay to trigger personalized sequences at the moment of maximum receptivity.

---

## RFPs & Certificates of Need

**Fields:** type (Request for Proposal), category (Technology Services, Real Estate, Construction), classification (Solicitation, Certificate of Need), datePosted, dateDue, contact info

**Powers:** Another trigger signal source. Technology RFPs and new-build Certificates of Need signal active buying cycles. Construction/renovation = new units = new deployment opportunities.

---

## Memberships

**Fields:** GPO, ACO affiliations by type and subtype

**Powers:** Useful for network-level targeting and understanding purchasing dynamics (GPO contracts may influence vendor selection).

---

## Query Capabilities

The API supports both GET and POST. Properties are queryable — we can filter by hospitalType, state, vendor, networkParentId, etc. This means we can programmatically pull just the accounts that match our target criteria rather than processing the entire universe.

---

## Infrastructure Mapping Summary

| API Capability | Account Score Weight | Message Layer | Infrastructure Use |
|---|---|---|---|
| Bed count / facility type | 20% | — | Segment assignment, scoring |
| EHR vendor | 20% | Layer 2 | EHR-segmented messaging |
| Operating margin | 15% | Layer 3 | Financial health matrix |
| CMS quality / Hospital Compare | 15% | — | Quality scoring, urgency framing |
| News & RFPs (triggers) | 20% | — | Outbound timing, signal hooks |
| Contact coverage | 10% | — | Enrichment pipeline (not from DH) |
| Network hierarchy | — | — | Parent/child account mapping |
| Executive contacts | — | — | Contact enrichment (titles, LinkedIn) |

**5 of 6 account scoring factors come directly from the HospitalView API.**
