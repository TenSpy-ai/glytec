---
description: Search contacts — auto-detects email, name, account, ICP, title
---

Search the local contact database. API filters are broken, so all searching is local.

Arguments: $ARGUMENTS

Auto-detects search type: email (contains @), title (CNO, CFO, etc.), ICP category, or name/account. Can also use explicit flags: --name, --email, --account, --icp, --title.

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/search_contacts.py $ARGUMENTS
```

After running, present results in a clean format. If many results, group by account or tier.
