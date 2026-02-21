---
description: Add to DNC — irreversible, adds to local + Salesforge DNC list
---

Add email addresses to the Do Not Contact list. IRREVERSIBLE in Salesforge — cannot remove via API.

Arguments: $ARGUMENTS

Expects: email address(es) and optionally --reason (opt_out, bounce, suppression, manual).

DRY-RUN by default. Add --live to actually push to Salesforge.

```bash
cd /Users/oliviagao/project/glytec/salesforge && source /Users/oliviagao/project/glytec/.venv/bin/activate && python ops/add_to_dnc.py $ARGUMENTS
```

IMPORTANT: Warn the user that Salesforge DNC is write-only — entries cannot be removed via API. Show the contact context before confirming.
