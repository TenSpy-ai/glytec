# Campaign: Account Deep Dive (Per-Account Template)

**Campaign Name:** `GHW_DeepDive_{account}`
**Recipe:** R1 / R2 / R9 / R10 — Account Intelligence Bundle
**Skills:** Multiple — see below
**Target Segment:** All ICP contacts at one specific high-priority health system
**Target Persona:** All ICP at one system (CNO, CFO, CMO, CQO, CMIO, Pharmacy, Directors)

---

## Overview

This is a **template** campaign — it's instantiated once per account. Before launching, gather the full intelligence bundle using these skills:

1. **`/dh-contacts {def_id}`** (R1) — Full contact extraction at one hospital
2. **`/dh-contacts icp {def_id}`** (R2) — ICP-matched discovery (filtered to 66 ICP titles)
3. **`/dh-signals enrich {def_id}`** (R9) — Account bundle (quality, financials, GPO, news)
4. **`/dh-contacts "{system_name}"`** (R10) — Every contact across all facilities in a parent system

The email content below uses account-specific intelligence to create highly personalized outreach.

---

## Targeting Criteria

```sql
-- Step 1: Get account intelligence
SELECT * FROM account_enrichment WHERE system_name = '{{target_account}}';

-- Step 2: Get all ICP contacts
SELECT e.first_name, e.last_name, e.email, e.title, e.hospital_name
FROM executives e
JOIN facilities f ON e.definitive_id = f.definitive_id
WHERE f.highest_level_parent = '{{target_account}}'
  AND e.icp_matched = 1
  AND e.primary_email IS NOT NULL
ORDER BY e.icp_intent_score DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — Account-Specific Opening (Day 0)

**Variant A:**
- **Subject:** Insulin management at {{company_name}} — a question
- **Body:**
  {{first_name}},

  I've been studying {{company_name}}'s profile in some depth — {{total_beds}} beds across {{facility_count}} facilities, {{primary_ehr}} EHR, and some interesting dynamics in your quality metrics and financial position.

  One area that stands out is insulin management. Given your patient volume and acuity, the gap between validated and unvalidated insulin dosing tools has a significant clinical and financial impact.

  I'd love to understand how {{company_name}} handles insulin dosing today. Is this something you're evaluating?

  {{sender_first_name}}

**Variant B:**
- **Subject:** {{company_name}}'s clinical technology priorities
- **Body:**
  {{first_name}},

  I've been researching {{company_name}} and wanted to ask: where does insulin management fall in your 2026 clinical technology priorities?

  Based on what I've seen — {{total_beds}} beds, {{primary_ehr}}, and the clinical complexity you're managing — this is an area where validated tools make a measurable difference.

  Glucommander is the only FDA-cleared insulin management system. I'd value the chance to learn how {{company_name}} approaches this today.

  {{sender_first_name}}

### Step 2 — Account-Specific Evidence (Day 4)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  To follow up with something specific to {{company_name}}: based on your bed count and patient population, the impact of Glucommander would be material — both in clinical outcomes (60%+ fewer hypo events) and financial performance (reduced LOS, fewer adverse events).

  Systems comparable to {{company_name}} have seen ROI within the first year of implementation. If this is relevant, I can share a case study from a similar system.

  {{sender_first_name}}

### Step 3 — Multi-Stakeholder Close (Day 8)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  I've reached out to a few people at {{company_name}} because insulin management is a cross-functional decision — it touches nursing, pharmacy, quality, and finance.

  If this is something {{company_name}} is evaluating (or should be), I'm happy to set up a brief overview for the relevant stakeholders. No pressure if the timing isn't right.

  {{sender_first_name}}

---

## Campaign Settings

| Setting | Value |
|---------|-------|
| daily_limit | 10 |
| email_gap | 20 min |
| stop_on_reply | true |
| stop_for_company | true |
| open_tracking | false |
| link_tracking | false |

---

## Custom Variables (per lead)

```json
{
  "title": "CNO",
  "company_name": "Baylor Scott & White",
  "total_beds": "5600",
  "facility_count": "52",
  "primary_ehr": "Epic",
  "operating_margin": "1.2%",
  "cms_rating": "3.5",
  "quality_penalties": "HAC: 2, Readmission: 3",
  "account_tier": "Active",
  "score": "78",
  "recipe": "R1/R2/R9/R10"
}
```

---

## Sender Assignment

2-3 warmed mailboxes. Use consistent sender per-account so the outreach feels coordinated, not random.

---

## Pre-Launch Checklist (Account Deep Dive Specific)

1. Run `/dh-contacts {def_id}` (R1) + `/dh-contacts icp {def_id}` (R2) for full contact coverage
2. Run `/dh-signals enrich {def_id}` (R9) for quality/financial intelligence
3. Customize step 1 body with account-specific data points
4. Review all contacts for suppressions and duplicates
5. Verify emails before enrollment
6. Assign 2-3 warmed mailboxes
7. Create campaign in Instantly with low daily_limit (10)
8. Launch and monitor closely — deep dives are high-touch
