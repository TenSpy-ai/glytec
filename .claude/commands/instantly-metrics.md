---
description: Pull metrics — sync from Instantly + dashboard + kill-switch check
---

Run the full metrics pipeline: pull analytics from Instantly via MCP, display dashboard, then run kill-switch checks.

Arguments: $ARGUMENTS

Default is dry-run mode. Use "--live" to pull real analytics from Instantly MCP. If a campaign name is provided, note it for filtering.

Steps:
1. Pull metrics from Instantly:
```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python pull_metrics.py $ARGUMENTS
```

2. Display full dashboard:
```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python check_status.py
```

After running both, summarize: key metrics, any kill-switch warnings (bounce >5%, spam >0.3%), and trends if visible.
