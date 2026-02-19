# Likely GTM Needs

Data, tooling, and access gaps that will need to be addressed to deliver the full infrastructure (v1–v4).

---

## 1. HospitalView API — The Case for Fast Implementation

**Status:** Access confirmed. Integration specialist assigned (Ryan McDonald, rmcdonald@definitivehc.com).

**Why this is the #1 implementation priority:**

The static CSV exports in `data/` are a snapshot from January 2026. They degrade in value every day. HospitalView API replaces static data with a live backbone that powers three things the CSVs cannot:

### A. Real-Time Account Scoring

The proposed scoring model (see [targeting-strategy.md](targeting-strategy.md)) depends on 5 of 6 factors coming from HospitalView:

| Scoring Factor | Available in CSV? | Available via API? |
|----------------|:-:|:-:|
| Bed count | Yes (but stale) | Yes (current) |
| Operating margin | Yes (but stale) | Yes (current) |
| EHR vendor | Yes (but stale) | Yes (current) |
| CMS quality signals (stars, readmissions) | Partial | Yes (full Hospital Compare objects) |
| News & RFP trigger signals | **No** | **Yes** |
| Facility count | Yes | Yes |

The trigger signals (news, RFPs) are **only available via API**. This is the single biggest capability gap between the CSV-based infrastructure and the live infrastructure.

### B. Trigger-Based Outbound Timing

HospitalView News & RFPs surface high-value "why now" signals:
- **EHR migrations** — A hospital announcing an Epic migration is receptive to the "don't build a DIY insulin calculator" message
- **Quality improvement initiatives** — Signals alignment with Glytec's CMS readiness positioning
- **Leadership changes** — New CNO/CQO/CMIO = new evaluation cycle = buying window
- **Capital projects** — New facility builds or expansions = new unit deployments

These signals feed directly into the Clay orchestration workflow to trigger personalized sequences at the moment of maximum receptivity — instead of batch-and-blast on a fixed schedule.

### C. Campaign Segmentation That Stays Current

The messaging/targeting matrix (see [messaging-targeting-matrix.md](messaging-targeting-matrix.md)) segments by EHR vendor, financial health, and facility size. All three change over time:
- Hospitals switch EHR vendors (Ascension is migrating from Cerner to Epic)
- Financial health fluctuates quarterly
- Bed counts change with expansions and closures

API-driven segmentation keeps campaign targeting aligned with reality. CSV-driven segmentation will diverge.

### Recommendation

**Start the HospitalView API integration immediately.** It is the foundation for the live infrastructure and the only source of trigger signals. Ryan McDonald is already assigned — schedule the implementation kickoff this week.

Minimum viable integration for v1:
1. Account lookup by Definitive ID (match to existing CSVs)
2. Pull current bed count, EHR, operating margin, CMS quality data
3. Subscribe to News & RFP feeds for the top 100 target accounts
4. Feed results into Clay for scoring and sequence triggering

---

## 2. PhysicianView API Gap — The Contact Enrichment Constraint

**Status:** Not available. Requires separate module purchase.

**What it would give us:** Programmatic discovery of clinical contacts at target hospitals — endocrinologists, hospitalists, pharmacy leaders, clinical informaticists. This maps directly to 33 of the 66 ICP titles (the entire Influencer tier).

**Why it matters:** The milestones target **15+ contacts per account** at 50% of accounts by Feb 27, scaling to 80% by Mar 13. Without PhysicianView, clinical contact discovery is manual and unstructured.

### The Workaround Stack

Without PhysicianView, contact enrichment relies on three sources plus manual effort:

| Source | What It Covers | Strengths | Gaps |
|--------|---------------|-----------|------|
| **ZoomInfo** | Decision Maker titles (C-suite, VP, Director) — roughly Tier 1 + upper Tier 2 ICP titles | Structured data, email/phone enrichment, intent signals, bulk API access | Weak on clinical titles (endocrinologists, hospitalists, pharmacists, diabetes specialists). ZoomInfo indexes business roles well but clinical roles poorly. |
| **Clay** | Enrichment orchestration, data normalization, dedup, contact-to-account mapping | Flexible workflows, multi-source waterfall enrichment, integrates with ZoomInfo and LinkedIn | Not a primary data source — only as good as the sources it orchestrates |
| **LinkedIn** | Profile verification, KOL identification, individual contact research | Good for verifying titles and finding clinical professionals that ZoomInfo misses | Manual process (no bulk API for contact discovery); rate limits on search |
| **Manual scraping** | Hospital leadership pages, department directories | Often the only source for clinical titles at specific hospitals | Does not scale; per Clayton's note, may be necessary for the pilot |

