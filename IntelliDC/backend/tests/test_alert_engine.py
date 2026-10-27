import pytest
from app.ai.alert_engine import (
    generate_alerts, map_risk_to_severity, compute_priority, alerts_collection
)
from app.routers.alerts import _update_status
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import get_current_user
import uuid

client = TestClient(app)

def test_map_risk_to_severity():
    assert map_risk_to_severity(20) == "INFO"
    assert map_risk_to_severity(40) == "LOW"
    assert map_risk_to_severity(60) == "MEDIUM"
    assert map_risk_to_severity(80) == "HIGH"
    assert map_risk_to_severity(95) == "CRITICAL"

def test_compute_priority():
    # Stale always gets 100
    assert compute_priority("CRITICAL", 100, "CRITICAL", True) == 100
    
    # Priority = (Severity Base) + (Workload Adjustment) - (Risk Score / 100) -> Wait, it was / 20.0
    # CRITICAL base = 10, Workload CRITICAL = 0, score 100 -> 10 + 0 - 5 = 5
    p1 = compute_priority("CRITICAL", 100.0, "CRITICAL", False)
    assert p1 == 5
    
    # INFO base = 50, Workload LOW = 6, score 10 -> 50 + 6 - 0.5 = 55
    p2 = compute_priority("INFO", 10.0, "LOW", False)
    assert p2 == 55
    
    assert p1 < p2  # p1 is higher priority

def test_generate_alerts_and_deduplication():
    server_id = f"test_server_{uuid.uuid4().hex[:6]}"
    
    agent_results = [
        {"agent_name": "TestAgent", "score": 80.0, "risk_level": "HIGH", "factors": ["High memory usage"]}
    ]
    
    # 1. First run, generates new alert
    alerts = generate_alerts(server_id, agent_results, "MEDIUM", False)
    assert len(alerts) == 1
    a1 = alerts[0]
    assert a1.severity == "HIGH"
    assert a1.status == "NEW"
    
    # 2. Second run, should deduplicate and update existing
    alerts2 = generate_alerts(server_id, agent_results, "MEDIUM", False)
    assert len(alerts2) == 1
    a2 = alerts2[0]
    assert a1.id == a2.id  # Same document updated
    assert a1.fingerprint == a2.fingerprint
    
    # 3. Acknowledge the alert
    _update_status(a1.id, "ACKNOWLEDGED")
    
    # 4. Third run, should STILL update the same alert because ACKNOWLEDGED is unresolved
    alerts3 = generate_alerts(server_id, agent_results, "MEDIUM", False)
    assert alerts3[0].id == a1.id
    
    # 5. Resolve the alert
    _update_status(a1.id, "RESOLVED")
    
    # 6. Fourth run, should create a NEW alert because previous is resolved
    alerts4 = generate_alerts(server_id, agent_results, "MEDIUM", False)
    assert alerts4[0].id != a1.id
    assert alerts4[0].status == "NEW"


def test_missing_stale_telemetry_alerts():
    server_id = f"test_server_{uuid.uuid4().hex[:6]}"
    
    # Even if an agent reports a high score, if it's stale, it shouldn't generate a normal CRITICAL alert
    agent_results = [
        {"agent_name": "TestAgent", "score": 90.0, "risk_level": "CRITICAL", "factors": ["High memory usage"]}
    ]
    
    alerts = generate_alerts(server_id, agent_results, "CRITICAL", True)
    assert len(alerts) == 1 # Only the STALE alert
    assert alerts[0].title == "Stale Telemetry Data"
    assert alerts[0].priority == 100


def test_invalid_status_transitions():
    server_id = f"test_server_{uuid.uuid4().hex[:6]}"
    alerts = generate_alerts(server_id, [{"agent_name": "Test", "score": 90.0}], "LOW", False)
    alert_id = alerts[0].id
    
    # NEW -> DISMISSED is valid
    _update_status(alert_id, "DISMISSED")
    
    from fastapi import HTTPException
    # DISMISSED -> RESOLVED is invalid
    with pytest.raises(HTTPException, match="Invalid transition"):
        _update_status(alert_id, "RESOLVED")


def test_endpoints():
    original_override = app.dependency_overrides.get(get_current_user)
    def override_get_current_user():
        return {"id": "admin", "role": "admin"}
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # test get alerts with filter
    res = client.get("/api/alerts?severity=INFO")
    assert res.status_code == 200
    
    app.dependency_overrides.pop(get_current_user, None)
    
    # Test auth failure
    res_unauth = client.post("/api/alerts/dummy_id/acknowledge")
    assert res_unauth.status_code == 401
    
    if original_override:
        app.dependency_overrides[get_current_user] = original_override
