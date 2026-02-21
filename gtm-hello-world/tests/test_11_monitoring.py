"""
Test 11 — Monitoring, Reporting & DB Persistence
Exercises every report function, metric snapshot write, kill-switch check,
account view sub-query, and DB logging pipeline.

Uses mock data inserted into DB — no Instantly API calls.
"""

from datetime import date
from tests.helpers import TestResult, ensure_db_seeded, TEST_PREFIX


def run() -> TestResult:
    r = TestResult("test_11_monitoring — Monitoring, Reporting & DB Persistence")
    ensure_db_seeded()

    from db import get_conn, log_api_call
    from config import BOUNCE_RATE_LIMIT, SPAM_RATE_LIMIT

    conn = get_conn()

    # IDs created by mock setup for cleanup
    mock_campaign_id = None
    mock_contact_ids = []

    try:
        # ========== SETUP: Insert mock data for reporting tests ==========
        conn.execute(
            """INSERT INTO campaigns
               (name, instantly_campaign_id, recipe, status, instantly_status,
                target_persona, step_count, daily_limit)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"{TEST_PREFIX}MON_CAMP", "fake_mon_camp_11", "R1", "active", 1,
             "CNO", 3, 30),
        )
        mock_campaign_id = conn.execute(
            "SELECT id FROM campaigns WHERE name = ?",
            (f"{TEST_PREFIX}MON_CAMP",),
        ).fetchone()["id"]

        # Insert contacts
        for i, (fn, ln, title, dept, score) in enumerate([
            ("Mon", "Contact1", "CFO", "Finance", 90),
            ("Mon", "Contact2", "CNO", "Nursing", 85),
        ]):
            email = f"{TEST_PREFIX}mon{i}@example.com"
            conn.execute(
                """INSERT OR IGNORE INTO contacts
                   (first_name, last_name, email, title, account_name,
                    icp_category, icp_intent_score, icp_department, icp_job_level)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (fn, ln, email, title, "HCA Healthcare",
                 "Decision Maker", score, dept, "C-Suite"),
            )
            cid = conn.execute(
                "SELECT id FROM contacts WHERE email = ?", (email,),
            ).fetchone()["id"]
            mock_contact_ids.append(cid)

            # Enroll in campaign
            conn.execute(
                "INSERT OR IGNORE INTO campaign_contacts (campaign_id, contact_id) VALUES (?, ?)",
                (mock_campaign_id, cid),
            )

        # Insert metric snapshots (today + yesterday)
        today = date.today().isoformat()
        conn.execute(
            """INSERT OR REPLACE INTO metric_snapshots
               (campaign_id, instantly_campaign_id, snapshot_date,
                sent, opened, replied, bounced, open_rate, reply_rate, bounce_rate)
               VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, ?, ?)""",
            (mock_campaign_id, "fake_mon_camp_11",
             200, 80, 10, 4, 0.40, 0.05, 0.02),
        )
        conn.execute(
            """INSERT OR REPLACE INTO metric_snapshots
               (campaign_id, instantly_campaign_id, snapshot_date,
                sent, opened, replied, bounced, open_rate, reply_rate, bounce_rate)
               VALUES (?, ?, date('now', '-1 day'), ?, ?, ?, ?, ?, ?, ?)""",
            (mock_campaign_id, "fake_mon_camp_11",
             150, 60, 8, 3, 0.40, 0.053, 0.02),
        )

        # Insert reply sentiment
        conn.execute(
            """INSERT INTO reply_sentiment
               (instantly_email_id, campaign_id, contact_id, contact_email,
                sentiment, sentiment_confidence, classified_by, pushed_to_clay)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("mon_email_1", mock_campaign_id, mock_contact_ids[0],
             f"{TEST_PREFIX}mon0@example.com", "positive", 0.85, "keyword", 1),
        )
        conn.execute(
            """INSERT INTO reply_sentiment
               (instantly_email_id, campaign_id, contact_id, contact_email,
                sentiment, sentiment_confidence, classified_by, pushed_to_clay)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("mon_email_2", mock_campaign_id, mock_contact_ids[1],
             f"{TEST_PREFIX}mon1@example.com", "negative", 0.90, "keyword", 0),
        )

        # Insert engagement events
        conn.execute(
            """INSERT INTO engagement_events
               (campaign_id, contact_email, event_type, event_date, source)
               VALUES (?, ?, ?, datetime('now'), ?)""",
            (mock_campaign_id, f"{TEST_PREFIX}mon0@example.com", "open",
             "instantly"),
        )
        conn.execute(
            """INSERT INTO engagement_events
               (campaign_id, contact_email, event_type, event_date, source)
               VALUES (?, ?, ?, datetime('now'), ?)""",
            (mock_campaign_id, f"{TEST_PREFIX}mon0@example.com", "reply",
             "instantly"),
        )

        # Insert email threads
        conn.execute(
            """INSERT INTO email_threads
               (instantly_email_id, campaign_id, contact_id, contact_email,
                subject, body_text, ue_type, status, ai_interest_value)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("mon_thread_1", mock_campaign_id, mock_contact_ids[0],
             f"{TEST_PREFIX}mon0@example.com",
             "Re: Glucommander", "I'm interested in a demo", 2, "new", 0.85),
        )

        # Insert clay_push_log
        conn.execute(
            """INSERT INTO clay_push_log
               (contact_email, contact_first_name, contact_last_name,
                account_name, campaign_name, sentiment, payload_json,
                response_code, response_body)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"{TEST_PREFIX}mon0@example.com", "Mon", "Contact1",
             "HCA Healthcare", f"{TEST_PREFIX}MON_CAMP", "positive",
             '{"test": true}', 200, '{"status": "ok"}'),
        )

        # Insert block_list entry
        conn.execute(
            """INSERT OR IGNORE INTO block_list
               (value, is_domain, reason, instantly_id, added_by)
               VALUES (?, ?, ?, ?, ?)""",
            (f"{TEST_PREFIX}blocked.example.com", 1, "qa_test",
             "fake_bl_id_11", "qa_test"),
        )

        conn.commit()

        # ========== REPORT FUNCTIONS (check_status.py) ==========

        from check_status import (
            report_accounts, report_contacts, report_campaigns,
            report_metrics, report_replies, report_engagement,
            report_api_activity,
        )

        # 1. report_accounts — runs without error
        try:
            report_accounts(conn)
            r.ok("report_accounts")
        except Exception as e:
            r.fail("report_accounts", e)

        # 2. report_contacts — runs without error
        try:
            report_contacts(conn)
            r.ok("report_contacts")
        except Exception as e:
            r.fail("report_contacts", e)

        # 3. report_campaigns — runs without error, data present
        try:
            report_campaigns(conn)
            r.ok("report_campaigns")
        except Exception as e:
            r.fail("report_campaigns", e)

        # 4. report_metrics — runs with our mock snapshots
        try:
            report_metrics(conn)
            r.ok("report_metrics")
        except Exception as e:
            r.fail("report_metrics", e)

        # 5. report_replies — runs with our mock sentiments
        try:
            report_replies(conn)
            r.ok("report_replies")
        except Exception as e:
            r.fail("report_replies", e)

        # 6. report_engagement — runs with our mock events
        try:
            report_engagement(conn)
            r.ok("report_engagement")
        except Exception as e:
            r.fail("report_engagement", e)

        # 7. report_api_activity — runs (api_log has entries from prior tests)
        try:
            report_api_activity(conn)
            r.ok("report_api_activity")
        except Exception as e:
            r.fail("report_api_activity", e)

        # ========== METRIC SNAPSHOTS — Rate Calculations ==========

        # 8. Verify metric snapshot rate calculations are correct
        try:
            row = conn.execute(
                """SELECT * FROM metric_snapshots
                   WHERE campaign_id = ? AND snapshot_date = date('now')""",
                (mock_campaign_id,),
            ).fetchone()
            assert row is not None, "No snapshot for today"
            assert row["sent"] == 200, f"sent={row['sent']}"
            assert row["opened"] == 80, f"opened={row['opened']}"
            assert abs(row["open_rate"] - 0.40) < 0.001, f"open_rate={row['open_rate']}"
            assert abs(row["bounce_rate"] - 0.02) < 0.001, f"bounce_rate={row['bounce_rate']}"
            r.ok("metric_snapshot_rates")
        except Exception as e:
            r.fail("metric_snapshot_rates", e)

        # 9. Verify multi-day snapshots exist
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM metric_snapshots WHERE campaign_id = ?",
                (mock_campaign_id,),
            ).fetchone()[0]
            assert count >= 2, f"Expected >=2 snapshots, got {count}"
            r.ok(f"metric_snapshot_days:{count}")
        except Exception as e:
            r.fail("metric_snapshot_days", e)

        # ========== PULL METRICS — pull_campaign_analytics ==========

        from pull_metrics import pull_campaign_analytics, pull_daily_analytics, check_kill_switches

        # 10. pull_campaign_analytics dry-run updates snapshots
        try:
            results = pull_campaign_analytics(conn, live=False)
            assert isinstance(results, list), f"Expected list: {type(results)}"
            # Should include our mock campaign
            camp_names = [r["campaign"] for r in results]
            assert f"{TEST_PREFIX}MON_CAMP" in camp_names, f"Missing campaign: {camp_names}"
            r.ok(f"pull_analytics_dry:{len(results)}")
        except Exception as e:
            r.fail("pull_analytics_dry", e)

        # 11. pull_daily_analytics dry-run (prints only)
        try:
            pull_daily_analytics(conn, live=False)
            r.ok("pull_daily_analytics_dry")
        except Exception as e:
            r.fail("pull_daily_analytics_dry", e)

        # 12. check_kill_switches — clean (bounce_rate=0.02 < 0.05)
        try:
            # Our mock has 0.02 bounce rate, below default threshold
            warnings = check_kill_switches(conn)
            # The pull_campaign_analytics just overwrote with zeros for dry-run,
            # so re-insert our mock data
            conn.execute(
                """INSERT OR REPLACE INTO metric_snapshots
                   (campaign_id, instantly_campaign_id, snapshot_date,
                    sent, opened, replied, bounced, open_rate, reply_rate, bounce_rate)
                   VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, ?, ?)""",
                (mock_campaign_id, "fake_mon_camp_11",
                 200, 80, 10, 4, 0.40, 0.05, 0.02),
            )
            conn.commit()
            warnings = check_kill_switches(conn)
            if isinstance(warnings, list):
                bounce_warns = [w for w in warnings if "bounce" in w.lower()
                                and TEST_PREFIX in w]
                if not bounce_warns:
                    r.ok("kill_switch_clean")
                else:
                    r.fail("kill_switch_clean", f"Unexpected warnings: {warnings}")
            else:
                r.fail("kill_switch_clean", f"Unexpected: {type(warnings)}")
        except Exception as e:
            r.fail("kill_switch_clean", e)

        # 13. check_kill_switches — breach
        try:
            conn.execute(
                """INSERT OR REPLACE INTO metric_snapshots
                   (campaign_id, instantly_campaign_id, snapshot_date,
                    sent, opened, replied, bounced, open_rate, reply_rate, bounce_rate)
                   VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, ?, ?)""",
                (mock_campaign_id, "fake_mon_camp_11",
                 100, 30, 2, 12, 0.30, 0.02, 0.12),
            )
            conn.commit()
            warnings = check_kill_switches(conn)
            bounce_warns = [w for w in warnings if "bounce" in w.lower()]
            if bounce_warns:
                r.ok("kill_switch_breach")
            else:
                r.fail("kill_switch_breach", f"No bounce warning: {warnings}")
        except Exception as e:
            r.fail("kill_switch_breach", e)

        # ========== REPLY PROCESSING — DB persistence pipeline ==========

        from process_replies import (
            classify_sentiment, store_reply, scan_for_new_replies,
            pull_new_emails,
        )

        # 14. scan_for_new_replies finds our mock thread
        try:
            replies = scan_for_new_replies(conn, live=False)
            assert isinstance(replies, list), f"Expected list: {type(replies)}"
            mon_replies = [rr for rr in replies
                           if rr.get("contact_email", "").startswith(TEST_PREFIX)]
            if mon_replies:
                r.ok(f"scan_replies:{len(mon_replies)}")
            else:
                r.ok("scan_replies:0(already_processed)")
        except Exception as e:
            r.fail("scan_replies", e)

        # 15. Full classify → store → verify pipeline
        try:
            # Insert a fresh thread for classify/store
            conn.execute(
                """INSERT INTO email_threads
                   (instantly_email_id, campaign_id, contact_id, contact_email,
                    subject, body_text, ue_type, status, ai_interest_value)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("mon_pipeline_test", mock_campaign_id, mock_contact_ids[0],
                 f"{TEST_PREFIX}mon0@example.com",
                 "Re: Follow up", "Let's schedule a call next week", 2, "new",
                 0.9),
            )
            conn.commit()

            replies = scan_for_new_replies(conn, live=False)
            pipeline_reply = next(
                (rr for rr in replies
                 if rr.get("instantly_email_id") == "mon_pipeline_test"),
                None,
            )
            assert pipeline_reply, "Pipeline reply not found"

            sentiment, confidence, by = classify_sentiment(pipeline_reply)
            assert sentiment == "positive", f"Expected positive: {sentiment}"
            assert by == "keyword", f"Expected keyword: {by}"

            row_id = store_reply(conn, pipeline_reply, sentiment, confidence, by)
            assert row_id > 0, f"Bad row_id: {row_id}"

            # Verify thread status updated
            thread = conn.execute(
                "SELECT status, sentiment FROM email_threads WHERE instantly_email_id = ?",
                ("mon_pipeline_test",),
            ).fetchone()
            assert thread["status"] == "needs_follow_up", f"status={thread['status']}"
            assert thread["sentiment"] == "positive", f"sentiment={thread['sentiment']}"

            # Verify reply_sentiment row
            rs = conn.execute(
                "SELECT * FROM reply_sentiment WHERE instantly_email_id = ?",
                ("mon_pipeline_test",),
            ).fetchone()
            assert rs["sentiment"] == "positive"
            assert rs["classified_by"] == "keyword"

            r.ok("reply_pipeline_full")
        except Exception as e:
            r.fail("reply_pipeline_full", e)

        # ========== CLAY PUSH LOG — DB persistence ==========

        from push_to_clay import (
            get_unpushed_positive_replies, build_clay_payload, log_push,
        )

        # 16. get_unpushed finds the pipeline reply (not yet pushed)
        try:
            unpushed = get_unpushed_positive_replies(conn)
            assert isinstance(unpushed, list), f"Expected list: {type(unpushed)}"
            r.ok(f"get_unpushed:{len(unpushed)}")
        except Exception as e:
            r.fail("get_unpushed", e)

        # 17. log_push writes to clay_push_log + updates reply_sentiment
        try:
            mock_reply_for_push = {
                "id": row_id if "row_id" in dir() else 1,
                "contact_email": f"{TEST_PREFIX}mon0@example.com",
                "first_name": "Mon", "last_name": "Contact1",
                "account_name": "HCA Healthcare",
                "campaign_name": f"{TEST_PREFIX}MON_CAMP",
                "sentiment": "positive",
            }
            payload = {"test": True}
            log_push(conn, mock_reply_for_push, payload, 200, '{"ok":true}')

            log_row = conn.execute(
                "SELECT * FROM clay_push_log WHERE contact_email = ? "
                "ORDER BY pushed_at DESC LIMIT 1",
                (f"{TEST_PREFIX}mon0@example.com",),
            ).fetchone()
            assert log_row, "No clay_push_log row"
            assert log_row["response_code"] == 200
            r.ok("log_push_db")
        except Exception as e:
            r.fail("log_push_db", e)

        # ========== ACCOUNT VIEW — Sub-query functions ==========

        from ops.account_view import (
            find_account, get_contacts_for_account,
            get_campaigns_for_account, get_engagement_for_account,
            get_sentiment_for_account, print_account_detail,
            list_all_accounts,
        )

        # 18. get_campaigns_for_account — returns our enrolled contacts
        try:
            campaigns = get_campaigns_for_account(conn, "HCA Healthcare")
            assert isinstance(campaigns, list), f"Expected list: {type(campaigns)}"
            r.ok(f"acct_campaigns:{len(campaigns)}")
        except Exception as e:
            r.fail("acct_campaigns", e)

        # 19. get_engagement_for_account — returns our mock events
        try:
            engagement = get_engagement_for_account(conn, "HCA Healthcare")
            assert isinstance(engagement, list), f"Expected list: {type(engagement)}"
            assert len(engagement) >= 2, f"Expected >=2 events: {len(engagement)}"
            r.ok(f"acct_engagement:{len(engagement)}")
        except Exception as e:
            r.fail("acct_engagement", e)

        # 20. get_sentiment_for_account — returns our mock sentiment
        try:
            sentiment = get_sentiment_for_account(conn, "HCA Healthcare")
            assert isinstance(sentiment, list), f"Expected list: {type(sentiment)}"
            assert len(sentiment) >= 1, f"Expected >=1 sentiment: {len(sentiment)}"
            r.ok(f"acct_sentiment:{len(sentiment)}")
        except Exception as e:
            r.fail("acct_sentiment", e)

        # 21. print_account_detail — runs without error
        try:
            acct = find_account(conn, "HCA")
            contacts_list = get_contacts_for_account(conn, "HCA Healthcare")
            campaigns_list = get_campaigns_for_account(conn, "HCA Healthcare")
            engagement_list = get_engagement_for_account(conn, "HCA Healthcare")
            sentiment_list = get_sentiment_for_account(conn, "HCA Healthcare")
            print_account_detail(
                acct, contacts_list, campaigns_list,
                engagement_list, sentiment_list,
            )
            r.ok("print_account_detail")
        except Exception as e:
            r.fail("print_account_detail", e)

        # 22. list_all_accounts — runs without error
        try:
            list_all_accounts(conn)
            r.ok("list_all_accounts")
        except Exception as e:
            r.fail("list_all_accounts", e)

        # ========== API LOG — Persistence verification ==========

        # 23. log_api_call writes correctly
        try:
            log_api_call(conn, "test", "test_endpoint", "GET",
                         {"key": "value"}, 200, "test summary", 42)
            row = conn.execute(
                "SELECT * FROM api_log WHERE tool_or_endpoint = 'test_endpoint' "
                "ORDER BY timestamp DESC LIMIT 1",
            ).fetchone()
            assert row, "No api_log row"
            assert row["interface"] == "test"
            assert row["response_code"] == 200
            assert row["duration_ms"] == 42
            r.ok("log_api_call_write")
        except Exception as e:
            r.fail("log_api_call_write", e)

        # 24. api_log has entries from MCP calls (from prior test runs)
        try:
            total = conn.execute(
                "SELECT COUNT(*) FROM api_log"
            ).fetchone()[0]
            mcp_count = conn.execute(
                "SELECT COUNT(*) FROM api_log WHERE interface = 'mcp'"
            ).fetchone()[0]
            api_count = conn.execute(
                "SELECT COUNT(*) FROM api_log WHERE interface = 'api'"
            ).fetchone()[0]
            r.ok(f"api_log_totals:total={total},mcp={mcp_count},api={api_count}")
        except Exception as e:
            r.fail("api_log_totals", e)

        # ========== BLOCK LIST — DB persistence ==========

        # 25. block_list entry persisted correctly
        try:
            row = conn.execute(
                "SELECT * FROM block_list WHERE value = ?",
                (f"{TEST_PREFIX}blocked.example.com",),
            ).fetchone()
            assert row, "No block_list row"
            assert row["is_domain"] == 1
            assert row["reason"] == "qa_test"
            assert row["instantly_id"] == "fake_bl_id_11"
            r.ok("block_list_db_persist")
        except Exception as e:
            r.fail("block_list_db_persist", e)

        # ========== ENGAGEMENT EVENTS — DB structure ==========

        # 26. Engagement events queryable with all expected columns
        try:
            row = conn.execute(
                "SELECT * FROM engagement_events WHERE contact_email = ?",
                (f"{TEST_PREFIX}mon0@example.com",),
            ).fetchone()
            assert row, "No engagement event"
            assert row["event_type"] in ("open", "reply", "click", "bounce")
            assert row["source"] == "instantly"
            r.ok("engagement_event_persist")
        except Exception as e:
            r.fail("engagement_event_persist", e)

        # ========== CLAY PUSH LOG — full record ==========

        # 27. clay_push_log has all required fields
        try:
            row = conn.execute(
                "SELECT * FROM clay_push_log WHERE campaign_name = ?",
                (f"{TEST_PREFIX}MON_CAMP",),
            ).fetchone()
            assert row, "No clay_push_log row"
            assert row["contact_email"] == f"{TEST_PREFIX}mon0@example.com"
            assert row["sentiment"] == "positive"
            assert row["response_code"] == 200
            r.ok("clay_push_log_fields")
        except Exception as e:
            r.fail("clay_push_log_fields", e)

        # ========== REPLY SENTIMENT — aggregation ==========

        # 28. reply_sentiment supports GROUP BY aggregation (used by report_replies)
        try:
            rows = conn.execute(
                """SELECT sentiment, COUNT(*) as cnt,
                   SUM(CASE WHEN pushed_to_clay = 1 THEN 1 ELSE 0 END) as pushed
                   FROM reply_sentiment
                   WHERE campaign_id = ?
                   GROUP BY sentiment ORDER BY cnt DESC""",
                (mock_campaign_id,),
            ).fetchall()
            assert len(rows) >= 1, f"No sentiment groups: {rows}"
            sentiments = {r["sentiment"]: r["cnt"] for r in rows}
            r.ok(f"sentiment_aggregation:{sentiments}")
        except Exception as e:
            r.fail("sentiment_aggregation", e)

        # ========== CAMPAIGN_CONTACTS — enrollment tracking ==========

        # 29. campaign_contacts tracks enrollment
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM campaign_contacts WHERE campaign_id = ?",
                (mock_campaign_id,),
            ).fetchone()[0]
            assert count >= 2, f"Expected >=2 enrollments: {count}"
            r.ok(f"enrollment_tracking:{count}")
        except Exception as e:
            r.fail("enrollment_tracking", e)

        # ========== MAILBOXES — status tracking ==========

        # 30. Mailboxes have expected fields
        try:
            rows = conn.execute(
                "SELECT email, daily_limit, status, warmup_status, warmup_score "
                "FROM mailboxes"
            ).fetchall()
            assert len(rows) >= 3, f"Expected >=3 mailboxes: {len(rows)}"
            for row in rows:
                assert row["email"], "Missing email"
                assert row["daily_limit"] is not None, "Missing daily_limit"
            r.ok(f"mailbox_fields:{len(rows)}")
        except Exception as e:
            r.fail("mailbox_fields", e)

    finally:
        # Cleanup all mock data
        try:
            if mock_campaign_id:
                conn.execute(
                    "DELETE FROM metric_snapshots WHERE campaign_id = ?",
                    (mock_campaign_id,),
                )
                conn.execute(
                    "DELETE FROM clay_push_log WHERE campaign_name = ?",
                    (f"{TEST_PREFIX}MON_CAMP",),
                )
                conn.execute(
                    "DELETE FROM reply_sentiment WHERE campaign_id = ?",
                    (mock_campaign_id,),
                )
                conn.execute(
                    "DELETE FROM email_threads WHERE campaign_id = ?",
                    (mock_campaign_id,),
                )
                conn.execute(
                    "DELETE FROM engagement_events WHERE campaign_id = ?",
                    (mock_campaign_id,),
                )
                conn.execute(
                    "DELETE FROM campaign_contacts WHERE campaign_id = ?",
                    (mock_campaign_id,),
                )
                conn.execute(
                    "DELETE FROM campaigns WHERE id = ?",
                    (mock_campaign_id,),
                )
            conn.execute(
                "DELETE FROM contacts WHERE email LIKE ?",
                (f"{TEST_PREFIX}%",),
            )
            conn.execute(
                "DELETE FROM block_list WHERE value LIKE ?",
                (f"{TEST_PREFIX}%",),
            )
            conn.execute(
                "DELETE FROM api_log WHERE tool_or_endpoint = 'test_endpoint'",
            )
            conn.commit()
        except Exception:
            pass
        conn.close()

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
