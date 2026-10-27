from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class WorkloadBase(BaseModel):
    workload_name: str
    application_type: str
    department: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
    criticality: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    sensitivity: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
    preferred_server_id: Optional[int] = None
    status: str = "pending"

class WorkloadCreate(WorkloadBase):
    pass

class WorkloadUpdate(BaseModel):
    workload_name: Optional[str] = None
    application_type: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    criticality: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    sensitivity: Optional[Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]] = None
    preferred_server_id: Optional[int] = None
    status: Optional[str] = None

class WorkloadResponse(WorkloadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
