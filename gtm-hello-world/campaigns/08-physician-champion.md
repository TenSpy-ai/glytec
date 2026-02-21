# Campaign: Physician Champion Strategy

**Campaign Name:** `GHW_Physician_Champion_Q1`
**Recipe:** R8 — Physician Champions
**Skill:** `/dh-contacts physicians {def_id}` — finds endocrinologists, hospitalists, medical directors
**Target Segment:** Endocrinologists, hospitalists, medical directors who can champion adoption
**Target Persona:** Endocrinologists, Medical Directors, Hospital Medicine Directors

---

## Targeting Criteria

Run `/dh-contacts physicians {def_id}` for target hospitals to pull physician champions, then query:

```sql
SELECT p.first_name, p.last_name, p.email, p.specialty,
       p.hospital_name, p.npi, p.medicare_claims
FROM physicians p
JOIN facilities f ON p.definitive_id = f.definitive_id
JOIN accounts a ON f.highest_level_parent = a.system_name
WHERE p.specialty IN ('Endocrinology', 'Hospital Medicine', 'Internal Medicine')
  AND a.tier IN ('Priority', 'Active')
  AND p.email IS NOT NULL
ORDER BY p.medicare_claims DESC;
```

---

## Email Sequence (3 steps)

### Step 1 — Clinical Evidence, Peer Influence (Day 0)

**Variant A:**
- **Subject:** Clinical evidence on insulin management, {{first_name}}
- **Body:**
  Dr. {{last_name}},

  I'm reaching out because your work in {{specialty}} at {{company_name}} puts you in a unique position to evaluate how insulin management is handled across the hospital.

  Most hospitals still rely on unvalidated insulin calculators — tools that have never been through FDA review. Glucommander is the only FDA-cleared insulin management system, and the evidence is compelling: 60%+ reduction in hypoglycemic events, measurable LOS reduction, and improved glycemic control across diverse patient populations.

  As a physician who sees these patients daily, I'd value your perspective on whether {{company_name}} might benefit from a validated approach. Would you be open to reviewing the clinical data?

  {{sender_first_name}}

**Variant B:**
- **Subject:** A clinical question about insulin dosing at {{company_name}}
- **Body:**
  Dr. {{last_name}},

  Quick question from a clinical perspective: how confident are you in the insulin dosing tools your nurses are using at {{company_name}}? Most hospital insulin calculators are homegrown and unvalidated.

  Glucommander replaces those tools with an FDA-cleared system that adapts dosing based on patient response. The outcomes data from 400+ hospitals is strong. If evidence-based insulin management is something you care about, I'd love to share the research.

  {{sender_first_name}}

### Step 2 — Protocol Ownership (Day 4)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  Dr. {{last_name}},

  One thing physicians appreciate about Glucommander is that it gives them protocol ownership without the maintenance burden. The system's algorithms are evidence-based and continuously updated — no more managing paper protocols or custom EHR builds.

  Endocrinologists and medical directors who champion the adoption often see it as an extension of their clinical standards, not a replacement. The nursing team benefits from clearer dosing guidance, and the patient outcomes speak for themselves.

  If you'd like to see the clinical publications, I'm happy to send them over.

  {{sender_first_name}}

### Step 3 — Low-Pressure Close (Day 8)

- **Subject:** Re: {{step1_subject}}
- **Body:**
  Dr. {{last_name}},

  I realize you're busy with clinical duties. If insulin management at {{company_name}} is something you think about — or if you've seen issues with the current approach — I'm available whenever it makes sense to connect.

  No sales pitch, just the evidence. Happy to work around your schedule.

  {{sender_first_name}}

---

## Campaign Settings

| Setting | Value |
|---------|-------|
| daily_limit | 15 |
| email_gap | 15 min |
| stop_on_reply | true |
| stop_for_company | false |
| open_tracking | false |
| link_tracking | false |

---

## Custom Variables (per lead)

```json
{
  "title": "Endocrinologist",
  "specialty": "Endocrinology",
  "company_name": "Baylor Scott & White",
  "npi": "1234567890",
  "total_beds": "5600",
  "recipe": "R8"
}
```

---

## Sender Assignment

2-3 warmed mailboxes. Lower volume — physician outreach should feel personal, not mass-market.
