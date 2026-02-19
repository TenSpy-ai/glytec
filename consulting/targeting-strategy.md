# Targeting Strategy

Quantitative foundation for account prioritization and outbound sequencing.

---

## The Core Insight: Beds Predict Everything

The Parent Account List shows a **0.98 correlation between bed count and opportunity dollar value**. This is near-perfect — bed count is effectively a proxy for deal size.

What this means practically:
- You don't need complex scoring models to rank accounts. **Sort by beds, and you've sorted by revenue potential.**
- HospitalView API delivers real-time bed counts, so this ranking stays current without manual updates.
- The relationship holds across segments: Enterprise/Strategic systems average 1,623 beds ($1.6M avg opp), Commercial averages 75 beds ($135K avg opp).

---

## Segment Economics

### The Four Segments

| Segment | Accounts | % of Accounts | Total $ Opp | Avg $ / Account | Total Beds | Definition |
|---------|----------|---------------|-------------|-----------------|------------|------------|
| **Enterprise/Strategic** | 296 | 17.6% | $485M | $1.64M | 480,414 | Multi-facility health systems (non-clients); 98% have 2+ facilities |
| **Partner Growth** | 54 | 3.2% | $110M | $2.04M | 113,797 | All 54 existing Glytec clients; relationship-based, not size-based |
| **Commercial** | 1,329 | 79.0% | $179M | $135K | 99,024 | Single-facility or 2-facility orgs; 79% have <100 beds |
| **Government** | 4 | 0.2% | $36M | $8.93M | 32,007 | VA, Defense Health Agency, Indian Health Service, Federal Bureau of Prisons |

### Where the Money Is

**Enterprise/Strategic is 17.6% of accounts but 59.9% of total dollar opportunity.** This is the primary hunting ground for the AI SDR.

Concentration is extreme:
- **Top 10 accounts = $157M (19.4% of TAM)**
- **Top 50 accounts = $333M (41.1%)**
- **Top 100 accounts = $436M (53.8%)**

This means a focused campaign on the top 100 Enterprise/Strategic accounts covers more than half of the entire addressable market.

### Segment Rules (Revealed by Data)

| Rule | Implication |
|------|-------------|
| Partner Growth = existing clients | Not a market-size segment. Ranges from 15-bed systems to 18,611-bed mega-systems. All 54 are current Glytec customers. |
| Enterprise/Strategic = multi-facility non-clients | The defining characteristic is 3+ facilities AND not yet a customer. This is the net-new target pool. |
| Commercial = single-facility organizations | 99.6% have <5 facilities. Max is 4. These are standalone hospitals — long tail, low average deal. |
| Government = federal entities only | 4 accounts. Specialized procurement. Long cycles but massive scale. |

---

## Priority Framework: Expand vs. Acquire

### Priority 1 — Expand Existing Clients (Partner Growth)

54 accounts. $110M opportunity. Only $21.2M current ARR. **The base is ~33% penetrated.**

The upsell math is staggering:

| Client | Current ARR | Total $ Opp | Upsell Ratio | Beds | Facilities |
|--------|-------------|-------------|-------------|------|------------|
| CommonSpirit Health | $107K | $21.5M | **201x** | 18,611 | 149 |
| Trinity Health | $46K | $12.2M | **268x** | 10,795 | 86 |
| Advocate Health | $135K | $9.4M | **70x** | 11,142 | 55 |
| AdventHealth | $2.58M | $8.5M | 3.3x | 9,287 | 55 |
| Orlando Health | $25K | $3.8M | **153x** | 2,597 | 13 |
| BJC HealthCare | $117K | $3.6M | **31x** | 3,628 | 16 |

CommonSpirit, Trinity, and Advocate alone represent **$43.2M in upsell opportunity against only $288K in combined ARR**. These three accounts should have dedicated expansion strategies — not AI SDR sequences.

**Expansion vectors:**
- **Facility rollout** — Most multi-hospital clients piloted at 2–3 sites. Every additional facility is incremental revenue.
- **SubQ expansion** — Clients using IV Glucommander in ICUs can expand to SubQ dosing on general floors.
- **Command Center upsell** — Many have dosing but not the AI-powered analytics/surveillance layer.
- **ED expansion** — Parkview's ED rollout is the proof point for this motion.

**Deepest-penetrated clients** (highest ARR, likely most facilities deployed): AdventHealth ($2.58M), Ardent ($2.13M), Piedmont ($1.86M), BayCare ($1.25M). These are candidates for Command Center / analytics upsell rather than facility expansion.

