from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime

class AdminDoc(BaseModel):
    email: EmailStr
    name: str
    role: str = "ADMIN"
    password_hash: str
    created_at: datetime
    updated_at: datetime

class ServerDoc(BaseModel):
    server_name: str
    hostname: str
    ip_address: str
    status: str
    location: str
    created_at: datetime
    updated_at: datetime

class InfrastructureMetricDoc(BaseModel):
    server_id: str
    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    storage_usage: float = Field(..., ge=0, le=100)
    network_usage: float = Field(..., ge=0, le=100)
    timestamp: datetime

class IoTDeviceDoc(BaseModel):
    device_id: str
    device_name: str
    location: str
    mac_address: str
    sensor_types: List[str]
    status: str
    last_seen: datetime
    created_at: datetime

class SensorReadingDoc(BaseModel):
    device_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = Field(None, ge=0, le=100)
    current: Optional[float] = Field(None, ge=0)
    power: Optional[float] = Field(None, ge=0)
    timestamp: datetime

class WorkloadDoc(BaseModel):
    workload_name: str
    application_type: str
    department: str
    priority: str
    criticality: str
    sensitivity: str
    preferred_server_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

class AgentResultDoc(BaseModel):
    server_id: str
    agent_name: str
    score: float
    risk_level: str
    factors: List[str]
    timestamp: datetime

class AIRecommendationDoc(BaseModel):
    server_id: str
    risk_score: float
    risk_level: str
    priority: str
    topsis_rank: Optional[int]
    topsis_score: Optional[float]
    agent_scores: Dict[str, float]
    contributing_factors: List[str]
    recommendation: str
    explanation: str
    status: str = "ADMINISTRATOR_REVIEW_REQUIRED"
    created_at: datetime

class AlertDoc(BaseModel):
    server_id: Optional[str] = None
    device_id: Optional[str] = None
    source: str
    metric: str
    value: float
    threshold: float
    severity: str
    message: str
    status: str = "ACTIVE"
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
