---
description: Push positive replies to Clay webhook for Salesforce integration
---

Push all unpushed positive replies to Clay webhook. This closes the Instantly → Clay → Salesforce loop.

Arguments: $ARGUMENTS

Default is dry-run mode (shows payloads without sending). Use "--live" to fire real HTTP POST to the Clay webhook URL.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python push_to_clay.py $ARGUMENTS
```

After running, summarize: how many replies were pushed, success/failure counts, and any warnings about missing CLAY_WEBHOOK_URL.
