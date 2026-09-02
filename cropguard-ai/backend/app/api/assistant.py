"""
Chat endpoint for the multilingual assistant.

This layer does the I/O: it authenticates the farmer, reads their fields and
recent scans from Supabase, and hands plain dicts to assistant_service. The
service builds the prompt and calls the model but touches no database, which
keeps its prompt-building and guardrail logic unit-testable with no network at
all (see tests/test_assistant_service.py).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.assistant import AssistantReply, AssistantRequest
from app.services import assistant_service
from app.services.mongo_client import DatabaseError, db_select
from app.utils.auth import get_current_user

logger = logging.getLogger("assistant")

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

# How much history to put in front of the model. Enough for "is it getting
# worse?" to be answerable, bounded so the prompt stays small.
RECENT_SCAN_LIMIT = 8


async def _load_context(user_id: str, field_id: str | None) -> tuple[list[dict], list[dict]]:
    """Fetch the farmer's fields and recent scans.

    Deliberately non-fatal: if Supabase is unreachable the assistant still
    answers general crop questions, it just can't refer to their specific
    fields. A farmer with a sick plant should not be blocked by a database
    hiccup.
    """
    fields: list[dict] = []
    scans: list[dict] = []

    try:
        fields = await db_select(
            "fields",
            {"user_id": f"eq.{user_id}", "order": "created_at.desc", "select": "*"},
        )
    except DatabaseError as e:
        logger.warning("Assistant context: could not load fields (%s)", e)

    scan_params = {
        "user_id": f"eq.{user_id}",
        "order": "timestamp.desc",
        "limit": str(RECENT_SCAN_LIMIT),
        "select": "*",
    }
    if field_id:
        # Scoped to the field the farmer has open, so the context is about what
        # they're actually looking at rather than their newest scan elsewhere.
        scan_params["field_id"] = f"eq.{field_id}"
    try:
        scans = await db_select("scans", scan_params)
    except DatabaseError as e:
        logger.warning("Assistant context: could not load scans (%s)", e)

    return fields, scans


@router.post("/chat", response_model=AssistantReply)
async def chat(payload: AssistantRequest, user: dict = Depends(get_current_user)):
    # The farmer's saved language wins over whatever the client sent, unless the
    # client explicitly asked for a different supported one. Sending "en" is the
    # schema's default for a missing field, so it's treated as "not specified".
    language = payload.language
    if language == "en" and user.get("language"):
        language = assistant_service.normalize_language(user["language"])

    fields, scans = await _load_context(user["id"], payload.field_id)

    try:
        result = await assistant_service.answer(
            message=payload.message,
            language=language,
            profile=user,
            fields=fields,
            scans=scans,
            history=[turn.model_dump() for turn in payload.history],
        )
    except assistant_service.AssistantError as e:
        raise HTTPException(e.status_code, str(e))

    return AssistantReply(**result)


@router.get("/languages")
async def languages():
    """The languages the assistant can answer in.

    Exposed so the frontend picker and this service can't drift apart — the
    registry here is the backend's copy of frontend/lib/i18n SUPPORTED_LANGUAGES.
    Unauthenticated on purpose: it's a static list, useful on the landing page.
    """
    return {
        "languages": [
            {"code": code, "name": meta["name"], "native": meta["native"]}
            for code, meta in assistant_service.LANGUAGES.items()
        ],
        "configured": assistant_service.is_configured(),
    }
