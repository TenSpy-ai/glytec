---
description: Campaign overview — list all sequences with inline stats
---

Run the campaign status script to show all Salesforge sequences with their current metrics.

Arguments: $ARGUMENTS

If no arguments provided, show all campaigns. If "active" or "paused", filter by that status. If "detail <name>", show detailed view of a specific campaign.

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/campaign_status.py $ARGUMENTS
```

After running, summarize the results in a clean table format showing campaign name, status, leads, open rate, reply rate, and bounce rate.
