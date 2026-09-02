"""
End-to-end tests for the routes that were migrated from PostgREST to MongoDB.

The point of this file is the seam the migration actually crossed: the route
modules were changed by an import swap alone, on the theory that
`db_select`/`db_insert`/`db_update` accept exactly the call shapes
`rest_select`/`rest_insert`/`rest_update` did. The unit tests in
test_mongo_client.py check that layer in isolation; these drive the real
FastAPI routes so a mismatch in a real call site — a filter the route builds,
a column a response model needs, a default the route stopped supplying —
fails here rather than on a farmer's dashboard.

Auth is stubbed via dependency_overrides. That is not a shortcut: signing in
for real requires Supabase Auth, which is the half of the migration that is
still pending, and hitting it here would make these tests depend on a network
service and a rate limit for no added coverage of the data layer.

Needs a live mongod; skips without one. Uses a throwaway database.

Run with: pytest backend/tests/test_routes_mongo.py -v
"""

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.services import mongo_client as mc

USER = {"id": "test-uid-0001", "name": "Test Farmer", "location": "Nashik",
        "language": "mr", "email": "t@f.example", "auth_email": "t@f.example"}
OTHER = {**USER, "id": "test-uid-0002"}


def _jpeg() -> bytes:
    """A real decodable JPEG, because validate_image_upload and the severity
    service both open it — a handful of magic bytes wouldn't survive either."""
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (86, 125, 70)).save(buffer, format="JPEG")
    return buffer.getvalue()


JPEG = _jpeg()


@pytest.fixture
def client(monkeypatch):
    """A TestClient whose caller is USER, talking to a throwaway database.

    `mc._client = None` before handing over: motor binds a client to the loop
    that created it, and TestClient runs the app on its own portal loop.
    """
    from app.main import app
    from app.utils.auth import get_current_user

    name = f"cropguard_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(mc.settings, "mongodb_db", name)
    monkeypatch.setattr(get_settings(), "mongodb_db", name)

    def run(coro_fn):
        mc._client = None
        try:
            return asyncio.run(coro_fn())
        finally:
            if mc._client is not None:
                mc._client.close()
            mc._client = None

    async def check():
        return await mc.ping()

    if not run(check):
        pytest.skip(f"no MongoDB at {mc.settings.mongodb_uri}")

    app.dependency_overrides[get_current_user] = lambda: USER
    mc._client = None
    try:
        with TestClient(app) as c:
            c.run = run  # for arranging rows the routes can't create themselves
            yield c
    finally:
        app.dependency_overrides.pop(get_current_user, None)

        async def drop():
            await mc.get_client().drop_database(name)

        run(drop)


