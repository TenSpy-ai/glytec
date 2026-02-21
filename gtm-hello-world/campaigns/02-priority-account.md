# Campaign: Priority Account Outreach

**Campaign Name:** `GHW_Priority_Account_Q1`
**Recipe:** R4 — Tiered Discovery
**Skill:** `/dh-accounts enterprise` — batch ICP discovery across Enterprise/Strategic systems
**Target Segment:** High-scoring health systems by bed count and opportunity $
**Target Persona:** CFO, CNO, CMO

---

## Targeting Criteria

Run `/dh-accounts enterprise` to refresh contact coverage, then query the enrichment DB:

```sql
SELECT c.first_name, c.last_name, c.email, c.title, a.system_name,
       a.total_beds, a.total_opp, a.score, a.tier
FROM contacts c
JOIN accounts a ON c.account_name = a.system_name
WHERE a.tier IN ('Priority', 'Active')
  AND a.score >= 65
  AND c.icp_category = 'Decision Maker'
  AND c.email IS NOT NULL
  AND c.suppressed = 0
ORDER BY a.score DESC, a.total_opp DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — System-Level Financial Impact (Day 0)

**Variant A:**
- **Subject:** {{company_name}}'s insulin management cost
- **Body:**
  {{first_name}},

  With {{total_beds}} beds across the {{company_name}} system, insulin management touches thousands of patients every month. The question is whether your current approach is costing more than it should — in both dollars and clinical outcomes.

  Most health systems your size are running unvalidated insulin calculators that create liability exposure and drive unnecessary hypoglycemic events. Glucommander — the only FDA-cleared system — typically delivers a 60%+ reduction in hypo events and measurable LOS improvement.

  For a system the size of {{company_name}}, the financial impact is significant. Worth a conversation?

  {{sender_first_name}}

**Variant B:**
- **Subject:** A question about insulin management at {{company_name}}
- **Body:**
  {{first_name}},

  I've been studying {{company_name}}'s profile — {{total_beds}} beds, {{primary_ehr}} EHR, complex patient population. One area that often gets overlooked at systems this size is insulin management.

  Are you currently using a validated insulin dosing system, or relying on homegrown calculators? The distinction matters more than most leaders realize — both for patient safety and for CMS quality metrics.

  Happy to share what we've seen at similar systems if this is on your radar.

  {{sender_first_name}}

### Step 2 — Peer Validation (Day 4)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  Following up — one thing I hear consistently from leaders at large systems is that they didn't realize the scope of the insulin management problem until they looked at the data.

  Glucommander is live in 400+ hospitals. Systems similar to {{company_name}} have seen 60%+ fewer hypo events, reduced LOS, and improved CMS quality scores — all from addressing this one clinical workflow.

  If you're evaluating clinical technology priorities for 2026, this is worth 15 minutes.

  {{sender_first_name}}

### Step 3 — Direct Ask (Day 8)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  I'll keep this brief — would it be helpful to see a short overview of what Glucommander has done at health systems comparable to {{company_name}}?

  No pressure either way. Just want to make sure you have the information if insulin management is something you're thinking about.

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
  "company_name": "HCA Healthcare",
  "total_beds": "47000",
  "total_opp": "$45M",
  "primary_ehr": "MEDITECH",
  "account_tier": "Active",
  "score": "72",
  "recipe": "R4"
}
```

---

## Sender Assignment

3-5 warmed mailboxes. Prioritize domain diversity for Enterprise/Strategic accounts.
