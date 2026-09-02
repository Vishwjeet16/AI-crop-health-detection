from fastapi import Header, HTTPException, status

from app.services.mongo_client import DatabaseError, db_insert, db_select
from app.services.supabase_client import SupabaseError, auth_get_user


def _profile_row_from_auth_user(auth_user: dict) -> dict:
    """Build a users row from whatever the auth record carries.

    Google/OAuth users have Google's metadata keys (`full_name`, `name`),
    password users have whatever register() put in `data`. Take the first
    thing that looks like a name rather than assuming one shape.
    """
    metadata = auth_user.get("user_metadata") or {}
    name = (
        metadata.get("name")
        or metadata.get("full_name")
        or (auth_user.get("email") or "").split("@")[0]
        or "Farmer"
    )
    return {
        "id": auth_user["id"],
        "name": name,
        "location": metadata.get("location") or "",
        "language": metadata.get("language") or "en",
        "phone": auth_user.get("phone") or metadata.get("phone") or None,
        "email": auth_user.get("email"),
    }


async def ensure_profile(auth_user: dict) -> dict:
    """Return the caller's profile row, creating it if it doesn't exist yet.

    With Postgres gone this is now the *only* thing that creates a profile row:
    the old signup trigger in database/schema.sql lived in DDL that MongoDB has
    no equivalent for. That is an improvement rather than a gap — the trigger
    never fired for users created before it was installed, and it wasn't
    guaranteed to have landed for an OAuth user by the time the callback hit
    this API, which produced a 404 from every protected route. Provisioning on
    first authenticated request has no such window.
    """
    user_id = auth_user["id"]
    rows = await db_select("users", {"id": f"eq.{user_id}", "select": "*"})
    if rows:
        return rows[0]

    row = _profile_row_from_auth_user(auth_user)
    try:
        return await db_insert("users", row)
    except DatabaseError:
        # Most likely two concurrent first requests racing on the unique index
        # — re-read rather than failing the request.
        rows = await db_select("users", {"id": f"eq.{user_id}", "select": "*"})
        if rows:
            return rows[0]
        raise


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """Resolves the caller's Supabase auth user + profile row.

    Every protected route depends on this. It validates the bearer token
    against Supabase Auth (GoTrue) rather than decoding the JWT locally, so
    revoked/expired sessions are always caught even without sharing the
    Supabase JWT signing secret with this service.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid Authorization header.")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid Authorization header.")

    try:
        auth_user = await auth_get_user(token)
    except SupabaseError as e:
        # 5xx from Supabase is not the caller's fault — don't log them out over it.
        if e.status_code >= 500:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))

    if not auth_user.get("id"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session.")

    try:
        profile = await ensure_profile(auth_user)
    except DatabaseError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Could not load profile: {e}")

    profile["auth_email"] = auth_user.get("email")
    return profile
