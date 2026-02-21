"""ICP title matching — maps DH executive titles to Glytec's 66 ICP titles."""

import csv
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICP_CSV = PROJECT_ROOT / "data" / "AI SDR_ICP Titles_2.12.26.csv"
ICP_JSON = PROJECT_ROOT / "outbound" / "ICP.json"

# Pre-built keyword mappings from ICP titles to DH API fields.
# Each entry maps keywords to search against standardizedTitle and department.
TITLE_KEYWORDS = {
    "Chief Executive Officer": ["chief executive", "ceo"],
    "Chief Operating Officer": ["chief operating", "coo"],
    "Chief Financial Officer": ["chief financial", "cfo"],
    "Chief Nursing Officer": ["chief nursing", "cno"],
    "Chief Quality Officer": ["chief quality", "cqo"],
    "Chief Medical Information Officer": ["cmio", "chief medical information"],
    "Chief Compliance Officer": ["chief compliance"],
    "Chief Innovation Officer": ["chief innovation"],
    "Chief Strategy Officer": ["chief strategy", "cso"],
    "Chief Data Officer": ["chief data"],
    "Chief Pharmacy Officer": ["chief pharmacy"],
    "Chief of Endocrinology": ["chief of endocrinology", "chief endocrin"],
    "Chief of Critical Care": ["chief of critical care"],
    "Director of Clinical Informatics": ["director of clinical informatics", "clinical informatics director"],
    "Director of Inpatient Nursing": ["director of inpatient nursing", "director of nursing"],
    "Director of Quality Improvement": ["director of quality", "quality improvement director"],
    "Director of Clinical Pharmacy": ["director of clinical pharmacy", "pharmacy director"],
    "Director of Nursing Informatics": ["director of nursing informatics"],
    "Medical Director of Hospital Medicine": ["medical director of hospital medicine", "medical director hospital"],
    "Medical Director, ICU": ["medical director.*icu", "icu medical director", "icu director"],
    "Medical Director, Diabetes Services": ["medical director.*diabetes", "diabetes.*medical director"],
    "Surgical ICU Director": ["surgical icu director", "sicu director"],
    "Perioperative Medical Director": ["perioperative medical director", "perioperative director"],
    "Chief of Cardiothoracic Surgery": ["chief of cardiothoracic", "cardiothoracic surgery"],
    "Chief of General Surgery": ["chief of general surgery"],
    "Chief of Vascular Surgery": ["chief of vascular surgery"],
    "Chief of Transplant Surgery": ["chief of transplant surgery"],
    "Vice President, Clinical Transformation": ["vp.*clinical transformation", "clinical transformation"],
    "Vice President, Evidence Based Medicine": ["vp.*evidence based", "evidence based medicine"],
    "Chair of Medicine": ["chair of medicine"],
    "Associate CMIO": ["associate cmio", "associate chief medical information"],
    "Associate Chief of Hospital Medicine": ["associate chief.*hospital medicine"],
}

# Words that are too common to be discriminating in title matching
STOP_WORDS = {"chief", "officer", "director", "of", "the", "and", "vice", "president",
              "manager", "lead", "senior", "associate", "assistant", "deputy"}

# Titles that appear in DH but are NOT in the 66 ICP titles AND are not relevant
# to Glucommander sales. Do not match these to a different ICP title.
NON_ICP_TITLES = {
    "chief of staff", "chief information officer",
    "chief human resources officer", "chief legal officer", "chief marketing officer",
    "chief development officer", "chief administrative officer",
    "chief communications officer", "chief experience officer",
    "chief revenue officer", "chief technology officer",
    "chief of radiology", "chief of pathology",
    "chief of anesthesiology", "chief of emergency medicine",
    "chief of pediatrics", "chief of psychiatry", "chief of neurology",
    "chief of obstetrics", "chief of orthopedics", "chief of urology",
    "chief of ophthalmology", "chief of dermatology",
}

# Important titles NOT in the 66 ICP titles CSV but still valuable for outreach.
# We create synthetic ICP entries for these.
SYNTHETIC_ICP = {
    "chief medical officer": {
        "Title": "Chief Medical Officer (CMO)", "Department": "Executive Leadership",
        "Category": "Decision Maker", "Intent Score": 90,
        "Function Type": "Clinical", "Job Level": "Executive",
    },
    "chief of medicine": {
        "Title": "Chief of Medicine", "Department": "Hospital Medicine",
        "Category": "Decision Maker", "Intent Score": 80,
        "Function Type": "Clinical", "Job Level": "Executive",
    },
}

DEPARTMENT_KEYWORDS = {
    "Pharmacy": ["pharmacy", "pharm"],
    "Nursing": ["nursing", "nurse"],
    "Critical Care": ["critical care", "icu", "intensive care"],
    "Quality Improvement": ["quality"],
    "Patient Safety": ["safety"],
    "Clinical Informatics": ["informatics"],
    "Endocrinology": ["endocrinology", "endocrin", "diabetes"],
    "Hospital Medicine": ["hospital medicine", "hospitalist"],
    "Surgery": ["surgery", "surgical"],
}


