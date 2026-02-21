---
description: Full sync — run all sync jobs from Salesforge
---

Run sync jobs to pull latest data from Salesforge into the local GTM Ops database.

Arguments: $ARGUMENTS

Specific jobs: "sequences", "contacts", "threads", "mailboxes", "metrics". Leave empty for all jobs.

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python sync/sync_all.py $ARGUMENTS
```

After running, summarize what was synced and any errors encountered.
