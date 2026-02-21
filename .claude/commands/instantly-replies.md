---
description: Check replies — pull from Instantly, classify sentiment, triage
---

Process email replies: pull new emails from Instantly MCP, classify sentiment (positive/negative/neutral/OOO), and triage for follow-up.

Arguments: $ARGUMENTS

Default is dry-run mode (processes existing email_threads only). Use "--live" to pull new emails from Instantly MCP first.

```bash
cd /Users/oliviagao/project/glytec/gtm-hello-world && source /Users/oliviagao/project/glytec/.venv/bin/activate && python process_replies.py $ARGUMENTS
```

After running, summarize:
1. How many new replies were pulled (live mode)
2. Sentiment breakdown (positive/negative/neutral/OOO)
3. Any positive replies that need follow-up or Clay push
4. Any negative replies that should be considered for the block list
