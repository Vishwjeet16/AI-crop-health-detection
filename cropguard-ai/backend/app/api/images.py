"""
Serves scan images out of GridFS.

Unauthenticated by design, and worth being explicit about why: this replaces a
*public* Supabase Storage bucket, and the thing that renders these URLs is an
`<img>` tag, which cannot send an Authorization header. The protection is that
a path contains a UUID4 scan id — unguessable, but a leaked URL stays valid.

That was already true before this migration; it is not a regression. If these
images ever need to be genuinely private, the fix is short-lived signed URLs
minted by the scan routes, not a bearer check here, because the browser still
won't send one.
"""

from fastapi import APIRouter, HTTPException, Response

from app.services.storage_service import StorageError, open_scan_image

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("/{path:path}")
async def get_scan_image(path: str):
    """`path` is "<user_id>/<field_id>/<scan_id>.<ext>" — matched whole, via
    `:path`, because it contains slashes."""
    try:
        data, content_type = await open_scan_image(path)
    except StorageError:
        raise HTTPException(404, "Image not found.")
    return Response(
        content=data,
        media_type=content_type,
        # Immutable: a scan id is never reused, so the bytes at a given URL
        # never change. Saves re-fetching the photo on every history view.
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
