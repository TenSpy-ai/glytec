"""
GTM Hello World — Autopilot Campaign Orchestrator

7-step pipeline: resolve template → select contacts → preflight → create → enroll → activate → record.
Reuses existing ops scripts — no new API logic.

Usage:
    from autopilot import Autopilot, AutopilotConfig
    from query_builder import ContactQuery

    config = AutopilotConfig(
        template='01-new-in-role',
        query=ContactQuery().tier('Active').top(10),
    )
    result = Autopilot().run(config)
"""

import json
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config import CAMPAIGNS_DIR, DB_PATH
from db import get_conn, log_api_call
from mcp import InstantlyMCP, MCPError
from ops.launch_campaign import (
    DEFAULT_SCHEDULE,
    DEFAULT_SEQUENCES,
    build_lead_payload,
    get_sender_accounts,
    launch,
)
from query_builder import ContactQuery


# ── Schedule presets ─────────────────────────────────────────────────────────

SCHEDULE_PRESETS = {
    "weekday": {
        "schedules": [{
            "name": "Weekdays",
            "timing": {"from": "08:00", "to": "17:00"},
            "days": {"1": True, "2": True, "3": True, "4": True, "5": True},
            "timezone": "America/New_York",
        }]
    },
    "aggressive": {
        "schedules": [{
            "name": "Extended",
            "timing": {"from": "07:00", "to": "19:00"},
            "days": {"1": True, "2": True, "3": True, "4": True, "5": True, "6": True},
            "timezone": "America/New_York",
        }]
    },
    "conservative": {
        "schedules": [{
            "name": "Mid-week",
            "timing": {"from": "09:00", "to": "16:00"},
            "days": {"2": True, "3": True, "4": True},
            "timezone": "America/New_York",
        }]
    },
}


# ── Template metadata ────────────────────────────────────────────────────────

TEMPLATE_MAP = {
    "01-new-in-role":       "01-new-in-role.md",
    "new-in-role":          "01-new-in-role.md",
    "02-priority-account":  "02-priority-account.md",
    "priority-account":     "02-priority-account.md",
    "03-ehr-epic":          "03-ehr-epic.md",
    "ehr-epic":             "03-ehr-epic.md",
    "epic":                 "03-ehr-epic.md",
    "04-ehr-cerner":        "04-ehr-cerner.md",
    "ehr-cerner":           "04-ehr-cerner.md",
    "cerner":               "04-ehr-cerner.md",
    "05-ehr-meditech":      "05-ehr-meditech.md",
    "ehr-meditech":         "05-ehr-meditech.md",
    "meditech":             "05-ehr-meditech.md",
    "06-financial-recovery": "06-financial-recovery.md",
    "financial-recovery":   "06-financial-recovery.md",
    "07-territory-outreach": "07-territory-outreach.md",
    "territory-outreach":   "07-territory-outreach.md",
    "territory":            "07-territory-outreach.md",
    "08-physician-champion": "08-physician-champion.md",
    "physician-champion":   "08-physician-champion.md",
    "physician":            "08-physician-champion.md",
    "09-account-deep-dive": "09-account-deep-dive.md",
    "account-deep-dive":    "09-account-deep-dive.md",
    "deep-dive":            "09-account-deep-dive.md",
}


@dataclass
class AutopilotConfig:
    """Everything needed to launch a campaign."""
    template: str                       # "01-new-in-role" or any alias
    query: ContactQuery                 # Lead selection criteria
    schedule_type: str = "weekday"      # weekday / aggressive / conservative / custom
    custom_schedule: dict | None = None
    daily_limit: int = 30
    email_gap: int = 10
    batch_size: int = 1000
    auto_activate: bool = False
    live: bool = False
    campaign_name: str | None = None    # Auto-generated if None


@dataclass
class TemplateInfo:
    """Parsed campaign template."""
    filename: str
    name: str           # Campaign Name from header
    recipe: str         # e.g. "R3"
    sequences: list     # Instantly-format sequences array
    settings: dict      # daily_limit, email_gap, etc.


