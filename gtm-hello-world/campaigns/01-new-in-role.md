# Campaign: New-in-Role Leadership Outreach

**Campaign Name:** `GHW_New_In_Role_Q1`
**Recipe:** R3 — Leadership Changes
**Skill:** `/dh-signals "{system_name}"` — detects leadership changes across a parent system
**Target Segment:** Executives who changed roles in the last 6 months at target health systems
**Target Persona:** CNO, CFO, CMO, CEO

---

## Targeting Criteria

Run the `/dh-signals` skill to pull leadership changes, then query the enrichment DB:

```bash
# Pull fresh signals for a specific system
/dh-signals "HCA Healthcare"

# Or query already-loaded R3 data (301K+ signals in enrichment.db)
sqlite3 ../enrichment/data/enrichment.db
```

```sql
SELECT e.first_name, e.last_name, e.email, e.title, e.hospital_name,
       ts.signal_type, ts.detected_date
FROM executives e
JOIN trigger_signals ts ON e.definitive_id = ts.definitive_id
WHERE ts.signal_type IN ('new_hire', 'title_change', 'role_change')
  AND ts.detected_date >= date('now', '-6 months')
  AND e.icp_matched = 1
  AND e.primary_email IS NOT NULL
ORDER BY ts.detected_date DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — Congratulations + Opening (Day 0)

**Variant A:**
- **Subject:** Congrats on the new role, {{first_name}}
- **Body:**
  {{first_name}},

  Congratulations on your move to {{title}} at {{company_name}}. Transitions like this are the perfect time to reassess clinical technology — especially insulin management, which touches every unit in the hospital.

  Most health systems still rely on unvalidated, homegrown insulin calculators. Glucommander is the only FDA-cleared insulin management system, and it's reduced hypo events by 60%+ at systems like yours.

  Would it be worth a 15-minute conversation about what the first 90 days could look like with a validated dosing system in place?

  Best,
  {{sender_first_name}}

**Variant B:**
- **Subject:** New role, new priorities — {{first_name}}
- **Body:**
  {{first_name}},

  Saw the news about your new position at {{company_name}} — congratulations. When leaders step into roles like {{title}}, one of the first questions is usually: "Where are our biggest clinical risk gaps?"

  For most health systems, insulin management is near the top. It's high-volume, high-risk, and most hospitals are still using spreadsheets or homegrown tools that have never been FDA-validated.

  Glucommander changes that equation. Happy to share what similar systems have done in the first 90 days.

  {{sender_first_name}}

### Step 2 — Evidence Follow-up (Day 3)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  Quick follow-up — wanted to share one data point that tends to resonate with leaders in your position:

  Health systems using Glucommander see a 60%+ reduction in hypoglycemic events and a measurable decrease in length of stay for insulin-dependent patients. That's not a pilot result — it's across 400+ hospitals.

  The clinical and financial case is strong. If insulin management is on your radar as you settle into the new role, I'd love to walk you through what the implementation timeline looks like.

  {{sender_first_name}}

### Step 3 — Soft Close (Day 7)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  Last note — I know the first few months in a new role are packed. If insulin management isn't a priority right now, no worries at all.

  But if it is something you're evaluating (or will be in 2026), I'm happy to send over a brief overview of what Glucommander does differently than the DIY calculators most systems are running.

  Either way, wishing you a great start at {{company_name}}.

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
| match_lead_esp | false |
| auto_variant_select | true |

---

## Custom Variables (per lead)

```json
{
  "title": "CNO",
  "company_name": "Regional Health System",
  "account_tier": "Active",
  "signal_type": "new_hire",
  "signal_date": "2026-01-15",
  "ehr_vendor": "Epic",
  "total_beds": "2500",
  "recipe": "R3"
}
```

---

## Sender Assignment

Rotate across 3-5 warmed mailboxes (all Clayton Maike personas). Assign based on domain diversity — don't send from the same domain to the same company.