def _create_field(client, name="North plot", crop="Tomato"):
    resp = client.post("/api/fields", json={
        "name": name, "crop": crop, "area_acres": 2.5,
        "latitude": 19.9975, "longitude": 73.7898,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


# --- fields -----------------------------------------------------------------


def test_create_field_returns_a_complete_field(client):
    """The insert supplies neither id nor health_status, so this also proves the
    defaults that used to live in Postgres DDL are being applied."""
    field = _create_field(client)
    assert uuid.UUID(field["id"])
    assert field["health_status"] == "healthy"
    assert field["area_acres"] == 2.5
    assert field["last_scan_at"] is None


def test_list_fields_returns_what_was_created(client):
    _create_field(client, "A")
    _create_field(client, "B")
    names = {f["name"] for f in client.get("/api/fields").json()}
    assert names == {"A", "B"}


def test_get_field_by_id(client):
    field = _create_field(client)
    resp = client.get(f"/api/fields/{field['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == field["id"]


def test_a_field_belonging_to_another_user_is_a_404_not_a_leak(client):
    """The route's authorization is the `user_id` filter it adds. If that filter
    were dropped — the failure mode mongo_client's parser refuses to allow —
    this would return 200 with another farmer's field."""
    field = _create_field(client)

    async def reassign():
        await mc.db_update("fields", {"id": field["id"]}, {"user_id": OTHER["id"]})

    client.run(reassign)

    assert client.get(f"/api/fields/{field['id']}").status_code == 404
    assert client.get("/api/fields").json() == []


def test_an_unknown_field_id_is_a_404_in_the_error_envelope(client):
    resp = client.get(f"/api/fields/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json() == {"status": "error", "error": "Field not found."}


def test_a_zero_area_is_rejected_by_the_schema_naming_the_field(client):
    resp = client.post("/api/fields", json={
        "name": "Bad", "crop": "Tomato", "area_acres": 0,
        "latitude": 0.0, "longitude": 0.0,
    })
    assert resp.status_code == 422
    assert "area_acres" in resp.json()["error"]


# --- dashboard --------------------------------------------------------------


def test_dashboard_counts_fields_by_health(client):
    healthy = _create_field(client, "Healthy")
    risky = _create_field(client, "Risky")

    async def make_risky():
        await mc.db_update("fields", {"id": risky["id"]}, {"health_status": "high"})

    client.run(make_risky)

    stats = client.get("/api/dashboard").json()["stats"]
    assert stats["total_fields"] == 2
    assert stats["healthy_fields"] == 1
    assert stats["at_risk_fields"] == 1
    assert healthy["id"] in [f["id"] for f in client.get("/api/dashboard").json()["fields"]]


def test_dashboard_on_a_brand_new_account_is_empty_rather_than_an_error(client):
    """This is the screen the user saw fail with "We couldn't load your
    dashboard". A fresh account has no rows, and that must render."""
    body = client.get("/api/dashboard").json()
    assert body["stats"] == {"total_fields": 0, "healthy_fields": 0,
                            "at_risk_fields": 0, "active_alerts": 0}
    assert body["fields"] == [] and body["recent_alerts"] == []


def test_dashboard_does_not_leak_mongos_internal_id(client):
    """`fields` is returned raw, not through a response model, so a leaked `_id`
    would reach the browser as an unserializable ObjectId."""
    _create_field(client)
    assert "_id" not in client.get("/api/dashboard").json()["fields"][0]


# --- alerts -----------------------------------------------------------------


def _create_alert(client, field_id, read=False):
    async def insert():
        return await mc.db_insert("alerts", {
            "user_id": USER["id"], "field_id": field_id,
            "message": "High disease risk detected.", "severity": "high", "read": read,
        })

    return client.run(insert)


def test_alerts_are_labelled_with_their_fields_name(client):
    field = _create_field(client, "South plot")
    _create_alert(client, field["id"])
    alert = client.get("/api/alerts").json()[0]
    assert alert["field_name"] == "South plot"
    assert alert["read"] is False


def test_an_alert_for_a_deleted_field_still_renders(client):
    """Mongo has no foreign keys, so an orphaned alert is now possible where
    Postgres would have cascaded. The route falls back to "Field" — check that
    it does, rather than raising a KeyError on the whole list."""
    _create_alert(client, str(uuid.uuid4()))
    assert client.get("/api/alerts").json()[0]["field_name"] == "Field"


def test_marking_an_alert_read_persists(client):
    field = _create_field(client)
    alert = _create_alert(client, field["id"])
    resp = client.patch(f"/api/alerts/{alert['id']}/read")
    assert resp.status_code == 200
    assert resp.json()["read"] is True
    assert client.get("/api/alerts").json()[0]["read"] is True


def test_marking_another_users_alert_read_is_a_404(client):
    """The route matches on {"id", "user_id"} together. A match that ignored
    user_id would let one farmer clear another's alerts."""
    field = _create_field(client)
    alert = _create_alert(client, field["id"])

    async def reassign():
        await mc.db_update("alerts", {"id": alert["id"]}, {"user_id": OTHER["id"]})

    client.run(reassign)

    assert client.patch(f"/api/alerts/{alert['id']}/read").status_code == 404


def test_unread_alerts_are_counted_on_the_dashboard(client):
    field = _create_field(client)
    _create_alert(client, field["id"], read=False)
    _create_alert(client, field["id"], read=True)
    assert client.get("/api/dashboard").json()["stats"]["active_alerts"] == 1


# --- the scan flow ----------------------------------------------------------
#
# POST /api/analyze is the one route that writes to three collections and
# GridFS in a single request, and the only place that supplies its own `id` and
# `timestamp` on insert (the image path and the row have to agree). If the
# migration broke a call shape anywhere, it breaks here.


def _analyze(client, field_id):
    return client.post(
        f"/api/analyze?field_id={field_id}",
        files={"file": ("leaf.jpg", JPEG, "image/jpeg")},
    )


def test_analyze_stores_a_scan_and_returns_it(client):
    field = _create_field(client)
    resp = _analyze(client, field["id"])
    assert resp.status_code == 200, resp.text
    scan = resp.json()
    assert uuid.UUID(scan["id"])
    assert scan["field_id"] == field["id"]
    assert scan["is_demo"] is True  # AI_MODE=demo
    assert scan["risk"]["level"] in {"healthy", "moderate", "high"}
    assert client.get(f"/api/scans/{scan['id']}").json()["id"] == scan["id"]


def test_the_stored_image_is_served_back_at_the_url_the_scan_reports(client):
    """The whole point of the absolute URL. A relative path would pass every
    backend assertion and still show a broken image in the browser."""
    field = _create_field(client)
    scan = _analyze(client, field["id"]).json()
    assert scan["image_url"].startswith("http://")
    path = scan["image_url"].split("/api/images/", 1)[1]
    assert path.startswith(f"{USER['id']}/{field['id']}/{scan['id']}")
    resp = client.get(f"/api/images/{path}")
    assert resp.status_code == 200
    assert resp.content == JPEG


def test_analyze_rolls_the_result_up_onto_the_field(client):
    """Step 10 of the route — the db_update call shape that replaced
    rest_update. The dashboard's health counts read this, not the scans."""
    field = _create_field(client)
    scan = _analyze(client, field["id"]).json()
    updated = client.get(f"/api/fields/{field['id']}").json()
    assert updated["last_scan_at"] == scan["timestamp"]
    assert updated["last_risk"] == scan["risk"]["level"]
    assert updated["health_status"] == scan["risk"]["level"]


def test_analyze_on_another_users_field_is_a_404(client):
    field = _create_field(client)

    async def reassign():
        await mc.db_update("fields", {"id": field["id"]}, {"user_id": OTHER["id"]})

    client.run(reassign)
    assert _analyze(client, field["id"]).status_code == 404


def test_scan_history_is_ordered_oldest_first(client):
    """`order=timestamp.asc` over ISO-8601 strings — the reason timestamps are
    stored as strings rather than BSON dates is that this sort has to be
    chronological, and in Mongo it is a plain string comparison."""
    field = _create_field(client)
    for _ in range(3):
        assert _analyze(client, field["id"]).status_code == 200
    history = client.get(f"/api/fields/{field['id']}/history").json()
    assert len(history) == 3
    timestamps = [h["date"] for h in history]
    assert timestamps == sorted(timestamps)


def test_scans_are_listed_newest_first_and_filtered_by_field(client):
    a = _create_field(client, "A")
    b = _create_field(client, "B")
    _analyze(client, a["id"])
    _analyze(client, b["id"])
    assert len(client.get("/api/scans").json()) == 2
    only_b = client.get(f"/api/scans?field_id={b['id']}").json()
    assert [s["field_id"] for s in only_b] == [b["id"]]


def test_field_risk_reflects_the_latest_scan(client):
    field = _create_field(client)
    scan = _analyze(client, field["id"]).json()
    assert client.get(f"/api/risk/{field['id']}").json() == scan["risk"]


def test_field_risk_before_any_scan_is_a_404_not_an_empty_body(client):
    field = _create_field(client)
    resp = client.get(f"/api/risk/{field['id']}")
    assert resp.status_code == 404
    assert "No scans yet" in resp.json()["error"]
