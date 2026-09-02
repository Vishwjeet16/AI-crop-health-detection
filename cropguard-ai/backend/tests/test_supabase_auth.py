"""
Regression tests for the Supabase auth layer.

The bug these exist for: auth_sign_in() used to raise
`SupabaseError(detail, 401)` for *every* failure. A rate limit, an unconfirmed
account, a project with no SMS provider, and an actual wrong password were all
reported to the user as "Invalid credentials", which is unactionable and, for
the rate-limit case, actively misleading — the user retries and makes it worse.

These tests stub the transport (`_request`) rather than hitting Supabase, so
they run offline.

Run with: pytest backend/tests/test_supabase_auth.py -v
"""

import json

import pytest

from app.services import supabase_client as sc


class FakeResponse:
    """Minimal stand-in for httpx.Response."""

    def __init__(self, status_code: int, body=None, *, text: str | None = None):
        self.status_code = status_code
        self._body = body
        self.text = text if text is not None else (json.dumps(body) if body is not None else "")

    def json(self):
        if self._body is None:
            raise ValueError("no JSON body")
        return self._body


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    """Pretend Supabase is configured so _require_config passes."""
    monkeypatch.setattr(sc.settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(sc.settings, "supabase_anon_key", "anon-key")
    monkeypatch.setattr(sc.settings, "supabase_service_key", "service-key")


def _stub(monkeypatch, response):
    async def fake_request(method, url, **kwargs):
        return response

    monkeypatch.setattr(sc, "_request", fake_request)


# --- identifier normalization ----------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("farmer@example.com", {"email": "farmer@example.com"}),
        ("  farmer@example.com  ", {"email": "farmer@example.com"}),
        ("9876543210", {"phone": "+919876543210"}),
        ("98765 43210", {"phone": "+919876543210"}),
        ("98765-43210", {"phone": "+919876543210"}),
        ("+919876543210", {"phone": "+919876543210"}),
    ],
)
def test_identity_payload_normalizes(raw, expected):
    """GoTrue needs E.164; the UI's placeholder is a bare 10-digit number."""
    assert sc._identity_payload(raw) == expected


def test_identity_payload_never_sends_both_fields():
    for raw in ("a@b.com", "9876543210"):
        payload = sc._identity_payload(raw)
        assert ("email" in payload) != ("phone" in payload)


# --- config guard -----------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_config_raises_503_not_a_transport_crash(monkeypatch):
    monkeypatch.setattr(sc.settings, "supabase_url", "")
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_in("a@b.com", "password1")
    assert exc.value.status_code == 503
    assert "SUPABASE_URL" in str(exc.value)


# --- error body parsing -----------------------------------------------------

def test_error_detail_survives_non_json_body():
    """A proxy returning HTML used to make resp.json() raise ValueError."""
    resp = FakeResponse(502, None, text="<html>Bad Gateway</html>")
    assert sc._error_detail(resp, "fallback") == "<html>Bad Gateway</html>"


def test_error_detail_falls_back_when_body_is_empty():
    assert sc._error_detail(FakeResponse(500, None, text=""), "fallback") == "fallback"


@pytest.mark.parametrize("key", ["error_description", "msg", "message", "error"])
def test_error_detail_reads_each_gotrue_field(key):
    assert sc._error_detail(FakeResponse(400, {key: "the reason"}), "fallback") == "the reason"


# --- sign-in status mapping -------------------------------------------------

@pytest.mark.asyncio
async def test_wrong_password_is_401(monkeypatch):
    _stub(monkeypatch, FakeResponse(400, {"error_description": "Invalid login credentials"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_in("a@b.com", "wrong")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_is_429_not_401(monkeypatch):
    _stub(monkeypatch, FakeResponse(429, {"msg": "Request rate limit reached"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_in("a@b.com", "password1")
    assert exc.value.status_code == 429
    assert "wait" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_server_error_is_502_not_401(monkeypatch):
    _stub(monkeypatch, FakeResponse(500, {"msg": "internal error"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_in("a@b.com", "password1")
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_unconfirmed_account_is_403_with_its_own_message(monkeypatch):
    _stub(monkeypatch, FakeResponse(400, {"msg": "Email not confirmed"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_in("a@b.com", "password1")
    assert exc.value.status_code == 403
    assert "confirm" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_phone_login_without_sms_provider_says_so(monkeypatch):
    _stub(monkeypatch, FakeResponse(400, {"msg": "Unsupported phone provider"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_in("9876543210", "password1")
    assert exc.value.status_code == 400
    assert "email" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_successful_sign_in_returns_body(monkeypatch):
    body = {"access_token": "tok", "refresh_token": "ref", "user": {"id": "u1"}}
    _stub(monkeypatch, FakeResponse(200, body))
    assert await sc.auth_sign_in("a@b.com", "password1") == body


# --- sign-up status mapping -------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_signup_is_409(monkeypatch):
    _stub(monkeypatch, FakeResponse(400, {"msg": "User already registered"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_up("a@b.com", "password1", {})
    assert exc.value.status_code == 409
    assert "logging in" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_phone_signup_without_sms_provider_points_at_email(monkeypatch):
    _stub(monkeypatch, FakeResponse(422, {"msg": "Unsupported phone provider"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_up("9876543210", "password1", {})
    assert exc.value.status_code == 400
    assert "email" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_signup_rate_limit_is_429(monkeypatch):
    _stub(monkeypatch, FakeResponse(429, {"msg": "email rate limit exceeded"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_sign_up("a@b.com", "password1", {})
    assert exc.value.status_code == 429


# --- session validation -----------------------------------------------------

@pytest.mark.asyncio
async def test_get_user_401_on_expired_token(monkeypatch):
    _stub(monkeypatch, FakeResponse(401, {"msg": "invalid claim"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_get_user("expired")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_502_on_upstream_outage(monkeypatch):
    """A Supabase outage must not read as "your session is invalid"."""
    _stub(monkeypatch, FakeResponse(503, None, text="upstream unavailable"))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_get_user("valid-token")
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_refresh_failure_is_401(monkeypatch):
    _stub(monkeypatch, FakeResponse(400, {"msg": "Invalid Refresh Token"}))
    with pytest.raises(sc.SupabaseError) as exc:
        await sc.auth_refresh("stale")
    assert exc.value.status_code == 401
