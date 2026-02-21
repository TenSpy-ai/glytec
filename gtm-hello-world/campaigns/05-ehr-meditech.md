# Campaign: MEDITECH Modernization

**Campaign Name:** `GHW_MEDITECH_Modern_Q1`
**Recipe:** R5 — EHR-Segmented Discovery
**Skill:** `/dh-accounts ehr enterprise` — EHR-segmented ICP discovery (Epic/Cerner/MEDITECH)
**Target Segment:** MEDITECH hospitals ready to leapfrog to FDA-cleared insulin management
**Target Persona:** CNO, CQO, Chief Pharmacy Officer, Director Pharmacy

---

## Targeting Criteria

Run `/dh-accounts ehr enterprise` to pull EHR-segmented contacts, then filter for MEDITECH:

```sql
SELECT c.first_name, c.last_name, c.email, c.title, a.system_name,
       a.total_beds, a.primary_ehr
FROM contacts c
JOIN accounts a ON c.account_name = a.system_name
WHERE a.primary_ehr = 'MEDITECH'
  AND c.icp_category = 'Decision Maker'
  AND c.icp_department IN ('Nursing', 'Quality', 'Pharmacy')
  AND c.email IS NOT NULL
  AND c.suppressed = 0
ORDER BY a.total_beds DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — Skip DIY, Leapfrog (Day 0)

**Variant A:**
- **Subject:** MEDITECH + insulin management at {{company_name}}
- **Body:**
  {{first_name}},

  MEDITECH hospitals face a unique challenge with insulin management — the platform's native tools for insulin dosing are more limited than what you'll find in Epic or Cerner. Many MEDITECH sites end up building workarounds, which are time-consuming and never get FDA-validated.

  The good news: you can skip the DIY phase entirely. Glucommander is the only FDA-cleared insulin management system, and it's designed to work alongside MEDITECH without requiring custom builds.

  400+ hospitals use it today. MEDITECH sites that adopt Glucommander see the same 60%+ reduction in hypo events as Epic and Cerner sites — without the tooling gap.

  Worth exploring?

  {{sender_first_name}}

**Variant B:**
- **Subject:** Insulin dosing on MEDITECH — a better path
- **Body:**
  {{first_name}},

  Quick question: how is {{company_name}} handling insulin dosing on MEDITECH? I ask because most MEDITECH hospitals either rely on paper protocols or build custom tools that create maintenance headaches and liability risk.

  Glucommander offers a different path — an FDA-cleared system that plugs into MEDITECH and eliminates the need for homegrown calculators. The clinical results (60%+ fewer hypo events) are consistent regardless of the underlying EHR.

  If you're looking to modernize without a full EHR migration, this is worth a conversation.

  {{sender_first_name}}

### Step 2 — Operational Simplicity (Day 3)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  One thing MEDITECH hospitals appreciate about Glucommander is the implementation simplicity. Because it's a standalone system (not an EHR module), it doesn't require MEDITECH customization or IT development cycles.

  Typical go-live is 8-12 weeks. Nursing adoption is fast because the interface is purpose-built for insulin management, not a general-purpose EHR workflow.

  If you're tired of maintaining workarounds, this is the alternative. Happy to share more.

  {{sender_first_name}}

### Step 3 — Final Touch (Day 7)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  Last note — if insulin management isn't a current priority at {{company_name}}, no worries. But if it comes up during quality reviews or budget planning, Glucommander is worth having on your short list.

  Happy to send a quick overview whenever it's useful.

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
  "title": "CNO",
  "company_name": "HCA Healthcare",
  "primary_ehr": "MEDITECH",
  "total_beds": "47000",
  "account_tier": "Active",
  "recipe": "R5"
}
```

---

## Sender Assignment

3-5 warmed mailboxes. Rotate domains.
