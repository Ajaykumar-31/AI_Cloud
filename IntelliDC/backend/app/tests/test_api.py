from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import settings

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "IntelliDC API"
    }


def test_firestore_crud():
    # Create
    create_resp = client.post(
        "/api/test/firestore",
        json={
            "message": "test",
            "value": 42
        }
    )

    assert create_resp.status_code == 200

    # Read
    read_resp = client.get("/api/test/firestore")

    assert read_resp.status_code == 200

    data = read_resp.json().get("data", {})

    assert data.get("message") == "test"
    assert data.get("value") == 42


def test_admin_login():
    # Use the same credentials configured in .env
    response = client.post(
        "/api/auth/login",
        data={
            "username": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD
        }
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test /me
    headers = {
        "Authorization": f"Bearer {data['access_token']}"
    }

    me_resp = client.get(
        "/api/auth/me",
        headers=headers
    )

    assert me_resp.status_code == 200

    me_data = me_resp.json()

    assert me_data.get("email") == settings.ADMIN_EMAIL
    assert me_data.get("role") == "ADMIN"


def test_servers_no_auth():
    response = client.get("/api/servers")

    assert response.status_code == 401


def test_iot_devices_no_auth():
    response = client.get("/api/iot/devices")

    assert response.status_code == 401


def test_workloads_no_auth():
    response = client.get("/api/workloads")

    assert response.status_code == 401


def test_alerts_no_auth():
    response = client.get("/api/alerts")

    assert response.status_code == 401


def test_reports_no_auth():
    response = client.get("/api/reports/infrastructure")

    assert response.status_code == 401

# --- Server & Infrastructure Tests ---

def get_auth_headers():
    response = client.post(
        "/api/auth/login",
        data={
            "username": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD
        }
    )
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}

def test_servers_no_auth_again():
    assert client.get("/api/servers").status_code == 401
    assert client.post("/api/servers", json={"server_name": "Test"}).status_code == 401

