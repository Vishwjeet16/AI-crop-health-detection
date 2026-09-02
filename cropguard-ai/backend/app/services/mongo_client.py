"""
MongoDB access layer.

Replaces the PostgREST half of the old Supabase client. The three functions
below deliberately keep the *shape* of the calls the API layer already makes —
a filter dict of `{"column": "eq.<value>"}` plus optional `order`, `limit` and
`select` — so the six route modules that use them needed an import swap and
nothing else. A storage swap shouldn't turn into a rewrite of every endpoint's
query logic.

Three choices worth knowing about:

* Timestamps are stored as ISO-8601 UTC strings, not BSON datetimes, because
  that is what PostgREST returned and every consumer downstream — the pydantic
  schemas, the assistant's context formatter, the frontend — was written
  against strings. ISO-8601 UTC also sorts lexicographically in chronological
  order, and sorting is the only thing this app does with them.
* `id` is an explicit UUID string field. Mongo's own `_id` is never exposed, so
  API responses stay byte-identical to the Postgres ones and nothing
  downstream had to learn about ObjectId.
* An unsupported filter operator raises instead of being ignored. Silently
  dropping a filter here would mean serving another farmer's rows, which is
  the worst failure this module could have.

Postgres enforced defaults, `gen_random_uuid()` and an `updated_at` trigger in
DDL. Mongo has no DDL, so `_DEFAULTS` and `_insert_defaults()` below carry
that responsibility instead — the API layer was written assuming the database
fills these in.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import get_settings

logger = logging.getLogger("mongo")
settings = get_settings()

_client: AsyncIOMotorClient | None = None


class DatabaseError(Exception):
    """Same shape as the old SupabaseError so route-level handlers are unchanged."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Defaults Postgres used to apply in DDL. Callables are evaluated per insert.
# `users` has no `id` default on purpose: a profile id is the auth provider's
# uid, so an absent one is a bug worth failing on rather than papering over.
_DEFAULTS: dict[str, dict[str, Any]] = {
    "users": {"language": "en", "created_at": _now, "updated_at": _now},
    "fields": {"id": uuid.uuid4, "health_status": "healthy", "created_at": _now,
               "updated_at": _now, "last_scan_at": None, "last_disease": None,
               "last_risk": None},
    "scans": {"id": uuid.uuid4, "is_demo": True, "timestamp": _now, "created_at": _now},
    "alerts": {"id": uuid.uuid4, "read": False, "created_at": _now},
    "weather": {"id": uuid.uuid4, "created_at": _now},
}

# Collections and the fields worth indexing. Every query in this app filters by
# id or by user_id (and scans additionally by field_id), so these three cover
# it. `id` is unique because the API treats it as a primary key.
_INDEXES: dict[str, list[tuple[str, bool]]] = {
    "users": [("id", True)],
    "fields": [("id", True), ("user_id", False)],
    "scans": [("id", True), ("user_id", False), ("field_id", False)],
    "alerts": [("id", True), ("user_id", False)],
    "weather": [("id", True), ("field_id", False)],
}


def get_client() -> AsyncIOMotorClient:
    """Lazily build the client so importing this module never opens a socket.

    Motor resolves the topology in the background, so this does not block and a
    down server surfaces at query time as a timeout rather than at import.
    """
    global _client
    if _client is None:
        if not settings.mongodb_uri:
            raise DatabaseError(
                "The server has no database configured — set MONGODB_URI in "
                "backend/.env and restart the API.",
                503,
            )
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            uuidRepresentation="standard",
            serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
        )
    return _client


def _collection(name: str):
    return get_client()[settings.mongodb_db][name]


# --- Query dialect ----------------------------------------------------------

_RESERVED = {"order", "limit", "offset", "select"}


