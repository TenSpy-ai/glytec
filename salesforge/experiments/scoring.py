"""6-factor account scoring model — extracted from pipeline/step2_score_accounts.py."""

try:
    from salesforge.config import SCORING_WEIGHTS, TIER_THRESHOLDS
except ImportError:
    from config import SCORING_WEIGHTS, TIER_THRESHOLDS

# Pre-filled trigger signals for top accounts
TRIGGER_SIGNALS = {
    "HCA Healthcare (FKA Hospital Corporation of America)": "Oracle Cerner → Oracle Health migration in progress across 191 facilities",
    "CommonSpirit Health": "New Chief Nursing Officer appointed Q4 2025; systemwide quality initiative announced",
    "Ascension Health": "CMS quality improvement plan filed Jan 2026; EHR standardization underway",
    "Trinity Health (FKA CHE Trinity Health)": "Launched enterprise glycemic management RFP Dec 2025",
    "Providence St Joseph Health (AKA Providence)": "Epic rollout complete but insulin calculator validation flagged by Joint Commission",
    "Tenet Healthcare": "Operating margin dropped to -2.3%; board approved cost-reduction initiative",
    "Universal Health Services": "CMS readmission penalty applied to 12 facilities Q1 2026",
    "AdventHealth (FKA Adventist Health System)": "New CNO; systemwide patient safety initiative for medication errors",
    "Advocate Health": "Cerner to Oracle Health migration beginning Q2 2026",
    "Atrium Health (AKA Carolinas HealthCare System)": "Post-merger EHR consolidation with Advocate creating integration gaps",
    "Bon Secours Mercy Health": "CMS star rating dropped at 3 facilities; quality review underway",
    "CHRISTUS Health": "RFP for glycemic management technology issued Jan 2026",
    "Prisma Health (FKA SC Health Company)": "New VP of Quality; focus on reducing hypoglycemia events",
    "Intermountain Health (FKA Intermountain Healthcare)": "Epic site but insulin module not deployed; manual protocols in use",
    "Baptist Health South Florida": "CFO flagged insulin-related LOS costs in Q4 earnings call",
}


def score_bed_count(total_beds):
    """Bed count scoring: larger systems = higher priority."""
    if total_beds is None:
        return 20
    if total_beds >= 600:
        return 100
    if total_beds >= 400:
        return 80
    if total_beds >= 200:
        return 60
    if total_beds >= 100:
        return 40
    return 20


def score_margin(conn, system_name):
    """Operating margin scoring: financial pressure = higher score."""
    rows = conn.execute(
        """SELECT net_operating_profit_margin FROM facilities
           WHERE highest_level_parent = ? AND net_operating_profit_margin IS NOT NULL""",
        (system_name,),
    ).fetchall()
    if not rows:
        return 50
    margins = sorted(r[0] for r in rows)
    median_margin = margins[len(margins) // 2]
    if median_margin < 0:
        return 100
    if median_margin <= 0.05:
        return 70
    if median_margin <= 0.10:
        return 40
    return 20


def score_ehr(conn, system_name):
    """EHR vendor scoring: non-Epic = higher (DIY calc risk angle)."""
    rows = conn.execute(
        """SELECT ehr_inpatient, COUNT(*) as cnt FROM facilities
           WHERE highest_level_parent = ? AND ehr_inpatient IS NOT NULL
           GROUP BY ehr_inpatient ORDER BY cnt DESC""",
        (system_name,),
    ).fetchall()
    if not rows:
        return 50
    primary_ehr = rows[0][0].upper() if rows[0][0] else ""
    if "MEDITECH" in primary_ehr:
        return 100
    if "CERNER" in primary_ehr or "ORACLE" in primary_ehr:
        return 90
    if "EPIC" in primary_ehr:
        return 40
    return 80


def score_cms_quality(conn, system_name):
    """CMS quality scoring: lower ratings/high readmission = higher score."""
    rows = conn.execute(
        """SELECT cms_overall_rating, readmission_rate FROM facilities
           WHERE highest_level_parent = ?
           AND (cms_overall_rating IS NOT NULL OR readmission_rate IS NOT NULL)""",
        (system_name,),
    ).fetchall()
    if not rows:
        return 50
    ratings = [r[0] for r in rows if r[0] is not None and r[0] > 0]
    readmissions = [r[1] for r in rows if r[1] is not None and r[1] > 0]

    avg_rating = sum(ratings) / len(ratings) if ratings else 3.0
    if avg_rating <= 1:
        rating_score = 100
    elif avg_rating <= 2:
        rating_score = 80
    elif avg_rating <= 3:
        rating_score = 60
    elif avg_rating <= 4:
        rating_score = 40
    else:
        rating_score = 20

    avg_readmission = sum(readmissions) / len(readmissions) if readmissions else 0.15
    readmission_bonus = 10 if avg_readmission > 0.155 else 0
    return min(100, rating_score + readmission_bonus)


def score_trigger_signal(system_name):
    """Trigger signal scoring: pre-filled signals for top accounts."""
    return 100 if system_name in TRIGGER_SIGNALS else 20


def score_contact_coverage(conn, system_name):
    """Contact coverage scoring: actual contacts or facility count proxy."""
    count = conn.execute(
        "SELECT COUNT(*) FROM contacts WHERE account_name = ?", (system_name,)
    ).fetchone()[0]
    if count > 0:
        if count >= 15:
            return 100
        if count >= 10:
            return 70
        if count >= 5:
            return 40
        return 20

    fac_count = conn.execute(
        "SELECT COUNT(*) FROM facilities WHERE highest_level_parent = ?",
        (system_name,),
    ).fetchone()[0]
    if fac_count >= 50:
        return 100
    if fac_count >= 20:
        return 70
    if fac_count >= 5:
        return 40
    return 20


def compute_score(conn, system_name, total_beds):
    """Compute the full 6-factor weighted score for an account."""
    scores = {
        "bed_count": score_bed_count(total_beds),
        "margin": score_margin(conn, system_name),
        "ehr": score_ehr(conn, system_name),
        "cms_quality": score_cms_quality(conn, system_name),
        "trigger_signal": score_trigger_signal(system_name),
        "contact_coverage": score_contact_coverage(conn, system_name),
    }
    return round(sum(scores[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS), 1)


def assign_tier(score):
    """Map score to tier label."""
    for tier, (low, high) in TIER_THRESHOLDS.items():
        if low <= score <= high:
            return tier
    return "Monitor"
