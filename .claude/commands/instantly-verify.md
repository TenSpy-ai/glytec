---
description: Verify emails before enrollment — checks deliverability via Instantly MCP
---

Verify email deliverability using Instantly MCP's verify_email tool. Updates the contacts table with verification results.

Arguments: $ARGUMENTS

Modes:
- Single email: "user@example.com"
- From DB, unverified only: "--from-db --unverified"
- From DB, by account: "--from-db --account HCA"
- With batch limit: "--from-db --unverified --limit 50"

Default is dry-run mode. Use "--live" to execute real verification calls. Each verification takes 5-45 seconds.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.verify_emails $ARGUMENTS
```

After running, summarize the verification results: valid/invalid/risky/unknown counts. Flag any invalid emails that should be added to the block list.
