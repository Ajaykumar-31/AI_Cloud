from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    severity: str
    title: str
    source: str
    server_id: Optional[int] = None
    device_id: Optional[int] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    description: Optional[str] = None
    status: str = "open"
    ai_recommendation_id: Optional[int] = None

class AlertResponse(AlertBase):
    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
