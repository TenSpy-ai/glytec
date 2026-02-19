# Messaging & Targeting Matrix

Operating playbook for persona-targeted, segment-aware outbound campaigns.

---

## How to Read This Document

The matrix is organized in three layers:

1. **Persona Tiers** — who to contact and in what order (derived from 66 ICP titles)
2. **EHR-Based Messaging** — what to say based on the prospect's EHR vendor
3. **Segment × Financial Health** — how to frame urgency based on account economics

Every outreach sequence should select from each layer to compose the right message for the right person at the right account.

---

## Layer 1: Persona Tiers

### Tier 1 — Primary Targets (Intent 90–95)

Open every account with these 7 titles. All are C-suite Decision Makers.

| Title | Intent | Department | Why They Care |
|-------|--------|------------|---------------|
| CEO | 95 | Executive Leadership | Institutional risk, CMS public reporting, board visibility |
| CNO (Chief Nursing Officer) | 95 | Nursing | Insulin titration is a nursing workflow problem; safety, staffing efficiency |
| CQO (Chief Quality Officer) | 90 | Quality Improvement | CMS HH-Hypo/HH-Hyper are quality measures; this is their domain |
| CMIO | 90 | Clinical Informatics | EHR integration, clinical decision support, data architecture |
| CFO | 90 | Finance | LOS reduction, readmission penalties, $20K/bed ROI |
| COO | 90 | Executive Leadership | Operational throughput, standardization across facilities |
| Chief of Endocrinology | 90 | Endocrinology | Clinical authority on glycemic management; internal champion |

**Sequencing:** Open with CNO or CQO (clinical safety angle). Expand to CMIO + CFO within the same week (integration + ROI). CEO and COO are escalation targets after clinical engagement.

---

### Tier 2 — Multi-Threading Targets (Intent 75–89)

Expand to these after Tier 1 engagement. 30 titles, mostly Director-level Decision Makers.

**Clinical Operations (highest value for multi-threading):**

| Title | Intent | Department |
|-------|--------|------------|
| Medical Director, Diabetes Services | 85 | Endocrinology |
| Medical Director, Hospital Medicine | 85 | Hospital Medicine |
| Director of Inpatient Nursing | 85 | Nursing |
| Director of Clinical Informatics | 85 | Clinical Informatics |
| Chief Pharmacy Officer | 85 | Pharmacy |
| Surgical ICU Director | 85 | Surgery |
| Chief of Cardiothoracic Surgery | 85 | Surgery |
| Perioperative Medical Director | 85 | Surgery |

**Strategic/Operational:**

| Title | Intent | Department |
|-------|--------|------------|
| Chief Strategy Officer | 85 | Strategy |
| VP, Clinical Transformation | 80 | Hospital Medicine |
| VP, Evidence-Based Medicine | 80 | Hospital Medicine |
| Chief Innovation Officer | 80 | Innovation |
| Chief of Critical Care | 80 | Critical Care |
| Medical Director, ICU | 80 | Critical Care |
| Director of Quality Improvement | 80 | Quality Improvement |
| Director of Clinical Pharmacy Services | 80 | Pharmacy |
| Director of Nursing Informatics | 80 | Nursing Informatics |
| Chair of Medicine | 80 | Hospital Medicine |
| Director of Inpatient Medicine | 80 | Hospital Medicine |

**Plus 11 additional titles** at 75–80: Associate CMIO, Associate Chief of Hospital Medicine, Chief Compliance Officer, Chief Data Officer, Chief of Transplant/Vascular/General Surgery, Cardiac Surgeon, Endocrinologist.

---

### Tier 3 — Influencer & Champion-Building Targets (Intent 50–74)

29 titles. All Influencers. Use for intelligence gathering, internal advocacy, and building grassroots support.

**Highest-value Influencers (intent 65–74):**

| Title | Intent | Department | Role in the Deal |
|-------|--------|------------|------------------|
| CDCES (Certified Diabetes Care & Education Specialist) | 70 | Diabetes Services | Frontline clinical champion; lives the problem daily |
| Diabetes Clinical Nurse Specialist | 70 | Diabetes Services | Same — direct workflow impact |
| Clinical Informaticist | 70 | Clinical Informatics | Evaluates integration feasibility |
| Clinical Nurse Informaticist | 70 | Nursing Informatics | Bridge between nursing workflow and IT |
| Patient Safety Officer | 70 | Patient Safety | Insulin is a high-alert medication; safety mandate |
| Transplant Surgeon / Vascular Surgeon | 70 | Surgery | High-acuity patients requiring tight glycemic control |
| Clinical Operations Lead, Hospitalist Service | 70 | Hospital Medicine | Operational champion on the floor |
| Assistant Director of Nursing, Quality & Safety | 70 | Nursing | Quality metrics owner at unit level |
| Nurse Educator, Diabetes | 70 | Nursing | Training and adoption gatekeeper |

