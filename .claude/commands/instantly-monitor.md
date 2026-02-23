---
description: Monitor — daily metrics + reply processing + Clay push + kill-switch check
---

Run the full daily monitoring cycle: pull metrics from Instantly, process new replies, push positive replies to Clay webhook, and check kill-switch thresholds.

Arguments: $ARGUMENTS

Default is dry-run mode. Use `--live` to pull real data from Instantly and push to Clay webhook.

## Execution

```python
import sys
sys.path.insert(0, "/Users/oliviagao/project/glytec/gtm-hello-world")
from autopilot import run_monitor
```

Run `run_monitor(live="--live" in args)` and report the results.

## What it does

1. **Pull Metrics** — syncs campaign analytics from Instantly into metric_snapshots table
2. **Process Replies** — scans for new reply emails, classifies sentiment (positive/negative/neutral/OOO)
3. **Push to Clay** — sends positive replies to Clay webhook for Salesforce integration
4. **Kill-Switch Check** — warns if bounce rate > 5% for any campaign

## After running, summarize:
1. How many campaigns had metrics pulled
2. How many replies were processed and their sentiment breakdown
3. How many positive replies were pushed to Clay
4. Any kill-switch warnings (bounce > 5%, recommend pausing campaign)
5. If there are warnings, suggest next steps (e.g., `/instantly-toggle <campaign> pause`)
