"""
Demo AI Mode outcome registry (section 23 of the spec).

Real trained-model inference is Stage 6 work. Until then, AI_MODE=demo
needs to feel like a real, varied pipeline rather than one fixed
"early blight, 94%" result repeated forever — so outcomes are:

  * keyed by the field's actual crop, so a Cotton field never returns a
    Tomato disease,
  * deterministic per image (same photo -> same result) so a live SIH
    demo run twice looks consistent, via a hash of the image bytes,
  * spread across the full severity range (low/moderate/high/critical)
    and including one deliberately low-confidence result per pool where
    possible, so the "AI is not confident enough" UI path and every
    severity badge actually get exercised during a demo.

Every `crop_class` key here must have a matching entry in
recommendation_service.TEMPLATES, or get_recommendation() falls back to
its default template.
"""

from app.schemas.scans import Detection, Severity
from app.services.detection_result import DetectionResult

CROP_DEMO_OUTCOMES: dict[str, list[DetectionResult]] = {
    "tomato": [
        DetectionResult(
            crop="Tomato",
            detections=[Detection(class_="early_blight", label="Early Blight", confidence=0.94, bbox=[28, 22, 42, 48])],
            severity=Severity(level="moderate", affected_area_percent=23, is_demo=True),
            is_demo=True,
        ),
        DetectionResult(
            crop="Tomato",
            detections=[Detection(class_="late_blight", label="Late Blight", confidence=0.89, bbox=[15, 10, 65, 70])],
            severity=Severity(level="critical", affected_area_percent=58, is_demo=True),
            is_demo=True,
        ),
        DetectionResult(
            crop="Tomato",
            detections=[],
            severity=Severity(level="low", affected_area_percent=0, is_demo=True),
            is_demo=True,
        ),
    ],
    "cotton": [
        DetectionResult(
            crop="Cotton",
            detections=[Detection(class_="leaf_curl", label="Leaf Curl (uncertain)", confidence=0.42, bbox=[30, 25, 35, 40])],
            severity=Severity(level="low", affected_area_percent=6, is_demo=True),
            is_demo=True,
        ),
        DetectionResult(
            crop="Cotton",
            detections=[Detection(class_="bollworm_damage", label="Bollworm Damage", confidence=0.81, bbox=[20, 30, 50, 45])],
            severity=Severity(level="high", affected_area_percent=34, is_demo=True),
            is_demo=True,
        ),
        DetectionResult(
            crop="Cotton",
            detections=[],
            severity=Severity(level="low", affected_area_percent=0, is_demo=True),
            is_demo=True,
        ),
    ],
    "soybean": [
        DetectionResult(
            crop="Soybean",
            detections=[Detection(class_="soybean_rust", label="Soybean Rust", confidence=0.77, bbox=[25, 20, 40, 35])],
            severity=Severity(level="moderate", affected_area_percent=15, is_demo=True),
            is_demo=True,
        ),
        DetectionResult(
            crop="Soybean",
            detections=[],
            severity=Severity(level="low", affected_area_percent=0, is_demo=True),
            is_demo=True,
        ),
    ],
    "wheat": [
        DetectionResult(
            crop="Wheat",
            detections=[Detection(class_="wheat_rust", label="Wheat Rust", confidence=0.88, bbox=[20, 15, 55, 50])],
            severity=Severity(level="moderate", affected_area_percent=27, is_demo=True),
            is_demo=True,
        ),
        DetectionResult(
            crop="Wheat",
            detections=[],
            severity=Severity(level="low", affected_area_percent=0, is_demo=True),
            is_demo=True,
        ),
    ],
    "rice": [
        DetectionResult(
            crop="Rice",
            detections=[Detection(class_="rice_blast", label="Rice Blast", confidence=0.91, bbox=[18, 12, 60, 55])],
            severity=Severity(level="high", affected_area_percent=44, is_demo=True),
            is_demo=True,
        ),
        DetectionResult(
            crop="Rice",
            detections=[],
            severity=Severity(level="low", affected_area_percent=0, is_demo=True),
            is_demo=True,
        ),
    ],
}

# Fallback pool for a crop that isn't in the registry above yet — better to
# return something clearly-demo than a 500 for an unrecognized crop string.
_FALLBACK_POOL = CROP_DEMO_OUTCOMES["tomato"]


def get_demo_outcome(crop: str, image_bytes: bytes) -> DetectionResult:
    pool = CROP_DEMO_OUTCOMES.get(crop.strip().lower(), _FALLBACK_POOL)
    digest = int.from_bytes(image_bytes[:8] or b"\x00", "big") if image_bytes else 0
    # Fall back to a length-based pick for tiny/empty inputs so this never
    # raises on an edge-case upload.
    index = (digest or len(image_bytes)) % len(pool)
    return pool[index]
