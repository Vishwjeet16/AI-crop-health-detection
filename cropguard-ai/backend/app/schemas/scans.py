from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["healthy", "moderate", "high"]
SeverityLevel = Literal["low", "moderate", "high", "critical"]


class Detection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(alias="class")
    label: str
    confidence: float
    bbox: list[float]  # [x%, y%, width%, height%] of the image frame


class Severity(BaseModel):
    level: SeverityLevel
    affected_area_percent: float
    is_demo: bool


class Risk(BaseModel):
    level: RiskLevel
    score: int
    factors: list[str]


class Weather(BaseModel):
    temperature_c: float
    humidity_percent: float
    rain_probability_percent: float
    wind_kph: float
    condition: str
    disease_risk_note: str


class Recommendation(BaseModel):
    title: str
    actions: list[str]
    prevention: list[str]
    next_scan: str


class ScanOut(BaseModel):
    id: str
    field_id: str
    image_url: str
    timestamp: str
    crop: str
    is_demo: bool
    detections: list[Detection]
    severity: Severity
    risk: Risk
    weather: Optional[Weather] = None
    recommendation: Recommendation


class HistoryPoint(BaseModel):
    date: str
    affected_area_percent: float
    severity: SeverityLevel
    risk: RiskLevel
