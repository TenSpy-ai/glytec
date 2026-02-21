"""GTM Operations configuration — constants, API keys, scoring weights."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Salesforge
# ---------------------------------------------------------------------------
SALESFORGE_API_KEY = os.getenv("SALESFORGE_API_KEY", "")
SALESFORGE_BASE_URL = "https://api.salesforge.ai/public/v2"
WORKSPACE_ID = "wks_05g6m7nsyweyerpgf0wuq"
PRODUCT_ID = "prod_jfxqn21476u6o3m5ocogi"

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
FACILITY_CSV = DATA_DIR / "AI SDR_Facility List_1.23.26.csv"
SUPPLEMENTAL_CSV = DATA_DIR / "AI SDR_Facility List_Supplemental Data_1.23.26.csv"
PARENT_CSV = DATA_DIR / "AI SDR_Parent Account List_1.23.26.csv"
ICP_CSV = DATA_DIR / "AI SDR_ICP Titles_2.12.26.csv"
ICP_JSON = PROJECT_ROOT / "outbound" / "ICP.json"

# GTM Ops paths
SALESFORGE_DIR = Path(__file__).resolve().parent
DB_PATH = SALESFORGE_DIR / "db" / "gtm_ops.db"
API_LOG_PATH = SALESFORGE_DIR / "api_call_log.md"

# Pipeline V1 (for migration)
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
PIPELINE_DB_PATH = PIPELINE_DIR / "glytec_v1.db"

# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------
SCORING_WEIGHTS = {
    "bed_count": 0.20,
    "margin": 0.15,
    "ehr": 0.20,
    "cms_quality": 0.15,
    "trigger_signal": 0.20,
    "contact_coverage": 0.10,
}

# ---------------------------------------------------------------------------
# Score tier thresholds
# ---------------------------------------------------------------------------
TIER_THRESHOLDS = {
    "Priority": (80, 100),
    "Active": (60, 79),
    "Nurture": (40, 59),
    "Monitor": (0, 39),
}

# ---------------------------------------------------------------------------
# Kill-switch thresholds
# ---------------------------------------------------------------------------
BOUNCE_THRESHOLD = 0.05   # >5% bounce → pause
SPAM_THRESHOLD = 0.003    # >0.3% spam → pause

# ---------------------------------------------------------------------------
# Dry-run mode — override with --live flag
# ---------------------------------------------------------------------------
DRY_RUN = True

def enable_live_mode():
    global DRY_RUN
    DRY_RUN = False

def salesforge_headers():
    """Return auth headers for Salesforge API (raw key, no Bearer prefix)."""
    return {
        "Authorization": SALESFORGE_API_KEY,
        "Content-Type": "application/json",
    }

def workspace_url(path: str = "") -> str:
    """Build a workspace-scoped Salesforge URL."""
    base = f"{SALESFORGE_BASE_URL}/workspaces/{WORKSPACE_ID}"
    if path:
        return f"{base}/{path.lstrip('/')}"
    return base
