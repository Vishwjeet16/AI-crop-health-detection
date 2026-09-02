"""
Tests for the MongoDB access layer.

Split in two on purpose:

* The query-dialect parsers (`_parse_filter`, `_parse_sort`, `_parse_projection`)
  and `_insert_defaults` are pure functions, so they are tested offline and
  always run. These carry the actual risk in this module — a filter that is
  parsed wrong serves another farmer's documents, and a default that isn't
  applied writes a row Postgres would have completed.
* The round-trip tests need a real mongod. They skip rather than fail when one
  isn't running, so the suite stays green on a machine (or CI runner) without
  MongoDB, and they use a throwaway database named per-run so they can never
  touch the developer's real `cropguard` data.

Run with: pytest backend/tests/test_mongo_client.py -v
"""

import uuid

import pytest
import pytest_asyncio

from app.services import mongo_client as mc
from app.services.mongo_client import DatabaseError

# --- Query dialect (offline) -------------------------------------------------


def test_eq_filter_is_stripped_to_a_plain_equality():
    assert mc._parse_filter({"user_id": "eq.abc"}) == {"user_id": "abc"}


def test_reserved_keys_are_not_treated_as_filters():
    """`order`/`limit`/`select` are query options, not columns. Leaking one into
    the filter would match zero documents and look like missing data."""
    params = {"user_id": "eq.abc", "order": "created_at.desc", "limit": "3", "select": "*"}
    assert mc._parse_filter(params) == {"user_id": "abc"}


def test_multiple_filters_are_all_applied():
    parsed = mc._parse_filter({"id": "eq.1", "user_id": "eq.2"})
    assert parsed == {"id": "1", "user_id": "2"}


@pytest.mark.parametrize("value", ["neq.abc", "gt.5", "in.(a,b)", "abc", "", "like.*x*"])
def test_an_unimplemented_operator_raises_instead_of_being_dropped(value):
    """The most important test in this file.

    A filter this layer didn't understand and silently discarded would widen
    the query from one farmer's rows to every farmer's rows. Failing loudly is
    the only acceptable behaviour.
    """
    with pytest.raises(DatabaseError) as exc:
        mc._parse_filter({"user_id": value})
    assert exc.value.status_code == 500


def test_eq_value_may_contain_dots_and_the_word_eq():
    """UUIDs and emails contain characters the parser must not choke on."""
    assert mc._parse_filter({"email": "eq.eq.user@example.com"}) == {
        "email": "eq.user@example.com"
    }


def test_empty_eq_value_is_allowed():
    """`eq.` with nothing after it is a filter for the empty string, which is a
    real value in this schema (`location` defaults to '')."""
    assert mc._parse_filter({"location": "eq."}) == {"location": ""}


def test_sort_defaults_to_ascending_and_reads_desc():
    assert mc._parse_sort("created_at.desc") == [("created_at", mc.DESCENDING)]
    assert mc._parse_sort("created_at.asc") == [("created_at", mc.ASCENDING)]
    assert mc._parse_sort("name") == [("name", mc.ASCENDING)]
    assert mc._parse_sort(None) is None
    assert mc._parse_sort("") is None


def test_projection_always_suppresses_mongos_own_id():
    """`_id` is Mongo's, not part of this API. If it ever leaks, responses stop
    matching the schemas and the frontend gets a field it can't read."""
    assert mc._parse_projection("*")["_id"] == 0
    assert mc._parse_projection(None)["_id"] == 0
    assert mc._parse_projection("name,crop")["_id"] == 0


def test_projection_lists_the_requested_columns():
    assert mc._parse_projection("timestamp,severity,risk") == {
        "_id": 0, "timestamp": 1, "severity": 1, "risk": 1,
    }
    # Whitespace in the select list is tolerated.
    assert mc._parse_projection(" name , crop ") == {"_id": 0, "name": 1, "crop": 1}


# --- Insert defaults (offline) ----------------------------------------------


def test_insert_defaults_fill_in_what_postgres_ddl_used_to():
    row = mc._insert_defaults("fields", {"user_id": "u1", "name": "A"})
    assert uuid.UUID(row["id"])  # a real UUID, as a string
    assert isinstance(row["id"], str)
    assert row["health_status"] == "healthy"
    assert row["created_at"] and row["updated_at"]


def test_insert_defaults_never_overwrite_a_supplied_value():
    """scans.py supplies its own id and timestamp so the image path and the row
    agree. A default that clobbered them would break the image URL."""
    row = mc._insert_defaults("scans", {"id": "fixed-id", "timestamp": "2026-01-01T00:00:00+00:00"})
    assert row["id"] == "fixed-id"
    assert row["timestamp"] == "2026-01-01T00:00:00+00:00"


def test_users_get_no_generated_id():
    """A profile id is the auth provider's uid. Generating one here would create
    an orphan row that the authenticated user can never read back."""
    row = mc._insert_defaults("users", {"name": "No id"})
    assert "id" not in row
    assert row["language"] == "en"


def test_false_defaults_are_applied_not_skipped():
    """`read: False` and `is_demo` are falsy — a truthiness check would leave
    them unset instead of set."""
    assert mc._insert_defaults("alerts", {"user_id": "u"})["read"] is False
    assert mc._insert_defaults("scans", {})["is_demo"] is True


