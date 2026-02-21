---
description: Block list (DNC) — add, list, or remove entries (reversible!)
---

Manage the Instantly block list via REST API. Unlike Salesforge DNC, entries are fully reversible.

Arguments: $ARGUMENTS

Commands:
- "--list" — show all block list entries (Instantly + local DB)
- "add user@example.com --reason opt_out" — block an email
- "add example.com --reason domain" — block an entire domain
- "remove <entry_id>" — unblock an entry (reversible!)

Default is dry-run mode. Use "--live" to execute real API calls.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.block_list $ARGUMENTS
```

After running, confirm what was added/removed and current block list count.
