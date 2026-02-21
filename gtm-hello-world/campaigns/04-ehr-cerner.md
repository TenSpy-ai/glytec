# Campaign: Oracle/Cerner Transition Urgency

**Campaign Name:** `GHW_Cerner_Transition_Q1`
**Recipe:** R5 — EHR-Segmented Discovery
**Skill:** `/dh-accounts ehr enterprise` — EHR-segmented ICP discovery (Epic/Cerner/MEDITECH)
**Target Segment:** Cerner hospitals navigating the Oracle Health transition
**Target Persona:** CFO, COO, CMIO

---

## Targeting Criteria

Run `/dh-accounts ehr enterprise` to pull EHR-segmented contacts, then filter for Cerner:

```sql
SELECT c.first_name, c.last_name, c.email, c.title, a.system_name,
       a.total_beds, a.primary_ehr
FROM contacts c
JOIN accounts a ON c.account_name = a.system_name
WHERE a.primary_ehr = 'Cerner'
  AND c.icp_category = 'Decision Maker'
  AND c.icp_department IN ('Finance', 'Operations', 'Medical')
  AND c.email IS NOT NULL
  AND c.suppressed = 0
ORDER BY a.total_beds DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — Transition Disruption (Day 0)

**Variant A:**
- **Subject:** Cerner → Oracle: what happens to your insulin dosing?
- **Body:**
  {{first_name}},

  The Cerner-to-Oracle Health transition is creating uncertainty across clinical workflows — and insulin management is one area where that uncertainty carries real patient safety risk.

  If {{company_name}} is currently using Cerner's insulin dosing tools, those tools may change, break, or require re-validation during the migration. And since they were never FDA-cleared in the first place, the liability exposure is already there.

  Glucommander is EHR-agnostic and FDA-cleared. It works alongside Cerner today and will integrate with whatever Oracle delivers tomorrow. No migration risk. No validation gap.

  Is this transition on your radar?

  {{sender_first_name}}

**Variant B:**
- **Subject:** Planning around the Oracle migration at {{company_name}}?
- **Body:**
  {{first_name}},

  Curious — as {{company_name}} navigates the Cerner → Oracle Health transition, has the team evaluated which clinical tools might be affected?

  Insulin management is one that often gets overlooked until something breaks. Glucommander is the only FDA-cleared insulin dosing system, and it's EHR-agnostic — meaning no migration risk when the underlying EHR changes.

  Worth a 15-minute conversation if the transition timeline is active.

  {{sender_first_name}}

### Step 2 — Risk Mitigation (Day 4)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  One more data point for context: health systems going through EHR migrations are 3x more likely to experience clinical workflow disruptions in the first 12 months.

  Glucommander eliminates insulin dosing as one of those risk points — it's a standalone, FDA-cleared system that doesn't depend on the EHR's native calculators. 400+ hospitals run it today across Epic, Cerner, and MEDITECH environments.

  If the Oracle timeline is heating up, this is worth getting ahead of.

  {{sender_first_name}}

### Step 3 — Low-Pressure Close (Day 8)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  Understand if the Oracle migration has you focused on other priorities right now. If insulin management comes up as part of the transition planning, I'm here to help.

  Happy to send over a brief overview whenever it's useful.

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
  "company_name": "MedStar Health",
  "primary_ehr": "Cerner",
  "total_beds": "4800",
  "account_tier": "Active",
  "recipe": "R5"
}
```

---

## Sender Assignment

3-5 warmed mailboxes. Rotate domains.
