from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "ADMIN"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Server Schemas
class ServerBase(BaseModel):
    server_name: str
    hostname: str
    ip_address: str
    status: str = "active"
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    storage_usage: float = 0.0
    network_usage: float = 0.0
    uptime: float = 0.0

class ServerCreate(ServerBase):
    pass

class ServerResponse(ServerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Workload Schemas
class WorkloadBase(BaseModel):
    workload_name: str
    application_type: str
    department: str
    priority: int = 1
    criticality: str
    sensitivity: str
    preferred_server_id: Optional[int] = None
    status: str = "pending"

class WorkloadCreate(WorkloadBase):
    pass

class WorkloadResponse(WorkloadBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# IoT Device Schemas
class IoTDeviceBase(BaseModel):
    device_id: str
    device_name: str
    location: str
    mac_address: str
    status: str = "online"
    firmware_version: str

class IoTDeviceCreate(IoTDeviceBase):
    pass

class IoTDeviceResponse(IoTDeviceBase):
    id: int
    last_seen: datetime
    created_at: datetime
    class Config:
        from_attributes = True
