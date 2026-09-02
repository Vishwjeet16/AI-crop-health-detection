"""
AI service — the pipeline behind POST /api/analyze.

    image bytes
        -> preprocessing
        -> detection (YOLO in production mode; canned results in demo mode)
        -> segmentation / severity estimate
        -> (risk + recommendation are composed by the route, not here —
            they need field/weather/history context this module doesn't have)

AI_MODE controls which path runs:

  * "demo"       — returns a crop-aware, realistic canned result from
                    app/services/demo_outcomes.py. No model file required.
  * "production" — loads backend/models/cropguard-yolo.pt (see
                    ml/training/train.py) and runs real inference. If
                    AI_MODE=production but no weights file is present, this
                    module logs a warning and falls back to demo mode
                    rather than crashing the request.

`analyze_image()`'s public contract (bytes + crop in, DetectionResult out)
is the same regardless of mode, so the route calling this never needs to
know which one is active.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from PIL import Image

from app.config import get_settings
from app.schemas.scans import Detection, Severity
from app.services import severity_service
from app.services.demo_outcomes import get_demo_outcome
from app.services.detection_result import DetectionResult

logger = logging.getLogger("ai_service")

MODEL_WEIGHTS_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "cropguard-yolo.pt"

_model_cache = None  # lazy-loaded, process-wide singleton — see _load_model()


def _yolo_available() -> bool:
    return MODEL_WEIGHTS_PATH.exists()


def _load_model():
    global _model_cache
    if _model_cache is None:
        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise RuntimeError(
                "AI_MODE=production requires ultralytics. Run: pip install ultralytics "
                "(see backend/requirements.txt — it's commented out until this stage is in use)."
            ) from e
        logger.info("Loading YOLO weights from %s", MODEL_WEIGHTS_PATH)
        _model_cache = YOLO(str(MODEL_WEIGHTS_PATH))
    return _model_cache


def _run_yolo_inference(image: Image.Image, crop: str) -> DetectionResult:
    model = _load_model()
    results = model(image)[0]

    img_w, img_h = image.size
    detections: list[Detection] = []
    boxes_percent: list[tuple[float, float, float, float]] = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        raw_label = model.names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # Convert absolute pixel coords to percentages of the image frame,
        # matching the contract DetectionResult (and the frontend's
        # DetectionResult component) expect — see section 12 of the spec.
        bbox_percent = (
            (x1 / img_w) * 100,
            (y1 / img_h) * 100,
            ((x2 - x1) / img_w) * 100,
            ((y2 - y1) / img_h) * 100,
        )
        detections.append(
            Detection(
                class_=raw_label,
                label=raw_label.replace("_", " ").title(),
                confidence=confidence,
                bbox=list(bbox_percent),
            )
        )
        boxes_percent.append(bbox_percent)

    # Affected-area estimate via real color-based segmentation (see
    # severity_service.py) rather than the box-area-sum proxy Stage 6
    # shipped — restricted to the union of detection boxes when there are
    # any, so the estimate reflects tissue condition within the region
    # YOLO actually flagged, not just the box's rectangle.
    affected_area_percent = severity_service.estimate_affected_area_percent(
        image, boxes_percent=boxes_percent or None
    )

    severity = Severity(
        level=severity_service.severity_level_from_area(affected_area_percent),
        affected_area_percent=affected_area_percent,
        is_demo=False,
    )

    return DetectionResult(crop=crop, detections=detections, severity=severity, is_demo=False)


async def preprocess_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("RGB")
    except Exception as exc:  # noqa: BLE001 — any Pillow failure means a bad/corrupt image
        raise ValueError("Could not read this image. Please try a different photo.") from exc
    return image


async def analyze_image(image_bytes: bytes, crop: str = "tomato") -> DetectionResult:
    settings = get_settings()
    image = await preprocess_image(image_bytes)

    if settings.ai_mode == "production":
        if _yolo_available():
            return _run_yolo_inference(image, crop)
        logger.warning(
            "AI_MODE=production but no model weights found at %s — falling back to demo mode.",
            MODEL_WEIGHTS_PATH,
        )
        result = get_demo_outcome(crop, image_bytes)
        result.demo_reason = "No trained model connected yet."
        return result

    result = get_demo_outcome(crop, image_bytes)
    result.demo_reason = "AI_MODE=demo"
    return result
