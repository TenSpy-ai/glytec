# Glytec AI SDR Data - Deep Dive & Insights

## 1. Facility List (9,774 facilities)

**Scale:** 9,774 facilities, 52 columns covering identity, location, financials, clinical metrics, and technology.

| Metric | Value |
|--------|-------|
| Active facilities | 8,384 (85.8%) |
| Closed | 1,335 (13.7%) |
| Short Term Acute Care | 4,479 (45.8%) |
| Critical Access Hospitals | 1,440 (14.7%) |
| Urban / Rural | 71.3% / 28.7% |
| Unique parent systems | 2,574 |

**Bed Distribution:** Huge range (median ~44 beds). Top facility is HCA Healthcare at 41,322 beds. 3,588 facilities have ICU beds (mean 43, total ~155K ICU beds nationwide).

**Financial Health - a key outreach lever:**
- **55.9% of facilities are unprofitable** (negative operating margin)
- Mean margin: -23.3% (heavily skewed by distressed facilities)
- Median margin: -2.2%
- This creates urgency for cost-saving solutions like Glytec (3.18-day LOS reduction)

**EHR Landscape (8,205 facilities with data):**

| EHR | Share |
|-----|-------|
| Epic (all variants) | ~40% |
| Oracle Cerner | ~19% |
| MEDITECH | ~12% |
| Vista (VA) | ~2% |
| Others (303 unique systems) | ~27% |

**Quality Ratings:** Mean CMS star rating of 3.08 (out of 5). HCAHPS mean 3.26. Readmission rate: mean 14.98%, range 11.7%–19.3%.

**Top 5 Parent Systems by Facility Count:**
1. HCA Healthcare — 267 facilities
2. Universal Health Services — 216
3. Dept. of Veterans Affairs — 189
4. Encompass Health — 180
5. CommonSpirit Health — 178

---

## 2. Supplemental Data (5,475 facilities - strict subset)

This file adds **rep assignments** and is a curated subset (56% of main list). All 5,475 IDs exist in the main file. Key finding: **9 columns have whitespace-padded names** — critical for joining.

**Rep Assignment — massive opportunity gap:**

| Rep | Facilities | % |
|-----|-----------|---|
| **Non Team Maike (unassigned)** | **3,995** | **73.0%** |
| Khirstyn | 445 | 8.1% |
| Reagan | 426 | 7.8% |
| Ian | 381 | 7.0% |
| Victoria | 228 | 4.2% |

**73% of facilities have no named rep.** This is the core AI SDR opportunity — automating outreach to the unassigned pool.

**Rep territories are geographically segmented:**
- **Ian:** Southeast/Midwest (GA, IL, OH, MS, IN, AL)
- **Khirstyn:** West/Southwest (TX, CA, LA, OK, WA)
- **Reagan:** Central/Plains (KS, NE, MN, MO, CO, IA)
- **Victoria:** Northeast + Puerto Rico (NY, PA, NC, NJ, PR)

**Named reps skew rural** (65.8%) while the unassigned pool is **68.6% urban** — suggesting the AI SDR should prioritize large urban systems.

---

## 3. Parent Account List (1,683 parent health systems)

This is the **strategic targeting list**, ranked with opportunity $ values.

**Total Addressable Market: $810M (Total $ Opp), $689M (Adj Total $ Opp)**

| Metric | Value |
|--------|-------|
| Parent systems | 1,683 |
| Total beds | 725,242 |
| Median beds/system | 44 |
| Beds-to-Opportunity correlation | **0.98** (near-perfect) |

**Segment Breakdown:**

| Segment | Count | Total Opp $ | Avg Opp |
|---------|-------|-------------|---------|
| Commercial | 1,329 (79%) | $102M | $77K |
| Enterprise/Strategic | 296 (18%) | $277M | $937K |
| Partner Growth | 54 (3%) | $63M | $1.16M |
| Government | 4 (0.2%) | $20M | $5.1M |

**Opportunity is highly concentrated:**
- Top 10 accounts = **19.4%** of total ($90M)
- Top 50 accounts = **41.1%** ($190M)
- Top 100 accounts = **53.8%** ($249M)

**Top 10 by Opportunity:**
1. HCA Healthcare — $19.9M
2. Dept. of Veterans Affairs — $15.0M
3. CommonSpirit Health — $12.3M
4. Trinity Health — $7.0M
5. Ascension Health — $6.7M
6. Kaiser Permanente — $6.4M
7. Tenet Healthcare — $6.4M
8. Community Health Systems — $5.5M
9. Advocate Health — $5.4M
10. Providence — $5.0M

**Existing Clients:** Only 54 systems (3.2%) are marked as current Glytec clients — enormous whitespace.

---

## 4. ICP Titles (66 target personas)

