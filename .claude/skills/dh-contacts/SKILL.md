# /dh-contacts — DH Contact Discovery

Discovers executive, physician, and RFP contacts at hospitals using the Definitive Healthcare API.

## Recipes Covered

- **Recipe 1** — Full Contact Extraction (all executives, physicians, RFPs, news at one hospital)
- **Recipe 2** — ICP-Matched Contact Discovery (targeted search using 66 ICP titles)
- **Recipe 8** — Physician Champion Pipeline (endocrinologists, hospitalists, medical directors)
- **Recipe 10** — Every Contact at a Company (exhaustive extraction for a parent system)

## Usage

Arguments: a Definitive ID, hospital name, or parent system name.

Examples:
- `/dh-contacts 2151` — Full extraction for Abbott Northwestern (Def ID 2151)
- `/dh-contacts "Tenet Healthcare"` — Every contact at all Tenet facilities
- `/dh-contacts icp 2151` — ICP-matched contacts at Def ID 2151
- `/dh-contacts physicians 2151` — Physician champions at Def ID 2151

## Instructions

When this skill is invoked:

1. Parse the argument to determine:
   - If it's a number → treat as Definitive ID
   - If it's a quoted string → treat as parent system name
   - If prefixed with "icp" → use Recipe 2
   - If prefixed with "physicians" → use Recipe 8
   - Otherwise → use Recipe 1 for single ID, Recipe 10 for parent name

2. Run the appropriate recipe via the enrichment runner:
   ```bash
   source /Users/oliviagao/project/glytec/.venv/bin/activate

   # Recipe 1: Single hospital full extraction
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 1 --def-id {ID} --live

   # Recipe 2: ICP-matched discovery
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 2 --def-id {ID} --live

   # Recipe 8: Physician champions
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 8 --def-id {ID} --live

   # Recipe 10: Every contact at a parent system
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 10 --parent "{NAME}" --live
   ```

3. After the run completes, query the enrichment database to report results:
   ```bash
   sqlite3 /Users/oliviagao/project/glytec/enrichment/data/enrichment.db "
     SELECT COUNT(*) as total_execs FROM executives WHERE run_id = (SELECT MAX(id) FROM runs);
     SELECT COUNT(*) as icp_matched FROM executives WHERE run_id = (SELECT MAX(id) FROM runs) AND icp_matched = 1;
     SELECT position_level, COUNT(*) FROM executives WHERE run_id = (SELECT MAX(id) FROM runs) GROUP BY position_level;
   "
   ```

4. Present a summary:
   - Total executives found
   - ICP-matched contacts (with intent scores)
   - Physicians found
   - RFP contacts found
   - Any errors or retries logged

## Notes

- Default is LIVE mode when invoked via skill (pass `--live`)
- Dry-run by adding "dry-run" to the arguments
- Results stored in `/Users/oliviagao/project/glytec/enrichment/data/enrichment.db`
- Logs in `/Users/oliviagao/project/glytec/enrichment/logs/`