### Expected Hit Rates by ICP Tier

| Tier | Titles | Likely Enrichment Source | Expected Hit Rate |
|------|--------|------------------------|-------------------|
| **Tier 1** (intent 90–95) | 7 C-suite titles | ZoomInfo (primary) | **70–85%** — C-suite titles are well-indexed |
| **Tier 2 Decision Makers** (intent 75–89) | 28 Director/VP titles | ZoomInfo + LinkedIn | **50–65%** — Directors are moderately indexed; some clinical directors will be missing |
| **Tier 2 Influencers** (intent 75–89) | 2 titles (Endocrinologist, Cardiac Surgeon) | LinkedIn + manual | **30–50%** — Clinical specialists are poorly indexed in business databases |
| **Tier 3 Influencers** (intent 50–74) | 29 clinical titles | Manual + LinkedIn | **15–30%** — CDCES, Nurse Educators, Clinical Pharmacists are rarely in ZoomInfo |

### Implication for Milestones

At these hit rates, the realistic contact coverage is:
- **Tier 1 (7 titles × 70–85%):** ~5–6 contacts per account → achievable
- **Tier 2 (30 titles × 50–65% for DMs, 30–50% for Influencers):** ~15–18 contacts per account → achievable for DM titles, uncertain for clinical
- **Tier 3 (29 titles × 15–30%):** ~4–9 contacts per account → low yield

**Net: Reaching 15+ contacts per account is achievable if you focus on Tier 1 + Tier 2 Decision Maker titles.** But multi-threading into the Influencer layer (clinical champions) will be thin without PhysicianView or significant manual effort.

### The Case for PhysicianView (If Budget Allows)

If Clayton decides the enrichment gap is unacceptable, here's the business case:

| Factor | Without PhysicianView | With PhysicianView |
|--------|----------------------|-------------------|
| Tier 3 contact coverage | 15–30% hit rate | ~70–80% hit rate (estimated) |
| Clinical champion identification | Manual research per account | Programmatic — endocrinology, hospitalist, pharmacy leaders across entire target universe |
| Physician affiliation mapping | Not possible | Cross-hospital connections visible — critical for system-level selling where a champion at one facility opens doors across the IDN |
| Multi-threading depth | 15–20 contacts per account (skewed to business titles) | 25–35 contacts per account (balanced business + clinical) |
| Time to 80% coverage at 15+ contacts | Manual effort-intensive; may not hit Mar 13 target | Automated; Mar 13 target achievable |

**Recommendation:** Run the v1 pilot without PhysicianView. Track enrichment hit rates by ICP tier. If Tier 3 coverage is below 20% and Clayton wants deeper clinical champion engagement, present the PhysicianView business case with real data from the pilot.

---

## 3. KOL / Thought Leader Intelligence (Monocl Gap)

**Status:** Not available. Requires Expert Insight Suite platform purchase.

**What it would give us:** Identification of Key Opinion Leaders (KOLs) in inpatient glycemic management — conference speakers, publication authors, advisory board members, clinical influencers.

**Why it matters for GTM:**
- KOLs influence purchasing decisions at the system level
- Conference targeting (ADA, Endocrine Society, SHM) benefits from knowing who speaks and who attends
- Webinar/content programs (see messaging framework Section 23) need credible speakers
- Warm introductions through peer networks accelerate enterprise sales

### Workaround

| Method | Effort | Coverage |
|--------|--------|----------|
| PubMed / Google Scholar searches for "inpatient glycemic management," "insulin dosing," "Glucommander" | Medium | Good for published researchers; misses clinical leaders who don't publish |
| Conference speaker lists (ADA, SHM, Endocrine Society proceedings) | Medium | Good for visible thought leaders; annual refresh needed |
| LinkedIn research (filter by title + institution + topic activity) | High | Case-by-case; useful for top 20–30 KOLs but doesn't scale |
| Clayton/Glytec's existing relationships | Low effort to collect | Likely the fastest source — ask Clayton for known KOLs and advisory contacts |

**Recommendation:** For Enterprise/Strategic accounts, manual KOL identification is viable at small scale. Prioritize the top 20 target accounts. Ask Clayton for Glytec's existing KOL relationships first — this is probably the highest-value, lowest-effort starting point.

---

## 4. Contact Data Quality (ZoomInfo + DH Email Gap)

