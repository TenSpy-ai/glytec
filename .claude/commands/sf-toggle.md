---
description: Pause or activate a campaign
---

Toggle a campaign between active and paused states.

Arguments: $ARGUMENTS

Expected format: "<campaign name> <pause|activate>". Defaults to dry-run. Add --live to execute.

WARNING: Activating a campaign starts sending emails immediately!

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/toggle_campaign.py $ARGUMENTS
```

After running, confirm the state change and remind about consequences (activating = emails start sending).
