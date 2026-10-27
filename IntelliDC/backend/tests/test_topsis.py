import pytest
import numpy as np
from app.ai.topsis import run_topsis, ServerTOPSISInput, DEFAULT_CRITERION_TYPES
from app.ai.scoring_config import reset_weights

from fastapi.testclient import TestClient
from app.main import app
from app.routers.auth import get_current_user

client = TestClient(app)

def get_base_alternatives():
    return [
        ServerTOPSISInput(server_id="1", criteria={"cpu": 90.0, "ram": 90.0}),
        ServerTOPSISInput(server_id="2", criteria={"cpu": 10.0, "ram": 10.0}),
        ServerTOPSISInput(server_id="3", criteria={"cpu": 50.0, "ram": 50.0}),
    ]

def test_topsis_basic_ranking():
    reset_weights()
    weights = {"cpu": 0.5, "ram": 0.5}
    alts = get_base_alternatives()
    
    # By default, cpu and ram are COST.
    # So higher = worse.
    # Ideal (best) = min(cost) = 10.0
    # Negative-Ideal (worst) = max(cost) = 90.0
    # Higher Closeness Coefficient = better = closer to ideal.
    # Therefore, server 2 should have rank 1, server 3 rank 2, server 1 rank 3.
    
    res = run_topsis(alts, weights=weights)
    
    assert res.coverage == 1.0
    assert "cpu" in res.criteria_names
    
    ranks = {r.server_id: r.rank for r in res.results}
    assert ranks["2"] == 1
    assert ranks["3"] == 2
    assert ranks["1"] == 3

def test_topsis_benefit_vs_cost():
    weights = {"uptime": 0.5, "latency": 0.5}
    types = {"uptime": "benefit", "latency": "cost"}
    
    alts = [
        ServerTOPSISInput(server_id="a", criteria={"uptime": 99.9, "latency": 50.0}), # high benefit, medium cost
        ServerTOPSISInput(server_id="b", criteria={"uptime": 90.0, "latency": 10.0}), # low benefit, low cost
        ServerTOPSISInput(server_id="c", criteria={"uptime": 99.9, "latency": 10.0}), # high benefit, low cost (BEST)
    ]
    
    res = run_topsis(alts, weights=weights, criterion_types=types)
    ranks = {r.server_id: r.rank for r in res.results}
    
    assert ranks["c"] == 1

def test_topsis_missing_data():
    weights = {"cpu": 0.5, "ram": 0.5}
    alts = [
        ServerTOPSISInput(server_id="1", criteria={"cpu": 90.0, "ram": 90.0}),
        ServerTOPSISInput(server_id="2", criteria={"cpu": 10.0, "ram": None}), # missing RAM
    ]
    
    res = run_topsis(alts, weights=weights)
    assert "ram" in res.excluded_criteria
    assert "cpu" in res.criteria_names
    assert res.coverage == 0.5

def test_topsis_insufficient_alternatives():
    with pytest.raises(ValueError, match="at least 2 alternatives"):
        run_topsis([ServerTOPSISInput(server_id="1", criteria={"cpu": 10.0})])

def test_topsis_ties_and_constant_columns():
    weights = {"cpu": 0.5, "ram": 0.5}
    alts = [
        ServerTOPSISInput(server_id="1", criteria={"cpu": 50.0, "ram": 50.0}),
        ServerTOPSISInput(server_id="2", criteria={"cpu": 50.0, "ram": 50.0}),
    ]
    
    # Constant columns should not crash (division by zero is protected).
    res = run_topsis(alts, weights=weights)
    ranks = {r.server_id: r.rank for r in res.results}
    # Both should be rank 1 due to tie logic
    assert ranks["1"] == 1
    assert ranks["2"] == 1

def test_topsis_endpoint_auth():
    original_override = app.dependency_overrides.get(get_current_user)
    if get_current_user in app.dependency_overrides:
        app.dependency_overrides.pop(get_current_user)
        
    response = client.post("/api/ai/rank")
    assert response.status_code == 401
    
    if original_override:
        app.dependency_overrides[get_current_user] = original_override
