from pydantic import BaseModel, Field, field_validator

# Kept in sync with frontend/lib/i18n/index.ts SUPPORTED_LANGUAGES.
SUPPORTED_LANGUAGE_CODES = ("en", "hi", "mr", "ta", "te")

# Matches the floor in frontend/lib/validation.ts (isStrongPassword), which
# additionally requires a letter and a digit. Keeping the backend at the same
# length floor means a password the form accepted is never rejected here with a
# 422 the form can't explain.
MIN_PASSWORD_LENGTH = 8


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    contact: str  # email or 10-digit mobile number
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    location: str = ""
    language: str = "en"

    @field_validator("name", "contact", "location")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @field_validator("language")
    @classmethod
    def _known_language(cls, value: str) -> str:
        value = (value or "en").strip().lower()
        return value if value in SUPPORTED_LANGUAGE_CODES else "en"


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1)
    password: str = Field(min_length=1)

    @field_validator("identifier")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class AuthUser(BaseModel):
    id: str
    name: str
    location: str
    language: str
    contact: str


class AuthResponse(BaseModel):
    """Result of register/login.

    `token` is None when the account was created but can't be used yet
    (Supabase is configured to require email/phone confirmation). That is a
    success, not an error — it used to be raised as an HTTPException(202),
    which the frontend rendered as a red failure box.
    """

    token: str | None = None
    refresh_token: str | None = None
    user: AuthUser | None = None
    pending_confirmation: bool = False
    message: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class PasswordResetRequest(BaseModel):
    identifier: str = Field(min_length=1)

    @field_validator("identifier")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()