def test_servers_crud():
    headers = get_auth_headers()
    
    # Create server
    create_payload = {
        "server_name": "Test-Server-A",
        "hostname": "test-a",
        "ip_address": "10.0.0.1",
        "location": "Rack-B"
    }
    create_resp = client.post("/api/servers", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    server_data = create_resp.json()
    assert "id" in server_data
    server_id = server_data["id"]
    
    # Get server
    get_resp = client.get(f"/api/servers/{server_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["server_name"] == "Test-Server-A"
    
    # Update server
    update_payload = {"status": "WARNING"}
    update_resp = client.put(f"/api/servers/{server_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "WARNING"
    
    # Create metric
    metric_payload = {
        "cpu_usage": 45.5,
        "memory_usage": 60.0,
        "storage_usage": 70.0,
        "network_usage": 10.5
    }
    metric_resp = client.post(f"/api/servers/{server_id}/metrics", json=metric_payload, headers=headers)
    assert metric_resp.status_code == 201
    
    # Get metrics
    metrics_get_resp = client.get(f"/api/servers/{server_id}/metrics", headers=headers)
    assert metrics_get_resp.status_code == 200
    metrics_data = metrics_get_resp.json()
    assert metrics_data["server_id"] == server_id
    assert len(metrics_data["metrics"]) > 0
    
    # Invalid CPU > 100
    bad_metric_1 = {**metric_payload, "cpu_usage": 105.0}
    bad_resp_1 = client.post(f"/api/servers/{server_id}/metrics", json=bad_metric_1, headers=headers)
    assert bad_resp_1.status_code == 422
    
    # Invalid RAM < 0
    bad_metric_2 = {**metric_payload, "memory_usage": -5.0}
    bad_resp_2 = client.post(f"/api/servers/{server_id}/metrics", json=bad_metric_2, headers=headers)
    assert bad_resp_2.status_code == 422
    
    # Non-existent server (Firestore returns 404)
    not_found_resp = client.get("/api/servers/does_not_exist_999", headers=headers)
    assert not_found_resp.status_code == 404
    
    # Delete server
    delete_resp = client.delete(f"/api/servers/{server_id}", headers=headers)
    assert delete_resp.status_code in [200, 204]

# --- IoT Device Tests ---

def test_iot_devices_no_auth_again():
    assert client.post("/api/iot/devices", json={"device_id": "test"}).status_code == 401

def test_iot_devices_crud():
    headers = get_auth_headers()
    
    device_payload = {
        "device_id": "esp32_test_001",
        "device_name": "Test-ESP32",
        "location": "Rack-C",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "sensor_types": ["DHT22", "ACS712"],
        "status": "OFFLINE",
        "firmware_version": "1.0.0"
    }
    
    # Create device
    create_resp = client.post("/api/iot/devices", json=device_payload, headers=headers)
    assert create_resp.status_code == 201
    
    # Duplicate device_id
    dup_resp = client.post("/api/iot/devices", json=device_payload, headers=headers)
    assert dup_resp.status_code == 409
    
    # Get all devices
    get_all_resp = client.get("/api/iot/devices", headers=headers)
    assert get_all_resp.status_code == 200
    assert len(get_all_resp.json()["devices"]) > 0
    
    # Get specific device
    get_one_resp = client.get("/api/iot/devices/esp32_test_001", headers=headers)
    assert get_one_resp.status_code == 200
    assert get_one_resp.json()["device_name"] == "Test-ESP32"
    
    # Update device
    update_resp = client.put("/api/iot/devices/esp32_test_001", json={"status": "WARNING"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "WARNING"
    
    # Heartbeat
    hb_resp = client.post("/api/iot/devices/esp32_test_001/heartbeat", headers=headers)
    assert hb_resp.status_code == 200
    assert hb_resp.json()["status"] == "ONLINE"
    
    # Valid reading
    reading_payload = {
        "device_id": "esp32_test_001",
        "temperature": 25.5,
        "humidity": 50.0,
        "current": 1.2,
        "power": 12.0,
        "timestamp": "2026-10-06T00:00:00Z"
    }
    client.post("/api/iot/devices/esp32_test_001/readings", json=reading_payload, headers=headers)

    # Invalid humidity > 100
    bad_humidity = {**reading_payload, "humidity": 150.0}
    assert client.post("/api/iot/devices/esp32_test_001/readings", json=bad_humidity, headers=headers).status_code == 422
    
    # Negative current
    bad_current = {**reading_payload, "current": -1.0}
    assert client.post("/api/iot/devices/esp32_test_001/readings", json=bad_current, headers=headers).status_code == 422
    
    # Negative power
    bad_power = {**reading_payload, "power": -5.0}
    assert client.post("/api/iot/devices/esp32_test_001/readings", json=bad_power, headers=headers).status_code == 422
    
    # Non-existent device (404)
    assert client.get("/api/iot/devices/does_not_exist_999", headers=headers).status_code == 404
    
    # Delete device
    delete_resp = client.delete("/api/iot/devices/esp32_test_001", headers=headers)
    assert delete_resp.status_code in [200, 204]

# --- ThingSpeak Integration Tests ---

from unittest.mock import patch, Mock
import requests
from app.services.thingspeak_service import thingspeak_service

def test_thingspeak_unauth():
    assert client.get("/api/iot/thingspeak/latest?device_id=test").status_code == 401
    assert client.post("/api/iot/thingspeak/sync?device_id=test").status_code == 401

@patch('app.services.thingspeak_service.requests.get')
def test_thingspeak_integration(mock_get):
    headers = get_auth_headers()
    
    # 1. Create a device first
    client.post("/api/iot/devices", json={
        "device_id": "ts_device_001",
        "device_name": "TS-Device",
        "location": "Lab",
        "mac_address": "00:11:22:33:44:55",
        "sensor_types": ["DHT22"],
        "status": "OFFLINE",
        "firmware_version": "1.0.0"
    }, headers=headers)

    thingspeak_service.channel_id = "test_channel"

    # 2. Test successful get
    mock_response = Mock()
    mock_response.json.return_value = {
        "created_at": "2026-10-06T10:00:00Z",
        "entry_id": 12345,
        "field1": "22.5",
        "field2": "45.0",
        "field3": "1.5",
        "field4": "15.0"
    }
    mock_get.return_value = mock_response
    
    get_resp = client.get("/api/iot/thingspeak/latest?device_id=ts_device_001", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["temperature"] == 22.5
    assert data["thingspeak_entry_id"] == 12345

    # 3. Test successful sync
    sync_resp = client.post("/api/iot/thingspeak/sync?device_id=ts_device_001", headers=headers)
    assert sync_resp.status_code == 201 or sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["source"] == "thingspeak"
    assert sync_data["device_id"] == "ts_device_001"
    
    # Verify device status updated to ONLINE
    dev_resp = client.get("/api/iot/devices/ts_device_001", headers=headers)
    assert dev_resp.json()["status"] == "ONLINE"

    # 4. Invalid ThingSpeak response (malformed)
    mock_response.json.return_value = {"junk": "data"}
    malformed_resp = client.get("/api/iot/thingspeak/latest?device_id=ts_device_001", headers=headers)
    assert malformed_resp.status_code == 422
    
    # 5. Missing temperature
    mock_response.json.return_value = {"field2": "45.0", "field3": "1.5", "field4": "15.0"}
    miss_temp = client.get("/api/iot/thingspeak/latest?device_id=ts_device_001", headers=headers)
    assert miss_temp.status_code == 422

    # 6. Missing humidity
    mock_response.json.return_value = {"field1": "22.5", "field3": "1.5", "field4": "15.0"}
    miss_hum = client.get("/api/iot/thingspeak/latest?device_id=ts_device_001", headers=headers)
    assert miss_hum.status_code == 422

    # 7. Invalid current (negative or string not parsing to positive)
    mock_response.json.return_value = {"field1": "22.5", "field2": "45.0", "field3": "not_a_number", "field4": "15.0"}
    inv_curr = client.get("/api/iot/thingspeak/latest?device_id=ts_device_001", headers=headers)
    assert inv_curr.status_code == 422
    
    # 8. Invalid power (negative value can be tested during validation check or parse, here let's just use string parsing failure as requested or let schema fail it on sync)
    # Actually wait, the service endpoint GET does NOT use Pydantic schema for output validation if not set, but sync does.
    # Sync will fail 422 if power is negative. Let's test sync for negative power.
    mock_response.json.return_value = {"field1": "22.5", "field2": "45.0", "field3": "1.5", "field4": "-10.0"}
    inv_power = client.post("/api/iot/thingspeak/sync?device_id=ts_device_001", headers=headers)
    assert inv_power.status_code == 422

    # 9. ThingSpeak timeout
    mock_get.side_effect = requests.exceptions.Timeout("Timeout")
    timeout_resp = client.get("/api/iot/thingspeak/latest?device_id=ts_device_001", headers=headers)
    assert timeout_resp.status_code == 504
    mock_get.side_effect = None # reset
    
    # 10. Non-existent device
    not_found = client.get("/api/iot/thingspeak/latest?device_id=does_not_exist_999", headers=headers)
    assert not_found.status_code == 404
    
    # Cleanup
    client.delete("/api/iot/devices/ts_device_001", headers=headers)