**Lowest-penetrated large clients** (biggest gap between ARR and opportunity): CommonSpirit, Trinity, Advocate, Orlando Health. These need a land-and-expand growth plan.

---

### Priority 2 — Acquire Enterprise/Strategic Accounts

296 accounts. $485M opportunity. **Zero current Glytec revenue.**

#### Top 20 Non-Client Targets

| # | System | Segment | Beds | Facilities | Total $ Opp | Primary EHR | Messaging Angle |
|---|--------|---------|------|------------|-------------|-------------|-----------------|
| 1 | HCA Healthcare | E/S | 38,726 | 191 | $34.7M | **MEDITECH** | Largest MEDITECH deployment in US; modernization angle |
| 2 | Dept of Veterans Affairs | Gov | 25,260 | 161 | $26.3M | **Vista** | Federal enterprise standardization |
| 3 | Ascension Health | E/S | 10,410 | 81 | $11.7M | **Cerner** (→ Epic) | EHR transition = integration opportunity |
| 4 | Kaiser Permanente | E/S | 12,770 | 59 | $11.3M | **Epic** | Wall-to-wall Epic; DIY calculator liability |
| 5 | Tenet Healthcare | E/S | 11,052 | 72 | $11.1M | **Cerner** | Heavy Cerner-Millennium |
| 6 | Community Health Systems | E/S | 7,660 | 66 | $9.7M | **Cerner** | Standardized Cerner across system |
| 7 | Providence St Joseph | E/S | 9,787 | 51 | $8.8M | **Epic** | Wall-to-wall Epic; DIY calculator liability |
| 8 | Prime Healthcare | E/S | 7,390 | 48 | $8.1M | Mixed | Multi-EHR environment |
| 9 | LifePoint Health | E/S | 5,718 | 61 | $8.1M | **MEDHOST** | Unique EHR; standardization need |
| 10 | Bon Secours Mercy | E/S | 6,006 | 42 | $6.6M | Mixed | Post-merger standardization opportunity |
| 11 | Universal Health Services | E/S | 5,995 | 39 | $6.3M | **Cerner** | Behavioral health + acute care; insulin management in psychiatric settings |
| 12 | Baylor Scott & White | E/S | 4,602 | 47 | $6.0M | Mixed | Large Texas system; financial pressure |
| 13 | UPMC | E/S | 6,560 | 34 | $5.8M | **Epic** | Multi-EHR (also Cerner, McKesson); academic |
| 14 | CHRISTUS Health | E/S | 4,485 | 36 | $5.1M | Mixed | Texas/Louisiana system |
| 15 | Mercy (MO) | E/S | 4,588 | 38 | $5.1M | Mixed | Midwest system |
| 16 | Defense Health Agency | Gov | 4,341 | 35 | $5.1M | **MHS GENESIS** | Federal; DoD procurement |
| 17 | Atrium Health/Advocate | E/S | ~4,500 | ~35 | ~$5.0M | Mixed | Post-merger with Advocate; system standardization |
| 18 | Banner Health | E/S | ~4,200 | ~30 | ~$4.8M | **Cerner** | Standardized Cerner |
| 19 | Intermountain Health | E/S | ~3,800 | ~30 | ~$4.5M | **Cerner** | Known innovation leader; quality-driven |
| 20 | SSM Health | E/S | ~3,500 | ~25 | ~$4.0M | Mixed | Midwest Catholic system |

#### EHR Distribution Across Top 50 Targets

| EHR | % of Target Beds | Implication |
|-----|-----------------|-------------|
| **Epic** | 53.2% | Primary integration — must be bulletproof |
| **Oracle Cerner** | 20.5% | Second priority; Oracle transition creates opening |
| **MEDITECH** | 13.7% | Third priority; driven almost entirely by HCA |
| Other (Vista, MEDHOST, Altera) | 12.6% | Government and niche |

**87.4% of beds in the top 50 systems run Epic, Cerner, or MEDITECH.** Integration with these three EHR families covers nearly the entire Enterprise/Strategic segment.

---

### Priority 3 — Government (Specialized)

4 accounts. $36M opportunity. Requires federal procurement expertise, long sales cycles, and likely a different team/partner.

| Account | Beds | Facilities | $ Opp | EHR |
|---------|------|------------|-------|-----|
| Dept of Veterans Affairs | 25,260 | 161 | $26.3M | Vista |
| Defense Health Agency | 4,341 | 35 | $5.1M | MHS GENESIS (Cerner) |
| Indian Health Service | 1,820 | 55 | $3.4M | RPMS |
| Federal Bureau of Prisons | 586 | 18 | $0.9M | Various |

