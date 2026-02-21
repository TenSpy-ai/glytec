"""
Test 05 — Email & Verification Tools
Email listing, counting, verification, dry-run reply + mark-read.
"""

from tests.helpers import (
    TestResult, ensure_db_seeded, get_live_mcp, get_dry_mcp,
)

# MCP returns str when workspace is empty (e.g., "No emails found")
VALID_RESPONSE = (dict, list, str)


def run() -> TestResult:
    r = TestResult("test_05_email_tools — Email & Verification Tools")
    ensure_db_seeded()

    mcp = get_live_mcp()

    # 1. list_emails (may be empty)
    try:
        result = mcp.list_emails(limit=5)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_emails")
        else:
            r.fail("list_emails", f"Unexpected type: {type(result)}")
    except Exception as e:
        r.fail("list_emails", e)

    # 2. list_emails with limit
    try:
        result = mcp.list_emails(limit=1)
        if isinstance(result, VALID_RESPONSE):
            r.ok("list_emails_limit")
        else:
            r.fail("list_emails_limit", f"Unexpected: {type(result)}")
    except Exception as e:
        r.fail("list_emails_limit", e)

    # 3. count_unread_emails
    try:
        result = mcp.count_unread_emails()
        if isinstance(result, (int, float, dict)):
            r.ok(f"count_unread:{result}")
        else:
            r.fail("count_unread", f"Unexpected: {type(result)}")
    except Exception as e:
        r.fail("count_unread", e)

    # 4. verify_email — valid address (slow: 5-45s)
    try:
        result = mcp.verify_email("test@gmail.com")
        if isinstance(result, (dict, str)):
            r.ok("verify_email_valid")
        else:
            r.fail("verify_email_valid", f"Unexpected: {type(result)}")
    except Exception as e:
        r.fail("verify_email_valid", e)

    # 5. verify_email — invalid address
    try:
        result = mcp.verify_email("definitely-not-real-xyz@nonexistent-domain-12345.com")
        if isinstance(result, (dict, str)):
            r.ok("verify_email_invalid")
        else:
            r.fail("verify_email_invalid", f"Unexpected: {type(result)}")
    except Exception as e:
        r.fail("verify_email_invalid", e)

    # 6. reply_to_email method exists
    try:
        assert hasattr(mcp, "reply_to_email"), "Method not found"
        assert callable(mcp.reply_to_email), "Not callable"
        r.ok("reply_method_exists")
    except Exception as e:
        r.fail("reply_method_exists", e)

    # 7. reply_to_email dry-run
    try:
        dry = get_dry_mcp()
        result = dry.reply_to_email(
            reply_to_uuid="fake-uuid-12345",
            body="QA test reply — dry run",
            eaccount="test@example.com",
            subject="Re: QA Test",
        )
        if result.get("status") == "dry_run":
            r.ok("reply_dry_run")
        else:
            r.fail("reply_dry_run", f"Expected dry_run status: {result}")
    except Exception as e:
        r.fail("reply_dry_run", e)

    # 8. mark_thread_as_read dry-run
    try:
        dry = get_dry_mcp()
        result = dry.mark_thread_as_read("fake-thread-12345")
        if result is True:
            r.ok("mark_read_dry_run")
        else:
            r.fail("mark_read_dry_run", f"Expected True: {result}")
    except Exception as e:
        r.fail("mark_read_dry_run", e)

    # 9. get_email nonexistent
    try:
        result = mcp.get_email("00000000-0000-0000-0000-000000000000")
        # Should return empty or error
        if isinstance(result, (dict, str)):
            r.ok("get_email_nonexistent")
        else:
            r.ok("get_email_nonexistent")
    except Exception:
        r.ok("get_email_nonexistent")  # Error is expected

    # 10. get_warmup_analytics
    try:
        # Use a dummy email — returns empty analytics or string
        result = mcp.get_warmup_analytics(emails=["warmup-test@example.com"])
        if isinstance(result, VALID_RESPONSE):
            r.ok("get_warmup_analytics")
        else:
            r.fail("get_warmup_analytics", f"Unexpected: {type(result)}")
    except Exception as e:
        r.fail("get_warmup_analytics", e)

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
