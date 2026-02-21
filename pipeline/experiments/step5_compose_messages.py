"""Step 5 — 3-Layer Message Composition: persona, EHR, financial + signal hook."""

from db import get_conn
from step2_score_accounts import TRIGGER_SIGNALS

# ---------------------------------------------------------------------------
# Layer 1: Persona-based messaging frames (mapped from ICP category)
# ---------------------------------------------------------------------------
PERSONA_FRAMES = {
    # category → (frame_name, subject_template, opening_template)
    "Chief Nursing Officer": (
        "safety_workflow",
        "Reducing insulin-related adverse events at {company}",
        "Patient safety is personal for nursing leaders. At {company}, with {beds} beds across your system, even a 1% reduction in hypoglycemia events could mean dozens of patients spared preventable harm each quarter.",
    ),
    "Chief Financial Officer": (
        "roi_los",
        "The hidden P&L impact of unmanaged glycemia at {company}",
        "When we look at {company}'s {beds}-bed footprint, insulin-related complications are likely adding $20K+ per affected patient stay to your cost structure — through extended LOS, readmissions, and ICU transfers.",
    ),
    "Chief Quality Officer": (
        "cms_compliance",
        "CMS glycemic metrics and {company}'s quality trajectory",
        "With CMS increasingly linking glycemic management to star ratings and readmission penalties, {company}'s quality team is in a position to turn compliance pressure into a competitive advantage.",
    ),
    "Chief Executive Officer": (
        "strategic_board",
        "{company}'s glycemic management gap — a board-level risk",
        "As {company} navigates margin pressure and CMS scrutiny, one clinical area continues to fly under the radar: inpatient glycemic management. The financial and quality implications are significant enough to warrant executive attention.",
    ),
    "Chief Operating Officer": (
        "operational_efficiency",
        "Streamlining insulin management across {company}'s {beds} beds",
        "Operational complexity in multi-site health systems creates gaps in standardization. At {company}, insulin management protocols likely vary across your facilities — creating both risk and opportunity.",
    ),
    "Chief Medical Officer": (
        "clinical_outcomes",
        "Clinical evidence: glycemic control impact at scale for {company}",
        "The clinical literature is clear: standardized insulin management reduces hypoglycemia by 50-80% and shortens LOS by 0.5-1.5 days. For a system of {company}'s scale, that translates to thousands of patient-days.",
    ),
    "Director": (
        "department_impact",
        "Glycemic management ROI for {company}'s clinical teams",
        "Department leaders are often the first to see the impact of unmanaged glycemia — longer stays, more nurse interventions, and preventable ICU transfers. At {company}, these patterns likely show up in your metrics.",
    ),
    "default": (
        "general_value",
        "Transforming glycemic management at {company}",
        "Hospitals that standardize insulin management with FDA-cleared technology see measurable improvements in patient safety, length of stay, and CMS quality metrics. For {company}, the opportunity is substantial.",
    ),
}

# ---------------------------------------------------------------------------
# Layer 2: EHR-based lead angles
# ---------------------------------------------------------------------------
EHR_ANGLES = {
    "EPIC": (
        "Epic sites often rely on unvalidated insulin calculators built in-house. "
        "Unlike FDA-cleared dosing software, these tools lack the clinical guardrails "
        "to prevent hypoglycemia — creating liability exposure that most Epic sites "
        "haven't fully assessed."
    ),
    "CERNER": (
        "With Oracle's transition from Cerner to Oracle Health, many insulin management "
        "workflows are being disrupted. This is the ideal window to implement a "
        "vendor-neutral, FDA-cleared glycemic management system that works across "
        "any EHR — protecting your investment regardless of Oracle's roadmap."
    ),
    "ORACLE": (
        "The Oracle Health transition is reshaping clinical workflows across your system. "
        "For insulin management specifically, this creates both risk (workflow disruption) "
        "and opportunity (clean-slate implementation of FDA-cleared dosing technology)."
    ),
    "MEDITECH": (
        "MEDITECH environments present a unique modernization opportunity. "
        "Where Epic/Cerner sites may have cobbled together insulin calculators, "
        "MEDITECH sites can leapfrog directly to FDA-cleared glycemic management — "
        "establishing best-in-class protocols without the technical debt."
    ),
    "default": (
        "Regardless of EHR vendor, most hospitals rely on manual insulin dosing "
        "or unvalidated calculators that lack FDA clearance. The clinical risk "
        "and financial impact are identical across platforms."
    ),
}

# ---------------------------------------------------------------------------
# Layer 3: Financial urgency based on operating margin
# ---------------------------------------------------------------------------
FINANCIAL_FRAMES = {
    "negative": (
        "With operating margins under pressure, every dollar matters. "
        "Glucommander clients report an average $20K savings per insulin-managed "
        "patient stay — driven by a 3.18-day reduction in length of stay and "
        "fewer ICU transfers. For your system, that could mean millions in "
        "recoverable costs annually."
    ),
    "low": (
        "At current margins, strategic investments need clear ROI. "
        "Glucommander delivers measurable savings: $20K per patient stay "
        "through LOS reduction (3.18 days average), plus reduced readmission "
        "penalties and ICU utilization."
    ),
    "moderate": (
        "Strong operational performance gives you the capital to invest in "
        "clinical quality. Glucommander drives both: CMS star rating improvement "
        "through glycemic outcomes, plus competitive differentiation in markets "
        "where patient safety is increasingly a differentiator."
    ),
    "healthy": (
        "From a position of financial strength, the case for Glucommander is "
        "about competitive leadership and quality differentiation. CMS is "
        "tightening glycemic metrics — early adopters will have the data "
        "and processes in place when these become mandatory reporting measures."
    ),
}


