"""
Risk model.

Deliberately rule-based and documented rather than a second opaque model —
see section 9 of the README ("SIH Novelty") for why: judges (and farmers)
can see exactly why a score landed where it did. Never claims scientific
certainty; `factors` always lists what fed the score so the UI can show its
work.
"""

from app.schemas.scans import Risk

HIGH_THRESHOLD = 60
MODERATE_THRESHOLD = 30


def compute_risk(
    *,
    detection_confidence: float | None,
    affected_area_percent: float,
    humidity_percent: float,
    recent_trend_worsening: bool,
) -> Risk:
    score = 0.0
    factors: list[str] = []

    if detection_confidence:
        score += detection_confidence * 45
        factors.append("Current disease detection")

    score += min(affected_area_percent, 40) * 0.6
    if affected_area_percent > 0:
        factors.append("Estimated affected area")

    if humidity_percent >= 70:
        score += 12
        factors.append("Recent humidity")

    if recent_trend_worsening:
        score += 15
        factors.append("Previous field observations")

    score = round(min(score, 100))

    if score >= HIGH_THRESHOLD:
        level = "high"
    elif score >= MODERATE_THRESHOLD:
        level = "moderate"
    else:
        level = "healthy"

    if not factors:
        factors = ["No disease detected", "Stable weather conditions"]

    return Risk(level=level, score=int(score), factors=factors)
