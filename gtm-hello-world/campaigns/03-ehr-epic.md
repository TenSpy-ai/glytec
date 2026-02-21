# Campaign: Epic DIY Calculator Liability

**Campaign Name:** `GHW_Epic_Liability_Q1`
**Recipe:** R5 — EHR-Segmented Discovery
**Skill:** `/dh-accounts ehr enterprise` — EHR-segmented ICP discovery (Epic/Cerner/MEDITECH)
**Target Segment:** Epic hospitals using DIY insulin calculators
**Target Persona:** CNO, CMIO, Chief Pharmacy Officer, Director Pharmacy

---

## Targeting Criteria

Run `/dh-accounts ehr enterprise` to pull EHR-segmented contacts, then filter for Epic:

```sql
SELECT c.first_name, c.last_name, c.email, c.title, a.system_name,
       a.total_beds, a.primary_ehr
FROM contacts c
JOIN accounts a ON c.account_name = a.system_name
WHERE a.primary_ehr = 'Epic'
  AND c.icp_category = 'Decision Maker'
  AND c.icp_department IN ('Nursing', 'Medical', 'Pharmacy')
  AND c.email IS NOT NULL
  AND c.suppressed = 0
ORDER BY a.total_beds DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — FDA Liability Angle (Day 0)

**Variant A:**
- **Subject:** The risk in Epic's insulin calculator
- **Body:**
  {{first_name}},

  Quick question — is {{company_name}} using Epic's built-in insulin dosing calculator, or a homegrown tool built on top of it?

  Either way, there's a regulatory nuance most health systems miss: those calculators have never been FDA-validated. They work, mostly — but when a dosing error leads to a hypoglycemic event, the liability falls entirely on the hospital, not on Epic.

  Glucommander is the only FDA-cleared insulin management system. It's designed to integrate with Epic and replaces the unvalidated calculators that create this risk. 400+ hospitals have made the switch.

  Is this something you've evaluated?

  {{sender_first_name}}

**Variant B:**
- **Subject:** Unvalidated insulin dosing at {{company_name}}
- **Body:**
  {{first_name}},

  Most Epic hospitals assume their insulin calculator is validated because it's inside the EHR. It's not. Epic's tools are general-purpose — they've never gone through the FDA clearance process for insulin dosing specifically.

  That distinction matters when a hypo event leads to a patient safety review. The hospital bears full liability for using an unvalidated tool.

  Glucommander solves this — it's the only FDA-cleared insulin management system, and it integrates cleanly with Epic. Worth knowing about if clinical risk is on your radar.

  {{sender_first_name}}

### Step 2 — Clinical Evidence (Day 3)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  To put a number on it: hospitals using Glucommander see a 60%+ reduction in hypoglycemic events compared to their previous insulin management approach — including Epic's built-in tools.

  That's a measurable patient safety improvement, a reduction in adverse event investigations, and a stronger position on CMS quality metrics.

  If you're using Epic at {{company_name}}, this is relevant. Happy to share a brief overview.

  {{sender_first_name}}

### Step 3 — Gentle Close (Day 7)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  Last thought on this — if insulin management isn't a current priority, totally understand. But if it's something that comes up in the next quarter (quality reviews, CMS audits, clinical risk assessments), it's worth having Glucommander on your radar.

  Happy to send a one-pager whenever it's useful.

  {{sender_first_name}}

---

## Campaign Settings

| Setting | Value |
|---------|-------|
| daily_limit | 30 |
| email_gap | 10 min |
| stop_on_reply | true |
| stop_for_company | true |
| open_tracking | false |
| link_tracking | false |

---

## Custom Variables (per lead)

```json
{
  "title": "CMIO",
  "company_name": "Allina Health",
  "primary_ehr": "Epic",
  "total_beds": "3200",
  "account_tier": "Active",
  "recipe": "R5"
}
```

---

## Sender Assignment

3-5 warmed mailboxes. Rotate domains.
