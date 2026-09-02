"""
Tests for GridFS image storage and the route that serves it.

These need a live mongod (GridFS is not meaningfully fakeable) and skip when
there isn't one, same as test_mongo_client.py. Everything runs against a
throwaway database so a developer's real scan images are never touched.

What's actually being guarded:

* The URL is absolute. A relative one stores fine and then 404s in the browser,
  because next/image resolves it against :3000 instead of the API's :8000 —
  a bug that only shows up on screen, never in a backend test.
* Re-uploading the same scan_id leaves one file, not two. GridFS allows
  duplicate filenames and `open_download_stream_by_name` picks a version, so
  without the delete-first step a re-scan could serve the previous photo next
  to the new detections.
* A missing image is a 404. An <img> pointing at a 500 is the same broken
  picture, but it pages whoever is watching error rates.

Run with: pytest backend/tests/test_image_storage.py -v
"""

import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.config import get_settings
from app.services import mongo_client as mc
from app.services import storage_service as ss

# Smallest valid PNG: 1x1, transparent.
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


@pytest_asyncio.fixture
async def scratch_db(monkeypatch):
    """Throwaway database, and a fresh motor client bound to this test's loop.

    See the same fixture in test_mongo_client.py for why `_client` is reset —
    motor ties a client to the loop that created it.
    """
    mc._client = None
    if not await mc.ping():
        pytest.skip(f"no MongoDB at {mc.settings.mongodb_uri}")
    name = f"cropguard_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(mc.settings, "mongodb_db", name)
    monkeypatch.setattr(get_settings(), "mongodb_db", name)
    try:
        yield name
    finally:
        await mc.get_client().drop_database(name)
        mc._client.close()
        mc._client = None


async def _upload(scan_id: str, content: bytes = PNG) -> str:
    return await ss.upload_scan_image(
        user_id="u1", field_id="f1", scan_id=scan_id,
        content=content, content_type="image/png",
    )


def test_extension_comes_from_the_content_type():
    assert ss._extension_for("image/png") == "png"
    assert ss._extension_for("image/webp") == "webp"
    # An unknown or absent type falls back to jpg rather than raising: the
    # detection result matters more than the file suffix.
    assert ss._extension_for("image/gif") == "jpg"
    assert ss._extension_for(None) == "jpg"


@pytest.mark.asyncio
async def test_upload_returns_an_absolute_url_the_browser_can_resolve(scratch_db):
    url = await _upload(str(uuid.uuid4()))
    assert url.startswith("http://")
    assert "/api/images/u1/f1/" in url and url.endswith(".png")


@pytest.mark.asyncio
async def test_bytes_and_content_type_survive_the_round_trip(scratch_db):
    url = await _upload(str(uuid.uuid4()))
    data, content_type = await ss.open_scan_image(url.split("/api/images/", 1)[1])
    assert data == PNG
    assert content_type == "image/png"


@pytest.mark.asyncio
async def test_reuploading_the_same_scan_id_replaces_rather_than_duplicates(scratch_db):
    scan_id = str(uuid.uuid4())
    url = await _upload(scan_id)
    path = url.split("/api/images/", 1)[1]
    await _upload(scan_id, PNG + b"second")

    files = mc._collection(f"{ss.BUCKET}.files")
    assert await files.count_documents({"filename": path}) == 1
    data, _ = await ss.open_scan_image(path)
    assert data == PNG + b"second"


@pytest.mark.asyncio
async def test_metadata_records_who_the_image_belongs_to(scratch_db):
    """Not used for authorization, but it is what makes a stray file in the
    bucket traceable back to a farmer and a field."""
    scan_id = str(uuid.uuid4())
    path = (await _upload(scan_id)).split("/api/images/", 1)[1]
    doc = await mc._collection(f"{ss.BUCKET}.files").find_one({"filename": path})
    assert doc["metadata"]["user_id"] == "u1"
    assert doc["metadata"]["field_id"] == "f1"
    assert doc["metadata"]["scan_id"] == scan_id


@pytest.mark.asyncio
async def test_a_missing_image_raises_storage_error(scratch_db):
    with pytest.raises(ss.StorageError):
        await ss.open_scan_image("u1/f1/never-stored.png")


@pytest.mark.asyncio
async def test_delete_is_idempotent(scratch_db):
    path = (await _upload(str(uuid.uuid4()))).split("/api/images/", 1)[1]
    await ss.delete_scan_image(path)
    await ss.delete_scan_image(path)  # must not raise
    with pytest.raises(ss.StorageError):
        await ss.open_scan_image(path)


@pytest.mark.asyncio
async def test_a_large_image_survives_gridfs_chunking(scratch_db):
    """The reason for GridFS over a plain document: chunking past 16 MB. This
    only crosses the 255 KB default chunk size, which is enough to prove the
    reassembly path is exercised rather than a single-chunk shortcut."""
    big = PNG + b"\x00" * (600 * 1024)
    path = (await _upload(str(uuid.uuid4()), big)).split("/api/images/", 1)[1]
    data, _ = await ss.open_scan_image(path)
    assert data == big
    assert await mc._collection(f"{ss.BUCKET}.chunks").count_documents({}) > 1


# --- The HTTP route ---------------------------------------------------------
#
# These two are sync tests on purpose. TestClient runs the app in its own event
# loop on a portal thread, and a motor client built in the test's loop cannot be
# used from that one ("attached to a different loop"). Driving the setup through
# asyncio.run() and clearing the cached client in between means each loop builds
# its own, which is also what happens in production — one client per process.


@pytest.fixture
def scratch_db_sync(monkeypatch):
    import asyncio

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

    if not run(mc.ping):
        pytest.skip(f"no MongoDB at {mc.settings.mongodb_uri}")
    try:
        yield run
    finally:
        # An `async def`, not a lambda: a lambda body calling get_client() would
        # be evaluated before asyncio.run() starts the loop motor needs.
        async def drop():
            await mc.get_client().drop_database(name)

        run(drop)


def test_the_route_serves_the_image_without_a_token(scratch_db_sync):
    """Unauthenticated on purpose — an <img> cannot send a bearer header, and
    this replaces a public bucket. Documented in app/api/images.py."""
    from app.main import app

    url = scratch_db_sync(lambda: _upload(str(uuid.uuid4())))
    path = url.split("/api/images/", 1)[1]
    mc._client = None
    with TestClient(app) as client:
        resp = client.get(f"/api/images/{path}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content == PNG
    assert "immutable" in resp.headers["cache-control"]


def test_the_route_404s_for_an_unknown_path(scratch_db_sync):
    from app.main import app

    mc._client = None
    with TestClient(app) as client:
        resp = client.get("/api/images/u1/f1/missing.png")
    assert resp.status_code == 404
    assert resp.json() == {"status": "error", "error": "Image not found."}
