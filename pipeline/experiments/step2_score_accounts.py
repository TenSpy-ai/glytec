"""Step 2 — Account Scoring: 6-factor weighted model."""

from db import get_conn
from config import SCORING_WEIGHTS, TIER_THRESHOLDS

# Pre-filled trigger signals for top accounts (simulates DH API news + research)
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


def _score_bed_count(total_beds):
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


def _score_margin(conn, system_name):
    """Operating margin scoring: financial pressure = higher score.
    Uses median margin across all child facilities."""
    rows = conn.execute(
        """SELECT net_operating_profit_margin FROM facilities
           WHERE highest_level_parent = ? AND net_operating_profit_margin IS NOT NULL""",
        (system_name,),
    ).fetchall()
    if not rows:
        return 50  # neutral if no data
    margins = sorted(r[0] for r in rows)
    median_margin = margins[len(margins) // 2]
    if median_margin < 0:
        return 100
    if median_margin <= 0.05:
        return 70
    if median_margin <= 0.10:
        return 40
    return 20


def _score_ehr(conn, system_name):
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
    return 80  # Other/unknown


def _score_cms_quality(conn, system_name):
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

    # Average CMS star rating
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

    # Bonus for high readmission rate (above national avg ~15%)
    avg_readmission = sum(readmissions) / len(readmissions) if readmissions else 0.15
    readmission_bonus = 10 if avg_readmission > 0.155 else 0

    return min(100, rating_score + readmission_bonus)


def _score_trigger_signal(system_name):
    """Trigger signal scoring: pre-filled signals for top accounts."""
    if system_name in TRIGGER_SIGNALS:
        return 100
    return 20


def _score_contact_coverage(conn, system_name):
    """Contact coverage scoring: check contacts in DB, or estimate from facility count.

    In production this checks Salesforge's 7,347 contacts.
    For the local demo, we estimate from facility count as a proxy for
    how many ICP-matching contacts Salesforge would have for this system.
    """
    # Check actual contacts first
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

    # Estimate from facility count (proxy for Salesforge coverage)
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


def _assign_tier(score):
    """Map score to tier label."""
    for tier, (low, high) in TIER_THRESHOLDS.items():
        if low <= score <= high:
            return tier
    return "Monitor"


def run():
    """Execute step 2."""
    print("\n=== Step 2: Score Accounts ===")
    conn = get_conn()
    try:
        accounts = conn.execute(
            "SELECT id, system_name, total_beds FROM accounts"
        ).fetchall()
        print(f"[step2] Scoring {len(accounts)} accounts...")

        tier_counts = {"Priority": 0, "Active": 0, "Nurture": 0, "Monitor": 0}

        for acct in accounts:
            acct_id = acct["id"]
            name = acct["system_name"]
            beds = acct["total_beds"]

            scores = {
                "bed_count": _score_bed_count(beds),
                "margin": _score_margin(conn, name),
                "ehr": _score_ehr(conn, name),
                "cms_quality": _score_cms_quality(conn, name),
                "trigger_signal": _score_trigger_signal(name),
                "contact_coverage": _score_contact_coverage(conn, name),
            }

            weighted = sum(
                scores[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS
            )
            tier = _assign_tier(weighted)
            tier_counts[tier] += 1

            conn.execute(
                "UPDATE accounts SET score = ?, tier = ? WHERE id = ?",
                (round(weighted, 1), tier, acct_id),
            )

        conn.commit()

        # Print distribution
        total = len(accounts)
        print(f"[step2] Scoring complete:")
        for tier, count in tier_counts.items():
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {tier}: {count} ({pct:.1f}%)")

        # Show top 10
        top = conn.execute(
            "SELECT system_name, score, tier FROM accounts ORDER BY score DESC LIMIT 10"
        ).fetchall()
        print(f"\n[step2] Top 10 accounts:")
        for i, row in enumerate(top, 1):
            signal = TRIGGER_SIGNALS.get(row["system_name"], "")
            signal_str = f" — {signal[:60]}..." if signal else ""
            print(f"  {i}. {row['system_name'][:50]} | Score: {row['score']} | {row['tier']}{signal_str}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
