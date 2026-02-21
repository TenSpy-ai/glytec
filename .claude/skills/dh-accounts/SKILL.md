# /dh-accounts — DH Account-Level Discovery

Batch contact discovery across many facilities, organized by account segment, EHR vendor, or financial distress signals.

## Recipes Covered

- **Recipe 4** — Tiered Discovery (Enterprise/Strategic first, then Commercial)
- **Recipe 5** — EHR-Segmented Discovery (Epic/Cerner/MEDITECH-specific ICP weighting)
- **Recipe 6** — Financial Distress + Quality Penalty (negative margin + HAC penalty targeting)

## Usage

Arguments: scope (enterprise, commercial, all) and optional recipe number.

Examples:
- `/dh-accounts enterprise` — Tiered discovery for ~242 Enterprise systems (Recipe 4)
- `/dh-accounts ehr enterprise` — EHR-segmented discovery for Enterprise (Recipe 5)
- `/dh-accounts distress enterprise` — Financial distress hospitals in Enterprise (Recipe 6)
- `/dh-accounts commercial` — Tiered discovery for Commercial segment

## Instructions

When this skill is invoked:

1. Parse the argument to determine:
   - Scope: "enterprise", "commercial", or "all"
   - Recipe variant: "ehr" → Recipe 5, "distress" → Recipe 6, default → Recipe 4

2. Run the appropriate recipe:
   ```bash
   source /Users/oliviagao/project/glytec/.venv/bin/activate

   # Recipe 4: Tiered discovery
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 4 --scope {SCOPE} --live

   # Recipe 5: EHR-segmented
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 5 --scope {SCOPE} --live

   # Recipe 6: Financial distress
   python /Users/oliviagao/project/glytec/enrichment/runner.py --recipe 6 --scope {SCOPE} --live
   ```

3. Monitor progress — these are long-running batch operations. Report periodic updates:
   ```bash
   sqlite3 /Users/oliviagao/project/glytec/enrichment/data/enrichment.db "
     SELECT r.recipe, r.status, r.facilities_completed, r.facilities_targeted, r.contacts_found
     FROM runs r WHERE r.id = (SELECT MAX(id) FROM runs);
   "
   ```

4. After completion, report summary statistics:
   ```bash
   sqlite3 /Users/oliviagao/project/glytec/enrichment/data/enrichment.db "
     SELECT COUNT(DISTINCT definitive_id) as facilities_processed FROM executives WHERE run_id = (SELECT MAX(id) FROM runs);
     SELECT COUNT(*) as total_contacts FROM executives WHERE run_id = (SELECT MAX(id) FROM runs);
     SELECT COUNT(*) as icp_matched FROM executives WHERE run_id = (SELECT MAX(id) FROM runs) AND icp_matched = 1;
     SELECT icp_category, COUNT(*) FROM executives WHERE run_id = (SELECT MAX(id) FROM runs) AND icp_matched = 1 GROUP BY icp_category;
     SELECT segment, COUNT(DISTINCT definitive_id) FROM executives WHERE run_id = (SELECT MAX(id) FROM runs) GROUP BY segment;
   "
   ```

## Notes

- These are batch operations — Enterprise scope processes ~242 systems (~3,600 facilities)
- Default is LIVE mode when invoked via skill
- Progress tracked in the `runs` table
- Can be resumed if interrupted (use --resume --run-id N)
