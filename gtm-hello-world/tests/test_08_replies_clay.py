"""
Test 08 — Reply Processing & Clay Push
Sentiment classification + Clay push with mock DB data. No Instantly calls.
"""

from tests.helpers import TestResult, ensure_db_seeded, TEST_PREFIX


def run() -> TestResult:
    r = TestResult("test_08_replies_clay — Reply Processing & Clay Push")
    ensure_db_seeded()

    from db import get_conn
    from process_replies import (
        classify_sentiment, store_reply, scan_for_new_replies, triage_reply,
    )
    from push_to_clay import (
        get_unpushed_positive_replies, build_clay_payload, push_to_clay, log_push,
    )
    from pull_metrics import pull_campaign_analytics, check_kill_switches

    conn = get_conn()
    mock_campaign_id = None
    mock_contact_id = None

    try:
        # --- Setup mock data ---
        conn.execute(
            "INSERT INTO campaigns (name, instantly_campaign_id, status) VALUES (?, ?, ?)",
            (f"{TEST_PREFIX}REPLY_CAMP", "fake_camp_reply_08", "active"),
        )
        mock_campaign_id = conn.execute(
            "SELECT id FROM campaigns WHERE name = ?", (f"{TEST_PREFIX}REPLY_CAMP",)
        ).fetchone()["id"]

        conn.execute(
            """INSERT OR IGNORE INTO contacts
               (first_name, last_name, email, title, account_name,
                icp_category, icp_intent_score, icp_department, icp_job_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("QA", "Reply08", f"{TEST_PREFIX}reply08@example.com",
             "CFO", "QA Test Health", "Decision Maker", 90, "Finance", "Executive"),
        )
        mock_contact_id = conn.execute(
            "SELECT id FROM contacts WHERE email = ?", (f"{TEST_PREFIX}reply08@example.com",)
        ).fetchone()["id"]
        conn.commit()

        # --- classify_sentiment: positive keyword ---
        try:
            s, c, by = classify_sentiment({"body_text": "I'm interested in a demo", "ai_interest_value": None})
            if s == "positive" and c == 0.85 and by == "keyword":
                r.ok("classify_positive_keyword")
            else:
                r.fail("classify_positive_keyword", f"Got ({s}, {c}, {by})")
        except Exception as e:
            r.fail("classify_positive_keyword", e)

        # --- classify_sentiment: negative keyword ---
        try:
            s, c, by = classify_sentiment({"body_text": "Not interested, remove me please", "ai_interest_value": None})
            if s == "negative" and c == 0.90 and by == "keyword":
                r.ok("classify_negative_keyword")
            else:
                r.fail("classify_negative_keyword", f"Got ({s}, {c}, {by})")
        except Exception as e:
            r.fail("classify_negative_keyword", e)

        # --- classify_sentiment: OOO keyword ---
        try:
            s, c, by = classify_sentiment({"body_text": "I am out of office until next week", "ai_interest_value": None})
            if s == "ooo" and c == 0.95 and by == "keyword":
                r.ok("classify_ooo_keyword")
            else:
                r.fail("classify_ooo_keyword", f"Got ({s}, {c}, {by})")
        except Exception as e:
            r.fail("classify_ooo_keyword", e)

        # --- classify_sentiment: neutral AI ---
        try:
            s, c, by = classify_sentiment({"body_text": "thanks", "ai_interest_value": 0.5})
            if s == "neutral" and by == "ai":
                r.ok("classify_neutral_ai")
            else:
                r.fail("classify_neutral_ai", f"Got ({s}, {c}, {by})")
        except Exception as e:
            r.fail("classify_neutral_ai", e)

        # --- classify_sentiment: positive AI ---
        try:
            s, c, by = classify_sentiment({"body_text": "ok sure", "ai_interest_value": 0.85})
            if s == "positive" and by == "ai":
                r.ok("classify_positive_ai")
            else:
                r.fail("classify_positive_ai", f"Got ({s}, {c}, {by})")
        except Exception as e:
            r.fail("classify_positive_ai", e)

        # --- classify_sentiment: negative AI ---
        try:
            s, c, by = classify_sentiment({"body_text": "hmm", "ai_interest_value": 0.1})
            if s == "negative" and by == "ai":
                r.ok("classify_negative_ai")
            else:
                r.fail("classify_negative_ai", f"Got ({s}, {c}, {by})")
        except Exception as e:
            r.fail("classify_negative_ai", e)

        # --- classify_sentiment: no score ---
        try:
            s, c, by = classify_sentiment({"body_text": "ok", "ai_interest_value": None})
            if s == "neutral" and c == 0.5:
                r.ok("classify_no_score")
            else:
                r.fail("classify_no_score", f"Got ({s}, {c}, {by})")
        except Exception as e:
            r.fail("classify_no_score", e)

        # --- store_reply ---
        try:
            # Insert a mock email thread first
            conn.execute(
                """INSERT INTO email_threads
                   (instantly_email_id, campaign_id, contact_id, contact_email,
                    subject, body_text, ue_type, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("fake_email_08", mock_campaign_id, mock_contact_id,
                 f"{TEST_PREFIX}reply08@example.com",
                 "Re: QA Test", "I'm interested in a demo", 2, "new"),
            )
            conn.commit()
            thread_id = conn.execute(
                "SELECT id FROM email_threads WHERE instantly_email_id = 'fake_email_08'"
            ).fetchone()["id"]

            mock_reply = {
                "id": thread_id,
                "instantly_email_id": "fake_email_08",
                "campaign_id": mock_campaign_id,
                "contact_id": mock_contact_id,
                "contact_email": f"{TEST_PREFIX}reply08@example.com",
                "body_text": "I'm interested in a demo",
                "ai_interest_value": 0.85,
            }

            row_id = store_reply(conn, mock_reply, "positive", 0.85, "keyword")
            if row_id and row_id > 0:
                r.ok("store_reply")
            else:
                r.fail("store_reply", f"Bad row_id: {row_id}")

            # Verify thread status updated
            thread = conn.execute(
                "SELECT status, sentiment FROM email_threads WHERE id = ?", (thread_id,)
            ).fetchone()
            if thread["status"] == "needs_follow_up" and thread["sentiment"] == "positive":
                r.ok("store_reply_updates_thread")
            else:
                r.fail("store_reply_updates_thread",
                        f"status={thread['status']}, sentiment={thread['sentiment']}")
        except Exception as e:
            r.fail("store_reply", e)

        # --- scan_for_new_replies (without live=False — just scans DB) ---
        try:
            # Insert another new reply
            conn.execute(
                """INSERT INTO email_threads
                   (instantly_email_id, campaign_id, contact_id, contact_email,
                    subject, body_text, ue_type, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("fake_email_08b", mock_campaign_id, mock_contact_id,
                 f"{TEST_PREFIX}reply08@example.com",
                 "Re: Follow up", "Let's schedule a call", 2, "new"),
            )
            conn.commit()

            replies = scan_for_new_replies(conn, live=False)
            if isinstance(replies, list) and len(replies) >= 1:
                r.ok(f"scan_for_new_replies:{len(replies)}")
            else:
                r.fail("scan_for_new_replies", f"Expected >=1 replies: {replies}")
        except Exception as e:
            r.fail("scan_for_new_replies", e)

        # --- triage_reply positive ---
        try:
            output = triage_reply("positive", "test@example.com")
            if "Clay push" in output or "follow-up" in output:
                r.ok("triage_positive")
            else:
                r.fail("triage_positive", f"Output: {output}")
        except Exception as e:
            r.fail("triage_positive", e)

        # --- triage_reply negative ---
        try:
            output = triage_reply("negative", "test@example.com")
            if "block list" in output or "handled" in output:
                r.ok("triage_negative")
            else:
                r.fail("triage_negative", f"Output: {output}")
        except Exception as e:
            r.fail("triage_negative", e)

        # --- build_clay_payload ---
        try:
            mock_reply_data = {
                "contact_email": "test@example.com",
                "first_name": "QA", "last_name": "Test",
                "title": "CFO", "account_name": "QA Health",
                "campaign_name": "Test Campaign", "recipe": "R4",
                "campaign_id": 1, "sentiment": "positive",
                "sentiment_confidence": 0.85,
                "icp_department": "Finance", "icp_intent_score": 90,
            }
            payload = build_clay_payload(mock_reply_data)
            if all(k in payload for k in ("contact", "campaign", "engagement")):
                r.ok("build_clay_payload")
            else:
                r.fail("build_clay_payload", f"Missing keys: {payload.keys()}")
        except Exception as e:
            r.fail("build_clay_payload", e)

        # --- push_to_clay dry-run ---
        try:
            code, body = push_to_clay({"test": True}, live=False)
            if code == 200 and "dry_run" in body:
                r.ok("push_to_clay_dry_run")
            else:
                r.fail("push_to_clay_dry_run", f"Got ({code}, {body})")
        except Exception as e:
            r.fail("push_to_clay_dry_run", e)

        # --- get_unpushed_positive_replies ---
        try:
            unpushed = get_unpushed_positive_replies(conn)
            if isinstance(unpushed, list):
                r.ok(f"get_unpushed:{len(unpushed)}")
            else:
                r.fail("get_unpushed", f"Unexpected: {type(unpushed)}")
        except Exception as e:
            r.fail("get_unpushed", e)

        # --- log_push ---
        try:
            if unpushed:
                reply_for_push = unpushed[0]
            else:
                reply_for_push = {
                    "id": row_id, "contact_email": f"{TEST_PREFIX}reply08@example.com",
                    "first_name": "QA", "last_name": "Reply08",
                    "account_name": "QA Test Health", "campaign_name": f"{TEST_PREFIX}REPLY_CAMP",
                    "sentiment": "positive",
                }
            test_payload = {"test": True}
            log_push(conn, reply_for_push, test_payload, 200, '{"status":"dry_run"}')

            log_row = conn.execute(
                "SELECT * FROM clay_push_log WHERE contact_email = ?",
                (f"{TEST_PREFIX}reply08@example.com",),
            ).fetchone()
            if log_row:
                r.ok("log_push")
            else:
                r.fail("log_push", "No row in clay_push_log")
        except Exception as e:
            r.fail("log_push", e)

        # --- pull_campaign_analytics dry-run ---
        # Run this BEFORE kill switch tests so INSERT OR REPLACE doesn't clobber our test data
        try:
            results = pull_campaign_analytics(conn, live=False)
            if isinstance(results, list):
                r.ok(f"pull_analytics_dry:{len(results)}")
            else:
                r.fail("pull_analytics_dry", f"Unexpected: {type(results)}")
        except Exception as e:
            r.fail("pull_analytics_dry", e)

        # --- check_kill_switches clean ---
        # After pull_analytics inserts zeros, kill switches should be clean
        # (zero sent → no rate violations)
        try:
            warnings = check_kill_switches(conn)
            if isinstance(warnings, list):
                r.ok(f"kill_switches_clean:{len(warnings)}_warnings")
            else:
                r.fail("kill_switches_clean", f"Unexpected: {type(warnings)}")
        except Exception as e:
            r.fail("kill_switches_clean", e)

        # --- check_kill_switches breach ---
        # Now overwrite with high-bounce data AFTER clean check
        # Use date('now') to match check_kill_switches SQL (SQLite UTC)
        try:
            conn.execute(
                """INSERT OR REPLACE INTO metric_snapshots
                   (campaign_id, instantly_campaign_id, snapshot_date, sent, bounced, bounce_rate)
                   VALUES (?, ?, date('now'), ?, ?, ?)""",
                (mock_campaign_id, "fake_camp_reply_08", 100, 10, 0.10),
            )
            conn.commit()
            warnings = check_kill_switches(conn)
            if any("bounce" in w.lower() for w in warnings):
                r.ok("kill_switches_breach")
            else:
                r.fail("kill_switches_breach", f"No bounce warning in: {warnings}")
        except Exception as e:
            r.fail("kill_switches_breach", e)

    finally:
        # Cleanup mock data
        try:
            if mock_campaign_id:
                conn.execute("DELETE FROM metric_snapshots WHERE campaign_id = ?", (mock_campaign_id,))
                conn.execute("DELETE FROM clay_push_log WHERE campaign_name LIKE ?",
                             (f"{TEST_PREFIX}%",))
                conn.execute("DELETE FROM reply_sentiment WHERE campaign_id = ?", (mock_campaign_id,))
                conn.execute("DELETE FROM email_threads WHERE campaign_id = ?", (mock_campaign_id,))
                conn.execute("DELETE FROM campaigns WHERE id = ?", (mock_campaign_id,))
            conn.execute("DELETE FROM contacts WHERE email LIKE ?", (f"{TEST_PREFIX}%",))
            conn.commit()
        except Exception:
            pass
        conn.close()

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
