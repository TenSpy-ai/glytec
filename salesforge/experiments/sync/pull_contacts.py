"""Weekly full contact sync from Salesforge."""

import sys
import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import SalesforgeClient
from db import get_conn


def pull_contacts():
    """Sync all contacts from Salesforge — updates salesforge_lead_id on local records."""
    client = SalesforgeClient(dry_run=False)
    conn = get_conn()

    try:
        all_contacts = []
        offset = 0
        while True:
            data = client.list_contacts(limit=50, offset=offset)
            batch = data.get("data", [])
            all_contacts.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        matched = 0
        new_sf_only = 0
        for c in all_contacts:
            email = c.get("email", "").lower()
            sf_id = c.get("id")
            if not email:
                continue

            # Try to match to local contact
            local = conn.execute(
                "SELECT id FROM contacts WHERE LOWER(email) = ?", (email,)
            ).fetchone()
            if local:
                conn.execute(
                    "UPDATE contacts SET salesforge_lead_id = ?, last_pushed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (sf_id, local["id"]),
                )
                matched += 1
            else:
                new_sf_only += 1

        conn.commit()

        conn.execute(
            """INSERT OR REPLACE INTO sync_state (entity, last_synced_at, total_records, notes, updated_at)
               VALUES ('contacts', ?, ?, ?, CURRENT_TIMESTAMP)""",
            (datetime.datetime.now().isoformat(), len(all_contacts),
             f"matched={matched}, sf_only={new_sf_only}"),
        )
        conn.commit()

        print(f"[sync:contacts] {len(all_contacts)} Salesforge contacts, {matched} matched locally, {new_sf_only} SF-only")

    finally:
        conn.close()


if __name__ == "__main__":
    pull_contacts()
