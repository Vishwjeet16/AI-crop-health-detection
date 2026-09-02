"""
Auth routes.

These wrap Supabase Auth (GoTrue) rather than implementing sessions here, so
the token the frontend stores is a real Supabase access token that PostgREST
and RLS understand. The route layer's job is to turn Supabase's error shapes
into statuses and messages a farmer can act on, and to make sure a profile row
exists so the rest of the app has something to read.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import (
    AuthResponse,
    AuthUser,
    LoginRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services.supabase_client import (
    SupabaseError,
    auth_refresh,
    auth_request_password_reset,
    auth_sign_in,
    auth_sign_up,
)
from app.utils.auth import ensure_profile, get_current_user

logger = logging.getLogger("auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _auth_user_from(auth_record: dict, profile: dict, fallback_contact: str) -> AuthUser:
    """Build the API's user shape, preferring the profile row over metadata."""
    metadata = auth_record.get("user_metadata") or {}
    contact = (
        profile.get("email")
        or profile.get("phone")
        or auth_record.get("email")
        or auth_record.get("phone")
        or fallback_contact
    )
    return AuthUser(
        id=str(profile.get("id") or auth_record.get("id") or ""),
        name=profile.get("name") or metadata.get("name") or "Farmer",
        location=profile.get("location") or metadata.get("location") or "",
        language=profile.get("language") or metadata.get("language") or "en",
        contact=contact,
    )


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest):
    try:
        result = await auth_sign_up(
            payload.contact,
            payload.password,
            metadata={
                "name": payload.name,
                "location": payload.location,
                "language": payload.language,
                "phone": payload.contact if "@" not in payload.contact else None,
            },
        )
    except SupabaseError as e:
        raise HTTPException(e.status_code, str(e))

    auth_record = result.get("user") or {}
    token = result.get("access_token")

    if not token:
        # The project requires email/phone confirmation. This is a successful
        # registration in a pending state, so it must not be an error response.
        return AuthResponse(
            pending_confirmation=True,
            message=(
                "Account created. Please open the confirmation link we sent to "
                f"{payload.contact}, then log in."
            ),
        )

    if not auth_record.get("id"):
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Signup succeeded but Supabase returned no user record. Please try logging in.",
        )

    profile: dict = {}
    try:
        profile = await ensure_profile(auth_record)
    except SupabaseError as e:
        # The account exists and the token is valid; a profile-write hiccup
        # shouldn't block the user from getting in. get_current_user() retries.
        logger.warning("Could not provision profile for %s: %s", auth_record.get("id"), e)

    return AuthResponse(
        token=token,
        refresh_token=result.get("refresh_token"),
        user=_auth_user_from(auth_record, profile, payload.contact),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    try:
        result = await auth_sign_in(payload.identifier, payload.password)
    except SupabaseError as e:
        raise HTTPException(e.status_code, str(e))

    token = result.get("access_token")
    auth_record = result.get("user") or {}
    if not token or not auth_record.get("id"):
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Sign-in did not return a usable session. Please try again.",
        )

    profile: dict = {}
    try:
        profile = await ensure_profile(auth_record)
    except SupabaseError as e:
        logger.warning("Could not load profile for %s: %s", auth_record.get("id"), e)

    return AuthResponse(
        token=token,
        refresh_token=result.get("refresh_token"),
        user=_auth_user_from(auth_record, profile, payload.identifier),
    )


@router.get("/me", response_model=AuthUser)
async def me(profile: dict = Depends(get_current_user)):
    """Validate a stored token and return the current profile.

    The frontend calls this on mount so a token that expired while the tab was
    closed is detected immediately, instead of the app rendering a logged-in
    shell that 401s on every subsequent request.
    """
    return AuthUser(
        id=str(profile.get("id") or ""),
        name=profile.get("name") or "Farmer",
        location=profile.get("location") or "",
        language=profile.get("language") or "en",
        contact=profile.get("email") or profile.get("phone") or profile.get("auth_email") or "",
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(payload: RefreshRequest):
    try:
        result = await auth_refresh(payload.refresh_token)
    except SupabaseError as e:
        raise HTTPException(e.status_code, str(e))

    token = result.get("access_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has expired. Please log in again.")

    auth_record = result.get("user") or {}
    profile: dict = {}
    if auth_record.get("id"):
        try:
            profile = await ensure_profile(auth_record)
        except SupabaseError as e:
            logger.warning("Could not load profile on refresh: %s", e)

    return AuthResponse(
        token=token,
        refresh_token=result.get("refresh_token") or payload.refresh_token,
        user=_auth_user_from(auth_record, profile, "") if auth_record.get("id") else None,
    )


@router.post("/forgot-password")
async def forgot_password(payload: PasswordResetRequest):
    """Send a password-reset email.

    Supabase's recover endpoint is email-only. For a mobile number this now
    says so plainly instead of returning {"sent": true} and leaving the user
    waiting for an SMS that was never going to arrive.
    """
    if "@" not in payload.identifier:
        return {
            "sent": False,
            "message": (
                "Password reset by mobile number isn't available yet. If you registered "
                "with an email address, enter that instead, or contact support."
            ),
        }

    try:
        await auth_request_password_reset(payload.identifier)
    except SupabaseError as e:
        if e.status_code == 429:
            raise HTTPException(e.status_code, str(e))
        # Don't confirm or deny whether an address is registered.
        logger.warning("Password reset for %s failed: %s", payload.identifier, e)

    return {
        "sent": True,
        "message": (
            f"If an account exists for {payload.identifier}, a reset link is on its way. "
            "Check your inbox and spam folder."
        ),
    }
