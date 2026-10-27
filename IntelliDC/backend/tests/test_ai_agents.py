import pytest
from datetime import datetime, timezone, timedelta
from app.ai.infrastructure_agent import InfrastructureAgent
from app.ai.environmental_agent import EnvironmentalAgent
from app.ai.energy_agent import EnergyAgent
from app.ai.workload_agent import WorkloadContextAgent
from app.ai.coordinator_agent import CoordinatorAgent

def test_infrastructure_agent():
    agent = InfrastructureAgent()
    
    # Normal
    res = agent.evaluate(cpu=50.0, ram=50.0, storage=50.0, network=10.0)
    assert res.risk_level == "LOW"
    assert res.score == 54.0
    
    # Threshold breaches
    res = agent.evaluate(cpu=95.0, ram=50.0, storage=50.0, network=10.0)
    assert res.risk_level == "CRITICAL"
    assert res.score == 36.0
    
    # Missing data
    res = agent.evaluate(cpu=None, ram=50.0, storage=50.0, network=10.0)
    assert res.risk_level == "UNKNOWN"

def test_environmental_agent():
    agent = EnvironmentalAgent()
    
    # Normal
    res = agent.evaluate(temperature=22.0, humidity=50.0)
    assert res.risk_level == "LOW"
    
    # Threshold breaches
    res = agent.evaluate(temperature=36.0, humidity=50.0)
    assert res.risk_level == "CRITICAL"
    
    # Missing data
    res = agent.evaluate(temperature=None, humidity=50.0)
    assert res.risk_level == "UNKNOWN"
    
    # Stale readings (6 minutes ago)
    stale_time = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
    res = agent.evaluate(temperature=22.0, humidity=50.0, timestamp=stale_time)
    assert res.risk_level == "UNKNOWN"

def test_energy_agent():
    agent = EnergyAgent()
    
    # Normal
    res = agent.evaluate(current=5.0, power=1000.0)
    assert res.risk_level == "LOW"
    
    # Threshold breach
    res = agent.evaluate(current=15.5, power=3400.0)
    assert res.risk_level == "CRITICAL"
    
    # Missing/invalid values
    res = agent.evaluate(current=None, power=1000.0)
    assert res.risk_level == "UNKNOWN"
    
    res = agent.evaluate(current=-5.0, power=1000.0)
    assert res.risk_level == "UNKNOWN"

def test_workload_agent():
    agent = WorkloadContextAgent()
    
    # Normal
    res = agent.evaluate("LOW", "LOW", "PUBLIC")
    assert res.risk_level == "LOW"
    
    # High Priority
    res = agent.evaluate("CRITICAL", "LOW", "PUBLIC")
    assert res.risk_level == "CRITICAL"

def test_coordinator_agent():
    agent = CoordinatorAgent()
    infra = InfrastructureAgent().evaluate(cpu=50.0, ram=50.0, storage=50.0, network=10.0)
    env = EnvironmentalAgent().evaluate(temperature=None, humidity=50.0) # Missing
    
    out = agent.compile_decision_input([infra, env])
    assert out["aggregate_risk_level"] == "UNKNOWN"
    
    # Coordinator with critical
    env_crit = EnvironmentalAgent().evaluate(temperature=40.0, humidity=50.0)
    out_crit = agent.compile_decision_input([infra, env_crit])
    assert out_crit["aggregate_risk_level"] == "CRITICAL"

from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import get_current_user
client = TestClient(app)

def test_ai_router_authentication():
    # Save original override if it exists
    original_override = app.dependency_overrides.get(get_current_user)
    if get_current_user in app.dependency_overrides:
        app.dependency_overrides.pop(get_current_user)
        
    response = client.post("/api/ai/analyze/dummy_id")
    assert response.status_code == 401
    
    # Restore
    if original_override:
        app.dependency_overrides[get_current_user] = original_override

def test_ai_router_server_not_found():
    original_override = app.dependency_overrides.get(get_current_user)
    def override_get_current_user():
        return {"id": "admin", "role": "admin"}
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    response = client.post("/api/ai/analyze/nonexistent_id")
    assert response.status_code == 404
    
    if original_override:
        app.dependency_overrides[get_current_user] = original_override
    else:
        app.dependency_overrides.pop(get_current_user, None)
