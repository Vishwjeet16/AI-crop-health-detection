"""
Supabase access layer.

The backend talks to Supabase over plain HTTPS (PostgREST for table data,
GoTrue for auth) using httpx rather than the supabase-py SDK, to keep the
dependency footprint small. Table writes use the service_role key — this
process is a trusted server context, so authorization is enforced here in
the API layer (every query is scoped to the authenticated user's id) while
Postgres RLS (database/schema.sql) remains the backstop if anything ever
talks to Supabase directly.
"""

from __future__ import annotations

import httpx

from app.config import get_settings

settings = get_settings()


def _rest_headers() -> dict:
    return {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
    }


class SupabaseError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def _require_config(*, need_service_key: bool = False) -> None:
    """Fail with a clear, actionable error rather than an httpx protocol crash.

    With an empty SUPABASE_URL, httpx raises UnsupportedProtocol from deep in
    the transport layer and FastAPI turns it into a bare 500, which reads to
    the user as "login is broken" rather than "the server has no config".
    """
    missing = []
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_anon_key:
        missing.append("SUPABASE_ANON_KEY")
    if need_service_key and not settings.supabase_service_key:
        missing.append("SUPABASE_SERVICE_KEY")
    if missing:
        raise SupabaseError(
            "The server is not configured to reach Supabase — missing "
            f"{', '.join(missing)}. Set these in backend/.env and restart the API.",
            503,
        )


