---
description: Enroll contacts into an existing campaign
---

Add contacts to an existing Salesforge campaign. DRY-RUN by default.

Arguments: $ARGUMENTS

Parse arguments for: campaign name, --tier, --ehr, --account, --persona, --live

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/enroll_contacts.py --campaign "$ARGUMENTS"
```

After running, report how many contacts were enrolled (or would be enrolled in dry-run mode). Note dedup results if any contacts were already enrolled.