### De-Prioritize — Commercial

1,329 accounts. $179M total. Average $135K per deal. **Median operating margin: -3.1%** (worst of any segment; only 30% profitable). The effort-to-return ratio is unfavorable for direct SDR outreach. Consider:
- Inbound/content marketing to generate demand
- Channel/partner strategy
- Self-serve or low-touch sales motion
- Cherry-pick the top 50 Commercial accounts by bed count for targeted outreach

---

## Financial Health as a Targeting Dimension

### Operating Margin Distribution by Segment

| Segment | Median Margin | Mean Margin | % Profitable (>0%) |
|---------|---------------|-------------|---------------------|
| Enterprise/Strategic | 0.0% | -0.7% | 41.7% |
| Partner Growth | 0.0% | -0.8% | 42.6% |
| Government | 0.0% | 0.0% | 0.4% |
| Commercial | -3.1% | -7.4% | 29.8% |

### How to Use This

For **Enterprise/Strategic** accounts, the distribution is bimodal:
- **30%** operate at 0–5% margin (breakeven) → Lead with efficiency ROI: "Every inpatient day you save goes straight to the bottom line"
- **21%** operate at 10%+ margin (healthy) → Lead with quality/safety: "Your reputation is about to be graded on outcomes you can't currently measure"
- **21%** are below -10% (distressed) → Lead with survival economics: "$20K/bed in annualized savings at your bed count = $[X]M"

HospitalView API provides real-time operating margin data, so this segmentation can be automated and kept current.

---

## The Unassigned Territory Opportunity

From the supplemental data (5,475 facilities with rep assignments):

| Pool | Facilities | Urban/Rural | Implication |
|------|-----------|-------------|-------------|
| **Unassigned** | 3,995 (73%) | 68.6% urban | Large urban systems sitting unworked; AI SDR sweet spot |
| Khirstyn | 445 (8.1%) | Skews rural | West/Southwest territory |
| Reagan | 426 (7.8%) | Skews rural | Central/Plains territory |
| Ian | 381 (7.0%) | Skews rural | Southeast/Midwest territory |
| Victoria | 228 (4.2%) | Skews rural | Northeast + Puerto Rico |

**Named reps are concentrated on rural Critical Access Hospitals (65.8% rural).** The unassigned pool — which is 68.6% urban and includes the largest health systems — is where the AI SDR creates the most value.

Cross-referencing: the top 20 Enterprise/Strategic targets listed above are almost certainly in the unassigned pool, since named reps focus on smaller rural facilities.

---

## Proposed Scoring Model

For the v1 pilot and beyond, a simple account scoring model:

| Factor | Weight | Data Source | Logic |
|--------|--------|-------------|-------|
| **Bed count** (proxy for deal size) | 30% | HospitalView API | Higher beds = higher score (0.98 correlation to $ opp) |
| **Operating margin** | 20% | HospitalView API | More negative = higher urgency score |
| **EHR vendor** | 15% | HospitalView API | Epic = highest (best integration story + biggest competitive displacement opportunity) |
| **CMS quality signals** | 15% | HospitalView API | Lower star rating + higher readmission rate = higher score |
| **Trigger signals** | 10% | HospitalView News/RFPs | Recent news (EHR migration, quality initiative, leadership change) = score boost |
| **Facility count** | 10% | HospitalView API | More facilities = larger enterprise deal potential |

This produces a composite score that can be automated through Clay, updated via HospitalView API, and used to rank the 296 Enterprise/Strategic accounts for outbound sequencing.

---

## Board Meeting Narrative (March 12)

The targeting data supports a clear story:

1. **Market size:** $810M TAM across 1,683 parent health systems. Only 54 (3.2%) are current clients.
2. **Concentration:** Top 100 accounts = $436M (54% of TAM). Focus is scalable.
3. **Coverage gap:** 73% of facilities have no rep. Named reps cover rural territory; the biggest urban systems are untouched.
4. **Why now:** CMS eCQM reporting began CY 2026. 55.9% of facilities are unprofitable. Financial + regulatory pressure is simultaneous.
5. **AI SDR results:** [v1 campaign data — to be filled in after Feb 23 launch]
6. **Expansion opportunity:** Existing clients have $110M in upsell against $21M ARR (33% penetrated). Three accounts alone have $43M in whitespace.
