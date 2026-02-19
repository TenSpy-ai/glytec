# Project Context

## Key People

| Name | Role | Contact |
|------|------|---------|
| **Clayton Maike** | VP, Growth @ Glytec (client stakeholder) | cmaike@glytec.com, 678-386-1026 |
| **Jeremy Ross** | GTM consultant (builder) | jross@glytec.com |
| **Joseph** | CRO advisor | — |

Clayton has signoff authority on all milestones. Jeremy builds and proposes; Clayton approves.

---

## Loom Videos (Reference)

| # | Video | Link | Speaker | Date | Duration |
|---|-------|------|---------|------|----------|
| 1 | Overview of the Current AI Lead Gen Process | [Loom](https://www.loom.com/share/bd60a5289a494eec9ad0c1b81778b4ac) | Clayton Maike | Feb 4, 2026 | ~9 min |
| 2 | Transitioning to a Sprint-Based Project Approach | [Loom](https://www.loom.com/share/6e4fb523717b4ddf8a10b36b3e10672f) | Clayton Maike | Feb 10, 2026 | ~4 min |
| 3 | Designing the Outbound and Contact Hygiene Process | [Loom](https://www.loom.com/share/63b6fffdb74844b1b3b23cfb502a1930) | Clayton Maike | Feb 11, 2026 | ~18 min |
| 4 | Pilot Goals and Action Items for Programmatic Outreach | [Loom](https://www.loom.com/share/3f6628e0dfac4d82a1031d0df0fcc1d7) | Clayton Maike | Feb 12, 2026 | ~14 min |

### Loom 1 — Overview of the Current AI Lead Gen Process (Feb 4)

Clayton walks through the existing "AI Legion" outreach workflow. Key process steps:

- **Clay** used for prospect identification and contact sourcing
- **Off-limits account filtering** — avoiding current customers and C-suite contacts
- **Data validation** — email validation via SalesForge to maintain low bounce rates
- **Reply management** — process for handling inbound replies from outreach

**Pain points identified:**
- Personalization is insufficient — messages are too template-driven
- Reporting is manual and lacks automation
- Need better process transparency and team visibility
- Need to filter restricted accounts more systematically

**Chapters:** 00:00 AI Legion Process Overview → 01:50 Off-Limits Account Filtering → 03:53 Data Validation Steps → 07:01 Reply Management Process

### Loom 2 — Transitioning to Sprint-Based Approach (Feb 10)

Clayton provides feedback on the initial project plan, advocating for a fundamental methodology shift:

- **Waterfall → sprints** — rapid iteration over sequential phases
- **4 structured releases** planned for refining the AI outbound and contact process
- **Sign-off session** scheduled for Friday Feb 13 to review future-state process and technical architecture
- Each infrastructure release followed by live outbound campaign for early feedback

**Chapters:** 00:00 Project Plan Feedback → 01:07 Proposed Milestone Structure → 02:00 Sign-off Session Details → 03:05 Weekly Progress Integration

### Loom 3 — Designing the Outbound and Contact Hygiene Process (Feb 11)

Longest and most detailed video. Clayton lays out the end-to-end vision:

- **Salesforce as system of record** — non-negotiable
- **Minimize manual steps** — automation-first in campaign messaging creation
- **Feedback loop** — built-in testing and learning mechanisms
- **Reporting/visibility** — Pat (CEO) specifically requesting a reporting interface for campaign transparency
- **Contact data sources** — multi-source strategy (ZoomInfo, LinkedIn, Clay)
- **Contact-to-account mapping** — using LeanData or equivalent
- **Parent-child account mapping** — handling IDN/health system hierarchies
- **Ongoing hygiene process** — continuous data quality management

**Chapters:** 00:00 Introduction and Context → 02:26 Automation and Manual Steps → 05:06 Learning and Feedback Loop → 08:16 Reporting and Visibility → 10:09 Contact Data Sources → 12:00 Mapping Contacts to Accounts → 14:40 Parent-Child Account Mapping → 17:06 Ongoing Hygiene Process

### Loom 4 — Pilot Goals and Action Items (Feb 12)

Clayton defines specific goals and action items for the pilot:

- **Pilot goal:** Execute 1:1 cold outreach programmatically, minimizing manual steps
- **Campaign goals** — define success metrics for outreach
- **Contact sourcing steps** — systematic approach to building contact lists
- **Reply management** — escalation protocols tied to engagement data tracked in Salesforce
- **Reporting and tracking** — deliverability metrics, engagement monitoring
- **Messaging framework** — introduction to Glytec's magnetic messaging framework for personalized copy

**Resources referenced:** ICP title listings, facility-level datasets, Salesforce integration for activity logging

**Chapters:** 00:00 Pilot Goals Overview → 02:05 Contact Sourcing Steps → 04:24 Reply Management Process → 06:39 Reporting and Tracking Needs → 13:09 Messaging Framework Introduction

---

## Clayton's Infrastructure Principles

From Clayton's email — these are the non-negotiable design constraints:

1. **Salesforce as system of record** (alternate DB if too many API calls)
2. **Sequencer is tool-agnostic** — not wedded to SalesForge
3. **All programmatic** — as few manual steps as possible
4. **Lean into AI/agents** — just can't be black box
5. **Clay as orchestrator**
6. **Learning/experimentation/tweaks/feedback loop** built in
7. **Reporting/dashboard/visibility** required
8. **ZoomInfo + other contact data sources** for enrichment
9. **LeanData** for mapping contacts to accounts
10. **Parent/child account mapping** must be handled
11. **Ongoing hygiene/validation process** for data quality

---

## Key Decisions

### Pivot: Waterfall → Rapid Pilot

- **Rationale:** Deliver tangible results for the **March 12 board meeting** and address sales team pressure on AI SDR investment
- **New approach:** Iterative pilot — 100 contacts, 10 accounts — to test v1 infrastructure and enable rapid refinement
- **Goal:** Ship functional infrastructure quickly, even if imperfect, to gather feedback and iterate

### SalesForge: API Over UI

- SalesForge UI is buggy (failed imports, broken Salesforce sync)
- **Decision:** Use the SalesForge API for programmatic control — this was the original rationale for selecting the tool
- Tool choice remains flexible per Clayton's principle #2

### LinkedIn as New Channel

- Start with Clayton's and Reagan's profiles
- If successful, onboard full sales team (15–20 profiles)
- **Requirement:** Dedicated email inboxes per rep for multi-channel outreach (email + LinkedIn) under a single identity
- **Lead time:** 2-week email warm-up period required

### Data Sources Unlocked

- **Definitive Healthcare** — access granted; primary source for hospital demographics (EHR, revenue, discharges); email data quality is poor
- **Claude Max** — access granted; for AI development
- **ZoomInfo** — for contact email/phone enrichment (DH emails are low quality)

---

## Meeting Notes — Jeremy/Clayton Sync (Feb 11, 2026)

57-minute alignment session. Key takeaways:

### Pilot Campaign & Data

- Pilot targets **20 contacts per account** (up from 5)
- ICP title list with permutations provided (now in `data/AI SDR_ICP Titles_2.12.26.csv`)
- Contact sourcing challenge: may need manual scraping of hospital leadership pages if automated tools fail
- Final system must be **maintainable by a non-technical analyst**

### AI Agent Knowledge Base

Building a knowledge base to train the AI agent on Glytec's GTM process. Content includes:
- ICP title list ✅ (in `data/`)
- Target account list ✅ (in `data/`)
- Messaging framework ✅ (in `data/`)
- Past campaign messaging (pending)
- Sales playbooks & call scripts (pending)
- Case studies & customer lists (pending)

### Action Items from 2/11

**Clayton:**
- [x] Send ICP title list with permutations
- [x] Send starter context (accounts CSV, messaging, playbooks)
- [x] Create pilot goals Loom video
- [ ] Confirm Definitive Healthcare API availability
- [ ] Provide campaign details for v1 launch (by 2/16 EOD)

**Jeremy:**
- [x] Build Claude Code repo; ingest Clayton's starter content
- [ ] Watch all Clayton Loom videos
- [ ] Review SalesForge campaigns/messaging; note bugs
- [ ] Investigate the Definitive Healthcare API
- [ ] Prepare "2B" future state process and tool stack proposal
- [ ] Attend Fri signoff w/ Clayton + Joseph
- [ ] Identify milestones and associated delivery dates based on SOW; share with Clayton before EOW (2/5)

### Action Items from ~Feb 13

**Clayton/Bryce:**
- [ ] Share additional knowledge base/onboarding materials

---

## Tool Stack (Emerging)

```
Salesforce (CRM / system of record)
    ↕
Clay (orchestrator / enrichment workflows)
    ↕
┌─────────────────────────────────────────┐
│  Data Sources                           │
│  ├─ Definitive Healthcare (HospitalView,│
│  │  PhysicianView, Monocl ExpertData)   │
│  ├─ ZoomInfo (contact emails/phones)    │
│  └─ LinkedIn (profile data)             │
└─────────────────────────────────────────┘
    ↕
LeanData (contact-to-account mapping)
    ↕
SalesForge API (sequencer / outbound)
    ├─ Email campaigns
    └─ LinkedIn outreach
    ↕
Reporting / Dashboard (TBD)
```

---

## Timeline Pressure

- **March 12:** Board meeting — must show tangible AI SDR results
- **March 27:** Full documentation, training, handoff, executive report-out
- **March 31:** Project stabilization/buffer

See [milestones.md](milestones.md) for the full sprint schedule.