def _error_detail(resp: httpx.Response, default: str) -> str:
    """Pull a human-usable message out of a Supabase error response.

    GoTrue and PostgREST disagree on the field name, and an upstream proxy can
    return HTML with no JSON at all — resp.json() raises ValueError on those,
    which previously turned a bad gateway into an unhandled 500.
    """
    try:
        body = resp.json()
    except ValueError:
        return (resp.text or "").strip()[:200] or default
    if isinstance(body, dict):
        for key in ("error_description", "msg", "message", "error", "hint", "details"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return default


async def _request(method: str, url: str, **kwargs) -> httpx.Response:
    """Single place where transport failures become SupabaseError."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            return await client.request(method, url, **kwargs)
    except httpx.TimeoutException as e:
        raise SupabaseError("Supabase did not respond in time. Please try again.", 504) from e
    except httpx.HTTPError as e:
        raise SupabaseError(
            f"Could not reach Supabase ({e.__class__.__name__}). Check SUPABASE_URL "
            "and this server's network access.",
            503,
        ) from e


async def rest_select(table: str, params: dict | None = None) -> list[dict]:
    _require_config(need_service_key=True)
    resp = await _request(
        "GET",
        f"{settings.supabase_url}/rest/v1/{table}",
        headers=_rest_headers(),
        params=params or {},
    )
    if resp.status_code >= 400:
        raise SupabaseError(
            f"Supabase select failed: {_error_detail(resp, resp.text)}", resp.status_code
        )
    return resp.json()


async def rest_insert(table: str, row: dict) -> dict:
    _require_config(need_service_key=True)
    resp = await _request(
        "POST",
        f"{settings.supabase_url}/rest/v1/{table}",
        headers={**_rest_headers(), "Prefer": "return=representation"},
        json=row,
    )
    if resp.status_code >= 400:
        raise SupabaseError(
            f"Supabase insert failed: {_error_detail(resp, resp.text)}", resp.status_code
        )
    result = resp.json()
    return result[0] if isinstance(result, list) else result


async def rest_update(table: str, match: dict, patch: dict) -> dict:
    _require_config(need_service_key=True)
    params = {f"{k}": f"eq.{v}" for k, v in match.items()}
    resp = await _request(
        "PATCH",
        f"{settings.supabase_url}/rest/v1/{table}",
        headers={**_rest_headers(), "Prefer": "return=representation"},
        params=params,
        json=patch,
    )
    if resp.status_code >= 400:
        raise SupabaseError(
            f"Supabase update failed: {_error_detail(resp, resp.text)}", resp.status_code
        )
    result = resp.json()
    if not result:
        raise SupabaseError("Not found", 404)
    return result[0] if isinstance(result, list) else result


# --- Auth (GoTrue) ----------------------------------------------------------

# Substrings GoTrue uses when the project has no SMS provider configured. The
# UI leads with "mobile number", so this has to be said plainly rather than
# surfacing as a generic failure.
_PHONE_UNSUPPORTED_HINTS = (
    "phone provider",
    "sms provider",
    "unsupported phone",
    "phone_provider_disabled",
    "signups not allowed for otp",
)


def _is_email(identifier: str) -> bool:
    return "@" in identifier


def _identity_payload(email_or_phone: str) -> dict:
    """GoTrue takes either an `email` or a `phone` field, never both."""
    identifier = email_or_phone.strip()
    if _is_email(identifier):
        return {"email": identifier}
    # Strip spaces/dashes and default a bare 10-digit Indian mobile to +91, as
    # GoTrue requires E.164 and the UI's placeholder is "98765 43210".
    digits = "".join(ch for ch in identifier if ch.isdigit() or ch == "+")
    if not digits.startswith("+"):
        digits = f"+91{digits}" if len(digits) == 10 else f"+{digits}"
    return {"phone": digits}


def _auth_headers() -> dict:
    return {"apikey": settings.supabase_anon_key, "Content-Type": "application/json"}


def _phone_unsupported(detail: str) -> bool:
    lowered = detail.lower()
    return any(hint in lowered for hint in _PHONE_UNSUPPORTED_HINTS)


async def auth_sign_up(email_or_phone: str, password: str, metadata: dict) -> dict:
    _require_config()
    payload: dict = {"password": password, "data": metadata, **_identity_payload(email_or_phone)}

    resp = await _request(
        "POST",
        f"{settings.supabase_url}/auth/v1/signup",
        headers=_auth_headers(),
        json=payload,
    )
    if resp.status_code < 400:
        return resp.json()

    detail = _error_detail(resp, "Registration failed.")
    lowered = detail.lower()

    if _phone_unsupported(detail) or (
        "phone" in payload and resp.status_code in (400, 422) and "provider" in lowered
    ):
        raise SupabaseError(
            "This server can't send SMS yet, so mobile-number signup is unavailable. "
            "Please register with an email address instead.",
            400,
        )
    if "already registered" in lowered or "already exists" in lowered or resp.status_code == 409:
        raise SupabaseError(
            "An account with these details already exists. Try logging in instead.", 409
        )
    if "password" in lowered and resp.status_code in (400, 422):
        raise SupabaseError(detail, 400)
    if resp.status_code == 429:
        raise SupabaseError(
            "Too many signup attempts. Please wait a minute and try again.", 429
        )
    if resp.status_code >= 500:
        raise SupabaseError(
            "The signup service is temporarily unavailable. Please try again shortly.", 502
        )
    raise SupabaseError(detail, resp.status_code)


async def auth_sign_in(email_or_phone: str, password: str) -> dict:
    """Password grant against GoTrue.

    Every failure used to collapse into 401 "Invalid credentials", which meant
    a rate limit, an unconfirmed account, a misconfigured project, and a real
    typo were indistinguishable to the user. Each now maps to its own status
    and message.
    """
    _require_config()
    payload = {"password": password, **_identity_payload(email_or_phone)}

    resp = await _request(
        "POST",
        f"{settings.supabase_url}/auth/v1/token",
        headers=_auth_headers(),
        params={"grant_type": "password"},
        json=payload,
    )
    if resp.status_code < 400:
        return resp.json()

    detail = _error_detail(resp, "Invalid credentials.")
    lowered = detail.lower()

    if resp.status_code == 429:
        raise SupabaseError(
            "Too many login attempts. Please wait a minute and try again.", 429
        )
    if resp.status_code >= 500:
        raise SupabaseError(
            "The sign-in service is temporarily unavailable. Please try again shortly.", 502
        )
    if "not confirmed" in lowered or "confirm your" in lowered:
        raise SupabaseError(
            "This account hasn't been confirmed yet. Open the confirmation link we "
            "sent you, then log in again.",
            403,
        )
    if _phone_unsupported(detail):
        raise SupabaseError(
            "Mobile-number login isn't available on this server yet. "
            "Please log in with the email address you registered with.",
            400,
        )
    if resp.status_code in (400, 401, 403):
        raise SupabaseError("Incorrect mobile number/email or password.", 401)
    raise SupabaseError(detail, resp.status_code)


async def auth_request_password_reset(email: str) -> None:
    """Ask GoTrue to email a password-reset link. Email only — no SMS path."""
    _require_config()
    resp = await _request(
        "POST",
        f"{settings.supabase_url}/auth/v1/recover",
        headers=_auth_headers(),
        json={"email": email.strip()},
    )
    if resp.status_code == 429:
        raise SupabaseError(
            "Too many reset requests. Please wait a minute and try again.", 429
        )
    if resp.status_code >= 400:
        raise SupabaseError(_error_detail(resp, "Could not send the reset email."), resp.status_code)


async def auth_refresh(refresh_token: str) -> dict:
    """Exchange a refresh token for a new access token."""
    _require_config()
    resp = await _request(
        "POST",
        f"{settings.supabase_url}/auth/v1/token",
        headers=_auth_headers(),
        params={"grant_type": "refresh_token"},
        json={"refresh_token": refresh_token},
    )
    if resp.status_code >= 400:
        raise SupabaseError("Your session has expired. Please log in again.", 401)
    return resp.json()


async def auth_get_user(access_token: str) -> dict:
    _require_config()
    resp = await _request(
        "GET",
        f"{settings.supabase_url}/auth/v1/user",
        headers={
            "apikey": settings.supabase_anon_key,
            "Authorization": f"Bearer {access_token}",
        },
    )
    if resp.status_code >= 400:
        if resp.status_code >= 500:
            raise SupabaseError(
                "Could not verify your session right now. Please try again shortly.", 502
            )
        raise SupabaseError("Invalid or expired session.", 401)
    return resp.json()
