"""
Regression tests for recommendation_service.py.

The important one here is test_every_model_class_has_a_template: the trained
detector's class names come straight from ml/training/data.yaml (ai_service.py
passes model.names[cls_id] through as the detection's `class_`), so a class in
that file without a matching template silently gets generic advice attached to
the wrong disease name. That is exactly the bug that existed before the
PlantDoc dataset was wired up — TEMPLATES covered 7 hand-written classes while
the dataset produced 14, and the fallback handed out the early_blight template
for anything unmapped.

Run with: pytest backend/tests/test_recommendation_service.py -v
"""

import re
from pathlib import Path

import pytest

from app.services.crop_safety import find_prohibited
from app.services.demo_outcomes import CROP_DEMO_OUTCOMES
from app.services.recommendation_service import TEMPLATES, get_recommendation

DATA_YAML = Path(__file__).resolve().parent.parent.parent / "ml" / "training" / "data.yaml"


def _data_yaml_class_names() -> list[str]:
    if not DATA_YAML.exists():
        pytest.skip(f"{DATA_YAML} not generated yet — run ml/dataset/prepare_dataset.py")
    text = DATA_YAML.read_text(encoding="utf-8")
    names_block = text.split("names:", 1)
    if len(names_block) < 2:
        pytest.fail("data.yaml has no `names:` block")
    return [
        match.group(2)
        for match in re.finditer(r"^\s+(\d+):\s+(\S+)", names_block[1], re.MULTILINE)
    ]


def test_data_yaml_has_classes():
    assert _data_yaml_class_names(), "data.yaml declared no classes"


def test_every_model_class_has_a_template():
    """Every class the trained model can emit must have reviewed guidance."""
    missing = [name for name in _data_yaml_class_names() if name not in TEMPLATES]
    assert not missing, (
        f"data.yaml classes with no recommendation template: {missing}. "
        "Add a template for each, or these detections will show another disease's advice."
    )


def test_every_demo_class_has_a_template():
    """Demo mode's canned outcomes must not fall through to the default either."""
    demo_classes = {
        detection.class_
        for pool in CROP_DEMO_OUTCOMES.values()
        for result in pool
        for detection in result.detections
    }
    missing = [name for name in sorted(demo_classes) if name not in TEMPLATES]
    assert not missing, f"demo_outcomes classes with no template: {missing}"


def test_unmapped_class_does_not_borrow_another_disease_template():
    """An unknown class must not be presented to the farmer as early blight."""
    result = get_recommendation("definitely_not_a_real_class", 0.95)
    assert result is TEMPLATES["unknown"]
    assert result is not TEMPLATES["early_blight"]
    assert "blight" not in result.title.lower()


def test_healthy_and_low_confidence_paths():
    assert get_recommendation(None, None) is TEMPLATES["healthy"]
    assert get_recommendation("early_blight", 0.3) is TEMPLATES["low_confidence"]
    # At/above the confidence floor the real template is used.
    assert get_recommendation("early_blight", 0.6) is TEMPLATES["early_blight"]


def test_known_class_returns_its_own_template():
    for name in ("early_blight", "late_blight", "bacterial_spot", "apple_scab"):
        assert get_recommendation(name, 0.9) is TEMPLATES[name]


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_no_template_names_a_pesticide_or_dose(key):
    """Section 33 of the spec: never invent pesticide names, doses, or concentrations.

    Uses the same crop_safety scan the AI assistant's output is run through, so
    hand-written and generated advice are held to one standard — and so a rule
    added for the assistant automatically starts checking these templates too.
    """
    template = TEMPLATES[key]
    text = " ".join(
        [template.title, *template.actions, *template.prevention, template.next_scan or ""]
    )
    tripped = find_prohibited(text)
    assert not tripped, f"template '{key}' tripped: {', '.join(tripped)}"


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_templates_are_well_formed(key):
    template = TEMPLATES[key]
    assert template.title.strip(), f"template '{key}' has an empty title"
    assert template.actions, f"template '{key}' has no actions"
    assert all(action.strip() for action in template.actions)
    assert template.prevention, f"template '{key}' has no prevention advice"
    assert all(item.strip() for item in template.prevention)