def resolve_template(template_key: str) -> TemplateInfo:
    """Load and parse a campaign markdown template.

    Returns TemplateInfo with sequences extracted from the Email Sequence section.
    """
    filename = TEMPLATE_MAP.get(template_key.lower().strip())
    if not filename:
        # Try direct filename
        candidates = list(CAMPAIGNS_DIR.glob(f"*{template_key}*"))
        if candidates:
            filename = candidates[0].name
        else:
            raise ValueError(f"Unknown template: {template_key}. "
                             f"Available: {', '.join(sorted(set(TEMPLATE_MAP.values())))}")

    path = CAMPAIGNS_DIR / filename
    if not path.exists():
        raise ValueError(f"Template file not found: {path}")

    text = path.read_text()

    # Extract campaign name
    name_match = re.search(r'\*\*Campaign Name:\*\*\s*`([^`]+)`', text)
    campaign_name = name_match.group(1) if name_match else filename.replace(".md", "")

    # Extract recipe
    recipe_match = re.search(r'\*\*Recipe:\*\*\s*(R\d+)', text)
    recipe = recipe_match.group(1) if recipe_match else ""

    # Extract email sequences
    sequences = _parse_sequences(text)

    # Extract settings
    settings = _parse_settings(text)

    return TemplateInfo(
        filename=filename,
        name=campaign_name,
        recipe=recipe,
        sequences=sequences,
        settings=settings,
    )


def _parse_sequences(text: str) -> list:
    """Parse the Email Sequence section into Instantly sequences format.

    Extracts step delays and variant subjects/bodies from the markdown.
    Falls back to DEFAULT_SEQUENCES if parsing fails.
    """
    # Find the Email Sequence section
    seq_match = re.search(r'## Email Sequence.*?\n(.*?)(?=\n---|\n## )', text, re.DOTALL)
    if not seq_match:
        return DEFAULT_SEQUENCES

    seq_text = seq_match.group(1)

    # Split into steps
    step_blocks = re.split(r'### Step \d+', seq_text)
    if len(step_blocks) < 2:  # first split is before Step 1
        return DEFAULT_SEQUENCES

    steps = []
    for i, block in enumerate(step_blocks[1:]):  # skip text before first step
        # Extract day number from header
        day_match = re.search(r'Day\s+(\d+)', block)
        delay = int(day_match.group(1)) if day_match else (i * 3)

        # Extract variants
        variants = []
        variant_blocks = re.split(r'\*\*Variant [A-Z]:\*\*', block)

        if len(variant_blocks) > 1:
            # Multiple variants
            for vblock in variant_blocks[1:]:
                variant = _extract_variant(vblock)
                if variant:
                    variants.append(variant)
        else:
            # Single variant (no Variant A/B headers)
            variant = _extract_variant(block)
            if variant:
                variants.append(variant)

        if not variants:
            variants = [{"subject": "{{subject_line}}", "body": "{{email_body}}"}]

        steps.append({
            "type": "email",
            "delay": delay if i > 0 else 0,
            "variants": variants,
        })

    if not steps:
        return DEFAULT_SEQUENCES

    return [{"steps": steps}]


def _extract_variant(block: str) -> dict | None:
    """Extract subject and body from a variant block."""
    subject_match = re.search(r'-\s*\*\*Subject:\*\*\s*(.+)', block)
    if not subject_match:
        return None

    subject = subject_match.group(1).strip()

    # Body is everything after "- **Body:**" until the next variant or section
    body_match = re.search(
        r'-\s*\*\*Body:\*\*\s*\n(.*?)(?=\n\*\*Variant|\n###|\n---|\Z)',
        block, re.DOTALL
    )
    body = ""
    if body_match:
        # Clean up body: strip leading whitespace from each line
        lines = body_match.group(1).split("\n")
        body = "\n".join(line.strip() for line in lines).strip()

    return {"subject": subject, "body": body}


def _parse_settings(text: str) -> dict:
    """Extract campaign settings from the settings table."""
    settings = {}
    settings_match = re.search(r'## Campaign Settings.*?\n(.*?)(?=\n---|\n## |\Z)', text, re.DOTALL)
    if not settings_match:
        return settings

    for match in re.finditer(r'\|\s*(\w+)\s*\|\s*(.+?)\s*\|', settings_match.group(1)):
        key = match.group(1).strip()
        val = match.group(2).strip()
        if key in ("daily_limit", "email_gap"):
            # Strip units like "min"
            num_match = re.search(r'(\d+)', val)
            if num_match:
                settings[key] = int(num_match.group(1))
        elif key in ("stop_on_reply", "stop_for_company", "open_tracking",
                      "link_tracking", "match_lead_esp", "auto_variant_select"):
            settings[key] = val.lower() == "true"

    return settings


