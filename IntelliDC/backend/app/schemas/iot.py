from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class IoTDeviceBase(BaseModel):
    device_id: str
    device_name: str
    location: str
    mac_address: str
    sensor_types: List[str] = []
    status: Optional[str] = "OFFLINE"
    firmware_version: str

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ["ONLINE", "OFFLINE", "WARNING"]:
            raise ValueError('Status must be ONLINE, OFFLINE, or WARNING')
        return v

class IoTDeviceCreate(IoTDeviceBase):
    pass

class IoTDeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    location: Optional[str] = None
    mac_address: Optional[str] = None
    sensor_types: Optional[List[str]] = None
    status: Optional[str] = None
    firmware_version: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ["ONLINE", "OFFLINE", "WARNING"]:
            raise ValueError('Status must be ONLINE, OFFLINE, or WARNING')
        return v

class IoTDeviceResponse(IoTDeviceBase):
    id: str
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SensorReading(BaseModel):
    device_id: str
    thingspeak_entry_id: Optional[int] = None
    temperature: Optional[float] = Field(None, ge=-50.0, le=100.0)
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0)
    current: Optional[float] = Field(None, ge=0.0)
    power: Optional[float] = Field(None, ge=0.0)
    timestamp: datetime
    source: Optional[str] = None