Defines the **exact people to contact** at each facility, split 50/50:
- **33 Decision Makers** (mean intent score: 83)
- **33 Influencers** (mean intent score: 65)

**Highest-priority targets (intent score 90-95):**

| Title | Score | Dept | Level |
|-------|-------|------|-------|
| CEO | 95 | Executive Leadership | Executive |
| CNO (Chief Nursing Officer) | 95 | Nursing | Executive |
| CMIO | 90 | Clinical Informatics | Executive |
| Chief of Endocrinology | 90 | Endocrinology | Executive |
| COO | 90 | Executive Leadership | Executive |
| CFO | 90 | Finance | Executive |
| CQO (Chief Quality Officer) | 90 | Quality Improvement | Executive |

**Top departments by volume:** Surgery (10 titles), Nursing (8), Hospital Medicine (8), Pharmacy (6), Critical Care (5), Endocrinology (5)

**Intent score by job level:** Executives (83) > Directors (79) > Individual Contributors (67) > Other (66) > Mid-Level (65)

---

## 5. Messaging Framework (Magnetic Messaging)

A 31-section **narrative operating system** built on StoryBrand principles:

**Core positioning:** Glytec has defined a new category — **"Intelligent Glycemic Management"** — positioning against three competitors:
1. **DIY/Epic insulin calculators** — unvalidated, hospital-maintained
2. **EndoTool (Glooko)** — 3 FDA recalls vs Glytec's zero
3. **Manual protocols/sliding scale** — reactive, variable

**Key proof points for outreach:**
- 867,000+ patients managed
- 400+ hospitals deployed
- 99.8% reduction in severe hypoglycemia
- 3.18-day average LOS reduction
- 0 FDA recalls
- 62% fewer severe hypo events vs EndoTool

**Urgency lever:** CMS glycemic eCQM measures are making glycemic harm publicly reportable.

---

## 6. Current Customers (54 Health Systems)

Glytec has **54 current clients** out of 1,683 tracked parent health systems (3.2%), all categorized under the **"Partner Growth"** segment. Combined ARR is **$21.2M** (avg $393K/system, range $6K–$2.6M).

### Why They Bought

Each customer's purchase rationale maps to one or more of these drivers, drawn from the messaging framework and clinical evidence:

**1. Patient Safety — Eliminating Preventable Glycemic Harm**
The single biggest driver. Hospitals using manual protocols, sliding-scale insulin, or unvalidated EHR calculators face real risk of severe hypoglycemia and hyperglycemia events. Glytec's Glucommander is **FDA-cleared with zero recalls** and delivers a **99.8% reduction in severe hypoglycemia**. For systems that had previous adverse drug events (ADEs) related to insulin dosing, this was the tipping point.

- *AdventHealth* ($2.6M ARR, 9,287 beds): Ran a head-to-head comparison — Glucommander produced **62% fewer severe hypoglycemia ADEs** than the competitor (EndoTool). Became Glytec's largest account.
- *Piedmont Healthcare* ($1.9M ARR): Multi-hospital system that needed standardized dosing across 16+ facilities to eliminate care variability.
- *Grady Health System*: Safety-net hospital serving a high-acuity, high-diabetes-prevalence population where glycemic events carry outsized clinical consequences.

**2. CMS Compliance & Regulatory Pressure**
CMS now requires **mandatory reporting of glycemic eCQMs** (severe hypoglycemia and hyperglycemia). Public reporting creates reputational and financial risk. Manual methods are no longer defensible — hospitals need to demonstrate real-time visibility and validated, standardized dosing.

- *Sentara Health* ($848K ARR, 2,446 beds): Quality-driven system preparing for public reporting; needed auditable, real-time glycemic surveillance.
- *Hartford HealthCare* ($694K ARR): Multi-site system requiring enterprise-wide compliance visibility across disparate facilities.
- *UVA Health*: Academic medical center where clinical rigor and regulatory defensibility are institutional priorities.

**3. Financial Impact — Length of Stay & Readmissions**
Glytec's clinical evidence shows a **3.18-day average reduction in length of stay** and **17.6% shorter LOS** vs. DIY approaches (5.4 vs. 6.5 days). For systems under financial pressure, this ROI argument closes deals.

- *Ardent Health Services* ($2.1M ARR, 3,216 beds): For-profit system where LOS reduction directly impacts margins across a national footprint.
- *BayCare Health System* ($1.2M ARR, 3,273 beds): Large community system focused on operational efficiency and reducing costly readmissions.
- *Ballad Health* ($692K ARR, 1,590 beds): Rural-serving system in Appalachia where operating margins are tight and every inpatient day matters.

**4. Replacing a Failed or Risky Competitor**
Several customers switched from **EndoTool (Glooko)**, which has had **3 FDA recalls** vs. Glytec's zero. Others replaced homegrown EHR calculators that shifted liability to the hospital's IT team.

