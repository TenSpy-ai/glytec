---
description: Launch a campaign — full lifecycle from sequence creation to enrollment
---

Launch a new Salesforge campaign. DRY-RUN by default — shows full preview without making API calls.

Arguments: $ARGUMENTS

The user should provide a campaign name and optionally: tier, EHR, persona filters. Example: "Q1 CNO Epic Priority"

Parse the arguments to extract:
- Campaign name (required)
- --tier: Priority, Active, Nurture
- --ehr: Epic, Cerner, Meditech
- --persona: "Decision Maker", "Influencer"
- --live: Actually execute API calls
- --activate: Auto-activate after creation

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/launch_campaign.py --campaign-name "$ARGUMENTS" --dry-run
```

IMPORTANT: This is DRY-RUN by default. Tell the user the preview results and ask if they want to proceed with --live.

After running, summarize:
1. How many contacts would be enrolled
2. The email content being used
3. Remind them this was a dry run unless --live was specified