**Supporting Influencers (intent 50–65):** Hospitalists, ICU Clinical Nurse Specialists, Pharmacy Informatics Leads, Quality Improvement Coordinators, Intensivists, Diabetes Program Coordinators, Inpatient RNs, and others. These are useful for content engagement (webinars, case studies) and building internal consensus.

---

## Layer 2: EHR-Based Messaging

### Epic Shops (~40% of universe, ~53% of top-50 target beds)

This is the largest single messaging segment and the primary competitive battleground.

| Element | Message |
|---------|---------|
| **Lead angle** | "Your hospital is maintaining an unvalidated insulin calculator while CMS publicly reports your glycemic harm outcomes." |
| **Competitive frame** | DIY Epic calculator liability — no FDA clearance, no analytics, no CMS measure alignment, maintenance burden on hospital IT |
| **Integration proof** | Glytec is in the **Epic vendor showroom** (Medication Ordering Decision Support, acute/inpatient) |
| **Customer proof** | MUSC Health selected Glytec specifically for Epic integration + CMS readiness |
| **Expansion proof** | Parkview Health: 10 facilities + ED + new hospitals, all Epic-integrated |
| **Technical frame** | Bidirectional EHR loop: ADT context → lab results → dosing recommendations → flowsheet charting → MAR confirmation |
| **CTA** | "Can your current Epic calculator tell you how many patients hit BG < 40 or BG > 300 last quarter?" |

**Key targets using Epic:** Kaiser Permanente ($11.3M opp), Providence ($8.8M), UPMC ($5.8M), plus many academic medical centers.

---

### Oracle Cerner Shops (~19% of universe, ~21% of top-50 beds)

| Element | Message |
|---------|---------|
| **Lead angle** | "Cerner's transition to Oracle Health creates uncertainty — you need a stable, FDA-cleared glycemic management layer that works regardless of your EHR roadmap." |
| **Competitive frame** | EHR transition risk — Glytec provides continuity while Oracle Health evolves |
| **Urgency** | CMS eCQM reporting doesn't pause for EHR migrations |
| **CTA** | "How are you planning to maintain glycemic management workflows during your Oracle transition?" |

**Key targets using Cerner:** Ascension ($11.7M opp, transitioning to Epic in some areas), Tenet ($11.1M), CHS ($9.7M), Universal Health Services ($6.3M), Banner Health.

---

### MEDITECH Shops (~12% of universe, ~14% of top-50 beds)

| Element | Message |
|---------|---------|
| **Lead angle** | "MEDITECH environments often lack robust clinical decision support for insulin management. CMS doesn't grade on a curve." |
| **Competitive frame** | Modernization — Glytec provides enterprise-grade glycemic management + analytics that may not exist natively in MEDITECH |
| **CTA** | "What's your current protocol for standardizing insulin dosing across units?" |