- *AdventHealth*: Directly replaced EndoTool after the head-to-head study revealed the safety gap.
- *Kettering Health Network* ($767K ARR): Moved off a DIY approach to an FDA-cleared, vendor-supported platform.

**5. Scale & Standardization Across Multi-Hospital Systems**
Large systems with 5+ hospitals face a consistency problem — different units, shifts, and sites managing insulin differently. Glytec's platform + Command Center provides enterprise-wide visibility and standardization.

- *CommonSpirit Health*: One of the nation's largest health systems (178 facilities); needs a single glycemic management standard.
- *Trinity Health*: 92-hospital system requiring systemwide protocol standardization.
- *Advocate Health*: Large integrated system where standardization across legacy Advocate and Aurora facilities is critical post-merger.
- *Hackensack Meridian Health*: 18-hospital New Jersey system driving system-level quality initiatives.

**6. Clinical Champion + Executive Sponsorship**
Per Glytec's own messaging: sustainable improvement requires *"a clinical champion AND an executive who will fund it."* Many customers bought because an internal champion (typically a CNO, endocrinologist, or CQO) pushed the initiative through with executive backing.

- *MUSC Health* ($745K ARR): Academic system where a clinical informatics leader championed the platform.
- *Cedars-Sinai*: Clinician-driven adoption at one of the country's top-ranked hospitals.

### Customer Profile by Size

| Tier | Beds | Count | Avg ARR | Examples |
|------|------|-------|---------|----------|
| Large (3,000+) | 3,000–9,300 | 8 | $1.6M | AdventHealth, Ardent, Piedmont, BayCare |
| Mid (1,000–3,000) | 1,000–3,000 | 12 | $590K | Sentara, Baptist Health, Hartford, Ballad |
| Community (200–1,000) | 200–999 | 18 | $280K | CoxHealth, NE Georgia, Sarasota Memorial |
| Small (<200) | 15–199 | 16 | $52K | Baraga County, MLK Community, Major Health |

### Geographic Concentration

Top states by customer count: **Florida (7), Georgia (5), California (5), Virginia (3), Tennessee (3), South Carolina (3), New York (3), Maryland (3), Michigan (3).**

Southeast and Mid-Atlantic are strongest — reflects both Glytec's Atlanta HQ proximity and the region's high diabetes prevalence.

### Expansion Opportunity Within Current Customers

Current clients represent **$63M in total opportunity** (combined GC + CC upsell). Even at $21M ARR, the existing base is only ~33% penetrated. Key expansion vectors:

- **Command Center upsell**: Many customers have Glucommander (dosing) but not the AI-powered Command Center (surveillance/decision support)
- **SubQ expansion**: Customers using IV insulin management in ICUs can expand to SubQ dosing on general floors
- **Facility rollout**: Multi-hospital systems often pilot at 2–3 sites before enterprise-wide deployment

### Logos Approved for External Use

Per the messaging framework, these customers are cleared for references and logo use: **AdventHealth, Ballad Health, Sentara, Sarasota Memorial, Kaweah Health, Kettering Health, UVA Health, Wellstar, Piedmont, Upstate University Hospital, Grady.**

---

## Cross-File Strategic Insights

### 1. The AI SDR's sweet spot: Unassigned urban systems with high opportunity
- 3,995 facilities (73%) have no rep → prime for AI automation
- These skew urban (69%) and include large health systems
- Cross-reference with Parent Account List to prioritize by $ opportunity

### 2. Target the Enterprise/Strategic segment first
- Only 296 accounts but **$277M in opportunity** (34% of total TAM)
- Average deal: $937K vs $77K for Commercial
- Top 10 accounts alone = $90M

### 3. EHR-based messaging segmentation
- **Epic shops (49%):** Lead with "DIY Epic calculator liability" messaging
- **Cerner/Oracle (19%):** Integration-focused messaging
- **MEDITECH (14%):** Modernization narrative
- **Vista/VA (2.5%):** Government procurement pathway

### 4. Financial distress = urgency
- 55.9% of facilities are operating at a loss
- Glytec's 3.18-day LOS reduction directly impacts bottom line
- Combine with readmission rate data (mean 15%) for ROI messaging

### 5. Persona sequencing for multi-threaded outreach
- **Open with:** CNO or CQO (intent 90-95, clinical champions)
- **Expand to:** CMIO, Chief of Endocrinology, CFO (intent 90)
- **Activate influencers:** Hospitalists, diabetes specialists, clinical pharmacists (intent 60-75)

### 6. Data quality issues to address
- Supplemental file has whitespace-padded column names (needs `.strip()` when joining)
- 18.3% of ownership data coded as "0" (missing)
- Revenue/bed data stored as formatted strings in supplemental file
- 13.5% of facilities are closed — filter these before outreach
