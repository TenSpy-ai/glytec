---
description: Account view — details + contacts + engagement for an account
---

Show full account details from local DB: account info, contacts, campaign enrollment, reply sentiment, and engagement events.

Arguments: $ARGUMENTS

If no arguments or "--all", list all accounts sorted by score. Otherwise, search for the named account and show its full detail view.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.account_view $ARGUMENTS
```

After running, highlight key insights: account tier, number of contacts, engagement status, and any positive replies.
