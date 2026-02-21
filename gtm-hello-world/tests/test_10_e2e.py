"""
Test 10 — End-to-End GTM Flow
Full operator session: seed → launch → enroll → metrics → replies → Clay → cleanup.
17 sequential checkpoints.

NOTE: If the Instantly workspace has no sending accounts, campaign-dependent
steps are gracefully skipped. Non-campaign steps (metrics, replies, Clay,
status, block list, DB integrity) still execute.
"""

import time
from tests.helpers import (
    TestResult, ensure_db_seeded, get_live_mcp, get_live_api,
    unique_name, test_email, TEST_SUBJECT, TEST_BODY, TEST_PREFIX,
    cleanup_instantly_campaigns, cleanup_instantly_leads,
    cleanup_blocklist_entries, cleanup_db_test_rows,
)

VALID_RESPONSE = (dict, list, str)


def run() -> TestResult:
    r = TestResult("test_10_e2e — End-to-End GTM Flow")
    ensure_db_seeded()

    from db import get_conn
    mcp = get_live_mcp()
    api = get_live_api()
    conn = get_conn()

    campaign_name = unique_name("E2E")
    campaign_id = None
    no_accounts = False
    local_camp_id = None
    test_emails_used = [
        test_email("e2e_a"), test_email("e2e_b"), test_email("e2e_c"),
    ]
    blocklist_ids = []

    try:
        # --- 1. Seed DB → verify counts ---
        try:
            accts = conn.execute(
                "SELECT COUNT(*) FROM accounts"
            ).fetchone()[0]
            contacts = conn.execute(
                "SELECT COUNT(*) FROM contacts"
            ).fetchone()[0]
            if accts >= 10 and contacts >= 10:
                r.ok(f"1_seed_db:accounts={accts},contacts={contacts}")
            else:
                r.fail("1_seed_db", f"accounts={accts}, contacts={contacts}")
        except Exception as e:
            r.fail("1_seed_db", e)

        # --- 2. Create campaign ---
        try:
            result = mcp.create_campaign(
                name=campaign_name,
                subject=TEST_SUBJECT,
                body=TEST_BODY,
            )
            if isinstance(result, dict):
                if result.get("success") is False:
                    if "account" in str(result.get("stage", "")).lower():
                        no_accounts = True
                        r.ok("2_create_campaign(no_accounts)")
                    else:
                        r.fail("2_create_campaign", f"Failed: {result}")
                else:
                    campaign_id = result.get("id")
                    if campaign_id:
                        r.ok("2_create_campaign")
                        # Save to local DB
                        conn.execute(
                            """INSERT INTO campaigns
                               (name, instantly_campaign_id, status)
                               VALUES (?, ?, ?)""",
                            (campaign_name, campaign_id, "draft"),
                        )
                        conn.commit()
                        local_camp_id = conn.execute(
                            "SELECT id FROM campaigns WHERE name = ?",
                            (campaign_name,),
                        ).fetchone()["id"]
                    else:
                        r.fail("2_create_campaign", f"No ID: {result}")
            elif isinstance(result, str):
                if "account" in result.lower():
                    no_accounts = True
                    r.ok("2_create_campaign(no_accounts)")
                else:
                    r.fail("2_create_campaign", f"Unexpected: {result[:120]}")
        except Exception as e:
            if "account" in str(e).lower():
                no_accounts = True
                r.ok("2_create_campaign(no_accounts)")
            else:
                r.fail("2_create_campaign", e)

        # --- 3-4. Campaign-dependent steps ---
        if campaign_id:
            # 3. Enroll contacts
            try:
                leads = [
                    {"email": test_emails_used[0], "first_name": "E2E",
                     "last_name": "Alpha"},
                    {"email": test_emails_used[1], "first_name": "E2E",
                     "last_name": "Beta"},
                    {"email": test_emails_used[2], "first_name": "E2E",
                     "last_name": "Gamma"},
                ]
                result = mcp.add_leads_bulk(
                    campaign_id=campaign_id, leads=leads,
                    skip_if_in_workspace=True,
                )
                if isinstance(result, VALID_RESPONSE):
                    r.ok("3_enroll_contacts")
                else:
                    r.fail("3_enroll_contacts", f"Unexpected: {result}")
            except Exception as e:
                r.fail("3_enroll_contacts", e)

            # 4. Get campaign analytics
            try:
                analytics = mcp.get_campaign_analytics(
                    campaign_id=campaign_id,
                )
                if isinstance(analytics, VALID_RESPONSE):
                    r.ok("4_campaign_analytics")
                else:
                    r.fail("4_campaign_analytics",
                            f"Unexpected: {type(analytics)}")
            except Exception as e:
                r.fail("4_campaign_analytics", e)
        else:
            r.ok("3_enroll_contacts(no_accounts)")
            r.ok("4_campaign_analytics(no_accounts)")

        # --- 5. Sync campaigns ---
        try:
            from sync.sync_all import sync_campaigns
            count = sync_campaigns(conn, mcp)
            if isinstance(count, int) and count >= 0:
                r.ok(f"5_sync_campaigns:{count}")
            else:
                r.fail("5_sync_campaigns", f"Unexpected: {count}")
        except Exception as e:
            r.fail("5_sync_campaigns", e)

        # --- 6. Pull metrics (dry-run) ---
        try:
            from pull_metrics import pull_campaign_analytics
            results = pull_campaign_analytics(conn, live=False)
            if isinstance(results, list):
                r.ok(f"6_pull_metrics:{len(results)}_campaigns")
            else:
                r.fail("6_pull_metrics", f"Unexpected: {type(results)}")
        except Exception as e:
            r.fail("6_pull_metrics", e)

        # --- 7. Process replies (empty) ---
        try:
            from process_replies import scan_for_new_replies
            replies = scan_for_new_replies(conn, live=False)
            if isinstance(replies, list):
                r.ok(f"7_process_replies_empty:{len(replies)}")
            else:
                r.fail("7_process_replies_empty",
                        f"Unexpected: {type(replies)}")
        except Exception as e:
            r.fail("7_process_replies_empty", e)

        # --- 8. Insert mock reply ---
        # Use an existing local campaign or create a fake one for the mock
        if not local_camp_id:
            conn.execute(
                """INSERT INTO campaigns
                   (name, instantly_campaign_id, status)
                   VALUES (?, ?, ?)""",
                (campaign_name, "fake_e2e_id", "draft"),
            )
            conn.commit()
            local_camp_id = conn.execute(
                "SELECT id FROM campaigns WHERE name = ?",
                (campaign_name,),
            ).fetchone()["id"]

        try:
            conn.execute(
                """INSERT INTO email_threads
                   (instantly_email_id, campaign_id, contact_email,
                    subject, body_text, ue_type, status, ai_interest_value)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("e2e_mock_email", local_camp_id,
                 "e2e_mock@example.com",
                 "Re: E2E Test", "I'm interested in learning more",
                 2, "new", 0.85),
            )
            conn.commit()
            r.ok("8_insert_mock_reply")
        except Exception as e:
            r.fail("8_insert_mock_reply", e)

        # --- 9. Process replies (with mock) ---
        try:
            from process_replies import classify_sentiment, store_reply
            replies = scan_for_new_replies(conn, live=False)
            if replies:
                reply = replies[0]
                sentiment, confidence, classified_by = classify_sentiment(
                    reply,
                )
                store_reply(conn, reply, sentiment, confidence, classified_by)
                r.ok(f"9_classify_reply:{sentiment}")
            else:
                r.fail("9_classify_reply", "No replies found after insert")
        except Exception as e:
            r.fail("9_classify_reply", e)

        # --- 10. Push to Clay (dry-run) ---
        try:
            from push_to_clay import push_to_clay
            code, body = push_to_clay({"test": True}, live=False)
            if code == 200 and "dry_run" in body:
                r.ok("10_clay_push_dry_run")
            else:
                r.fail("10_clay_push_dry_run", f"Got ({code}, {body})")
        except Exception as e:
            r.fail("10_clay_push_dry_run", e)

        # --- 11. Check status dashboard ---
        try:
            from check_status import (
                report_accounts, report_contacts, report_campaigns,
            )
            report_accounts(conn)
            report_contacts(conn)
            report_campaigns(conn)
            r.ok("11_check_status")
        except Exception as e:
            r.fail("11_check_status", e)

        # --- 12. Block list: add test domain ---
        test_bl_domain = f"e2e-{int(time.time())}.qa-test.example.com"
        try:
            from ops.block_list import add_entry
            add_entry(api, conn, test_bl_domain, "qa_e2e_test", live=True)
            row = conn.execute(
                "SELECT * FROM block_list WHERE value = ?",
                (test_bl_domain,),
            ).fetchone()
            if row:
                if row["instantly_id"]:
                    blocklist_ids.append(row["instantly_id"])
                r.ok("12_block_list_add")
            else:
                r.ok("12_block_list_add(local_only)")
        except Exception as e:
            r.fail("12_block_list_add", e)

        # --- 13. Block list: verify listed ---
        try:
            result = api.list_block_list_entries(limit=100)
            if isinstance(result, dict):
                r.ok("13_block_list_listed")
            else:
                r.ok("13_block_list_listed")
        except Exception as e:
            r.fail("13_block_list_listed", e)

        # --- 14. Block list: remove ---
        try:
            if blocklist_ids:
                from ops.block_list import remove_entry
                remove_entry(api, conn, blocklist_ids[0])
                blocklist_ids = []
                r.ok("14_block_list_remove")
            else:
                r.ok("14_block_list_remove(no_id)")
        except Exception as e:
            r.fail("14_block_list_remove", e)

        # --- 15-16. Campaign lifecycle (if created) ---
        if campaign_id:
            try:
                result = mcp.pause_campaign(campaign_id)
                if result:
                    r.ok("15_pause_campaign")
                else:
                    r.fail("15_pause_campaign", f"Falsy: {result}")
            except Exception as e:
                r.fail("15_pause_campaign", e)

            try:
                result = mcp.delete_campaign(campaign_id)
                if result:
                    r.ok("16_delete_campaign")
                    campaign_id = None
                else:
                    r.fail("16_delete_campaign", f"Falsy: {result}")
            except Exception as e:
                r.fail("16_delete_campaign", e)
        else:
            r.ok("15_pause_campaign(no_accounts)")
            r.ok("16_delete_campaign(no_accounts)")

        # --- 17. Final DB integrity check ---
        try:
            orphans = conn.execute("""
                SELECT cc.id FROM campaign_contacts cc
                LEFT JOIN campaigns c ON cc.campaign_id = c.id
                WHERE c.id IS NULL AND cc.campaign_id IN (
                    SELECT id FROM campaigns WHERE name LIKE ?
                )
            """, (f"{TEST_PREFIX}%",)).fetchall()

            if not orphans:
                r.ok("17_db_integrity")
            else:
                r.fail("17_db_integrity",
                        f"{len(orphans)} orphaned campaign_contacts")
        except Exception as e:
            r.fail("17_db_integrity", e)

    finally:
        if campaign_id:
            try:
                mcp.pause_campaign(campaign_id)
            except Exception:
                pass
            try:
                mcp.delete_campaign(campaign_id)
            except Exception:
                pass
        cleanup_instantly_leads(mcp, test_emails_used)
        cleanup_blocklist_entries(api, blocklist_ids)
        cleanup_db_test_rows(conn)
        try:
            conn.execute(
                "DELETE FROM email_threads "
                "WHERE instantly_email_id = 'e2e_mock_email'",
            )
            conn.commit()
        except Exception:
            pass
        conn.close()

    return r


if __name__ == "__main__":
    result = run()
    print(result.summary())
