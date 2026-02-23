"""
GTM Hello World — Configuration
Paths, env vars, constants, API keys.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "gtm_hello_world.db"
CAMPAIGNS_DIR = BASE_DIR / "campaigns"
ENRICHMENT_DB_PATH = BASE_DIR.parent / "enrichment" / "data" / "enrichment.db"

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv(BASE_DIR.parent / ".env")

INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY", "")
CLAY_WEBHOOK_URL = os.getenv("CLAY_WEBHOOK_URL", "")

# ---------------------------------------------------------------------------
# Operational constants
# ---------------------------------------------------------------------------
DRY_RUN = False  # LIVE MODE — set True to re-enable safe mode

# Kill-switch thresholds
BOUNCE_RATE_LIMIT = 0.05       # 5% — auto-pause campaign
SPAM_RATE_LIMIT = 0.003        # 0.3%
UNSUBSCRIBE_RATE_LIMIT = 0.02  # 2%

# Sentiment thresholds
POSITIVE_THRESHOLD = 0.7   # ai_interest_value above this = positive
NEGATIVE_THRESHOLD = 0.3   # ai_interest_value below this = negative

# Instantly API
INSTANTLY_BASE_URL = "https://api.instantly.ai/api/v2"
INSTANTLY_MCP_URL_TEMPLATE = "https://mcp.instantly.ai/mcp/{api_key}"


def instantly_headers() -> dict:
    """Headers for Instantly REST API v2 (Bearer token auth)."""
    return {
        "Authorization": f"Bearer {INSTANTLY_API_KEY}",
        "Content-Type": "application/json",
    }


def instantly_api_url(path: str) -> str:
    """Build full Instantly REST API URL from a path segment."""
    return f"{INSTANTLY_BASE_URL}/{path.lstrip('/')}"
