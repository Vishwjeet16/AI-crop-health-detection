from typing import Literal

from pydantic import BaseModel

RiskLevel = Literal["healthy", "moderate", "high"]


class AlertOut(BaseModel):
    id: str
    field_id: str
    field_name: str
    message: str
    severity: RiskLevel
    created_at: str
    read: bool
