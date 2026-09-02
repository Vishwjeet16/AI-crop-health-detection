"""
Severity estimation via color-based segmentation.

Stage 6 shipped a coarse placeholder: affected area = summed YOLO box
area. That's a real gap flagged honestly in the Stage 6 README notes — box
area over-counts (a box is a rectangle around an irregular lesion) and
tells you nothing about how much of the *plant tissue* inside that box is
actually diseased versus healthy leaf sharing the same box.

This module replaces that proxy with classical HSV color segmentation:

  1. Identify plant tissue (green + yellow/brown/necrotic tones) versus
     background (soil, sky, hands, pots) — the `plant_mask`.
  2. Within plant tissue, identify healthy green versus everything else —
     the `lesion_mask` is plant tissue that ISN'T healthy green.
  3. affected_area_percent = lesion pixels / plant pixels, restricted to
     the union of detection boxes when boxes are available (narrows the
     estimate to the region YOLO actually flagged, rather than the whole
     photo).

This is a real, tested technique from plant pathology imaging literature
(HSV-based lesion segmentation) — but it is still a heuristic, not ground
truth. It will misfire on: non-green cultivars, heavy shadow/glare,
photos with lots of non-leaf green (grass, other plants) inside the
frame, and diseases that don't discolor tissue (some viral symptoms,
early pest damage). Treat its output the same way the rest of this app
treats any single-model number — a decision-support estimate, not a lab
measurement.
"""

from __future__ import annotations

from PIL import Image

# Severity thresholds — kept identical to ai_service.py's, so a real
# segmentation result and a demo-mode canned result land in the same
# severity buckets given the same affected-area number.
_SEVERITY_THRESHOLDS = [(50, "critical"), (30, "high"), (10, "moderate")]

_MIN_PLANT_PIXELS = 200  # below this, there's not enough plant tissue detected to trust a ratio


def severity_level_from_area(affected_area_percent: float) -> str:
    for threshold, level in _SEVERITY_THRESHOLDS:
        if affected_area_percent >= threshold:
            return level
    return "low"


def _pil_to_bgr(image: Image.Image):
    import cv2
    import numpy as np

    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _leaf_and_lesion_masks(bgr):
    import cv2
    import numpy as np

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Healthy green leaf tissue. OpenCV hue range is 0-179. Lower bound is
    # 35 (not the more commonly-cited ~25) specifically to exclude
    # yellow/yellow-green lesion tones (chlorosis, early rust, necrotic
    # yellowing) from being misclassified as healthy — caught via testing
    # with a synthetic yellow lesion that the wider range let through
    # entirely. True healthy leaf green sits comfortably above 35 here.
    healthy_mask = cv2.inRange(hsv, (35, 40, 40), (95, 255, 255))

    # Broader plant-tissue mask: healthy green PLUS yellow/brown/necrotic
    # tones (lesions, blight, rust), while still excluding near-white,
    # near-black, and blue/gray backgrounds (sky, soil, pots, hands).
    plant_mask = cv2.inRange(hsv, (10, 30, 20), (95, 255, 255))

    # Light morphological opening to drop single-pixel noise from
    # compression artifacts, without erasing genuinely small lesions.
    kernel = np.ones((3, 3), np.uint8)
    healthy_mask = cv2.morphologyEx(healthy_mask, cv2.MORPH_OPEN, kernel)
    plant_mask = cv2.morphologyEx(plant_mask, cv2.MORPH_OPEN, kernel)

    lesion_mask = cv2.bitwise_and(plant_mask, cv2.bitwise_not(healthy_mask))
    return plant_mask, lesion_mask


def estimate_affected_area_percent(
    image: Image.Image,
    boxes_percent: list[tuple[float, float, float, float]] | None = None,
) -> float:
    """Returns an affected-area percentage (0-100).

    `boxes_percent` — optional list of (x, y, width, height), each as a
    percentage of the image frame (matching Detection.bbox's format). When
    provided, the estimate is restricted to the union of those regions
    rather than the whole photo — narrower and more relevant when YOLO has
    already flagged where the problem is.
    """
    import cv2
    import numpy as np

    bgr = _pil_to_bgr(image)
    h_img, w_img = bgr.shape[:2]

    if boxes_percent:
        region_mask = np.zeros((h_img, w_img), dtype=np.uint8)
        for x, y, w, h in boxes_percent:
            x1 = max(0, int(x / 100 * w_img))
            y1 = max(0, int(y / 100 * h_img))
            x2 = min(w_img, int((x + w) / 100 * w_img))
            y2 = min(h_img, int((y + h) / 100 * h_img))
            if x2 > x1 and y2 > y1:
                region_mask[y1:y2, x1:x2] = 255
    else:
        region_mask = np.full((h_img, w_img), 255, dtype=np.uint8)

    plant_mask, lesion_mask = _leaf_and_lesion_masks(bgr)
    plant_mask = cv2.bitwise_and(plant_mask, region_mask)
    lesion_mask = cv2.bitwise_and(lesion_mask, region_mask)

    plant_pixels = int(np.count_nonzero(plant_mask))
    lesion_pixels = int(np.count_nonzero(lesion_mask))

    if plant_pixels < _MIN_PLANT_PIXELS:
        # Not enough plant tissue found to trust a ratio (e.g. a photo
        # that's mostly background, or a color profile this heuristic
        # doesn't handle well) — 0 rather than a misleadingly precise
        # number computed from noise.
        return 0.0

    percent = (lesion_pixels / plant_pixels) * 100
    return round(min(percent, 100.0), 1)
