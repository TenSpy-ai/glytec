---
description: Check replies — pull threads and show unhandled
---

Pull reply threads from Salesforge and show unhandled replies.

Arguments: $ARGUMENTS

"all" shows all threads. A number limits results. Default shows only unhandled replies.

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/check_replies.py $ARGUMENTS
```

After running, summarize reply threads grouped by type (lead_replied vs ooo). Offer to mark specific threads as "handled" or "needs_follow_up" if requested.
