# /dh-signals — DH Trigger Signal Detection & Enrichment

Detects leadership changes, M&A activity, EHR migrations, and other trigger signals. Also pulls comprehensive account enrichment (quality, financials, memberships).

## Recipes Covered

- **Recipe 3** — Full Network Contact Map (all contacts + leadership changes across a system)
- **Recipe 7** — Geographic / Rep Territory Discovery (contacts by rep assignment)
- **Recipe 9** — Comprehensive Account Enrichment Bundle (quality, financials, GPO, news)

## Usage

Arguments: parent system name, rep name, or scope.

Examples:
- `/dh-signals "CommonSpirit Health"` — Network map + signals for CommonSpirit (Recipe 3)
- `/dh-signals rep Khirstyn` — Territory contacts for rep Khirstyn (Recipe 7)
- `/dh-signals enrich 2151` — Full enrichment bundle for Def ID 2151 (Recipe 9)
- `/dh-signals enrich enterprise` — Enrichment bundle for all Enterprise facilities (Recipe 9)

## Instructions

When this skill is invoked:

1. Parse the argument to determine:
   - If "rep {name}" → Recipe 7 with --rep flag
   - If "enrich {id_or_scope}" → Recipe 9
   - If quoted system name → Recipe 3 with --parent flag

2. Run the appropriate recipe:
   ```bash
   source /Users/oliviagao/project/glytec/.venv/bin/activate

   # Recipe 3: Network map + leadership changes
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 3 --parent "{NAME}" --live

   # Recipe 7: Rep territory
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 7 --rep "{REP}" --live

   # Recipe 9: Account enrichment (single)
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 9 --def-id {ID} --live

   # Recipe 9: Account enrichment (batch)
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 9 --scope enterprise --live
   ```

3. After the run, report trigger signals found:
   ```bash
   sqlite3 /Users/oliviagao/project/glytec/enrichment/data/enrichment.db "
     SELECT signal_type, COUNT(*) FROM trigger_signals WHERE run_id = (SELECT MAX(id) FROM runs) GROUP BY signal_type;
     SELECT signal_type, facility_name, summary FROM trigger_signals WHERE run_id = (SELECT MAX(id) FROM runs) ORDER BY signal_date DESC LIMIT 20;
   "
   ```

4. Report enrichment data:
   ```bash
   sqlite3 /Users/oliviagao/project/glytec/enrichment/data/enrichment.db "
     SELECT data_type, COUNT(*) FROM account_enrichment WHERE run_id = (SELECT MAX(id) FROM runs) GROUP BY data_type;
     SELECT metric_name, metric_value FROM account_enrichment WHERE run_id = (SELECT MAX(id) FROM runs) AND data_type = 'quality' LIMIT 20;
   "
   ```

## Notes

- Recipe 3 detects leadership changes via `lastUpdatedDate > 2025-12-01` — faster than news
- Recipe 9 pulls quality metrics, financial metrics, GPO/ACO memberships, and high-value news
- Trigger signals stored in `trigger_signals` table with type classification
- Account enrichment stored in `account_enrichment` table
