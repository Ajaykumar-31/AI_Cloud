from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
from app.services.firestore_service import FirestoreService
from app.routers.auth import get_current_user
from app.schemas.iot import IoTDeviceCreate, IoTDeviceUpdate, SensorReading

router = APIRouter(prefix="/api/iot", tags=["iot"])
iot_devices_collection = FirestoreService("iot_devices")

@router.get("/devices")
def get_devices(current_user: dict = Depends(get_current_user)):
    devices = iot_devices_collection.list_documents()
    return {"devices": devices}

@router.get("/devices/{device_id}")
def get_device(device_id: str, current_user: dict = Depends(get_current_user)):
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    return existing[0]

@router.post("/devices", status_code=status.HTTP_201_CREATED)
def create_device(device_data: IoTDeviceCreate, current_user: dict = Depends(get_current_user)):
    existing = iot_devices_collection.query_documents("device_id", "==", device_data.device_id)
    if existing:
        raise HTTPException(status_code=409, detail="Device ID already registered")
        
    data = device_data.model_dump()
    timestamp = datetime.now(timezone.utc).isoformat()
    data["last_seen"] = None
    data["created_at"] = timestamp
    data["updated_at"] = timestamp
    
    doc_id = iot_devices_collection.create_document(data=data)
    return iot_devices_collection.get_document(doc_id)

@router.put("/devices/{device_id}")
def update_device(device_id: str, device_data: IoTDeviceUpdate, current_user: dict = Depends(get_current_user)):
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    device_doc = existing[0]
        
    update_dict = device_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    return iot_devices_collection.update_document(device_doc["id"], update_dict)

@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: str, current_user: dict = Depends(get_current_user)):
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    device_doc = existing[0]
    
    iot_devices_collection.delete_document(device_doc["id"])
    return None

@router.post("/devices/{device_id}/heartbeat")
def device_heartbeat(device_id: str, current_user: dict = Depends(get_current_user)):
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    device_doc = existing[0]
    
    timestamp = datetime.now(timezone.utc).isoformat()
    update_dict = {
        "status": "ONLINE",
        "last_seen": timestamp,
        "updated_at": timestamp
    }
    iot_devices_collection.update_document(device_doc["id"], update_dict)
    
    return {
        "message": "Device heartbeat updated",
        "device_id": device_id,
        "status": "ONLINE",
        "last_seen": timestamp
    }

sensor_readings_collection = FirestoreService("sensor_readings")

@router.post("/devices/{device_id}/readings", status_code=status.HTTP_201_CREATED)
def add_device_reading(device_id: str, reading: SensorReading, current_user: dict = Depends(get_current_user)):
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    
    data = reading.model_dump()
    data["device_id"] = device_id
    doc_id = sensor_readings_collection.create_document(data=data)
    return sensor_readings_collection.get_document(doc_id)

from app.services.thingspeak_service import thingspeak_service

from pydantic import ValidationError

@router.get("/thingspeak/latest")
def get_thingspeak_latest(device_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id parameter is required")
        
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
        
    reading = thingspeak_service.get_latest_reading(device_id)
    try:
        SensorReading(**reading)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return reading

@router.post("/thingspeak/sync")
def sync_thingspeak(device_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id parameter is required")
        
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    device_doc = existing[0]
        
    reading = thingspeak_service.get_latest_reading(device_id)
    reading["source"] = "thingspeak"
    
    try:
        validated = SensorReading(**reading)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    # Store reading if not exists using entry_id
    doc_id = f"{device_id}_{reading.get('thingspeak_entry_id')}"
    try:
        sensor_readings_collection.create_document(document_id=doc_id, data=validated.model_dump())
    except HTTPException as e:
        if e.status_code != 400:
            raise
    
    # Update device status
    timestamp = datetime.now(timezone.utc).isoformat()
    update_dict = {
        "status": "ONLINE",
        "last_seen": timestamp,
        "updated_at": timestamp
    }
    iot_devices_collection.update_document(device_doc["id"], update_dict)
    
    return sensor_readings_collection.get_document(doc_id)

@router.get("/devices/{device_id}/historical", summary="Get historical IoT telemetry")
def get_historical_readings(
    device_id: str, 
    limit: int = 100, 
    start_time: Optional[str] = None, 
    end_time: Optional[str] = None, 
    current_user: dict = Depends(get_current_user)
):
    """Retrieve historical readings from Firestore by device ID with limit and optional time filters."""
    existing = iot_devices_collection.query_documents("device_id", "==", device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        query = sensor_readings_collection.collection.where("device_id", "==", device_id)
        if start_time:
            query = query.where("timestamp", ">=", start_time)
        if end_time:
            query = query.where("timestamp", "<=", end_time)
            
        # Order by timestamp descending and limit
        query = query.order_by("timestamp", direction="DESCENDING").limit(limit)
        
        results = []
        for doc in query.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")

async def sync_all_thingspeak_devices():
    """Background task to sync all IoT devices configured for thingspeak."""
    try:
        devices = iot_devices_collection.list_documents()
        for device in devices:
            device_id = device.get("device_id")
            if not device_id:
                continue
            
            try:
                readings = thingspeak_service.get_historical_readings(device_id, results=20)
                
                latest_timestamp = None
                for reading in readings:
                    if reading.get("thingspeak_entry_id") is None:
                        continue
                        
                    doc_id = f"{device_id}_{reading['thingspeak_entry_id']}"
                    try:
                        sensor_readings_collection.create_document(document_id=doc_id, data=reading)
                        if not latest_timestamp or reading["timestamp"] > latest_timestamp:
                            latest_timestamp = reading["timestamp"]
                    except HTTPException as e:
                        if e.status_code != 400: # Ignore already exists error
                            print(f"Error saving reading {doc_id}: {e.detail}")
                            
                if latest_timestamp:
                    timestamp = datetime.now(timezone.utc).isoformat()
                    update_dict = {
                        "status": "ONLINE",
                        "last_seen": timestamp,
                        "updated_at": timestamp
                    }
                    iot_devices_collection.update_document(device["id"], update_dict)
            except Exception as e:
                print(f"Failed to sync device {device_id}: {e}")
    except Exception as e:
        print(f"Global sync error: {e}")





