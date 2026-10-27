import pytest
from app.ai.weighted_scoring import (
    calculate_weighted_score,
    normalize_criterion,
    classify_risk,
)
from app.ai.scoring_config import validate_weights, update_weights, DEFAULT_WEIGHTS, reset_weights
from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import get_current_user

client = TestClient(app)

def test_validate_weights():
    assert validate_weights(DEFAULT_WEIGHTS) is True
    
    # Sum != 1
    invalid_weights = dict(DEFAULT_WEIGHTS)
    invalid_weights["cpu"] = 0.5
    assert validate_weights(invalid_weights) is False
    
    # Negative weight
    negative_weights = dict(DEFAULT_WEIGHTS)
    negative_weights["cpu"] = -0.25
    assert validate_weights(negative_weights) is False

def test_normalize_criterion():
    assert normalize_criterion("cpu", 50.0) == 50.0
    assert normalize_criterion("cpu", 150.0) == 100.0
    assert normalize_criterion("temperature", 17.5) == 50.0 # 35.0 max
    assert normalize_criterion("temperature", 35.0) == 100.0
    assert normalize_criterion("temperature", 70.0) == 100.0
    assert normalize_criterion("power", 3500.0) == 100.0
    assert normalize_criterion("invalid_metric", -10.0) is None
    assert normalize_criterion("cpu", None) is None

def test_classify_risk():
    assert classify_risk(0) == "Healthy"
    assert classify_risk(30) == "Healthy"
    assert classify_risk(31) == "Low"
    assert classify_risk(50) == "Low"
    assert classify_risk(51) == "Medium"
    assert classify_risk(70) == "Medium"
    assert classify_risk(71) == "High"
    assert classify_risk(85) == "High"
    assert classify_risk(86) == "Critical"
    assert classify_risk(100) == "Critical"

def test_calculate_weighted_score():
    reset_weights()
    criteria = {
        "cpu": 50.0,
        "ram": 50.0,
        "storage": 50.0,
        "network": 50.0,
        "temperature": 50.0,
        "power": 50.0,
        "humidity": 50.0,
        "workload_criticality": 50.0,
    }
    result = calculate_weighted_score(criteria)
    assert result.overall_score == 50.0
    assert result.risk_level == "Low"
    assert result.coverage == 1.0
    assert len(result.unavailable_criteria) == 0
    assert len(result.individual_contributions) == 8

def test_calculate_weighted_score_missing_data():
    reset_weights()
    # Provide only half the metrics
    criteria = {
        "cpu": 100.0,
        "ram": 100.0,
        "storage": None,
        "network": None,
        "temperature": None,
        "power": None,
        "humidity": None,
        "workload_criticality": None,
    }
    result = calculate_weighted_score(criteria)
    # CPU (0.25) + RAM (0.15) = 0.40 total weight. 
    # Both are 100, so score should reweight to 100.0.
    assert result.overall_score == 100.0
    assert result.risk_level == "Critical"
    assert result.coverage == 0.40
    assert "storage" in result.unavailable_criteria
    assert "temperature" in result.unavailable_criteria
    
def test_calculate_weighted_score_all_missing():
    reset_weights()
    criteria = {k: None for k in DEFAULT_WEIGHTS.keys()}
    result = calculate_weighted_score(criteria)
    assert result.overall_score == 0.0
    assert result.risk_level == "Unknown"
    assert result.coverage == 0.0
    assert len(result.unavailable_criteria) == 8

def test_weighted_scoring_endpoint_auth():
    original_override = app.dependency_overrides.get(get_current_user)
    if get_current_user in app.dependency_overrides:
        app.dependency_overrides.pop(get_current_user)
    response = client.post("/api/ai/score/dummy_id")
    assert response.status_code == 401
    if original_override:
        app.dependency_overrides[get_current_user] = original_override

def test_weighted_scoring_endpoint_not_found():
    original_override = app.dependency_overrides.get(get_current_user)
    def override_get_current_user():
        return {"id": "admin", "role": "admin"}
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    response = client.post("/api/ai/score/nonexistent_id")
    assert response.status_code == 404
    
    if original_override:
        app.dependency_overrides[get_current_user] = original_override
    else:
        app.dependency_overrides.pop(get_current_user, None)
