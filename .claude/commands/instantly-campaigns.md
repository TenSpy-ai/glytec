---
description: Campaign overview — list all Instantly campaigns with inline stats
---

Run the campaign status script to show all Instantly campaigns with their current status, lead counts, and performance.

Arguments: $ARGUMENTS

If no arguments provided, show all campaigns. If "active" or "paused", filter by that status. If "detail <name>", show detailed view of a specific campaign.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.campaign_status $ARGUMENTS
```

After running, summarize the results in a clean table format showing campaign name, status, leads, and recipe.
