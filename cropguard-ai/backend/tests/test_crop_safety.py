"""
Tests for the deterministic treatment-advice guardrail.

Two halves, and the second matters as much as the first: a rule that blocks
"my field is 2 acres" would silently replace perfectly good advice with a
"contact your KVK" message, and nobody would notice because the failure looks
like the guardrail working.

Run with: pytest backend/tests/test_crop_safety.py -v
"""

import pytest

from app.services.crop_safety import (
    PROHIBITED_PATTERNS,
    contains_prohibited,
    find_prohibited,
)

# (text, expected rule label). Every rule in PROHIBITED_PATTERNS must appear
# here at least once — test_every_rule_is_covered enforces that.
BLOCKED = [
    # named active ingredient
    ("Spray mancozeb on the affected leaves.", "named active ingredient"),
    ("Avoid using monocrotophos, it is banned.", "named active ingredient"),
    ("Copper Oxychloride works well here.", "named active ingredient"),
    ("Use Lambda-cyhalothrin for the borer.", "named active ingredient"),
    ("Apply 2,4-D to the weeds.", "named active ingredient"),
    ("apply 2 , 4 D along the bund", "named active ingredient"),
    # dose per unit volume or area
    ("Mix 2 ml/litre of water.", "dose per unit volume or area"),
    ("Apply 500 g per acre before flowering.", "dose per unit volume or area"),
    ("Use 1.5 kg/ha at sowing.", "dose per unit volume or area"),
    ("Give 10 ml per plant.", "dose per unit volume or area"),
    ("Add 25 gm/pump to the sprayer.", "dose per unit volume or area"),
    # dose unit ratio (no leading number)
    ("The standard rate is ml/l for this product.", "dose unit ratio"),
    ("Follow the g/acre figure on the label.", "dose unit ratio"),
    # formulation concentration
    ("Ask the shop for the 75% WP formulation.", "formulation concentration"),
    ("The 25 % EC version is cheaper.", "formulation concentration"),
    # spray concentration
    ("Spray at 0.2% on both leaf surfaces.", "spray concentration"),
    ("Dilute to 1% and drench the base.", "spray concentration"),
]

# Real sentences the assistant should be free to say. Every one of these was a
# plausible false positive while the patterns were being tightened.
ALLOWED = [
    "Your field is 2 acres, so check the corners as well as the middle.",
    "Rescan within 2-3 days rather than waiting for the usual interval.",
    "About 18.4% of the leaf area is affected, which is moderate.",
    "Remove and safely dispose of severely affected plant material.",
    "Late blight spreads fastest when humidity stays above 80% overnight.",
    "Water in the morning so the leaves dry before evening.",
    "Your last scan was 24 days ago — scan again this week.",
    "Leave about 60 cm between plants so air moves through the canopy.",
    "Contact your nearest Krishi Vigyan Kendra for treatment advice.",
    "Roughly 5 of the 20 plants you showed me have symptoms.",
    "I cannot recommend any chemical treatment or quantity.",
    "Sulphur and neem-based practices are common in organic farming.",
    "The confidence on that detection was 87%, so it is fairly reliable.",
    "Rotate to a non-host crop such as maize next season.",
    "Yields dropped 30% in fields left unmanaged last year.",
]


@pytest.mark.parametrize("text,expected_label", BLOCKED)
def test_blocked_text_trips_the_expected_rule(text, expected_label):
    tripped = find_prohibited(text)
    assert tripped, f"guardrail let this through: {text!r}"
    assert expected_label in tripped, (
        f"{text!r} tripped {tripped} but not the expected {expected_label!r}"
    )


@pytest.mark.parametrize("text", [t for t, _ in BLOCKED])
def test_contains_prohibited_agrees(text):
    assert contains_prohibited(text) is True


@pytest.mark.parametrize("text", ALLOWED)
def test_ordinary_advice_is_not_blocked(text):
    """A false positive is a silent failure — it looks like the guard working."""
    assert find_prohibited(text) == [], f"innocent sentence blocked: {text!r}"


def test_every_rule_is_covered():
    """Adding a pattern without a test case is easy to miss in review."""
    covered = {label for _, label in BLOCKED}
    declared = {label for label, _ in PROHIBITED_PATTERNS}
    assert declared - covered == set(), (
        f"rules in PROHIBITED_PATTERNS with no BLOCKED test case: {declared - covered}"
    )


def test_rule_labels_are_unique():
    labels = [label for label, _ in PROHIBITED_PATTERNS]
    assert len(labels) == len(set(labels)), f"duplicate rule labels: {labels}"


def test_matching_is_case_insensitive():
    assert find_prohibited("MANCOZEB") == find_prohibited("mancozeb")


def test_empty_and_none_are_clean():
    assert find_prohibited("") == []
    assert find_prohibited(None) == []  # type: ignore[arg-type]
    assert contains_prohibited("") is False


def test_ingredient_needs_a_word_boundary():
    """Substring matching would block unrelated words; \\b prevents that."""
    assert find_prohibited("The gluten in wheat is unrelated.") == []
