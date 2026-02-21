---
description: Mailbox health — check connectivity, warmup, and alert on problems
---

Run the mailbox health script to show all Instantly sending accounts with their status, warmup progress, and connectivity.

Arguments: $ARGUMENTS

If no arguments, list all sending accounts with status. If "test", run connectivity tests on all accounts. If "detail <email>", show full details for one account.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.mailbox_health $ARGUMENTS
```

After running, highlight any warnings (disconnected accounts, banned warmups, connection errors) and recommend actions.