def test_an_explicit_false_survives_the_defaults_pass():
    assert mc._insert_defaults("scans", {"is_demo": False})["is_demo"] is False


def test_timestamps_sort_lexicographically_in_chronological_order():
    """The reason they are stored as ISO-8601 UTC strings: `order=created_at.desc`
    is a string sort in Mongo, and it has to mean "newest first"."""
    first = mc._now()
    second = mc._now()
    assert first <= second
    assert mc._now().endswith("+00:00")


def test_an_unknown_collection_gets_no_defaults_rather_than_an_error():
    assert mc._insert_defaults("not_a_collection", {"a": 1}) == {"a": 1}


# --- Round trip (needs a live mongod) ---------------------------------------


@pytest_asyncio.fixture
async def scratch_db(monkeypatch):
    """Point the module at a throwaway database, and drop it afterwards.

    Skips the test when no mongod answers, so this file is safe to run on a
    machine without MongoDB installed.

    The `_client = None` reset is a test-only concern: motor binds a client to
    the event loop that created it, and pytest-asyncio gives every test a fresh
    loop, so a cached client from the previous test raises "Event loop is
    closed". The running server has one loop for its whole lifetime, which is
    why the module caches at all.
    """
    mc._client = None
    if not await mc.ping():
        pytest.skip(f"no MongoDB at {mc.settings.mongodb_uri}")
    name = f"cropguard_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(mc.settings, "mongodb_db", name)
    try:
        yield name
    finally:
        await mc.get_client().drop_database(name)
        mc._client.close()
        mc._client = None


@pytest.mark.asyncio
async def test_insert_then_select_round_trips_without_exposing_mongos_id(scratch_db):
    await mc.db_insert("fields", {"user_id": "u1", "name": "A", "crop": "Tomato",
                                 "area": 1.0, "latitude": 20.0, "longitude": 73.0})
    rows = await mc.db_select("fields", {"user_id": "eq.u1", "select": "*"})
    assert len(rows) == 1
    assert "_id" not in rows[0]
    assert rows[0]["health_status"] == "healthy"


@pytest.mark.asyncio
async def test_select_filters_by_user_and_does_not_return_another_users_rows(scratch_db):
    for owner in ("u1", "u1", "u2"):
        await mc.db_insert("fields", {"user_id": owner, "name": owner, "crop": "C",
                                      "area": 1.0, "latitude": 0.0, "longitude": 0.0})
    assert len(await mc.db_select("fields", {"user_id": "eq.u1"})) == 2
    assert len(await mc.db_select("fields", {"user_id": "eq.u2"})) == 1
    assert await mc.db_select("fields", {"user_id": "eq.nobody"}) == []


@pytest.mark.asyncio
async def test_order_and_limit_return_the_newest_rows(scratch_db):
    for i in range(4):
        await mc.db_insert("scans", {"user_id": "u1", "field_id": "f1", "crop": "C",
                                     "image_url": "x", "severity": {}, "risk": {},
                                     "recommendation": {}, "timestamp": f"2026-01-0{i + 1}T00:00:00+00:00"})
    rows = await mc.db_select("scans", {"user_id": "eq.u1", "order": "timestamp.desc", "limit": "2"})
    assert [r["timestamp"][:10] for r in rows] == ["2026-01-04", "2026-01-03"]


@pytest.mark.asyncio
async def test_update_returns_the_new_document_and_bumps_updated_at(scratch_db):
    row = await mc.db_insert("fields", {"user_id": "u1", "name": "A", "crop": "C",
                                        "area": 1.0, "latitude": 0.0, "longitude": 0.0})
    updated = await mc.db_update("fields", {"id": row["id"]}, {"health_status": "high"})
    assert updated["health_status"] == "high"
    assert updated["updated_at"] >= row["updated_at"]
    assert "_id" not in updated


@pytest.mark.asyncio
async def test_update_scoped_to_another_user_is_a_404_not_a_silent_success(scratch_db):
    """alerts.py updates with {"id": ..., "user_id": ...} as its authorization
    check. If a non-matching user_id updated the row anyway, one farmer could
    mark another's alerts read."""
    row = await mc.db_insert("alerts", {"user_id": "u1", "field_id": "f1",
                                        "message": "m", "severity": "high"})
    with pytest.raises(DatabaseError) as exc:
        await mc.db_update("alerts", {"id": row["id"], "user_id": "someone-else"}, {"read": True})
    assert exc.value.status_code == 404
    assert (await mc.db_select("alerts", {"id": f"eq.{row['id']}"}))[0]["read"] is False


@pytest.mark.asyncio
async def test_a_duplicate_id_is_a_409(scratch_db):
    await mc.ensure_indexes()
    await mc.db_insert("users", {"id": "uid-1", "name": "A"})
    with pytest.raises(DatabaseError) as exc:
        await mc.db_insert("users", {"id": "uid-1", "name": "B"})
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_ensure_indexes_is_safe_to_run_twice(scratch_db):
    """It runs on every startup, so a second call must not raise."""
    await mc.ensure_indexes()
    await mc.ensure_indexes()
    names = await mc._collection("scans").index_information()
    assert {"user_id_i", "field_id_i", "id_u"} <= set(names)
