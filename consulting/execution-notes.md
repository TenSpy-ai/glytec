# Execution Notes

## Current-State Process (from Clayton's Loom — Feb 4)

The existing "AI Legion" outbound workflow (pre-project):

```
Clay (prospect ID) → Off-limits filter → SalesForge (email validation) → Outbound → Reply mgmt
```

**Known issues with current state:**
- Personalization is template-driven, not truly 1:1
- No automated reporting — manual visibility only
- CEO Pat wants a reporting/dashboard layer
- Off-limits filtering (current customers, C-suite) needs to be more systematic
- Bounce rate management is reactive, not proactive

This is the baseline we're improving upon with v1–v4 infrastructure releases.

---

## Definitive Healthcare API Strategy

The existing data files (`data/`) are static exports from Definitive Healthcare. For the live infrastructure (v1–v4), we can tap into DH APIs to power real-time enrichment, trigger-based outreach, and contact discovery.

### Access Status (confirmed Feb 2026)

| API | Status | Notes |
|-----|--------|-------|
| **HospitalView API** | **HAVE ACCESS** | Included with HospitalView product subscription |
| PhysicianView API | **NO ACCESS** | Would need PhysicianView module (separate purchase) |
| Monocl ExpertData API | **NO ACCESS** | Would need Monocl Expert Insight Suite platform (separate purchase) |

**Integration specialist:** Ryan McDonald (rmcdonald@definitivehc.com) — assigned via CRM Integration package. He's our point of contact for HospitalView API implementation.

### Implication for Infrastructure

PhysicianView and Monocl are off the table unless Clayton decides to purchase those modules. This means:

- **Contact enrichment must rely on other sources** — ZoomInfo, LinkedIn, Clay enrichment, and manual scraping of hospital leadership pages (per Clayton's principle #8)
- **HospitalView API is the sole DH backbone** — account segmentation, trigger signals, executive contacts, and quality data all come from here
- **KOL/thought leader intelligence** will need alternative sourcing (LinkedIn, conference attendee lists, publication databases)

---

### HospitalView API (AVAILABLE)

**Purpose:** Enterprise account segmentation + outbound trigger signals

Supports:
- **Account segmentation** — beds, facility type, ownership, geographic classification
- **Technology install base** — EHR vendor identification (Epic, Cerner, MEDITECH) for messaging segmentation
- **Executive contacts** — leadership-level contacts at target facilities
- **Financials** — revenue, margins, operating performance for distress-based prioritization
- **Quality/volume signals** — Hospital Compare-related objects (star ratings, readmission rates, eCQM readiness indicators)
- **News & RFPs** — high-value trigger signals for outbound timing (e.g., EHR migrations, quality improvement initiatives, leadership changes, capital projects)

**Use in our infrastructure:** Primary data backbone for account scoring, segmentation, and trigger-based campaign timing. News/RFP signals feed directly into "why now" outreach hooks.

---

### PhysicianView API (NOT AVAILABLE — requires separate module)

**Purpose:** Clinical champion identification + multi-threading

Would support:
- **Champion identification** — finding endocrinology, hospital medicine, and pharmacy/med safety leaders at target accounts
- **Influencer mapping** — clinical informaticists, quality improvement leads, nursing informatics directors
- **Affiliation mapping** — connecting physicians across hospitals and health systems (critical for system-level selling where a champion at one facility can open doors across the IDN)
- **Multi-threading** — building 15+ contact coverage per account using the 66 ICP titles

**Workaround:** Use ZoomInfo + LinkedIn + Clay for clinical contact enrichment. Less structured than PhysicianView but functional for pilot.

---

### Monocl ExpertData API (NOT AVAILABLE — requires Expert Insight Suite)

**Purpose:** Thought leader identification for top-of-funnel and peer influence

Would support:
- **Inpatient diabetes thought leaders** — KOLs in glycemic management, endocrinology, hospital medicine
- **Advisory board members** — identify who influences clinical decisions at the system level
- **Conference targeting** — map which leaders present at relevant conferences (ADA, Endocrine Society, SHM)
- **Peer referral mapping** — understand clinical influence networks for warm introductions
- **Webinar/content targeting** — identify speakers and panelists for Glytec-hosted events (see messaging framework Section 23 for webinar titles)

**Workaround:** Manual KOL identification via publication searches, conference speaker lists, and LinkedIn research. Lower scale but viable for Enterprise/Strategic accounts.

---

### Revised API Integration Architecture

```
HospitalView API ──→ Account scoring & segmentation
                 ──→ Trigger signals (news, RFPs) → campaign timing
                 ──→ Executive contacts → CTA targeting

ZoomInfo ──→ Contact enrichment (emails, phones, titles)
         ──→ Multi-threading by ICP title/intent score

Clay ──→ Enrichment orchestration
     ──→ Data normalization & dedup
     ──→ Contact-to-account mapping

LinkedIn ──→ Profile verification
         ──→ KOL/thought leader identification (manual)
         ──→ Outbound channel (Clayton + Reagan profiles)
```