def _get_persona_frame(title, icp_job_level):
    """Select persona messaging frame based on title and job level."""
    title_upper = (title or "").upper()
    for key in PERSONA_FRAMES:
        if key != "default" and key.upper() in title_upper:
            return PERSONA_FRAMES[key]
    # Fall back to job level
    if icp_job_level == "Director":
        return PERSONA_FRAMES["Director"]
    return PERSONA_FRAMES["default"]


def _get_ehr_angle(ehr_vendor):
    """Select EHR-based messaging angle."""
    if not ehr_vendor:
        return EHR_ANGLES["default"]
    ehr_upper = ehr_vendor.upper()
    for key in EHR_ANGLES:
        if key != "default" and key in ehr_upper:
            return EHR_ANGLES[key]
    return EHR_ANGLES["default"]


def _get_financial_frame(margin):
    """Select financial urgency frame based on operating margin."""
    if margin is None:
        return FINANCIAL_FRAMES["low"]
    if margin < 0:
        return FINANCIAL_FRAMES["negative"]
    if margin <= 0.05:
        return FINANCIAL_FRAMES["low"]
    if margin <= 0.10:
        return FINANCIAL_FRAMES["moderate"]
    return FINANCIAL_FRAMES["healthy"]


def _get_signal_hook(account_name):
    """Get trigger signal for personalized opening."""
    signal = TRIGGER_SIGNALS.get(account_name)
    if signal:
        return f"I noticed {signal.lower()}. This is exactly the kind of moment where glycemic management technology can make the biggest impact."
    return None


def compose_message(contact, account, facility):
    """Compose a 3-layer message for a single contact."""
    title = contact["title"] or ""
    company = contact["company"] or account["system_name"]
    beds = account["total_beds"] or 0
    ehr = facility["ehr_inpatient"] if facility else None
    margin = facility["net_operating_profit_margin"] if facility else None

    # Layer 1: Persona
    frame_name, subject_tpl, opening_tpl = _get_persona_frame(title, contact["icp_job_level"])
    subject = subject_tpl.format(company=company, beds=beds)
    opening = opening_tpl.format(company=company, beds=beds)

    # Layer 2: EHR angle
    ehr_paragraph = _get_ehr_angle(ehr)

    # Layer 3: Financial
    financial_paragraph = _get_financial_frame(margin)

    # Signal hook
    signal_hook = _get_signal_hook(contact["account_name"])
    signal_section = f"\n\n{signal_hook}" if signal_hook else ""

    # Compose full body
    body = f"""{contact['first_name']},
{signal_section}
{opening}

{ehr_paragraph}

{financial_paragraph}

Would it make sense to schedule 15 minutes to walk through how this applies specifically to {company}?

Best,
Glytec AI SDR"""

    return {
        "subject": subject,
        "body": body,
        "layer1_persona": frame_name,
        "layer2_ehr": ehr.split(" ")[0].upper() if ehr else "UNKNOWN",
        "layer3_financial": "negative" if margin and margin < 0 else "low" if margin and margin <= 0.05 else "moderate" if margin and margin <= 0.10 else "healthy",
        "signal_hook": signal_hook,
    }


def run():
    """Execute step 5."""
    print("\n=== Step 5: Compose Messages ===")
    conn = get_conn()
    try:
        # Get clean, unsuppressed, ICP-matched contacts at Priority/Active accounts
        contacts = conn.execute(
            """SELECT c.*, a.system_name as acct_name, a.total_beds, a.tier
               FROM contacts c
               JOIN accounts a ON c.account_name = a.system_name
               WHERE c.golden_record = 1
               AND c.suppressed = 0
               AND c.icp_matched = 1
               AND a.tier IN ('Priority', 'Active')
               ORDER BY a.score DESC"""
        ).fetchall()

        if not contacts:
            print("[step5] No eligible contacts found — check steps 3 and 4")
            return

        print(f"[step5] Composing messages for {len(contacts)} contacts...")
        composed = 0

        for c in contacts:
            # Get primary facility for EHR/margin data
            facility = conn.execute(
                """SELECT ehr_inpatient, net_operating_profit_margin
                   FROM facilities
                   WHERE highest_level_parent = ?
                   ORDER BY staffed_beds DESC LIMIT 1""",
                (c["account_name"],),
            ).fetchone()

            # Get account data
            account = conn.execute(
                "SELECT * FROM accounts WHERE system_name = ?",
                (c["account_name"],),
            ).fetchone()

            if not account:
                continue

            msg = compose_message(c, account, facility)

            conn.execute(
                """INSERT INTO messages
                   (contact_id, subject, body, layer1_persona, layer2_ehr,
                    layer3_financial, signal_hook)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    c["id"],
                    msg["subject"],
                    msg["body"],
                    msg["layer1_persona"],
                    msg["layer2_ehr"],
                    msg["layer3_financial"],
                    msg["signal_hook"],
                ),
            )
            composed += 1

        conn.commit()

        # Print sample messages
        print(f"\n[step5] Composed {composed} messages. Sample:")
        samples = conn.execute(
            """SELECT m.subject, m.layer1_persona, m.layer2_ehr, m.layer3_financial,
                      c.first_name, c.last_name, c.title, c.account_name
               FROM messages m JOIN contacts c ON m.contact_id = c.id
               LIMIT 3"""
        ).fetchall()
        for s in samples:
            print(f"\n  To: {s['first_name']} {s['last_name']} ({s['title']}) @ {s['account_name']}")
            print(f"  Subject: {s['subject']}")
            print(f"  Layers: persona={s['layer1_persona']}, ehr={s['layer2_ehr']}, financial={s['layer3_financial']}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