def _extract_metadata(text: str) -> dict:
    """Extract header metadata: skill, target_segment, target_persona from markdown header."""
    meta = {}
    for key, field in [
        (r'\*\*Skill(?:s)?:\*\*\s*(.+)', "skill"),
        (r'\*\*Target Segment:\*\*\s*(.+)', "target_segment"),
        (r'\*\*Target Persona:\*\*\s*(.+)', "target_persona"),
    ]:
        m = re.search(key, text)
        if m:
            val = m.group(1).strip()
            if field == "skill":
                # Strip trailing description after em-dash, then backticks
                val = re.split(r'\s*[—–]\s*', val, maxsplit=1)[0].strip()
                val = val.strip("`")
            meta[field] = val
    return meta


def _extract_title(text: str) -> str:
    """Extract the campaign title from the first markdown heading."""
    m = re.search(r'^#\s+Campaign:\s*(.+)', text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _extract_description(text: str, meta: dict) -> str:
    """Extract from ## Overview section, or fall back to target_segment."""
    # Try Overview section first
    m = re.search(r'## Overview\s*\n(.*?)(?=\n---|\n## )', text, re.DOTALL)
    if m:
        return m.group(1).strip().split("\n\n")[0].strip().replace("**", "")

    # Fall back to target_segment from header metadata
    return meta.get("target_segment", "").replace("**", "")


def _extract_targeting(text: str) -> str:
    """Extract ## Targeting Criteria section text (including code blocks)."""
    m = re.search(r'## Targeting Criteria\s*\n(.*?)(?=\n---)', text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_custom_vars_json(text: str) -> dict:
    """Extract JSON from ## Custom Variables code block."""
    m = re.search(r'## Custom Variables.*?```json\s*\n(.*?)```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    return {}


def _extract_personalization_vars(sequences: list) -> list:
    """Find all {{var}} patterns in subjects + bodies. Return sorted unique list."""
    found = set()
    for seq in sequences:
        for step in seq.get("steps", []):
            for variant in step.get("variants", []):
                for field in ("subject", "body"):
                    for m in re.finditer(r'\{\{(\w+)\}\}', variant.get(field, "")):
                        found.add(m.group(1))
    return sorted(found)


def _extract_step_titles(text: str) -> dict:
    """Extract step titles from ### Step N — Title (Day X) headers. Returns {step_num: title}."""
    titles = {}
    for m in re.finditer(r'### Step (\d+)\s*[—–-]\s*(.+?)(?:\(|$)', text, re.MULTILINE):
        titles[int(m.group(1))] = m.group(2).strip().rstrip(" —–-")
    return titles


_TEMPLATE_EXAMPLES = {
    "01-new-in-role": [
        "Launch new-in-role for top 20 CNOs at Epic hospitals",
        "Run new-in-role campaign for all Active tier accounts --live",
        "/instantly-autopilot new-in-role top 5 verified CNOs",
    ],
    "02-priority-account": [
        "Launch priority-account for Enterprise tier top 15 CFOs",
        "Run priority-account for all Active accounts with 1000+ beds",
        "/instantly-autopilot priority-account top 10 CMOs --live",
    ],
    "03-ehr-epic": [
        "Launch ehr-epic for Active tier Epic hospitals",
        "Run ehr-epic for CNOs at Epic systems with 500+ beds",
        "/instantly-autopilot ehr-epic top 20 pharmacy directors",
    ],
    "04-ehr-cerner": [
        "Launch ehr-cerner for Cerner hospitals with 500+ beds",
        "Run ehr-cerner for CFOs at Oracle Health transition systems",
        "/instantly-autopilot ehr-cerner top 15 COOs --live",
    ],
    "05-ehr-meditech": [
        "Launch ehr-meditech for MEDITECH hospitals Active tier",
        "Run ehr-meditech for CNOs at MEDITECH systems",
        "/instantly-autopilot ehr-meditech top 10 pharmacy directors",
    ],
    "06-financial-recovery": [
        "Launch financial-recovery for negative-margin systems",
        "Run financial-recovery for CFOs at systems with CMS penalties",
        "/instantly-autopilot financial-recovery top 20 CEOs --live",
    ],
    "07-territory-outreach": [
        "Launch territory for Clayton's territory CNOs",
        "Run territory-outreach for all contacts in Clayton's book --live",
        "/instantly-autopilot territory top 15 CFOs",
    ],
    "08-physician-champion": [
        "Launch physician-champion for endocrinologists at HCA",
        "Run physician for top 10 medical directors at Epic hospitals",
        "/instantly-autopilot physician-champion hospitalists Active tier",
    ],
    "09-account-deep-dive": [
        "/instantly-autopilot account-deep-dive CommonSpirit Health",
        "Launch deep-dive campaign for Tenet Healthcare --live",
        "Run account-deep-dive for HCA Healthcare all ICP contacts",
    ],
}


def _generate_examples(template_id: str, target_persona: str) -> list:
    """Return curated examples for a template, or generate fallback."""
    if template_id in _TEMPLATE_EXAMPLES:
        return _TEMPLATE_EXAMPLES[template_id]
    # Fallback
    short_id = template_id.split("-", 1)[1] if "-" in template_id else template_id
    return [
        f"Launch {short_id} for top 20 contacts",
        f"Run {short_id} campaign for Active tier --live",
        f"/instantly-autopilot {short_id} top 10 contacts",
    ]


def list_all_templates() -> list:
    """Parse all 9 campaign MDs and return structured template data for the /templates API."""
    seen = set()
    templates = []

    for key, filename in sorted(TEMPLATE_MAP.items()):
        if filename in seen:
            continue
        seen.add(filename)

        try:
            info = resolve_template(key)
        except (ValueError, FileNotFoundError):
            continue

        path = CAMPAIGNS_DIR / filename
        text = path.read_text()

        meta = _extract_metadata(text)
        title = _extract_title(text)
        description = _extract_description(text, meta)
        targeting = _extract_targeting(text)
        custom_vars = _extract_custom_vars_json(text)
        step_titles = _extract_step_titles(text)

        # Build flattened steps with titles and variants
        steps_flat = []
        if info.sequences:
            for seq in info.sequences:
                for i, step in enumerate(seq.get("steps", [])):
                    step_num = i + 1
                    steps_flat.append({
                        "step": step_num,
                        "title": step_titles.get(step_num, f"Step {step_num}"),
                        "day": step.get("delay", 0),
                        "variants": [
                            {"label": chr(65 + vi), "subject": v.get("subject", ""),
                             "body": v.get("body", "")}
                            for vi, v in enumerate(step.get("variants", []))
                        ],
                    })

        pvars = _extract_personalization_vars(info.sequences)
        template_id = filename.replace(".md", "")
        persona = meta.get("target_persona", "")
        examples = _generate_examples(template_id, persona)

        templates.append({
            "id": template_id,
            "filename": filename,
            "name": info.name,
            "title": title,
            "recipe": info.recipe,
            "skill": meta.get("skill", ""),
            "target_segment": meta.get("target_segment", ""),
            "target_persona": persona,
            "description": description,
            "targeting": targeting,
            "settings": info.settings,
            "steps": steps_flat,
            "personalization_vars": pvars,
            "custom_variables": custom_vars,
            "examples": examples,
        })

    return templates


class Autopilot:
    """7-step campaign orchestrator with per-step logging."""

    def _serialize_config(self, config: AutopilotConfig) -> str:
        """Serialize config to JSON for storage."""
        return json.dumps({
            "template": config.template,
            "query_desc": config.query.describe(),
            "schedule_type": config.schedule_type,
            "daily_limit": config.daily_limit,
            "email_gap": config.email_gap,
            "batch_size": config.batch_size,
            "auto_activate": config.auto_activate,
            "live": config.live,
            "campaign_name": config.campaign_name,
        })

    def _log_step(self, conn: sqlite3.Connection, run_id: int, step_number: int,
                  step_name: str, status: str, detail: str = None,
                  data_json: str = None, duration_ms: int = None) -> int:
        """Insert a step record into autopilot_steps. Returns step row ID."""
        completed = datetime.now().isoformat() if status in ("completed", "failed", "skipped") else None
        cursor = conn.execute(
            """INSERT INTO autopilot_steps
               (run_id, step_number, step_name, status, detail, data_json,
                duration_ms, started_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)""",
            (run_id, step_number, step_name, status,
             detail[:1000] if detail else None,
             data_json[:5000] if data_json else None,
             duration_ms, completed),
        )
        conn.commit()
        return cursor.lastrowid

    def run(self, config: AutopilotConfig) -> dict:
        """Execute the full pipeline. Returns result dict with status at each step."""
        conn = get_conn()
        run_start = time.monotonic()
        result = {
            "steps_completed": [],
            "status": "pending",
            "mode": "live" if config.live else "dry_run",
        }
        run_id = None

        try:
            # Record run start
            run_id = self._record_start(conn, config)
            result["run_id"] = run_id

            # ── Step 1: Resolve template ─────────────────────────
            t0 = time.monotonic()
            print("Step 1: Resolving template...")
            template = resolve_template(config.template)
            result["template"] = template.name
            result["recipe"] = template.recipe
            result["steps_completed"].append("resolve_template")
            step_detail = f"Template: {template.filename}, Campaign: {template.name}, Recipe: {template.recipe}"
            step_data = json.dumps({"filename": template.filename, "name": template.name,
                                    "recipe": template.recipe, "step_count": len(template.sequences[0]["steps"]) if template.sequences else 0})
            self._log_step(conn, run_id, 1, "resolve_template", "completed",
                           step_detail, step_data, int((time.monotonic() - t0) * 1000))
            print(f"  Template: {template.filename}")
            print(f"  Campaign: {template.name}")
            print(f"  Recipe: {template.recipe}")
            print(f"  Steps: {len(template.sequences[0]['steps']) if template.sequences else 0}")

            # ── Step 2: Select contacts ──────────────────────────
            t0 = time.monotonic()
            print("\nStep 2: Selecting contacts...")
            contacts = config.query.execute(conn)
            result["contact_count"] = len(contacts)
            result["query_desc"] = config.query.describe()
            result["steps_completed"].append("select_contacts")
            contact_summary = [{"id": c["id"], "name": f"{c['first_name']} {c['last_name']}",
                                "title": c["title"], "account": c["account_name"],
                                "email": c["email"]} for c in contacts[:50]]
            self._log_step(conn, run_id, 2, "select_contacts", "completed",
                           f"Query: {config.query.describe()} | Found: {len(contacts)} contacts",
                           json.dumps({"total": len(contacts), "contacts": contact_summary}),
                           int((time.monotonic() - t0) * 1000))
            print(f"  Query: {config.query.describe()}")
            print(f"  Found: {len(contacts)} contacts")
            for c in contacts[:5]:
                print(f"    {c['first_name']} {c['last_name']} ({c['title']}) @ {c['account_name']}")
            if len(contacts) > 5:
                print(f"    ... and {len(contacts) - 5} more")

            # ── Step 3: Preflight check ──────────────────────────
            t0 = time.monotonic()
            print("\nStep 3: Preflight checks...")
            senders = get_sender_accounts(conn)
            issues = []
            if not contacts:
                issues.append("No contacts matched the query")
            if not senders:
                issues.append("No active sender accounts in local DB")

            if issues:
                for issue in issues:
                    print(f"  FAIL: {issue}")
                self._log_step(conn, run_id, 3, "preflight", "failed",
                               "; ".join(issues), None, int((time.monotonic() - t0) * 1000))
                result["status"] = "failed"
                result["error"] = "; ".join(issues)
                self._record_finish(conn, run_id, result, run_start)
                return result

            result["sender_count"] = len(senders)
            result["steps_completed"].append("preflight")
            self._log_step(conn, run_id, 3, "preflight", "completed",
                           f"Contacts: {len(contacts)} OK, Senders: {len(senders)} OK",
                           json.dumps({"contacts": len(contacts), "senders": len(senders), "sender_emails": senders}),
                           int((time.monotonic() - t0) * 1000))
            print(f"  Contacts: {len(contacts)} OK")
            print(f"  Senders: {len(senders)} OK")

            # ── Step 4: Create campaign ──────────────────────────
            t0 = time.monotonic()
            campaign_name = config.campaign_name or template.name
            result["campaign_name"] = campaign_name

            schedule = config.custom_schedule or SCHEDULE_PRESETS.get(
                config.schedule_type, DEFAULT_SCHEDULE
            )

            mcp = InstantlyMCP(dry_run=not config.live)

            print(f"\nStep 4-6: Launching campaign '{campaign_name}'...")
            print(f"  Schedule: {config.schedule_type}")
            print(f"  Mode: {'LIVE' if config.live else 'DRY RUN'}")
            print(f"  Auto-activate: {config.auto_activate}")

            launch_result = launch(
                mcp=mcp,
                conn=conn,
                name=campaign_name,
                contacts=contacts,
                senders=senders,
                activate=config.auto_activate,
                schedule=schedule,
                sequences=template.sequences,
            )
            launch_ms = int((time.monotonic() - t0) * 1000)

            result["campaign_id"] = launch_result.get("campaign_id", "")
            result["enrolled"] = launch_result.get("enrolled", 0)
            result["campaign_status"] = launch_result.get("status", "draft")
            result["steps_completed"].extend(launch_result.get("steps_completed", []))

            if launch_result.get("activation_error"):
                result["activation_error"] = launch_result["activation_error"]

            # Log sub-steps from launch
            launch_steps = launch_result.get("steps_completed", [])
            self._log_step(conn, run_id, 4, "create_campaign", "completed",
                           f"Campaign: {campaign_name}, ID: {launch_result.get('campaign_id', '—')}",
                           json.dumps({"campaign_name": campaign_name, "campaign_id": launch_result.get("campaign_id", ""),
                                       "schedule_type": config.schedule_type}),
                           launch_ms // max(len(launch_steps), 1))
            self._log_step(conn, run_id, 5, "enroll_contacts", "completed",
                           f"Enrolled: {launch_result.get('enrolled', 0)} contacts in campaign {campaign_name}",
                           json.dumps({"enrolled": launch_result.get("enrolled", 0), "batch_size": config.batch_size}),
                           launch_ms // max(len(launch_steps), 1))

            activate_status = "completed" if config.auto_activate and "activate" in launch_steps else "skipped"
            activate_detail = f"Campaign status: {launch_result.get('status', 'draft')}"
            if launch_result.get("activation_error"):
                activate_status = "failed"
                activate_detail = launch_result["activation_error"]
            self._log_step(conn, run_id, 6, "activate", activate_status,
                           activate_detail, None, 0)

            # ── Step 7: Record run ───────────────────────────────
            t0 = time.monotonic()
            print("\nStep 7: Recording run...")
            result["status"] = "completed"
            result["steps_completed"].append("record_run")
            self._record_finish(conn, run_id, result, run_start)
            self._log_step(conn, run_id, 7, "record_run", "completed",
                           "Run recorded in autopilot_runs + autopilot_steps",
                           None, int((time.monotonic() - t0) * 1000))
            print("  Run recorded in autopilot_runs + autopilot_steps tables")

            log_api_call(conn, "local", "autopilot.py", "RUN",
                         {"template": config.template, "mode": result["mode"],
                          "contacts": len(contacts)},
                         None, f"Autopilot: {campaign_name} ({result['mode']})")

            return result

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            if run_id:
                self._record_finish(conn, run_id, result, run_start)
            raise

        finally:
            conn.close()

    def _record_start(self, conn: sqlite3.Connection, config: AutopilotConfig) -> int:
        """Insert initial autopilot_runs row. Returns run ID."""
        cursor = conn.execute(
            """INSERT INTO autopilot_runs
               (template, query_desc, schedule_type, mode, config_json, status)
               VALUES (?, ?, ?, ?, ?, 'running')""",
            (config.template, config.query.describe(),
             config.schedule_type, "live" if config.live else "dry_run",
             self._serialize_config(config)),
        )
        conn.commit()
        return cursor.lastrowid

    def _record_finish(self, conn: sqlite3.Connection, run_id: int, result: dict,
                       run_start: float = None) -> None:
        """Update autopilot_runs with final state."""
        duration = int((time.monotonic() - run_start) * 1000) if run_start else None
        conn.execute(
            """UPDATE autopilot_runs
               SET campaign_name = ?,
                   instantly_campaign_id = ?,
                   contact_count = ?,
                   sender_count = ?,
                   status = ?,
                   error_message = ?,
                   steps_completed = ?,
                   duration_ms = ?,
                   completed_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (result.get("campaign_name"),
             result.get("campaign_id"),
             result.get("contact_count", 0),
             result.get("sender_count"),
             result.get("status", "failed"),
             result.get("error"),
             json.dumps(result.get("steps_completed", [])),
             duration,
             run_id),
        )
        conn.commit()


# ── Monitor function ─────────────────────────────────────────────────────────

def run_monitor(live: bool = False) -> dict:
    """Run the daily monitoring cycle: metrics → replies → clay push → kill-switch.

    Returns summary dict.
    """
    from process_replies import classify_sentiment, scan_for_new_replies, store_reply
    from pull_metrics import check_kill_switches, pull_campaign_analytics, pull_daily_analytics
    from push_to_clay import (
        build_clay_payload,
        get_unpushed_positive_replies,
        log_push,
        push_to_clay,
    )

    conn = get_conn()
    summary = {"mode": "live" if live else "dry_run", "steps": []}

    try:
        mode = "LIVE" if live else "DRY RUN"

        # Step 1: Pull metrics
        print(f"\n{'='*60}")
        print(f"  GTM Monitor — Full Cycle ({mode})")
        print(f"{'='*60}")

        print("\n--- Step 1: Pull Metrics ---")
        metrics = pull_campaign_analytics(conn, live)
        pull_daily_analytics(conn, live)
        summary["metrics_count"] = len(metrics)
        summary["steps"].append("pull_metrics")
        print(f"  Processed {len(metrics)} campaigns")

        # Step 2: Process replies
        print("\n--- Step 2: Process Replies ---")
        replies = scan_for_new_replies(conn, live)
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "ooo": 0}
        for reply in replies:
            sentiment, confidence, classified_by = classify_sentiment(reply)
            store_reply(conn, reply, sentiment, confidence, classified_by)
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            print(f"  [{sentiment}] ({confidence:.2f}) {reply['contact_email']}")
        summary["replies_processed"] = len(replies)
        summary["sentiment"] = sentiment_counts
        summary["steps"].append("process_replies")
        if not replies:
            print("  No new replies to process")

        # Step 3: Push to Clay
        print("\n--- Step 3: Push Positive Replies to Clay ---")
        unpushed = get_unpushed_positive_replies(conn)
        pushed = 0
        for reply in unpushed:
            payload = build_clay_payload(reply)
            code, body = push_to_clay(payload, live)
            log_push(conn, reply, payload, code, body)
            if code == 200:
                pushed += 1
            print(f"  {'OK' if code == 200 else 'FAIL'}: "
                  f"{reply['first_name']} {reply['last_name']} @ {reply['account_name']}")
        summary["clay_pushed"] = pushed
        summary["clay_total"] = len(unpushed)
        summary["steps"].append("push_to_clay")
        if not unpushed:
            print("  No unpushed positive replies")

        # Step 4: Kill-switch check
        print("\n--- Step 4: Kill-Switch Check ---")
        warnings = check_kill_switches(conn)
        summary["kill_switch_warnings"] = warnings
        summary["steps"].append("kill_switch_check")

        # Summary
        print(f"\n{'='*60}")
        print(f"  Monitor Complete")
        print(f"{'='*60}")
        print(f"  Campaigns monitored: {len(metrics)}")
        print(f"  Replies processed:   {len(replies)}")
        print(f"  Clay pushes:         {pushed}/{len(unpushed)}")
        print(f"  Kill-switch alerts:  {len(warnings)}")
        if warnings:
            for w in warnings:
                print(f"    {w}")

        log_api_call(conn, "local", "autopilot.py:monitor", "RUN",
                     {"mode": mode}, None,
                     f"Monitor: {len(metrics)} campaigns, {len(replies)} replies")

        return summary

    finally:
        conn.close()
