---
description: Pause or activate an Instantly campaign
---

Toggle an Instantly campaign between paused and active states.

Arguments: $ARGUMENTS

First argument is the campaign name (or partial match). Second argument is the action: "pause" or "activate". Default is dry-run mode. Use "--live" to execute real API calls.

Examples:
- "GHW_New_In_Role pause" — dry run pause
- "GHW_New_In_Role activate --live" — live activate

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.toggle_campaign $ARGUMENTS
```

After running, confirm the campaign's new status. If activation failed, explain the prerequisites (senders, leads, sequences, schedule must all be configured).
