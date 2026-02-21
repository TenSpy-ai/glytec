"""ICP title matching — extracted from pipeline/step4_wash_contacts.py."""

import json
from difflib import get_close_matches

try:
    from salesforge.config import ICP_JSON
except ImportError:
    from config import ICP_JSON


def load_icp_titles():
    """Load ICP titles from JSON for fuzzy matching."""
    with open(ICP_JSON, "r") as f:
        return json.load(f)


def match_title(contact_title, icp_titles=None):
    """Match a contact title against the 66-title ICP taxonomy.

    Returns an ICP dict with Department, Title, Category, Intent Score,
    Function Type, Job Level — or None if no match.
    """
    if not contact_title or not contact_title.strip():
        return None

    if icp_titles is None:
        icp_titles = load_icp_titles()

    title_lookup = {t["Title"].lower(): t for t in icp_titles}
    title_list = list(title_lookup.keys())
    lower_title = contact_title.lower().strip()

    # Exact match
    icp = title_lookup.get(lower_title)
    if icp:
        return icp

    # Fuzzy match
    matches = get_close_matches(lower_title, title_list, n=1, cutoff=0.6)
    if matches:
        return title_lookup[matches[0]]

    # Keyword overlap match
    for icp_title, icp_data in title_lookup.items():
        icp_words = set(icp_title.split())
        contact_words = set(lower_title.split())
        overlap = icp_words & contact_words
        if len(overlap) >= 2 and len(overlap) / len(icp_words) >= 0.5:
            return icp_data

    return None
