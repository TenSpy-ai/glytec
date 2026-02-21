---
description: Search contacts — local DB + Instantly, auto-detects email/name/account
---

Search for contacts across local DB and Instantly. Auto-detects whether the query is an email, name, account, ICP category, or title.

Arguments: $ARGUMENTS

Examples:
- `steven.dickson` — searches by name
- `steven.dickson@allinahealth.org` — searches by email + checks campaign enrollment
- `HCA` — searches by account name
- `--icp "Decision Maker"` — filters by ICP category
- `--title CNO` — filters by title

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python -m ops.search_contacts $ARGUMENTS
```

After running, present the results in a clean format. If searching by email, also show which campaigns the contact is enrolled in.
