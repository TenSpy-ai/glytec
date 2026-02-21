# ops/ — GTM Operations Scripts

25 operational scripts covering the full Salesforge campaign lifecycle. All default to `DRY_RUN=True`.

## Status: All Operational

None of these are experiments. Each script is a tested, standalone CLI tool.

## Campaign Management

| Script | What it does |
|--------|-------------|
| `launch_campaign.py` | Full 5-step lifecycle: create seq -> add steps -> assign mailboxes -> enroll contacts -> activate |
| `toggle_campaign.py` | Activate or pause campaigns, tracks launched_at/paused_at |
| `delete_campaign.py` | Permanently delete sequences (irreversible, requires `--live`) |
| `enroll_contacts.py` | Add contacts to existing campaigns, dedupes against enrolled + DNC |
| `ab_test.py` | Set up A/B variants on campaign steps with split weights |
| `campaign_status.py` | Overview of all sequences with inline stats (opens, replies, bounces) |

## Metrics & Reporting

| Script | What it does |
|--------|-------------|
| `pull_metrics.py` | Pull analytics from Salesforge, save daily snapshots (30-day default) |
| `weekly_metrics.py` | Week-over-week aggregates with deltas |
| `trend_report.py` | 30/60/90-day rolling windows + 14-day daily trend |
| `compare_campaigns.py` | Side-by-side metrics for 2+ campaigns |
| `segment_report.py` | Breakdowns by EHR vendor and ICP persona |
| `pipeline_report.py` | Meeting attribution to campaigns, conversion rates |

## Contact & Account Management

| Script | What it does |
|--------|-------------|
| `search_contacts.py` | Multi-field search (name, email, account, ICP, title), auto-detects type |
| `account_view.py` | Deep-dive: tier, score, contacts, engagement, facilities, triggers |
| `update_contact.py` | Local-only field updates, re-runs ICP matching if title changes |
| `bulk_import.py` | CSV import with dedup, ICP matching, flexible field mapping |
| `view_suppressed.py` | Suppressed contact summary grouped by reason |
| `account_tiers.py` | Scored account list by tier, optional `--rescore` |

## Mailbox & Compliance

| Script | What it does |
|--------|-------------|
| `mailbox_health.py` | Sync mailbox status, flag disconnected (must reconnect in UI) |
| `add_to_dnc.py` | Add to local + Salesforge DNC (irreversible) |
| `kill_switch.py` | Monitor bounce rate (>5%), auto-pause campaigns |

## Planning

| Script | What it does |
|--------|-------------|
| `campaign_planner.py` | 3 subcommands: `plan` (eligible contacts), `backlog` (ideas), `coverage` (reach) |
| `plan_wave.py` | Find untouched Priority/Active accounts for next outreach wave |
| `draft_emails.py` | List draft steps, templates, preview email content |