class ICPMatcher:
    """Match DH executive records against 66 ICP titles."""

    def __init__(self):
        self.icp_titles = self._load_icp_titles()
        self._build_index()

    def _load_icp_titles(self) -> list[dict]:
        """Load ICP titles from JSON file."""
        with open(ICP_JSON, "r") as f:
            return json.load(f)

    def _build_index(self):
        """Build lookup structures for matching."""
        self.by_title = {}
        self.by_department = {}
        for icp in self.icp_titles:
            title_lower = icp["Title"].lower()
            self.by_title[title_lower] = icp
            # Also index the title without parenthetical abbreviation
            # e.g. "Chief Executive Officer (CEO)" -> "chief executive officer"
            stripped = re.sub(r'\s*\([^)]*\)\s*$', '', title_lower).strip()
            if stripped != title_lower:
                self.by_title[stripped] = icp
            dept = icp["Department"]
            self.by_department.setdefault(dept, []).append(icp)

    def match(self, standardized_title: str, department: str = None,
              position_level: str = None) -> dict | None:
        """Match a DH executive against ICP titles.

        Returns the best ICP match dict or None.
        """
        if not standardized_title:
            return None

        title_lower = standardized_title.lower().strip()
        # Strip anything after "/" (e.g. "Chief Nursing Officer/ VP of Patient Care")
        title_primary = title_lower.split("/")[0].strip()
        dept_lower = (department or "").lower().strip()

        # Check synthetic ICP entries (important titles not in CSV)
        if title_primary in SYNTHETIC_ICP:
            return self._format_match(SYNTHETIC_ICP[title_primary])

        # Reject known non-ICP titles before fuzzy matching
        if title_primary in NON_ICP_TITLES:
            return None

        # Strategy 1: Exact title match
        for icp_title, icp in self.by_title.items():
            if icp_title == title_lower or icp_title == title_primary:
                return self._format_match(icp)

        # Strategy 2: Keyword match on standardized title
        best_match = None
        best_score = 0
        for icp in self.icp_titles:
            score = self._score_match(title_lower, dept_lower, position_level, icp)
            if score > best_score:
                best_score = score
                best_match = icp

        if best_score >= 50:
            return self._format_match(best_match)

        return None

    def _score_match(self, title_lower: str, dept_lower: str,
                     position_level: str, icp: dict) -> int:
        """Score how well an executive matches an ICP title (0-100)."""
        score = 0
        icp_title_lower = icp["Title"].lower()

        # Check keyword matches for specific titles
        # Strip parenthetical from ICP title for comparison: "Chief Executive Officer (CEO)" -> "chief executive officer"
        icp_title_stripped = re.sub(r'\s*\([^)]*\)\s*', '', icp_title_lower).strip()
        for ref_title, keywords in TITLE_KEYWORDS.items():
            if ref_title.lower() in (icp_title_lower, icp_title_stripped):
                for kw in keywords:
                    if re.search(kw, title_lower):
                        score += 60
                        break

        # Title substring matching — exclude stop words to avoid false positives
        icp_words = set(re.findall(r'\w+', icp_title_lower)) - STOP_WORDS
        title_words = set(re.findall(r'\w+', title_lower)) - STOP_WORDS
        common = icp_words & title_words
        if icp_words and common:
            word_overlap = len(common) / len(icp_words)
            score += int(word_overlap * 40)

        # Department matching
        if dept_lower:
            icp_dept_lower = icp["Department"].lower()
            for dept, keywords in DEPARTMENT_KEYWORDS.items():
                if dept.lower() == icp_dept_lower:
                    for kw in keywords:
                        if kw in dept_lower:
                            score += 20
                            break

        # Position level boost
        if position_level:
            icp_level = icp.get("Job Level", "").lower()
            pl = position_level.lower()
            if pl == "c-level" and icp_level == "executive":
                score += 10
            elif pl == "vice president" and icp_level in ("director", "executive"):
                score += 5
            elif pl == "manager/director" and icp_level in ("director", "mid-level"):
                score += 5

        return score

    def _format_match(self, icp: dict) -> dict:
        """Format an ICP match result."""
        return {
            "icp_title": icp["Title"],
            "icp_department": icp["Department"],
            "icp_category": icp["Category"],
            "icp_intent_score": icp["Intent Score"],
            "icp_function_type": icp["Function Type"],
            "icp_job_level": icp["Job Level"],
        }

    def get_search_batches(self) -> list[dict]:
        """Return DH API filter batches for ICP discovery (Recipe 2 pattern)."""
        return [
            {"name": "C-Suite", "filters": [
                {"propertyName": "positionLevel", "operatorType": "Equals", "value": "C-Level"}
            ]},
            {"name": "Pharmacy", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Pharm"}
            ]},
            {"name": "Nursing", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Nurs"}
            ]},
            {"name": "Quality", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Quality"}
            ]},
            {"name": "Safety", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Safety"}
            ]},
            {"name": "Informatics", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Informati"}
            ]},
            {"name": "Critical Care", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Critical"}
            ]},
            {"name": "Surgery", "filters": [
                {"propertyName": "department", "operatorType": "Contains", "value": "Surg"}
            ]},
            {"name": "Endocrinology", "filters": [
                {"propertyName": "standardizedTitle", "operatorType": "Contains", "value": "Endocrin"}
            ]},
            {"name": "Diabetes", "filters": [
                {"propertyName": "standardizedTitle", "operatorType": "Contains", "value": "Diabetes"}
            ]},
            {"name": "Hospital Medicine", "filters": [
                {"propertyName": "standardizedTitle", "operatorType": "Contains", "value": "Hospital"}
            ]},
        ]
