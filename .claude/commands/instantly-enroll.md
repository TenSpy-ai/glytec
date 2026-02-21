---
description: Enroll contacts into an existing Instantly campaign
---

Enroll contacts from the local DB into an existing Instantly campaign via MCP bulk add (up to 1000 per call).

Arguments: $ARGUMENTS

Required: --campaign <name>. Optional filters: --account <name>, --tier <tier>, --all. Default is dry-run mode. Use "--live" to execute real API calls.

Examples:
- "--campaign GHW_New_In_Role --account HCA" — dry run, HCA contacts only
- "--campaign GHW_New_In_Role --tier Active --live" — live, Active tier only
- "--campaign GHW_New_In_Role --all --live" — live, all eligible contacts

Contacts are deduped against existing enrollments and the block list.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.enroll_contacts $ARGUMENTS
```

After running, summarize how many contacts were enrolled and any notable ICP categories represented.
