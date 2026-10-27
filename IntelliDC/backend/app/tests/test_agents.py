import pytest
from app.ai.infrastructure_agent import InfrastructureAgent
from app.ai.environmental_agent import EnvironmentalAgent
from app.ai.energy_agent import EnergyAgent
from app.ai.workload_agent import WorkloadContextAgent
from app.ai.coordinator_agent import CoordinatorAgent
from app.ai.base_agent import AgentResult

def test_infrastructure_agent():
    agent = InfrastructureAgent()
    # Test healthy scenario
    res = agent.evaluate(cpu=20.0, ram=40.0, storage=50.0, network=10.0)
    assert res.risk_level in ["LOW", "MEDIUM"]
    assert res.score > 50.0
    
    # Test critical scenario
    res_crit = agent.evaluate(cpu=95.0, ram=80.0, storage=90.0, network=50.0)
    assert res_crit.risk_level == "CRITICAL"
    assert any("CPU" in f for f in res_crit.findings)

def test_environmental_agent():
    agent = EnvironmentalAgent()
    # Test optimal
    res = agent.evaluate(temperature=22.5, humidity=50.0)
    assert res.risk_level == "LOW"
    assert res.score == 100.0
    
    # Test critical heat
    res_crit = agent.evaluate(temperature=38.0, humidity=50.0)
    assert res_crit.risk_level == "CRITICAL"

def test_energy_agent():
    agent = EnergyAgent()
    # Test normal
    res = agent.evaluate(current=5.0, power=1000.0)
    assert res.risk_level == "LOW"
    
    # Test critical overload
    res_crit = agent.evaluate(current=15.5, power=3400.0)
    assert res_crit.risk_level == "CRITICAL"

def test_workload_agent():
    agent = WorkloadContextAgent()
    # Test standard workload
    res = agent.evaluate(priority="LOW", criticality="LOW", sensitivity="PUBLIC")
    assert res.risk_level == "LOW"
    
    # Test highly critical workload
    res_crit = agent.evaluate(priority="CRITICAL", criticality="HIGH", sensitivity="CONFIDENTIAL")
    assert res_crit.risk_level == "CRITICAL"

def test_coordinator_agent():
    coordinator = CoordinatorAgent()
    
    # Create mock results mimicking agent outputs
    r1 = AgentResult(score=90.0, findings=["All good in Infra"], risk_level="LOW", agent_name="InfrastructureAgent")
    r2 = AgentResult(score=40.0, findings=["High Temp"], risk_level="HIGH", agent_name="EnvironmentalAgent")
    
    decision = coordinator.compile_decision_input([r1, r2])
    
    assert decision["overall_health_score"] == 65.0
    assert decision["aggregate_risk_level"] == "HIGH"
    assert decision["action_required"] is True
    assert len(decision["combined_findings"]) == 2
