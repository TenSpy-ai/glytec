"""
GTM Hello World — Contact Query Builder

Chainable query builder that compiles to SQL against gtm_hello_world.db.
Reuses patterns from ops/launch_campaign.py and ops/enroll_contacts.py.

Usage:
    from query_builder import ContactQuery, parse_natural_language
    from db import get_conn

    conn = get_conn()
    q = ContactQuery().tier('Active').titles('CNO', 'CFO').top(5)
    contacts = q.execute(conn)

    q2 = parse_natural_language('top 30 CNOs at Epic hospitals')
    contacts = q2.execute(conn)
"""

import re
import sqlite3


class ContactQuery:
    """Chainable contact filter that compiles to SQL."""

    def __init__(self):
        self._limit = None
        self._account = None
        self._tiers = []
        self._ehr = None
        self._segment = None
        self._titles = []
        self._departments = []
        self._job_levels = []
        self._icp_category = None
        self._verified_only = False
        self._exclude_campaigns = []
        self._exclude_blocked = True  # on by default

    def top(self, n: int) -> "ContactQuery":
        self._limit = n
        return self

    def account(self, name: str) -> "ContactQuery":
        self._account = name
        return self

    def tier(self, *tiers: str) -> "ContactQuery":
        self._tiers.extend(tiers)
        return self

    def ehr(self, vendor: str) -> "ContactQuery":
        self._ehr = vendor
        return self

    def segment(self, seg: str) -> "ContactQuery":
        self._segment = seg
        return self

    def titles(self, *titles: str) -> "ContactQuery":
        self._titles.extend(titles)
        return self

    def department(self, *depts: str) -> "ContactQuery":
        self._departments.extend(depts)
        return self

    def job_level(self, *levels: str) -> "ContactQuery":
        self._job_levels.extend(levels)
        return self

    def icp_category(self, cat: str) -> "ContactQuery":
        self._icp_category = cat
        return self

    def verified_only(self) -> "ContactQuery":
        self._verified_only = True
        return self

    def exclude_campaign(self, name: str) -> "ContactQuery":
        self._exclude_campaigns.append(name)
        return self

    def exclude_blocked(self) -> "ContactQuery":
        self._exclude_blocked = True
        return self

    def include_blocked(self) -> "ContactQuery":
        """Opt out of block list exclusion (for testing)."""
        self._exclude_blocked = False
        return self

    def execute(self, conn: sqlite3.Connection) -> list[dict]:
        """Build SQL, run query, return list of contact dicts."""
        conditions = ["c.email IS NOT NULL"]
        params = []

        if self._account:
            conditions.append("c.account_name LIKE ?")
            params.append(f"%{self._account}%")

        if self._tiers:
            placeholders = ", ".join("?" for _ in self._tiers)
            conditions.append(f"a.tier IN ({placeholders})")
            params.extend(self._tiers)

        if self._ehr:
            conditions.append("a.primary_ehr LIKE ?")
            params.append(f"%{self._ehr}%")

        if self._segment:
            conditions.append("a.segment LIKE ?")
            params.append(f"%{self._segment}%")

        if self._titles:
            title_conds = []
            for t in self._titles:
                title_conds.append("c.title LIKE ?")
                params.append(f"%{t}%")
            conditions.append(f"({' OR '.join(title_conds)})")

        if self._departments:
            placeholders = ", ".join("?" for _ in self._departments)
            conditions.append(f"c.icp_department IN ({placeholders})")
            params.extend(self._departments)

        if self._job_levels:
            placeholders = ", ".join("?" for _ in self._job_levels)
            conditions.append(f"c.icp_job_level IN ({placeholders})")
            params.extend(self._job_levels)

        if self._icp_category:
            conditions.append("c.icp_category = ?")
            params.append(self._icp_category)

        if self._verified_only:
            conditions.append("c.email_verified = 'valid'")

        if self._exclude_blocked:
            conditions.append("c.email NOT IN (SELECT value FROM block_list)")

        for campaign_name in self._exclude_campaigns:
            conditions.append(
                """c.email NOT IN (
                    SELECT ct.email FROM contacts ct
                    JOIN campaign_contacts cc ON ct.id = cc.contact_id
                    JOIN campaigns camp ON cc.campaign_id = camp.id
                    WHERE camp.name LIKE ?
                )"""
            )
            params.append(f"%{campaign_name}%")

        where = " AND ".join(conditions)
        limit_clause = f" LIMIT {self._limit}" if self._limit else ""

        query = f"""
            SELECT c.id, c.first_name, c.last_name, c.email, c.title,
                   c.account_name, c.icp_category, c.icp_intent_score,
                   c.icp_department, c.icp_job_level, c.email_verified,
                   a.tier, a.primary_ehr, a.segment, a.total_beds, a.score
            FROM contacts c
            LEFT JOIN accounts a ON c.account_name = a.system_name
            WHERE {where}
            ORDER BY c.icp_intent_score DESC
            {limit_clause}
        """

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def describe(self) -> str:
        """Human-readable description of active filters."""
        parts = []
        if self._limit:
            parts.append(f"top {self._limit}")
        if self._titles:
            parts.append(f"titles: {', '.join(self._titles)}")
        if self._account:
            parts.append(f"account: {self._account}")
        if self._tiers:
            parts.append(f"tier: {', '.join(self._tiers)}")
        if self._ehr:
            parts.append(f"EHR: {self._ehr}")
        if self._segment:
            parts.append(f"segment: {self._segment}")
        if self._departments:
            parts.append(f"department: {', '.join(self._departments)}")
        if self._job_levels:
            parts.append(f"job level: {', '.join(self._job_levels)}")
        if self._icp_category:
            parts.append(f"ICP category: {self._icp_category}")
        if self._verified_only:
            parts.append("verified only")
        if self._exclude_campaigns:
            parts.append(f"excluding campaigns: {', '.join(self._exclude_campaigns)}")
        if self._exclude_blocked:
            parts.append("excluding blocked")
        return " | ".join(parts) if parts else "all contacts"


