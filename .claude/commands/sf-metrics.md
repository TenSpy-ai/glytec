---
description: Pull metrics — sync + dashboard + kill-switch check
---

Run the full metrics pipeline: sync metrics from Salesforge, display dashboard, then run kill-switch check.

Arguments: $ARGUMENTS

If a campaign name is provided, filter to that campaign. If "30d" or "90d", set the time range. Default is 30 days, all campaigns.

Steps:
1. Sync metrics from Salesforge:
```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python sync/pull_metrics.py
```

2. Display dashboard:
```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/pull_metrics.py $ARGUMENTS
```

3. Run kill-switch check:
```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/kill_switch.py
```

After running all three, summarize: key metrics, any campaigns paused by kill-switch, and trends if visible.
