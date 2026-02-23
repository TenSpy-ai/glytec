# PROCESS.md — 12-Step Operational Playbook

How to run one outbound campaign from start to finish. Recommended starting point: **01-new-in-role.md** (R3 — Leadership Changes), because the enrichment data for R3 has already been run.

---

## Step 1: Pick a Recipe-Campaign

Choose a campaign from `campaigns/`. Each file maps to an enrichment recipe:

| File | Recipe | Best for |
|------|--------|----------|
| 01-new-in-role.md | R3 | First campaign — enrichment data already available |
| 02-priority-account.md | R4 | High-value accounts by score and opportunity |
| 03-ehr-epic.md | R5 | Epic hospitals — requires R5 run first |
| 04-ehr-cerner.md | R5 | Cerner hospitals — requires R5 run first |
| 05-ehr-meditech.md | R5 | MEDITECH hospitals — requires R5 run first |
| 06-financial-recovery.md | R6 | Financially distressed systems |
| 07-territory-outreach.md | R7 | Rep-assigned territories — requires R7 run first |
| 08-physician-champion.md | R8 | Physician outreach — enrichment data available |
| 09-account-deep-dive.md | R1/R2/R9/R10 | Single-account deep targeting |

**For your first campaign, use 01-new-in-role.md.** R3 data (301,510 trigger signals) is already in the enrichment DB.

---

## Step 2: Discover Contacts via Skills

Use the enrichment skills to pull contacts. Each campaign file lists the matching skill.

**Skill quick reference:**

| Skill | Recipe | What it does |
|-------|--------|-------------|
| `/dh-signals "{system}"` | R3 | Leadership changes + contacts across a parent system |
| `/dh-accounts enterprise` | R4 | Tiered ICP discovery for Enterprise/Strategic systems |
| `/dh-accounts ehr enterprise` | R5 | EHR-segmented discovery (Epic/Cerner/MEDITECH) |
| `/dh-accounts distress enterprise` | R6 | Financially distressed hospitals with CMS penalties |
| `/dh-signals rep {name}` | R7 | Territory contacts filtered by rep assignment |
| `/dh-contacts physicians {def_id}` | R8 | Physician champions at a specific hospital |
| `/dh-contacts {def_id}` | R1 | Full contact extraction at one hospital |
| `/dh-contacts icp {def_id}` | R2 | ICP-matched contacts at one hospital |
| `/dh-signals enrich {scope}` | R9 | Account enrichment bundle (quality, financials, GPO) |
| `/dh-contacts "{system}"` | R10 | Every contact across all facilities in a system |

**Example for R3 (new-in-role):** R3 data is already loaded (301K+ signals). Query the enrichment DB:

```bash
sqlite3 ../enrichment/data/enrichment.db
```

```sql
SELECT e.first_name, e.last_name, e.primary_email, e.title,
       e.hospital_name, ts.signal_type, ts.detected_date
FROM executives e
JOIN trigger_signals ts ON e.definitive_id = ts.definitive_id
WHERE ts.signal_type IN ('new_hire', 'title_change', 'role_change')
  AND ts.detected_date >= date('now', '-6 months')
  AND e.icp_matched = 1
  AND e.primary_email IS NOT NULL
ORDER BY ts.detected_date DESC
LIMIT 100;
```

To refresh signals for a specific system: `/dh-signals "HCA Healthcare"`

Review the results. Filter further by account tier, EHR, or geography as needed.

---

## Step 3: Create Campaign in Instantly

Use the MCP `create_campaign` tool (two-step process):

**Step 3a — Create with content:**
```
create_campaign:
  name: "GHW_New_In_Role_Q1"
  subject: "Congrats on the new role, {{first_name}}"
  body: [body from campaign MD file, Variant A]
  daily_limit: 30
  email_gap: 10
  stop_on_reply: true
  stop_for_company: true
  open_tracking: false
  link_tracking: false
```

**Step 3b — Assign senders:**
The first step returns available senders. Pick 3-5 warmed mailboxes and pass them as email_list.

Record the `instantly_campaign_id` returned.

---

## Step 4: Set Email Steps

Add all 3 steps with A/B variant on step 1 using `update_campaign`:

