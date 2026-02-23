---
description: Autopilot — end-to-end campaign creation from template + lead criteria
---

Run the GTM Autopilot pipeline: select a campaign template, match contacts, create campaign, enroll leads, and optionally activate — all in one step.

Arguments: $ARGUMENTS

## How to use

If **no arguments** are provided, ask the user:
1. Which campaign template? (new-in-role, priority-account, ehr-epic, ehr-cerner, ehr-meditech, financial-recovery, territory-outreach, physician-champion, account-deep-dive)
2. Lead criteria — natural language like "top 20 CNOs at Epic hospitals" or structured filters (tier, account, titles, EHR, department)
3. Schedule — weekday (default), aggressive, conservative
4. Mode — dry run (default) or --live

If **arguments are provided**, parse them:
- First word = template name (e.g., "new-in-role", "priority-account", "epic")
- Remaining = natural language lead criteria (e.g., "top 20 CNOs at Epic hospitals")
- `--live` = execute real API calls
- `--activate` = auto-activate after setup
- `--schedule <type>` = weekday / aggressive / conservative

## Execution

```python
import sys
sys.path.insert(0, "/Users/oliviagao/project/glytec/gtm-hello-world")
from autopilot import Autopilot, AutopilotConfig
from query_builder import ContactQuery, parse_natural_language
```

1. **Build the query** — use `parse_natural_language()` for natural text, or chain `ContactQuery()` methods for structured filters
2. **Build the config** — create `AutopilotConfig(template=..., query=..., live=..., auto_activate=..., schedule_type=...)`
3. **Show preflight** — print the template name, query description, contact count, schedule, and mode. Ask user to confirm.
4. **Run** — call `Autopilot().run(config)`
5. **Report** — summarize: campaign name, ID, status, enrolled count, steps completed, any errors

## Examples

- `/instantly-autopilot` — interactive mode, ask questions
- `/instantly-autopilot new-in-role top 20 CNOs` — New-in-Role template, top 20 CNOs
- `/instantly-autopilot priority-account all Active tier --live` — live Priority Account for Active tier
- `/instantly-autopilot epic top 5 Active tier --schedule aggressive` — Epic EHR, aggressive schedule
- `/instantly-autopilot account-deep-dive "HCA Healthcare" --live --activate` — all HCA contacts, live + activate
