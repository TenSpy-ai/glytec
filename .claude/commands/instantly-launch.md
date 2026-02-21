---
description: Launch a campaign — full lifecycle from creation to enrollment
---

Launch a new Instantly campaign: create campaign with schedule + sequences, assign sender accounts, bulk enroll contacts, and optionally activate.

Arguments: $ARGUMENTS

Required: --name <name>. Contact filters (at least one required): --account <name>, --tier <tier>, --all. Options: --activate (auto-activate after setup). Default is dry-run mode. Use "--live" to execute real API calls.

Examples:
- "--name GHW_New_In_Role --account HCA" — dry run, HCA contacts
- "--name GHW_New_In_Role --tier Active --activate --live" — live, Active tier, auto-activate
- "--name GHW_Smoke_Test --all --live" — live, all eligible, leave as draft

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.launch_campaign $ARGUMENTS
```

After running, summarize:
1. Campaign ID and status (draft/active)
2. How many contacts were enrolled
3. How many sender accounts were assigned
4. Steps completed and any errors
5. If draft, remind to use /instantly-toggle to activate when ready
