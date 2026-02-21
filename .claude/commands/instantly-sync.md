---
description: Full sync — run all sync jobs from Instantly
---

Run the full sync pipeline: pull campaigns, leads, emails, accounts, and metrics from Instantly MCP into the local SQLite DB.

Arguments: $ARGUMENTS

Default is dry-run mode. Use "--live" to pull real data from Instantly MCP.

5 sync jobs run sequentially:
1. Campaigns → campaigns table
2. Leads → match to contacts by email, update instantly_lead_id
3. Emails → email_threads table
4. Accounts → mailboxes table
5. Metrics → metric_snapshots

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m sync.sync_all $ARGUMENTS
```

After running, summarize how many records were synced per job and any errors encountered.
