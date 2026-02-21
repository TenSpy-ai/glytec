# Campaign: Financial Recovery / CMS Penalties

**Campaign Name:** `GHW_Financial_Recovery_Q1`
**Recipe:** R6 — Financial Distress + Quality
**Skill:** `/dh-accounts distress enterprise` — targets negative-margin hospitals with CMS penalties
**Target Segment:** Health systems with negative margins, CMS penalties, or quality gaps
**Target Persona:** CFO, CEO, COO

---

## Targeting Criteria

Run `/dh-accounts distress enterprise` to pull contacts at financially distressed hospitals, then query:

```sql
SELECT c.first_name, c.last_name, c.email, c.title, a.system_name,
       a.total_beds, a.operating_margin_avg, a.cms_rating_avg
FROM contacts c
JOIN accounts a ON c.account_name = a.system_name
WHERE (a.operating_margin_avg < 0 OR a.cms_rating_avg < 3.0)
  AND c.icp_category = 'Decision Maker'
  AND c.icp_department IN ('Finance', 'Operations', 'Executive')
  AND c.email IS NOT NULL
  AND c.suppressed = 0
ORDER BY a.operating_margin_avg ASC;
```

---

## Email Sequence (3 steps)

### Step 1 — Financial Pressure + Opportunity (Day 0)

**Variant A:**
- **Subject:** Margin pressure and insulin management at {{company_name}}
- **Body:**
  {{first_name}},

  I've been looking at the financial landscape for systems like {{company_name}} — and the pressure on operating margins is real. When margins are tight, every clinical workflow needs to earn its keep.

  Insulin management is one of those workflows that most hospitals don't think of as a financial lever. But it is: uncontrolled blood glucose drives longer lengths of stay, more ICU transfers, and higher readmission rates — all of which hit the bottom line.

  Glucommander typically delivers a measurable reduction in LOS and hypo events. For a system with {{total_beds}} beds, the financial impact is material.

  Worth a brief conversation?

  {{sender_first_name}}

**Variant B:**
- **Subject:** A clinical lever for {{company_name}}'s margins
- **Body:**
  {{first_name}},

  When operating margins are under pressure, the instinct is to look at volume and contracts. But there's a clinical lever most systems overlook: insulin management.

  Poorly managed insulin leads to longer stays, more adverse events, and CMS quality penalties — all of which erode margins. Glucommander addresses all three by standardizing insulin dosing across the hospital.

  The ROI case is strong for systems facing financial headwinds. Interested in seeing the numbers?

  {{sender_first_name}}

### Step 2 — CMS Quality Angle (Day 4)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  One additional angle — CMS quality metrics. Hospital-acquired conditions (HAC) penalties, readmission rates, and value-based purchasing scores are all affected by insulin management quality.

  Glucommander helps on all three fronts: fewer hypo events (HAC reduction), shorter LOS (readmission risk), and standardized protocols (quality scores). 400+ hospitals have the data to prove it.

  If {{company_name}} is navigating CMS penalties or quality improvement, this is directly relevant.

  {{sender_first_name}}

### Step 3 — Brief Close (Day 8)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  I'll keep this short — if financial recovery or quality improvement is on the 2026 agenda at {{company_name}}, Glucommander is a proven lever. Happy to share a brief case study from a similar system.

  {{sender_first_name}}

---

## Campaign Settings

| Setting | Value |
|---------|-------|
| daily_limit | 25 |
| email_gap | 12 min |
| stop_on_reply | true |
| stop_for_company | true |
| open_tracking | false |
| link_tracking | false |

---

## Custom Variables (per lead)

```json
{
  "title": "CFO",
  "company_name": "LifePoint Health",
  "total_beds": "9200",
  "operating_margin": "-2.1%",
  "cms_rating": "2.8",
  "account_tier": "Active",
  "recipe": "R6"
}
```

---

## Sender Assignment

3-5 warmed mailboxes. Rotate domains.