**Known issue:** Definitive Healthcare email data quality is poor (per Clayton). ZoomInfo is the primary source for verified email addresses and phone numbers.

| Need | Tool | Status |
|------|------|--------|
| Verified business email addresses | ZoomInfo | Available — primary enrichment source |
| Direct phone numbers | ZoomInfo | Available |
| Email validation / deliverability check | Clay (or dedicated tool like NeverBounce) | Needs setup — critical before v1 launch to avoid bounce rate damage to sender reputation |
| Deduplication across sources | Clay | Needs workflow configuration |
| Contact-to-account mapping | LeanData | Available per Clayton's principles; needs configuration |

**Risk:** If email deliverability is not validated before the v1 campaign launch (Feb 23), high bounce rates could damage sender domain reputation. This is especially important given the SalesForge API-over-UI decision — programmatic sends at scale amplify deliverability problems.

**Recommendation:** Add an email validation step in the Clay workflow before any contact enters a SalesForge sequence. Budget 2–3 days for this setup.

---

## 5. LinkedIn Channel Infrastructure

**Status:** Decided (Clayton + Reagan profiles). 2-week email warm-up required for dedicated inboxes.

| Need | Detail | Timeline |
|------|--------|----------|
| Dedicated email inboxes per profile | Required for multi-channel (email + LinkedIn) under single identity | Must start warm-up by Feb 16 to be ready for v1 launch on Feb 23 |
| LinkedIn outreach tooling | Integrate with SalesForge API or standalone LinkedIn automation | Needs evaluation — SalesForge LinkedIn capabilities unclear |
| Profile optimization | Clayton and Reagan profiles need to be optimized for prospect-facing outreach (headline, summary, content cadence) | Before v1 launch |
| Connection strategy | How many connection requests/day, message templates, follow-up sequences | Part of campaign design (Clayton to provide by 2/16 EOD) |

**Risk:** The 2-week warm-up period is a hard constraint. If inboxes aren't created by Feb 16, LinkedIn outreach slips to v2.

---

## 6. Reporting & Dashboard

**Status:** TBD per Clayton's principle #7 ("Reporting/dashboard/visibility required").

Minimum viable reporting for v1:
- Emails sent / opened / replied / bounced per campaign
- Contacts enriched per account (coverage tracking vs 15+ target)
- Account coverage by segment (Enterprise/Strategic, Partner Growth, Commercial)
- Pipeline attribution: which AI SDR-sourced contacts generated meetings

More sophisticated metrics for v2+:
- Enrichment hit rate by ICP tier (validates PhysicianView need)
- Trigger signal → outreach → response correlation (validates HospitalView API investment)
- EHR-segmented response rates (validates messaging matrix effectiveness)
- Multi-threading depth per account vs meeting conversion

---

## Summary: What to Buy, Build, and Ask For

| Need | Category | Action | Owner | By When |
|------|----------|--------|-------|---------|
| HospitalView API integration | **Buy** (already have access) | Schedule kickoff with Ryan McDonald; build minimum viable integration | Jeremy | This week |
| Email validation tool | **Build** (via Clay) | Add validation step to Clay enrichment workflow | Jeremy | Before Feb 23 |
| PhysicianView API | **Evaluate** | Run v1 pilot; track Tier 3 hit rates; present business case to Clayton if coverage <20% | Jeremy → Clayton | After v1 data (late Feb) |
| Monocl Expert Data | **Defer** | Manual KOL research for top 20 accounts; collect Clayton's existing KOL relationships | Jeremy | Ongoing |
| LinkedIn warm-up inboxes | **Build** | Create dedicated inboxes for Clayton + Reagan; start warm-up | Clayton's team | By Feb 16 |
| Reporting dashboard | **Build** | Define v1 metrics; implement in Salesforce or standalone | Jeremy | By Feb 20 (v1 release) |
| Campaign content from Clayton | **Ask** | Campaign details for v1 launch (messaging, target accounts, sequencing) | Clayton | By Feb 16 EOD |
| KOL list from Clayton | **Ask** | Existing Glytec KOL relationships and advisory contacts | Clayton | ASAP |
| Past campaign messaging | **Ask** | Previous SalesForge campaigns for tone/template reference | Clayton | ASAP |
| Sales playbooks & call scripts | **Ask** | For AI agent knowledge base training | Clayton | Pending |
| Case studies & customer lists | **Ask** | For proof points and reference-able logos | Clayton | Pending |
