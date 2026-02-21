---
description: Mailbox health — check connectivity and alert on disconnects
---

Check mailbox health across all Salesforge mailboxes. Reports healthy vs disconnected, creates UI tasks for any disconnected mailboxes.

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/mailbox_health.py
```

After running, summarize: total mailboxes, how many healthy, any disconnected (with reasons). If disconnected, note that reconnection must be done in the Salesforge UI.
