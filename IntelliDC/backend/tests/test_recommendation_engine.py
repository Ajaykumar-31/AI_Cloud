import pytest
from app.ai.recommendation_engine import (
    generate_recommendations,
    update_recommendation_status,
    VALID_STATUS_TRANSITIONS,
    ai_recommendations_collection
)
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import get_current_user
import uuid

client = TestClient(app)

def test_generate_high_risk_and_duplicate_prevention():
    server_id = f"test_server_{uuid.uuid4().hex[:6]}"
    
    agent_results = [
        {"agent_name": "InfrastructureAgent", "factors": ["CPU Utilization is very high"]},
        {"agent_name": "EnvironmentalAgent", "factors": ["Temperature is dangerously high"]}
    ]
    
    # 1. First run (Normal + High risk)
    recs = generate_recommendations(server_id, agent_results)
    assert len(recs) == 2
    summaries = [r.summary for r in recs]
    assert "High CPU Utilization" in summaries
    assert "Thermal Warning" in summaries
    
    # Check severity
    for r in recs:
        if r.summary == "Thermal Warning":
            assert r.severity == "CRITICAL"
        elif r.summary == "High CPU Utilization":
            assert r.severity == "HIGH"
            
    # 2. Second run (Duplicate prevention)
    recs2 = generate_recommendations(server_id, agent_results)
    assert len(recs2) == 0 # Should prevent duplicates because previous are in NEW state

    # 3. Resolve them
    for r in recs:
        update_recommendation_status(r.id, "RESOLVED")
        
    # 4. Third run (Should recreate because previous are RESOLVED)
    recs3 = generate_recommendations(server_id, agent_results)
    assert len(recs3) == 2


def test_missing_telemetry_recommendation():
    server_id = f"test_server_missing_{uuid.uuid4().hex[:6]}"
    agent_results = [
        {"agent_name": "EnvironmentalAgent", "factors": ["Telemetry is MISSING"]}
    ]
    recs = generate_recommendations(server_id, agent_results)
    assert len(recs) == 1
    assert recs[0].summary == "Missing Telemetry"
    assert recs[0].severity == "UNKNOWN"
    assert recs[0].data_freshness == "Stale/Missing"
    assert recs[0].confidence == 0.0


def test_invalid_status_transitions():
    server_id = f"test_server_trans_{uuid.uuid4().hex[:6]}"
    recs = generate_recommendations(server_id, [{"agent_name": "EnvironmentalAgent", "factors": ["Temperature is high"]}])
    assert len(recs) == 1
    rec_id = recs[0].id
    
    # NEW -> RESOLVED is valid
    update_recommendation_status(rec_id, "RESOLVED")
    
    # RESOLVED -> ACCEPTED is invalid
    with pytest.raises(ValueError, match="Invalid transition"):
        update_recommendation_status(rec_id, "ACCEPTED")


def test_endpoint_authentication():
    # Attempt to patch without auth
    original_override = app.dependency_overrides.get(get_current_user)
    if get_current_user in app.dependency_overrides:
        app.dependency_overrides.pop(get_current_user)
        
    response = client.patch("/api/ai/recommendations/dummy_id/status", json={"status": "REVIEWED"})
    assert response.status_code == 401
    
    if original_override:
        app.dependency_overrides[get_current_user] = original_override
