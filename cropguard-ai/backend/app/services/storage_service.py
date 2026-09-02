"""
Image storage — MongoDB GridFS.

Replaces Supabase Storage. Scan images are written to a GridFS bucket in the
same database as everything else, which means one thing to run, one thing to
back up, and no second set of credentials.

GridFS rather than a plain document because a document is capped at 16 MB and
a phone camera JPEG can approach that; GridFS chunks transparently and streams
on read. GridFS rather than local disk because the rest of the app's state
already lives in Mongo, and a disk path is one more thing that has to survive a
redeploy.

Two behaviours are kept deliberately identical to the old Supabase bucket, so
nothing downstream had to change:

* `image_url` is an **absolute** URL. `next/image` resolves a relative path
  against the frontend's origin (:3000), not the API's (:8000), so a relative
  path would 404 in the browser even though the bytes were stored fine.
* The read endpoint is unauthenticated, exactly as the old bucket was public.
  `<img src>` cannot send a bearer header, and the previous design relied on
  scan ids being unguessable UUID4s. See app/api/images.py — that tradeoff is
  documented there, and it is the one thing in this module worth revisiting
  before a real deployment.
"""

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.services.mongo_client import _collection, get_client

_ALLOWED_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

# One bucket, so `fs.files`/`fs.chunks` don't collide with any future use.
BUCKET = "crop_images"


class StorageError(Exception):
    pass


def _extension_for(content_type: str | None) -> str:
    return _ALLOWED_EXT.get(content_type or "", "jpg")


def _bucket() -> AsyncIOMotorGridFSBucket:
    settings = get_settings()
    return AsyncIOMotorGridFSBucket(
        get_client()[settings.mongodb_db], bucket_name=BUCKET
    )


async def upload_scan_image(
    *, user_id: str, field_id: str, scan_id: str, content: bytes, content_type: str | None
) -> str:
    """Store the image and return the URL the frontend should render.

    The filename keeps the old "<user_id>/<field_id>/<scan_id>.<ext>" layout.
    It is no longer load-bearing for authorization the way the storage policies
    made it, but it still makes a stray file self-describing when someone is
    looking at the bucket by hand.
    """
    settings = get_settings()
    ext = _extension_for(content_type)
    path = f"{user_id}/{field_id}/{scan_id}.{ext}"

    try:
        # A re-scan reusing a scan_id would otherwise leave two files with the
        # same name and GridFS would serve the older one.
        await delete_scan_image(path)
        await _bucket().upload_from_stream(
            path,
            content,
            metadata={
                "user_id": user_id,
                "field_id": field_id,
                "scan_id": scan_id,
                "content_type": content_type or "image/jpeg",
            },
        )
    except PyMongoError as e:
        raise StorageError(
            f"Image upload failed. Check that MongoDB is running at "
            f"{settings.mongodb_uri}. ({e})"
        ) from e

    return f"{settings.api_base_url.rstrip('/')}/api/images/{path}"


async def open_scan_image(path: str) -> tuple[bytes, str]:
    """Return (bytes, content_type) for a stored image, or raise StorageError."""
    try:
        stream = await _bucket().open_download_stream_by_name(path)
        data = await stream.read()
    except PyMongoError as e:
        # Motor raises NoFile (a PyMongoError subclass) for a missing name, so
        # the caller can't distinguish "gone" from "server down" here. The route
        # turns this into a 404, which is the right answer for an <img> either
        # way — a broken image beats a 500 page.
        raise StorageError(f"Image not found: {path} ({e})") from e
    content_type = (stream.metadata or {}).get("content_type", "image/jpeg")
    return data, content_type


async def delete_scan_image(path: str) -> None:
    """Remove every file stored under this name. Silent when there is none."""
    files = _collection(f"{BUCKET}.files")
    async for doc in files.find({"filename": path}, {"_id": 1}):
        await _bucket().delete(doc["_id"])
