# recipes/ — DH Discovery Recipes

10 operational recipes for Definitive Healthcare contact discovery and account enrichment. Each targets a different sales angle or data strategy.

## Status: All Operational

These are production tools, not experiments. Each recipe is tuned for Glytec's ICP and sales motion.

## Recipes

| Recipe | Name | What it does | Concurrency |
|--------|------|-------------|-------------|
| `recipe01` | Full Extract | Exhaustive contact pull for a single hospital: executives, physicians, RFP contacts, news-derived leadership changes | Sequential |
| `recipe02` | ICP Match | Targeted discovery using 11 ICP search batches (C-Suite, Pharmacy, Nursing, Quality, etc.), then ICP scoring | Sequential |
| `recipe03` | Network Map | Scans all facilities in target parent systems for recently updated executives (leadership change signals) | Concurrent |
| `recipe04` | Tiered Discovery | Prioritizes non-client parent systems by opportunity value, groups facilities by system, runs ICP discovery on each | Concurrent |
| `recipe05` | EHR-Segmented | Classifies hospitals by EHR vendor (Epic/Cerner/MEDITECH), runs vendor-specific + common search batches | Sequential |
| `recipe06` | Financial Distress | Pre-filters for negative-margin hospitals with ICU beds, enriches with CMS quality penalties, then ICP discovery | Concurrent |
| `recipe07` | Geo Territory | Filters facilities by assigned rep (from Supplemental Data CSV), sorts by hospital type/size, runs ICP discovery | Sequential |
| `recipe08` | Physician Champion | Finds endocrinologists, hospitalists, internal medicine physicians, and medical directors at SAC hospitals with >=10 ICU beds | Concurrent |
| `recipe09` | Account Bundle | Pulls quality metrics, financial metrics, GPO/ACO memberships, and news/trigger signals for each hospital | Concurrent |
| `recipe10` | Every Contact | Exhaustive extraction for all facilities in a parent system. Fills CSV gaps by searching DH API for unlisted facilities | Sequential |

## Recipe Selection Guide

| Goal | Use |
|------|-----|
| Deep-dive on one hospital | `recipe01` (full extract) or `recipe02` (ICP-focused) |
| Prioritized bulk discovery | `recipe04` (tiered by opp value) or `recipe07` (by rep territory) |
| Targeted by pain point | `recipe06` (financial distress) or `recipe05` (EHR vendor) |
| Find physician champions | `recipe08` (endocrinology, hospitalists, medical directors) |
| Account intelligence | `recipe09` (quality + financial + trigger signals) |
| Complete coverage | `recipe10` (every contact at a parent system) |
| Leadership change signals | `recipe03` (network map for recent exec updates) |

## Internal Dependencies

```
recipe01 (standalone — base recipe)
recipe02 -> recipe01 (_store_executives), icp_matcher
recipe03 -> recipe01 (storage functions)
recipe04 -> recipe02, recipe03
recipe05 -> recipe01 (_store_executives), icp_matcher
recipe06 -> recipe02
recipe07 -> recipe02
recipe08 -> recipe01 (_store_physicians)
recipe09 -> dh_client (direct)
recipe10 -> recipe01, recipe03
```

## Known Issues

- Recipes 01, 09, 10 use a hardcoded news date filter (`> 2025-06-01`) — should be parameterized to a rolling window
- Recipe 03 uses a hardcoded leadership change threshold (`> 2025-12-01`) — should also be a rolling window
