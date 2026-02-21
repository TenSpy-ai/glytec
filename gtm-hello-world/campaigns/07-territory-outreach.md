# Campaign: Territory-Aligned Outreach

**Campaign Name:** `GHW_Territory_Q1`
**Recipe:** R7 — Geographic / Rep Territory
**Skill:** `/dh-signals rep {rep_name}` — discovers contacts filtered by sales rep assignment
**Target Segment:** Contacts at facilities assigned to a specific sales rep
**Target Persona:** CNO, CFO, CMO

---

## Targeting Criteria

Run `/dh-signals rep Clayton` (or the assigned rep name) to pull territory contacts, then query:

```sql
SELECT c.first_name, c.last_name, c.email, c.title, a.system_name,
       a.total_beds, a.assigned_rep, f.state, f.city
FROM contacts c
JOIN accounts a ON c.account_name = a.system_name
JOIN facilities f ON f.highest_level_parent = a.system_name
WHERE a.assigned_rep = '{{rep_name}}'
  AND c.icp_category = 'Decision Maker'
  AND c.email IS NOT NULL
  AND c.suppressed = 0
GROUP BY c.email
ORDER BY a.score DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — Rep-Introduced, Personal (Day 0)

**Variant A:**
- **Subject:** {{first_name}}, quick intro from your Glytec contact
- **Body:**
  {{first_name}},

  I'm {{sender_first_name}}, and I work with health systems in your region on insulin management solutions. I wanted to introduce myself since {{company_name}} is in my territory and I've been following your system's clinical initiatives.

  I work with hospitals that are looking to modernize their insulin dosing — moving from homegrown calculators to Glucommander, the only FDA-cleared insulin management system. The clinical results are significant: 60%+ fewer hypo events, shorter LOS, and improved quality scores.

  Would it be worth connecting for a quick intro? I'd love to understand what {{company_name}} is doing in this space.

  Best,
  {{sender_first_name}}

**Variant B:**
- **Subject:** Insulin management conversation, {{first_name}}?
- **Body:**
  {{first_name}},

  I've been meaning to reach out — I support health systems in your area and wanted to connect about insulin management at {{company_name}}.

  Most systems I work with are still using unvalidated dosing tools. Glucommander offers a validated alternative with strong clinical evidence. If this is something you're thinking about, I'd value the chance to learn about your current approach.

  {{sender_first_name}}

### Step 2 — Value Add (Day 4)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  Following up — I wanted to share that several systems in your region have adopted Glucommander in the past year. The feedback has been consistently positive, especially around nursing adoption speed and the reduction in hypo events.

  If you're evaluating clinical technology for 2026, I'd be happy to share what your peers are seeing.

  {{sender_first_name}}

### Step 3 — Meeting Offer (Day 8)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  {{first_name}},

  I know your calendar is packed. If insulin management is anywhere on the 2026 roadmap for {{company_name}}, I'm happy to work around your schedule for a brief conversation.

  If not, no worries — I'll be here whenever it becomes relevant.

  {{sender_first_name}}

---

## Campaign Settings

| Setting | Value |
|---------|-------|
| daily_limit | 20 |
| email_gap | 15 min |
| stop_on_reply | true |
| stop_for_company | true |
| open_tracking | false |
| link_tracking | false |

---

## Custom Variables (per lead)

```json
{
  "title": "CNO",
  "company_name": "Providence",
  "assigned_rep": "Clayton Maike",
  "state": "WA",
  "total_beds": "8500",
  "account_tier": "Active",
  "recipe": "R7"
}
```

---

## Sender Assignment

Use the rep's own mailbox domains when possible for authenticity. Supplement with shared warmed mailboxes.
