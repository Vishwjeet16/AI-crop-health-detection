"""
Regression tests for severity_service.py.

Unlike most of this backend, these tests were actually run — cv2/numpy/PIL
are available without network access, so this module's core logic (color
segmentation) could be genuinely validated rather than only reasoned
through. FastAPI/pydantic/ultralytics aren't installable in the sandbox
this was built in, so the route layer around this function remains
unexecuted like the rest of the backend — see the Stage 7 README notes.

Run with: pytest backend/tests/test_severity_service.py -v
"""

import math

import pytest
from PIL import Image, ImageDraw

from app.services.severity_service import (
    estimate_affected_area_percent,
    severity_level_from_area,
)


def make_leaf(lesion_fraction: float, lesion_color=(101, 67, 33), size=(400, 400)) -> Image.Image:
    """A green square 'leaf' on a dark background, with a circular lesion
    sized to cover roughly `lesion_fraction` of the leaf's area."""
    img = Image.new("RGB", size, (30, 30, 30))
    draw = ImageDraw.Draw(img)
    leaf_box = [40, 40, size[0] - 40, size[1] - 40]
    draw.rectangle(leaf_box, fill=(34, 139, 34))
    if lesion_fraction > 0:
        leaf_w = leaf_box[2] - leaf_box[0]
        leaf_area = leaf_w * leaf_w
        r = math.sqrt(lesion_fraction * leaf_area / math.pi)
        cx, cy = size[0] // 2, size[1] // 2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=lesion_color)
    return img


class TestAffectedAreaEstimation:
    @pytest.mark.parametrize(
        "lesion_fraction",
        [0.0, 0.05, 0.15, 0.25, 0.40, 0.55, 0.75],
    )
    def test_tracks_ground_truth_within_tolerance(self, lesion_fraction):
        img = make_leaf(lesion_fraction)
        estimated = estimate_affected_area_percent(img)
        expected = lesion_fraction * 100
        assert abs(estimated - expected) < 2.0, f"expected ~{expected}%, got {estimated}%"

    def test_no_plant_tissue_returns_zero(self):
        blank = Image.new("RGB", (300, 300), (20, 20, 25))
        assert estimate_affected_area_percent(blank) == 0.0

    def test_yellow_lesion_is_detected(self):
        # Regression test for a real bug caught during development: an
        # earlier hue threshold classified yellow lesions as healthy green.
        img = make_leaf(0.08, lesion_color=(200, 180, 40))
        estimated = estimate_affected_area_percent(img)
        assert estimated > 5.0, (
            f"yellow lesion should be detected as unhealthy tissue, got {estimated}% "
            "(if this regresses to ~0, check the healthy_mask hue lower bound)"
        )

    def test_box_restricts_to_region(self):
        img = make_leaf(0.08, lesion_color=(200, 180, 40))

        # A box over a corner with no lesion should read ~0.
        healthy_only_box = estimate_affected_area_percent(img, boxes_percent=[(5, 5, 20, 20)])
        assert healthy_only_box < 2.0

        # A box tightly around the lesion should read higher than the
        # whole-image estimate (same lesion, smaller denominator).
        whole_image = estimate_affected_area_percent(img)
        tight_box = estimate_affected_area_percent(img, boxes_percent=[(30, 30, 40, 40)])
        assert tight_box > whole_image

    def test_result_never_exceeds_100(self):
        img = make_leaf(0.95)
        assert estimate_affected_area_percent(img) <= 100.0


class TestSeverityLevelMapping:
    @pytest.mark.parametrize(
        "area_percent,expected_level",
        [(0, "low"), (9.9, "low"), (10, "moderate"), (29.9, "moderate"), (30, "high"), (49.9, "high"), (50, "critical"), (100, "critical")],
    )
    def test_thresholds(self, area_percent, expected_level):
        assert severity_level_from_area(area_percent) == expected_level
