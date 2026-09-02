from dataclasses import dataclass, field

from app.schemas.scans import Detection, Severity


@dataclass
class DetectionResult:
    crop: str
    detections: list[Detection]
    severity: Severity
    is_demo: bool
    demo_reason: str | None = field(default=None)
