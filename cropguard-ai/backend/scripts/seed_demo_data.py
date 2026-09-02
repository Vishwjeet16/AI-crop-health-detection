"""
Seed a demo farmer account + sample fields/alerts into MongoDB, for local
development or an SIH demo rehearsal that needs real backend data instead
of the frontend's built-in mock layer.

Usage (from backend/):

    python -m scripts.seed_demo_data                 # seeds against the auth
                                                     # provider's demo account
    python -m scripts.seed_demo_data --user-id UID   # seeds against a uid you
                                                     # already signed in as

Safe to re-run — it looks up the demo user first and reuses it instead of
creating duplicates.

About `--user-id`: every row is scoped by `user_id`, and the API only ever
returns rows matching the *authenticated* caller's uid. So seeded data is only
visible if the uid here is the uid you log in as. When the auth provider can't
be driven from a script — or you just want to load your own already-created
account with data — sign in, copy your uid, and pass it.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.config import get_settings
from app.services.mongo_client import db_insert, db_select, ping

DEMO_EMAIL = "demo.farmer@cropguard.test"
DEMO_PASSWORD = "cropguard-demo-1"
DEMO_NAME = "Ramesh Patil"
DEMO_LOCATION = "Nashik, Maharashtra"

# Used when no auth provider is configured. Fixed rather than random so
# re-running the script tops up the same account instead of creating a new
# orphan every time.
OFFLINE_DEMO_UID = "demo-farmer-offline"


async def _admin_headers() -> dict:
    settings = get_settings()
    return {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
    }


async def get_or_create_demo_user() -> str:
    """Create the demo account in Supabase Auth and return its uid.

    Supabase-specific, and the only part of this script that is: it goes away
    with the rest of the Supabase auth layer, at which point `--user-id` (or a
    Firebase equivalent of this function) is how you seed.
    """
    settings = get_settings()
    async with httpx.AsyncClient(timeout=15) as client:
        # Admin list-users supports filtering by email in recent GoTrue versions.
        resp = await client.get(
            f"{settings.supabase_url}/auth/v1/admin/users",
            headers=await _admin_headers(),
            params={"email": DEMO_EMAIL},
        )
        existing = resp.json().get("users", []) if resp.status_code < 400 else []
        if existing:
            print(f"Demo user already exists: {existing[0]['id']}")
            return existing[0]["id"]

        resp = await client.post(
            f"{settings.supabase_url}/auth/v1/admin/users",
            headers=await _admin_headers(),
            json={
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD,
                "email_confirm": True,
                "user_metadata": {
                    "name": DEMO_NAME,
                    "location": DEMO_LOCATION,
                    "language": "en",
                },
            },
        )
    if resp.status_code >= 400:
        raise RuntimeError(f"Could not create demo user: {resp.text}")
    user_id = resp.json()["id"]
    print(f"Created demo user: {user_id}")
    return user_id


async def ensure_demo_profile(user_id: str) -> None:
    existing = await db_select("users", {"id": f"eq.{user_id}", "select": "id"})
    if existing:
        return

    await db_insert(
        "users",
        {
            "id": user_id,
            "name": DEMO_NAME,
            "email": DEMO_EMAIL,
            "phone": None,
            "location": DEMO_LOCATION,
            "language": "en",
        },
    )
    print("Created demo profile row.")


async def seed_fields(user_id: str) -> list[dict]:
    existing = await db_select("fields", {"user_id": f"eq.{user_id}", "select": "id,name"})
    if existing:
        print(f"{len(existing)} fields already exist for demo user — skipping field seed.")
        return existing

    fields_to_create = [
        {"name": "Field A", "crop": "Tomato", "area": 2.1, "latitude": 19.9975, "longitude": 73.7898},
        {"name": "Field B", "crop": "Cotton", "area": 3.4, "latitude": 20.005, "longitude": 73.775},
        {"name": "Field C", "crop": "Soybean", "area": 1.6, "latitude": 19.99, "longitude": 73.80},
    ]
    created = []
    for f in fields_to_create:
        row = await db_insert("fields", {**f, "user_id": user_id, "health_status": "healthy"})
        created.append(row)
        print(f"Created field: {row['name']} ({row['id']})")
    return created


async def seed_alert(user_id: str, field: dict):
    # Re-running used to stack up a second, third, fourth copy of the same
    # alert, which then showed as an inflated "active alerts" count on the
    # dashboard. The fields seed already guarded against this; the alert didn't.
    existing = await db_select(
        "alerts", {"user_id": f"eq.{user_id}", "field_id": f"eq.{field['id']}", "select": "id"}
    )
    if existing:
        print(f"An alert already exists for {field['name']} — skipping alert seed.")
        return

    await db_insert(
        "alerts",
        {
            "user_id": user_id,
            "field_id": field["id"],
            "message": f"High disease risk detected in {field['name']}.",
            "severity": "high",
            "read": False,
        },
    )
    print(f"Seeded a demo alert for {field['name']}.")


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--user-id",
        help="Seed against this uid instead of creating/looking up a demo account. "
             "Use the uid you actually log in as — rows are only visible to their owner.",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not await ping():
        raise SystemExit(
            f"No MongoDB at {settings.mongodb_uri}. Start mongod (or fix MONGODB_URI "
            "in backend/.env) and run this again."
        )

    if args.user_id:
        user_id = args.user_id.strip()
        print(f"Seeding against the supplied uid: {user_id}")
    elif settings.supabase_url and settings.supabase_service_key:
        user_id = await get_or_create_demo_user()
    else:
        # No auth provider configured yet. Still worth seeding: the data layer
        # and every screen that reads it can be exercised, and the rows become
        # reachable as soon as you re-run with --user-id.
        user_id = OFFLINE_DEMO_UID
        print(
            f"No auth provider configured — seeding against {user_id}.\n"
            "You will not see this data after logging in as a real account. "
            "Re-run with --user-id <your uid> once you have one."
        )

    await ensure_demo_profile(user_id)
    fields = await seed_fields(user_id)
    if fields:
        await seed_alert(user_id, fields[0])

    print(f"\nDone. Data seeded for uid {user_id}.")
    if user_id != args.user_id:
        print("Log in with:")
        print(f"  email:    {DEMO_EMAIL}")
        print(f"  password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
