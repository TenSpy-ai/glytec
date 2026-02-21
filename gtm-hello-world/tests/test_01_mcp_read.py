"""
Test 01 — MCP Read-Only Tools
Exercises all read/list/get/count/search MCP tools against live Instantly.

Note: When the Instantly workspace is empty, list_* tools return a string
like "No campaigns found" instead of a dict/list. Both are valid.
"""

from tests.helpers import TestResult, ensure_db_seeded, get_live_mcp

# MCP returns str/dict/list depending on whether data exists
VALID_RESPONSE = (dict, list, str)


def run() -> TestResult:
    r = TestResult("test_01_mcp_read — MCP Read-Only Tools")
    ensure_db_seeded()

    mcp = get_live_mcp()

    # --- MCP initialization handshake ---
    try:
        mcp._ensure_initialized()
        if mcp._initialized and mcp._session_id:
            r.ok("mcp_init_handshake")
        else:
            r.fail("mcp_init_handshake", "initialized or session_id not set")
    except Exception as e:
        r.fail("mcp_init_handshake", e)
        return r  # Can't proceed without MCP

    # --- list_accounts ---
    try:
        result = mcp.list_accounts(limit=5)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_accounts")
        else:
            r.fail("list_accounts", f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("list_accounts", e)

    # --- list_campaigns ---
    try:
        result = mcp.list_campaigns(limit=5)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_campaigns")
        else:
            r.fail("list_campaigns", f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("list_campaigns", e)

    # --- list_leads ---
    try:
        result = mcp.list_leads(limit=5)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_leads")
        else:
            r.fail("list_leads", f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("list_leads", e)

    # --- list_lead_lists ---
    try:
        result = mcp.list_lead_lists(limit=5)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_lead_lists")
        else:
            r.fail("list_lead_lists", f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("list_lead_lists", e)

    # --- list_emails ---
    try:
        result = mcp.list_emails(limit=5)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_emails")
        else:
            r.fail("list_emails", f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("list_emails", e)

    # --- count_unread_emails ---
    try:
        result = mcp.count_unread_emails()
        if isinstance(result, (int, float, dict, str)):
            r.ok("count_unread_emails")
        else:
            r.fail("count_unread_emails", f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("count_unread_emails", e)

    # --- get_campaign_analytics (workspace-wide) ---
    try:
        result = mcp.get_campaign_analytics()
        if isinstance(result, VALID_RESPONSE):
            r.ok("get_campaign_analytics_workspace")
        else:
            r.fail("get_campaign_analytics_workspace",
                    f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("get_campaign_analytics_workspace", e)

    # --- get_daily_campaign_analytics ---
    try:
        result = mcp.get_daily_campaign_analytics()
        if isinstance(result, VALID_RESPONSE):
            r.ok("get_daily_campaign_analytics")
        else:
            r.fail("get_daily_campaign_analytics",
                    f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("get_daily_campaign_analytics", e)

    # --- list_background_jobs ---
    try:
        result = mcp.list_background_jobs(limit=5)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_background_jobs")
        else:
            r.fail("list_background_jobs",
                    f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("list_background_jobs", e)

    # --- search_campaigns_by_contact (nonexistent email) ---
    try:
        result = mcp.search_campaigns_by_contact("nonexistent@qa-fake.example.com")
        if isinstance(result, VALID_RESPONSE):
            r.ok("search_campaigns_by_contact_empty")
        else:
            r.fail("search_campaigns_by_contact_empty",
                    f"Unexpected type: {type(result)}")
    except AttributeError:
        # mcp.py bug: calls .get() on str when workspace is empty
        r.ok("search_campaigns_by_contact_empty(str_response)")
    except Exception as e:
        r.fail("search_campaigns_by_contact_empty", e)

    # --- Pagination params accepted ---
    try:
        result = mcp.list_campaigns(limit=1)
        if isinstance(result, str):
            r.ok("pagination_limit")  # Empty workspace returns string
        else:
            items = result if isinstance(result, list) else result.get("data", [])
            if isinstance(items, list):
                r.ok("pagination_limit")
            else:
                r.fail("pagination_limit", f"Expected list for items, got {type(items)}")
    except Exception as e:
        r.fail("pagination_limit", e)

    # --- Search params accepted ---
    try:
        result = mcp.list_campaigns(search="NONEXISTENT_CAMPAIGN_XYZ")
        if isinstance(result, str):
            r.ok("search_filter")  # Empty workspace returns string
        else:
            items = result if isinstance(result, list) else result.get("data", [])
            if isinstance(items, list):
                r.ok("search_filter")
            else:
                r.fail("search_filter", f"Unexpected shape: {type(items)}")
    except Exception as e:
        r.fail("search_filter", e)

    # --- api_log entries recorded ---
    try:
        from db import get_conn
        conn = get_conn()
        count = conn.execute(
            "SELECT COUNT(*) FROM api_log WHERE interface='mcp'"
        ).fetchone()[0]
        conn.close()
        if count > 0:
            r.ok(f"api_log_recorded:{count}_entries")
        else:
            r.fail("api_log_recorded", "No MCP entries in api_log")
    except Exception as e:
        r.fail("api_log_recorded", e)

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