def _parse_filter(params: dict[str, str]) -> dict[str, Any]:
    """Turn `{"user_id": "eq.abc"}` into `{"user_id": "abc"}`.

    Only `eq.` is implemented, because it is the only operator the API layer
    uses. Anything else raises: a filter this function didn't understand and
    quietly discarded would widen the query to every user's documents.
    """
    query: dict[str, Any] = {}
    for key, raw in params.items():
        if key in _RESERVED:
            continue
        value = str(raw)
        if not value.startswith("eq."):
            raise DatabaseError(
                f"Unsupported filter {key}={value!r}. This layer implements only "
                "'eq.'; add the operator to _parse_filter rather than leaving the "
                "filter to be dropped.",
                500,
            )
        query[key] = value[3:]
    return query


def _parse_sort(order: str | None) -> list[tuple[str, int]] | None:
    """`"created_at.desc"` -> `[("created_at", DESCENDING)]`."""
    if not order:
        return None
    column, _, direction = order.partition(".")
    if not column:
        return None
    return [(column, DESCENDING if direction.lower().startswith("desc") else ASCENDING)]


def _parse_projection(select: str | None) -> dict[str, int]:
    """`_id` is always suppressed — it is Mongo's, not part of this API."""
    if not select or select.strip() == "*":
        return {"_id": 0}
    projection = {"_id": 0}
    for column in (c.strip() for c in select.split(",")):
        if column:
            projection[column] = 1
    return projection


# --- Public API -------------------------------------------------------------


def _wrap(operation: str, e: Exception) -> DatabaseError:
    """One place where driver failures become an actionable message.

    A server that isn't running is by far the most common cause here, and the
    driver's own text for it ("ServerSelectionTimeoutError: localhost:27017:
    [WinError 10061]") reads as a crash rather than as something to fix.
    """
    logger.error("Mongo %s failed: %s", operation, e)
    return DatabaseError(
        f"Database {operation} failed. Check that MongoDB is running at "
        f"{settings.mongodb_uri} and reachable from this server.",
        503,
    )


def _insert_defaults(collection: str, doc: dict) -> dict:
    row = dict(doc)
    for key, default in _DEFAULTS.get(collection, {}).items():
        if key not in row or row[key] is None:
            value = default() if callable(default) else default
            row[key] = str(value) if isinstance(value, uuid.UUID) else value
    return row


async def db_select(collection: str, params: dict | None = None) -> list[dict]:
    params = params or {}
    cursor = _collection(collection).find(
        _parse_filter(params), _parse_projection(params.get("select"))
    )
    sort = _parse_sort(params.get("order"))
    if sort:
        cursor = cursor.sort(sort)
    if params.get("limit"):
        cursor = cursor.limit(int(params["limit"]))
    if params.get("offset"):
        cursor = cursor.skip(int(params["offset"]))
    try:
        return await cursor.to_list(length=None)
    except PyMongoError as e:
        raise _wrap("select", e) from e


async def db_insert(collection: str, doc: dict) -> dict:
    row = _insert_defaults(collection, doc)
    try:
        await _collection(collection).insert_one(dict(row))
    except DuplicateKeyError as e:
        raise DatabaseError("A record with these details already exists.", 409) from e
    except PyMongoError as e:
        raise _wrap("insert", e) from e
    row.pop("_id", None)  # insert_one mutates the dict it is given
    return row


async def db_update(collection: str, match: dict, patch: dict) -> dict:
    """Returns the updated document, or raises 404 — mirrors rest_update().

    `match` is a plain equality dict here (not the `eq.` dialect), because that
    is how the API layer already called rest_update().
    """
    changes = {k: v for k, v in patch.items() if k != "_id"}
    if collection in ("users", "fields"):
        changes["updated_at"] = _now()
    try:
        row = await _collection(collection).find_one_and_update(
            match, {"$set": changes}, projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as e:
        raise _wrap("update", e) from e
    if row is None:
        raise DatabaseError("Not found", 404)
    return row


async def ensure_indexes() -> None:
    """Called once at startup. Safe to re-run; Mongo ignores existing indexes."""
    for collection, specs in _INDEXES.items():
        for field, unique in specs:
            await _collection(collection).create_index(
                [(field, ASCENDING)], unique=unique, name=f"{field}_{'u' if unique else 'i'}"
            )


async def ping() -> bool:
    try:
        await get_client().admin.command("ping")
        return True
    except (PyMongoError, DatabaseError):
        return False



