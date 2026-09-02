"""
Consistency checks for the frontend translation dictionaries.

These live in the backend suite for a practical reason: the frontend has no
test runner, and `pytest` is the only thing in this project that runs in CI.
There is precedent — test_recommendation_service.py reads ml/training/data.yaml
the same way. What's checked here is exactly the kind of thing that fails
silently: a missing key falls back to English, so a half-translated build looks
finished, and a character copied from the wrong script renders as a stray letter
nobody notices unless they read that language.

Run with: pytest backend/tests/test_i18n_dictionaries.py -v
"""

import json
import re
import unicodedata
from pathlib import Path

import pytest

from app.schemas.auth import SUPPORTED_LANGUAGE_CODES
from app.services.assistant_service import LANGUAGES

I18N_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "lib" / "i18n"
SCHEMA_SQL = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"

# (unicode block start, end, human name) per language. English is Latin-only.
SCRIPT_BLOCKS = {
    "hi": (0x0900, 0x097F, "Devanagari"),
    "mr": (0x0900, 0x097F, "Devanagari"),
    "ta": (0x0B80, 0x0BFF, "Tamil"),
    "te": (0x0C00, 0x0C7F, "Telugu"),
}


def _load(code: str) -> dict[str, str]:
    path = I18N_DIR / f"{code}.json"
    if not path.exists():
        pytest.fail(f"missing translation file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def test_backend_and_frontend_agree_on_the_language_list():
    """Three registries have to match or the pickers offer dead options."""
    assert set(SUPPORTED_LANGUAGE_CODES) == set(LANGUAGES)
    for code in SUPPORTED_LANGUAGE_CODES:
        assert (I18N_DIR / f"{code}.json").exists(), f"no frontend dictionary for {code}"


@pytest.mark.parametrize("code", [c for c in SUPPORTED_LANGUAGE_CODES if c != "en"])
def test_every_language_has_every_english_key(code):
    """A missing key silently renders in English — a half-done build looks done."""
    english = _load("en")
    translated = _load(code)
    missing = sorted(set(english) - set(translated))
    assert not missing, f"{code}.json is missing: {missing}"


@pytest.mark.parametrize("code", [c for c in SUPPORTED_LANGUAGE_CODES if c != "en"])
def test_no_language_has_keys_english_lacks(code):
    """An extra key is dead weight — nothing can look it up (TranslationKey is
    derived from en.json)."""
    extra = sorted(set(_load(code)) - set(_load("en")))
    assert not extra, f"{code}.json has keys en.json doesn't: {extra}"


@pytest.mark.parametrize("code", SUPPORTED_LANGUAGE_CODES)
def test_no_value_is_blank(code):
    blank = [k for k, v in _load(code).items() if not v.strip()]
    assert not blank, f"{code}.json has empty strings for: {blank}"


@pytest.mark.parametrize("code", sorted(SCRIPT_BLOCKS))
def test_values_use_only_the_expected_script(code):
    """Catches a letter copied from the wrong language's string.

    Strict on purpose: a check for "contains any Tamil" passes even when one
    character is Devanagari, which is the actual mistake this guards against.
    """
    low, high, name = SCRIPT_BLOCKS[code]
    offenders = []
    for key, value in _load(code).items():
        for ch in value:
            point = ord(ch)
            # Latin, digits and punctuation are expected (brand names, "KVK",
            # "AI"); U+2000-206F is general punctuation (ellipsis, ZWNJ, ZWJ).
            if point < 0x0900 or 0x2000 <= point <= 0x206F:
                continue
            if not (low <= point <= high):
                offenders.append(
                    f"{key}: U+{point:04X} {unicodedata.name(ch, '?')} (expected {name})"
                )
    assert not offenders, f"{code}.json mixes scripts — " + "; ".join(offenders)


@pytest.mark.parametrize("code", sorted(SCRIPT_BLOCKS))
def test_translations_are_not_just_the_english_string(code):
    """An untranslated copy is worse than a missing key: the fallback would at
    least be intentional."""
    english = _load("en")
    translated = _load(code)
    # No carve-out list on purpose: as of writing, every key differs from
    # English in all four languages. If a genuinely untranslatable string is
    # added later (a proper noun), allow it here with a note saying why.
    identical = [
        key
        for key, value in translated.items()
        if value == english.get(key) and any(ch.isalpha() for ch in value)
    ]
    assert not identical, f"{code}.json left untranslated: {identical}"


@pytest.mark.parametrize("code", SUPPORTED_LANGUAGE_CODES)
def test_assistant_disclaimer_names_an_authority(code):
    """The one string a farmer must be able to act on when the guardrail fires."""
    assert "KVK" in _load(code)["assistant.disclaimer"]


@pytest.mark.parametrize("code", SUPPORTED_LANGUAGE_CODES)
def test_no_dictionary_names_a_pesticide_or_dose(code):
    """Same rule as the templates and the assistant's output."""
    from app.services.crop_safety import find_prohibited

    for key, value in _load(code).items():
        tripped = find_prohibited(value)
        assert not tripped, f"{code}.json [{key}] tripped: {', '.join(tripped)}"


def test_database_accepts_every_language_the_app_offers():
    """The fourth registry, and the one that fails hardest when it drifts.

    public.handle_new_user() copies the chosen language into public.users from
    inside an AFTER INSERT trigger on auth.users. A value this CHECK rejects
    therefore aborts the signup transaction, rolling back the auth record too —
    so registration dies with an opaque 500 rather than a field error. That
    shipped: the app was widened to five languages while the constraint still
    listed two.
    """
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    match = re.search(r"language\s+text[^,]*?check\s*\(\s*language\s+in\s*\(([^)]*)\)", sql)
    assert match, "could not find the users.language CHECK constraint in schema.sql"
    allowed = set(re.findall(r"'([a-z]{2})'", match.group(1)))
    assert allowed == set(SUPPORTED_LANGUAGE_CODES), (
        f"schema.sql allows {sorted(allowed)} but the app offers "
        f"{sorted(SUPPORTED_LANGUAGE_CODES)}"
    )

