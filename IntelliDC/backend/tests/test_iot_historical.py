import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app
from app.services.thingspeak_service import ThingSpeakService

client = TestClient(app)

# Mock user for auth
def override_get_current_user():
    return {"id": "admin_user", "role": "admin"}
    
from app.routers.auth import get_current_user
app.dependency_overrides[get_current_user] = override_get_current_user

# Mock Firestore
@pytest.fixture
def mock_firestore():
    with patch("app.routers.iot.sensor_readings_collection") as mock_sensor, \
         patch("app.routers.iot.iot_devices_collection") as mock_device:
        yield mock_sensor, mock_device

@pytest.fixture
def mock_thingspeak():
    with patch("app.routers.iot.thingspeak_service") as mock_ts:
        yield mock_ts

def test_get_historical_readings_auth_required():
    app.dependency_overrides.pop(get_current_user, None)
    response = client.get("/api/iot/devices/test_dev/historical")
    assert response.status_code == 401
    app.dependency_overrides[get_current_user] = override_get_current_user

def test_get_historical_readings_pagination(mock_firestore):
    mock_sensor, mock_device = mock_firestore
    mock_device.query_documents.return_value = [{"id": "doc1", "device_id": "esp32_001"}]
    
    mock_query = MagicMock()
    mock_sensor.collection.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {"temperature": 25.0}
    mock_doc.id = "mock_id"
    mock_query.stream.return_value = [mock_doc, mock_doc]
    
    response = client.get("/api/iot/devices/esp32_001/historical?limit=2&start_time=2023-01-01T00:00:00Z")
    assert response.status_code == 200
    assert len(response.json()) == 2
    
    mock_sensor.collection.where.assert_called_with("device_id", "==", "esp32_001")
    mock_query.where.assert_called_with("timestamp", ">=", "2023-01-01T00:00:00Z")
    mock_query.limit.assert_called_with(2)

def test_thingspeak_timestamp_parsing():
    ts = ThingSpeakService()
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feeds": [
                {"entry_id": 1, "field1": "25.5", "created_at": "2023-10-10T12:00:00Z"},
                {"entry_id": 2, "field1": "invalid", "created_at": "2023-10-10T12:10:00Z"}
            ]
        }
        mock_get.return_value = mock_response
        readings = ts.get_historical_readings("esp32_001")
        assert len(readings) == 2
        assert readings[0]["temperature"] == 25.5
        assert readings[0]["timestamp"] == "2023-10-10T12:00:00Z"
        assert readings[1]["temperature"] is None

def test_sync_duplicate_prevention(mock_firestore, mock_thingspeak):
    mock_sensor, mock_device = mock_firestore
    mock_device.query_documents.return_value = [{"id": "doc1", "device_id": "esp32_001"}]
    
    mock_thingspeak.get_latest_reading.return_value = {
        "device_id": "esp32_001",
        "thingspeak_entry_id": 123,
        "temperature": 25.0,
        "humidity": 50.0,
        "current": 1.0,
        "power": 220.0,
        "timestamp": "2023-10-10T12:00:00Z"
    }
    
    # Simulate first insertion
    mock_sensor.create_document.return_value = "esp32_001_123"
    mock_sensor.get_document.return_value = {"id": "esp32_001_123"}
    
    response = client.post("/api/iot/thingspeak/sync?device_id=esp32_001")
    assert response.status_code == 200
    
    # Assert called with data having a datetime object
    called_args = mock_sensor.create_document.call_args[1]
    assert called_args["document_id"] == "esp32_001_123"
    assert called_args["data"]["device_id"] == "esp32_001"
    assert called_args["data"]["thingspeak_entry_id"] == 123
    assert called_args["data"]["temperature"] == 25.0
    
    # Simulate duplicate insertion error
    mock_sensor.create_document.side_effect = HTTPException(status_code=400, detail="Document already exists")
    
    response = client.post("/api/iot/thingspeak/sync?device_id=esp32_001")
    # Our API returns 200 for the sync endpoint but swallows the 400 error for create_document internally
    assert response.status_code == 200

def test_sync_failure(mock_firestore, mock_thingspeak):
    mock_sensor, mock_device = mock_firestore
    mock_device.query_documents.return_value = [{"id": "doc1", "device_id": "esp32_001"}]
    
    mock_thingspeak.get_latest_reading.side_effect = HTTPException(status_code=502, detail="ThingSpeak API Error")
    
    response = client.post("/api/iot/thingspeak/sync?device_id=esp32_001")
    assert response.status_code == 502
    assert response.json()["detail"] == "ThingSpeak API Error"