# ── Title abbreviation mapping ──────────────────────────────────────────────

TITLE_ALIASES = {
    "cno": "CNO",
    "cfo": "CFO",
    "cmo": "CMO",
    "ceo": "CEO",
    "cqo": "CQO",
    "cio": "CIO",
    "coo": "COO",
    "cpo": "Chief Pharmacy Officer",
    "vp": "VP",
    "director": "Dir",
    "pharmacy": "Pharmacy",
    "nursing": "Nursing",
}

# EHR vendor names recognized in natural language
EHR_KEYWORDS = {"epic", "cerner", "meditech", "allscripts", "athenahealth"}

# Tier names recognized in natural language
TIER_KEYWORDS = {"priority", "active", "nurture", "monitor"}


def parse_natural_language(text: str) -> ContactQuery:
    """Parse natural language like 'top 30 CNOs at Epic hospitals' into a ContactQuery.

    Handles patterns:
    - 'top N' → .top(N)
    - title keywords (CNO, CFO, CMO, etc.) → .titles(...)
    - 'at {account}' → .account(...)
    - EHR names (Epic, Cerner, MEDITECH) → .ehr(...)
    - tier names (Priority, Active, Nurture) → .tier(...)
    - 'verified' → .verified_only()
    - segment keywords (Enterprise, Commercial) → .segment(...)
    - department keywords (pharmacy, nursing, finance) → .department(...)
    - job level keywords (Executive, Director, VP) → .job_level(...)
    """
    q = ContactQuery()
    text_lower = text.lower().strip()

    # Extract 'top N'
    top_match = re.search(r'\btop\s+(\d+)\b', text_lower)
    if top_match:
        q.top(int(top_match.group(1)))

    # Extract 'at {account name}' — greedy match after 'at'
    at_match = re.search(r'\bat\s+(.+?)(?:\s+hospitals?|\s+systems?|\s*$)', text_lower)
    if at_match:
        account = at_match.group(1).strip()
        # Don't treat EHR names as accounts
        if account.lower() not in EHR_KEYWORDS:
            q.account(account)

    # Extract title abbreviations
    found_titles = []
    for alias, title in TITLE_ALIASES.items():
        # Match as whole word
        if re.search(rf'\b{re.escape(alias)}s?\b', text_lower):
            found_titles.append(title)
    if found_titles:
        q.titles(*found_titles)

    # Extract EHR
    for ehr in EHR_KEYWORDS:
        if re.search(rf'\b{ehr}\b', text_lower):
            q.ehr(ehr.capitalize() if ehr != "meditech" else "MEDITECH")
            break

    # Extract tier
    for tier in TIER_KEYWORDS:
        if re.search(rf'\b{tier}\b', text_lower):
            q.tier(tier.capitalize())

    # Extract 'verified'
    if "verified" in text_lower:
        q.verified_only()

    # Extract segment
    if "enterprise" in text_lower or "strategic" in text_lower:
        q.segment("Enterprise/Strategic")
    elif "commercial" in text_lower:
        q.segment("Commercial")

    # Extract job level
    for level in ["executive", "director", "vp", "manager"]:
        if re.search(rf'\bjob.?level\s+{level}\b', text_lower):
            q.job_level(level.capitalize())

    return q
