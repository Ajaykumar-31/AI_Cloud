from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ServerBase(BaseModel):
    server_name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = "ONLINE"

    @validator('status')
    def validate_status(cls, v):
        if v not in ["ONLINE", "OFFLINE", "WARNING", "CRITICAL"]:
            raise ValueError('Status must be ONLINE, OFFLINE, WARNING, or CRITICAL')
        return v

class ServerCreate(ServerBase):
    pass

class ServerUpdate(BaseModel):
    server_name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ["ONLINE", "OFFLINE", "WARNING", "CRITICAL"]:
            raise ValueError('Status must be ONLINE, OFFLINE, WARNING, or CRITICAL')
        return v

class MetricCreate(BaseModel):
    cpu_usage: float = Field(..., ge=0.0, le=100.0)
    memory_usage: float = Field(..., ge=0.0, le=100.0)
    storage_usage: float = Field(..., ge=0.0, le=100.0)
    network_usage: float = Field(..., ge=0.0, le=100.0)