**Key target using MEDITECH:** HCA Healthcare ($34.7M opp, #1 target by opportunity, largest MEDITECH deployment in the US).

---

### Vista / VA (~2% of universe, Government segment)

| Element | Message |
|---------|---------|
| **Lead angle** | "Enterprise standardization at federal scale — 161 facilities, one protocol." |
| **Caveat** | Government procurement cycles are long; requires specialized contracting approach |
| **Scale** | VA: $26.3M total opportunity, 25,260 beds, 161 facilities |

---

## Layer 3: Segment × Financial Health Matrix

### How to Combine: The 2×2 Urgency Grid

|  | **Unprofitable** (55.9% of facilities) | **Profitable** (44.1% of facilities) |
|--|----------------------------------------|---------------------------------------|
| **Enterprise/Strategic** (296 accounts, $485M opp) | **Lead with ROI + CMS.** $20K/bed savings, 3.18-day LOS reduction. "You're losing money AND being publicly measured on glycemic harm." | **Lead with CMS + Quality.** 99.8% hypo reduction, CMS readiness analytics. "Your reputation is about to be graded on outcomes you can't currently measure." |
| **Commercial** (1,329 accounts, $179M opp) | **Lead with survival ROI.** $7.49M annualized savings case study. "Insulin management efficiency is a margin lever you haven't pulled." | **Lead with competitive advantage.** 93% KLAS repurchase, 400+ hospitals. "Your peers are standardizing. CMS will show who didn't." |
| **Partner Growth** (54 existing clients, $110M opp) | **Lead with expansion ROI.** "You've seen the results in [current unit]. Every additional unit has the same opportunity." | **Lead with platform expansion.** SubQ, ED, Command Center, analytics. "You've solved ICU insulin. What about the rest of the hospital?" |

### Financial Health Detail by Segment

| Segment | Median Margin | % Profitable | Messaging Implication |
|---------|---------------|--------------|----------------------|
| Enterprise/Strategic | 0.0% | 41.7% | Split: 42% get quality/safety messaging, 58% get ROI messaging |
| Partner Growth | 0.0% | 42.6% | Similar split; but add expansion economics |
| Commercial | -3.1% | 29.8% | Heavily ROI-driven; 70% are losing money |
| Government | 0.0% | 0.4% | Budget-neutral; lead with standardization + compliance |

---

## Layer 4: Proof Points Library

Attach these to messages based on persona and urgency context.

### Safety & Clinical Outcomes
| Proof Point | Use When |
|-------------|----------|
| 99.8% reduction in severe hypoglycemia | CNO, CQO, Patient Safety Officer, nursing titles |
| 62% fewer severe hypo events vs EndoTool | Prospects evaluating EndoTool or with EndoTool installed |
| 867,000+ patients managed | Credibility — any persona, any segment |
| 0 FDA recalls (vs EndoTool's 3) | Safety-conscious personas; competitive displacement |

### Financial ROI
| Proof Point | Use When |
|-------------|----------|
| $20,000 annualized savings per licensed bed | CFO, CEO, COO; unprofitable facilities |
| 3.18-day average LOS reduction | CFO, COO; any facility with capacity constraints |
| $7.49M annualized savings (case study) | Large systems; board-level conversations |
| 35–68% readmission reduction | CFO; facilities with CMS readmission penalties |

### Scale & Trust
| Proof Point | Use When |
|-------------|----------|
| 400+ hospitals deployed | Any prospect questioning adoption risk |
| 93% "would buy again" (KLAS) | Late-stage evaluation; competitive displacement |
| 95%+ utilization of eligible patients | Prospects worried about clinician adoption |
| 150M+ hospitalizations in data set | Command Center / analytics conversations |

### Regulatory & Compliance
| Proof Point | Use When |
|-------------|----------|
| FDA-cleared (multiple 510(k)s) | Clinicians worried about liability; vs DIY calculators |
| CMS HH-Hypo/HH-Hyper eCQMs effective CY 2026 | Universal urgency — every hospital, every persona |
| Severe hypo = BG < 40 mg/dL; severe hyper = BG > 300 mg/dL | CQO, Quality Directors; makes the measure concrete |

---

## Objection Handling

### "We already have insulin protocols / order sets."
CMS HH-Hypo and HH-Hyper eCQMs now formalize severe glycemic events as publicly reported hospital harm outcomes. Existing protocols cannot generate the structured data, analytics, or measure-aligned workflows required for reliable CMS reporting. *Ask: "Can your current protocol tell you today how many patients hit BG < 40 or BG > 300 last quarter, and which units are trending?"*

### "Integration will be painful and IT won't prioritize it."
Glytec is in the Epic vendor showroom. MUSC Health explicitly selected Glytec because of Epic integration. Parkview deployed across 10 facilities + ED + new hospitals. Glytec's implementation services ("Blueprint for Success") provide structured, milestone-based go-live support.

### "Clinicians won't trust the algorithm."
Glucommander is FDA-cleared (multiple 510(k)s) and classified as clinical decision support — not autonomous. It provides dosing recommendations; clinicians retain judgment. 400+ hospitals trust it; 93% would buy again per KLAS. The product includes explicit contraindications, warnings, and guardrails.

### "The ROI isn't real."
Anchor to CMS-defined measures already being tracked: severe events (BG < 40, BG > 300), LOS, readmissions, POC testing volume. Propose a baseline assessment and measurement plan. Proof points: $20K/bed savings, 3.18-day LOS reduction, 99.8% hypo reduction, $7.49M at one institution, 95%+ utilization.

---

## Putting It Together: Example Sequences

### Sequence A: Epic + Enterprise/Strategic + Unprofitable + CNO

**Email 1 (CNO):** "Your nurses are titrating insulin using an unvalidated Epic calculator while CMS publicly reports your glycemic harm outcomes starting this year. 55.9% of facilities are already losing money — Glytec reduces LOS by 3.18 days on average. MUSC Health chose Glytec specifically for Epic integration and CMS readiness. Worth 15 minutes?"

**Email 2 (CQO, same account):** "CMS now defines severe hypoglycemia as BG < 40 mg/dL and severe hyperglycemia as BG > 300 mg/dL — and publishes the results. Can your current system tell you how many patients hit those thresholds last quarter? Glytec delivers 99.8% reduction in severe hypo events and purpose-built CMS reporting dashboards."

**Email 3 (CFO, same account):** "Glytec customers report $20,000 in annualized savings per licensed bed. At [X beds], that's [$Y]. One institution documented $7.49M in annualized savings. Your current margin is [Z%] — this moves the needle."

### Sequence B: MEDITECH + Enterprise/Strategic + HCA

**Email 1 (CNO/CQO):** "HCA is the largest MEDITECH deployment in the US. CMS doesn't grade on a curve based on your EHR vendor — HH-Hypo and HH-Hyper reporting is mandatory for everyone in 2026. Glytec provides enterprise-grade glycemic management + analytics that MEDITECH doesn't offer natively. 400+ hospitals, 0 FDA recalls."

### Sequence C: Partner Growth (Existing Client) + Expansion

**Email 1 (Operational sponsor):** "You've seen the results in [current unit] — [reference their specific outcomes if available]. Every unit running manual protocols or basic order sets has the same opportunity. SubQ, ED, and Command Center analytics are the natural next steps. Let's map the expansion plan."
