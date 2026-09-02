from typing import Literal, Optional

from pydantic import BaseModel, Field

RiskLevel = Literal["healthy", "moderate", "high"]


class FieldCreate(BaseModel):
    name: str
    crop: str
    area_acres: float = Field(gt=0)
    latitude: float
    longitude: float


class FieldOut(BaseModel):
    id: str
    name: str
    crop: str
    area_acres: float
    latitude: float
    longitude: float
    health_status: RiskLevel
    last_scan_at: Optional[str] = None
    last_disease: Optional[str] = None
    last_risk: Optional[RiskLevel] = None
