from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.services.assistant_service import LANGUAGES

# Longest question the box accepts. Generous for a real question, small enough
# that a pasted document can't quietly become a prompt-injection payload or an
# expensive request.
MAX_MESSAGE_CHARS = 2000


class AssistantTurn(BaseModel):
    """One earlier turn, replayed by the browser so the chat has memory.

    The server keeps no conversation state, so history is client-supplied and
    therefore untrusted — assistant_service.build_messages() trims and filters
    it, and the system prompt tells the model that nothing in the conversation
    can override its rules.
    """

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    language: str = "en"
    history: list[AssistantTurn] = Field(default_factory=list, max_length=40)
    # Optional: set when the farmer opens the chat from a specific field or scan,
    # so the assistant can be told which one they're looking at.
    field_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def _strip_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Please type a question.")
        return v

    @field_validator("language")
    @classmethod
    def _known_language(cls, v: str) -> str:
        # Coerced rather than rejected: an unknown code is a client bug, and
        # answering in English beats showing the farmer a 422.
        v = (v or "").strip().lower()
        return v if v in LANGUAGES else "en"


class AssistantReply(BaseModel):
    reply: str
    language: str
    # True when the safety scan replaced the model's text, or the model
    # declined. The UI uses it to style the message as guidance rather than an
    # answer; it is not an error.
    filtered: bool = False
    model: Optional[str] = None