```
update_campaign:
  campaign_id: "<instantly_campaign_id>"
  sequences:
    - step: 0
      subject: ["Congrats on the new role, {{first_name}}", "New role, new priorities — {{first_name}}"]
      body: [Variant A body, Variant B body]
    - step: 1
      subject: "Re: {{step1_subject}}"
      body: [Step 2 body]
      delay_days: 3
    - step: 2
      subject: "Re: {{step1_subject}}"
      body: [Step 3 body]
      delay_days: 7
```

---

## Step 5: Assign Sender Mailboxes

Confirm mailbox assignment via MCP. Use 3-5 warmed accounts:

```
check_status.py → MAILBOXES section shows available warmed mailboxes
```

Assign mailboxes that are:
- Status: Active (1)
- Warmup: Active (1) with score > 85
- Domain-diverse (don't send from the same domain to the same company)

---

## Step 6: Enroll Contacts

Use MCP `add_leads_to_campaign_or_list_bulk` (up to 1,000 per call):

```
add_leads_to_campaign_or_list_bulk:
  campaign_id: "<instantly_campaign_id>"
  leads:
    - email: "steven.dickson@allinahealth.org"
      first_name: "Steven"
      last_name: "Dickson"
      company_name: "Allina Health"
      custom_variables:
        title: "CNO"
        account_tier: "Active"
        signal_type: "new_hire"
        signal_date: "2026-01-15"
        ehr_vendor: "Epic"
        total_beds: "3200"
        recipe: "R3"
  skip_if_in_workspace: true
```

After enrollment, update the local DB:

```sql
INSERT INTO campaign_contacts (campaign_id, contact_id)
SELECT c.id, ct.id
FROM campaigns c, contacts ct
WHERE c.name = 'GHW_New_In_Role_Q1'
  AND ct.email IN ('steven.dickson@allinahealth.org', ...);
```

---

## Step 7: Activate Campaign

**Pre-flight checklist:**

- [ ] Campaign has 3 email steps with A/B variant on step 1
- [ ] 3-5 warmed mailboxes assigned
- [ ] Contacts enrolled with custom_variables
- [ ] Daily limit set (30 or lower)
- [ ] stop_on_reply = true
- [ ] stop_for_company = true
- [ ] open_tracking = false (for cold outreach)
- [ ] Email content reviewed for personalization accuracy

Then activate:

```
activate_campaign:
  campaign_id: "<instantly_campaign_id>"
```

Update local DB:

```sql
UPDATE campaigns SET status = 'active', launched_at = datetime('now')
WHERE name = 'GHW_New_In_Role_Q1';
```

---

## Step 8: Daily Monitoring

Run metrics pull daily:

```bash
python pull_metrics.py --live
```

This will:
1. Pull aggregate analytics for all active campaigns
2. Pull daily analytics breakdown
3. Run kill-switch checks (bounce rate > 5% → WARNING)
4. Log all API calls to api_log

Review the dashboard:

```bash
python check_status.py
```

**Kill switches** — if any threshold is breached:
- Bounce rate > 5% → pause campaign immediately
- Spam rate > 0.3% → pause and investigate
- Unsubscribe rate > 2% → pause and review content

---

## Step 9: Reply Processing

Run reply processing daily:

```bash
python process_replies.py --live
```

This will:
1. Pull new replies from Instantly via MCP
2. Classify sentiment (AI interest score + keyword overrides)
3. Store in email_threads and reply_sentiment tables
4. Triage: positive → needs_follow_up, negative → handled, OOO → archived

For positive replies, respond via MCP:

```
reply_to_email:
  reply_to_uuid: "<email_uuid>"
  body: "Thanks for the interest, {{first_name}}. I'd love to set up a brief call..."
  eaccount: "clayton@glytec-outreach.com"
```

Then push to Clay:

```bash
python push_to_clay.py --live
```

---

## Step 10: Weekly Reporting

Run the full dashboard weekly:

```bash
python check_status.py
```

Review:
- Campaign metrics trends (sent, opened, replied, bounced)
- Reply sentiment breakdown (positive/negative/neutral/OOO)
- Clay push status (pushed vs pending)
- Mailbox health (all Active and warmed?)
- API activity (any errors?)

Compare week-over-week:

```sql
SELECT snapshot_date, SUM(sent) as total_sent, SUM(opened) as total_opened,
       SUM(replied) as total_replied, SUM(bounced) as total_bounced
FROM metric_snapshots
WHERE snapshot_date >= date('now', '-14 days')
GROUP BY snapshot_date
ORDER BY snapshot_date;
```

---

## Step 11: Monthly Signal Refresh

Re-run R3 (Leadership Changes) and R9 (Account Bundle) monthly to catch:
- New leadership hires and departures
- Financial shifts (margin changes, revenue updates)
- Quality penalty updates (HAC, readmission, VBP)
- Membership changes (GPO, IDN)

Use the enrichment skills:

```
/dh-signals "CommonSpirit Health"    # R3 — leadership changes for a specific system
/dh-signals enrich enterprise        # R9 — account enrichment bundle across Enterprise systems
```

Or for batch operations across all systems, invoke the runner directly:
```bash
source ../.venv/bin/activate
python ../enrichment/runner.py --recipe 3 --scope enterprise --live
python ../enrichment/runner.py --recipe 9 --scope enterprise --live
```

After refresh, re-query for new contacts matching campaign criteria and enroll them.

---

## Step 12: Quarterly Contact Refresh

Re-run R4 (Tiered Discovery) quarterly for full ICP contact coverage:

```
/dh-accounts enterprise       # R4 — tiered ICP discovery for Enterprise systems
/dh-accounts commercial        # R4 — tiered ICP discovery for Commercial segment
```

After refresh:
1. Dedup new contacts against existing DB
2. Verify new emails via MCP `verify_email`
3. Score new contacts against ICP taxonomy
4. Plan next wave of campaigns

---

## Appendix: Autopilot Shortcuts

**`/instantly-autopilot`** automates Steps 3–7 (create campaign → enroll → activate). Provide a template and lead criteria in natural language:

```
/instantly-autopilot new-in-role top 20 CNOs at Epic hospitals
/instantly-autopilot priority-account all Active tier --live
/instantly-autopilot                    # interactive — picks template and leads interactively
```

**`/instantly-monitor`** automates Steps 8–9 (daily metrics + reply processing + Clay push + kill-switch):

```
/instantly-monitor          # dry run
/instantly-monitor --live   # live
```

Both commands log every step to `autopilot_runs` + `autopilot_steps` tables. View run history and step details in the Autopilot tab of `tracker.html`.

---

## Appendix: Quick Command Reference

| Task | Command |
|------|---------|
| Create/seed DB | `python seed_db.py` |
| Status dashboard | `python check_status.py` |
| Pull metrics (dry) | `python pull_metrics.py` |
| Pull metrics (live) | `python pull_metrics.py --live` |
| Process replies (dry) | `python process_replies.py` |
| Process replies (live) | `python process_replies.py --live` |
| Push to Clay (dry) | `python push_to_clay.py` |
| Push to Clay (live) | `python push_to_clay.py --live` |
| Query enrichment DB | `sqlite3 ../enrichment/data/enrichment.db` |
| Open hello-world DB | `sqlite3 data/gtm_hello_world.db` |
| Run test suite | `python -m tests.run_all` |
| Run tests (quick) | `python -m tests.run_all --quick` |
| Run single test | `python -m tests.run_all test_00_db` |
| Autopilot (dry) | `/instantly-autopilot new-in-role top 5 Active tier` |
| Autopilot (live) | `/instantly-autopilot priority-account all Active --live` |
| Monitor (dry) | `/instantly-monitor` |
| Monitor (live) | `/instantly-monitor --live` |

---

## Appendix: Potential Future Enhancements

These are not blockers — the system is fully functional today. Ideas for future improvement:

| Enhancement | Area | Details |
|-------------|------|---------|
| Auto-pause on kill-switch breach | pull_metrics.py | Currently logs WARNING when bounce > 5%. Could auto-call `pause_campaign`. |
| Pre-flight checklist validation | launch_campaign.py | Automated checks before activation (mailboxes? leads? sequences? warmup > 85?). |
| Week-over-week trend queries | check_status.py | Automated `metric_snapshots` comparison across dates. Currently manual SQL. |
| Webhook retry logic | push_to_clay.py | Retry on 5xx with exponential backoff. Currently fails silently. |
| Scheduled automation | Ops | Cron for daily pull_metrics + process_replies, monthly signal refresh, quarterly contact refresh. |
| Domain diversity checker | launch_campaign.py | Warn if all mailboxes share the same domain. |
| Contact scoring in DB | enroll | Apply ICP scoring from enrichment pipeline before enrollment. |
| Keyword admin UI | config_server.py | Edit sentiment keyword lists via config UI instead of editing process_replies.py. |
