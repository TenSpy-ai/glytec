# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Glytec AI SDR — an AI-powered Sales Development Representative targeting hospital systems for Glytec's insulin management solutions. The project uses the Datagen SDK/MCP to orchestrate outreach tools (email, CRM, etc.) and operates against prospect data in `data/`.

## Environment

- Python 3.11, virtualenv at `.venv/`
- Activate: `source .venv/bin/activate`
- Auth: `DATAGEN_API_KEY` must be set in `.env`
- Install SDK: `pip install datagen-python-sdk`

## Data Files (`data/`)

| File | Contents |
|------|----------|
| `AI SDR_Facility List_1.23.26.csv` | Hospital facilities with beds, revenue, EHR, ICU stats, geo, ownership |
| `AI SDR_Facility List_Supplemental Data_1.23.26.csv` | Same facilities with rep assignments and additional clinical detail |
| `AI SDR_Parent Account List_1.23.26.csv` | Ranked parent health systems with bed counts, segment, opportunity $ |
| `AI SDR_ICP Titles_2.12.26.csv` | Ideal Customer Profile titles with department, category, intent score, job level |
| `AI SDR_Glytec_New Story_Magnetic Messaging Framework_1.28.26.docx` | Messaging framework for outreach |

Key join fields: `Definitive ID` links facilities across CSVs; `Highest Level Parent` groups facilities under parent systems.

## Datagen SDK (tool execution in code)

- Execute tools by alias: `client.execute_tool("<tool_alias>", params)`
- Tool aliases: `mcp_<Provider>_<tool_name>` for connected MCP servers, or first-party like `listTools`, `searchTools`, `getToolDetails`
- **Always be schema-first**: confirm params via `getToolDetails` before calling a tool

### Required workflow

1. Verify `DATAGEN_API_KEY` exists (ask user if missing)
2. Create client: `from datagen_sdk import DatagenClient; client = DatagenClient()`
3. Discover tool alias with `searchTools` (never guess)
4. Confirm schema with `getToolDetails`
5. Execute with `client.execute_tool(tool_alias, params)`
6. Errors: 401/403 = bad key or unconnected MCP server; 400/422 = wrong params, re-check schema

### Quick reference

```python
from datagen_sdk import DatagenClient
client = DatagenClient()

client.execute_tool("listTools")                                    # all tools
client.execute_tool("searchTools", {"query": "send email"})         # search by intent
client.execute_tool("getToolDetails", {"tool_name": "mcp_Gmail_gmail_send_email"})  # schema
```

## Datagen MCP vs SDK

- **MCP**: interactive discovery/debugging of tool names and schemas
- **SDK**: execution in scripts and apps via `DatagenClient`
- In Claude Code (has shell access), prefer writing and running local SDK scripts over `executeCode`
