"""
Unit tests for the IntelliDC TOPSIS implementation.

Uses small, hand-verifiable decision matrices so every intermediate
value can be traced and confirmed.
"""

import pytest
import math
from app.ai.topsis import run_topsis, ServerTOPSISInput


# ──────────────────────────────────────────────────────────
#  Helper: build simple 3-server, 2-criteria scenario
# ──────────────────────────────────────────────────────────

def _simple_alternatives():
    """
    3 servers, 2 cost criteria (cpu, ram) with trivial weights.

    Decision matrix:
        Server  CPU   RAM
        A (1)   90    80
        B (2)   50    40
        C (3)   20    10

    Weights: cpu=0.5, ram=0.5  (all other weights 0)
    All criteria are cost → ideal = min, negative-ideal = max.

    Manual calculation:
      norm_cpu  = sqrt(90²+50²+20²) = sqrt(8100+2500+400) = sqrt(11000) ≈ 104.8809
      norm_ram  = sqrt(80²+40²+10²) = sqrt(6400+1600+100) = sqrt(8100)  = 90.0

      Normalized:
        A: cpu=90/104.8809≈0.858, ram=80/90≈0.889
        B: cpu=50/104.8809≈0.477, ram=40/90≈0.444
        C: cpu=20/104.8809≈0.191, ram=10/90≈0.111

      Weighted (×0.5):
        A: cpu≈0.429, ram≈0.444
        B: cpu≈0.238, ram≈0.222
        C: cpu≈0.095, ram≈0.056

      Ideal (cost→min):       cpu≈0.095, ram≈0.056
      Neg-ideal (cost→max):   cpu≈0.429, ram≈0.444

      Distances:
        S⁺_A = sqrt((0.429-0.095)²+(0.444-0.056)²) ≈ sqrt(0.1116+0.1508) ≈ 0.5121
        S⁻_A = sqrt((0.429-0.429)²+(0.444-0.444)²) = 0.0
        CC_A  = 0 / (0.5121+0) = 0.0  → rank 3 (worst)

        S⁺_C = 0.0
        S⁻_C ≈ 0.5121
        CC_C  = 0.5121 / (0+0.5121) = 1.0  → rank 1 (best)

        CC_B somewhere in between → rank 2
    """
    return [
        ServerTOPSISInput(server_id=1, criteria={"cpu": 90, "ram": 80}),
        ServerTOPSISInput(server_id=2, criteria={"cpu": 50, "ram": 40}),
        ServerTOPSISInput(server_id=3, criteria={"cpu": 20, "ram": 10}),
    ]


def _simple_weights():
    return {
        "cpu": 0.5, "ram": 0.5,
    }


def _simple_criterion_types():
    return {"cpu": "cost", "ram": "cost"}


# ──────────────────────────────────────────────────────────
#  Basic ranking tests
# ──────────────────────────────────────────────────────────

def test_best_server_is_lowest_cost():
    """Server C (id=3) has the lowest CPU and RAM → should rank 1."""
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    assert result.results[0].server_id == 3
    assert result.results[0].rank == 1

def test_worst_server_is_highest_cost():
    """Server A (id=1) has the highest CPU and RAM → should rank last."""
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    assert result.results[-1].server_id == 1
    assert result.results[-1].rank == 3

def test_middle_server_ranks_second():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    middle = [r for r in result.results if r.server_id == 2][0]
    assert middle.rank == 2


# ──────────────────────────────────────────────────────────
#  Closeness coefficient boundaries
# ──────────────────────────────────────────────────────────

def test_best_alternative_cc_is_one():
    """The ideal alternative should have CC = 1.0."""
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    best = result.results[0]
    assert best.closeness_coefficient == pytest.approx(1.0, abs=1e-4)

def test_worst_alternative_cc_is_zero():
    """The worst alternative should have CC = 0.0."""
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    worst = result.results[-1]
    assert worst.closeness_coefficient == pytest.approx(0.0, abs=1e-4)

def test_cc_values_between_zero_and_one():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    for r in result.results:
        assert 0.0 <= r.closeness_coefficient <= 1.0


# ──────────────────────────────────────────────────────────
#  Intermediate values
# ──────────────────────────────────────────────────────────

def test_normalized_values_are_correct():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    norm_cpu_denom = math.sqrt(90**2 + 50**2 + 20**2)
    server_a = [r for r in result.results if r.server_id == 1][0]
    assert server_a.normalized_criteria["cpu"] == pytest.approx(
        90 / norm_cpu_denom, abs=1e-4
    )

def test_weighted_values_are_correct():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    norm_cpu_denom = math.sqrt(90**2 + 50**2 + 20**2)
    server_a = [r for r in result.results if r.server_id == 1][0]
    expected_weighted_cpu = 0.5 * (90 / norm_cpu_denom)
    assert server_a.weighted_criteria["cpu"] == pytest.approx(
        expected_weighted_cpu, abs=1e-4
    )

def test_ideal_solution_is_minimum_for_cost():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    # For cost criteria, ideal = min weighted value
    server_c = [r for r in result.results if r.server_id == 3][0]
    assert result.ideal_solution["cpu"] == pytest.approx(
        server_c.weighted_criteria["cpu"], abs=1e-4
    )

def test_negative_ideal_is_maximum_for_cost():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    server_a = [r for r in result.results if r.server_id == 1][0]
    assert result.negative_ideal_solution["cpu"] == pytest.approx(
        server_a.weighted_criteria["cpu"], abs=1e-4
    )


# ──────────────────────────────────────────────────────────
#  Benefit criterion flips ideal/negative-ideal
# ──────────────────────────────────────────────────────────

def test_benefit_criterion_ranking():
    """
    If RAM is a benefit criterion (higher=better), then:
      Server A (ram=80) should be rewarded, not penalised.
    """
    alts = [
        ServerTOPSISInput(server_id=1, criteria={"cpu": 50, "ram": 80}),
        ServerTOPSISInput(server_id=2, criteria={"cpu": 50, "ram": 40}),
        ServerTOPSISInput(server_id=3, criteria={"cpu": 50, "ram": 10}),
    ]
    result = run_topsis(
        alts,
        weights={"cpu": 0.5, "ram": 0.5},
        criterion_types={"cpu": "cost", "ram": "benefit"},
    )
    # Same CPU → RAM decides. Benefit → higher is better → Server 1 wins.
    assert result.results[0].server_id == 1


# ──────────────────────────────────────────────────────────
#  Output structure
# ──────────────────────────────────────────────────────────

def test_output_contains_all_servers():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    ids = {r.server_id for r in result.results}
    assert ids == {1, 2, 3}

def test_ranks_are_unique_and_sequential():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    ranks = sorted(r.rank for r in result.results)
    assert ranks == [1, 2, 3]

def test_results_sorted_by_rank():
    result = run_topsis(
        _simple_alternatives(),
        weights=_simple_weights(),
        criterion_types=_simple_criterion_types(),
    )
    for i in range(len(result.results) - 1):
        assert result.results[i].rank < result.results[i + 1].rank


# ──────────────────────────────────────────────────────────
#  Edge-case validation
# ──────────────────────────────────────────────────────────

def test_rejects_fewer_than_two_alternatives():
    with pytest.raises(ValueError, match="at least 2"):
        run_topsis(
            [ServerTOPSISInput(server_id=1, criteria={"cpu": 50, "ram": 30})],
            weights=_simple_weights(),
            criterion_types=_simple_criterion_types(),
        )

def test_rejects_missing_criterion():
    alts = [
        ServerTOPSISInput(server_id=1, criteria={"cpu": 50, "ram": 30}),
        ServerTOPSISInput(server_id=2, criteria={"cpu": 40}),  # missing ram
    ]
    with pytest.raises(ValueError, match="missing criterion"):
        run_topsis(
            alts,
            weights=_simple_weights(),
            criterion_types=_simple_criterion_types(),
        )


# ──────────────────────────────────────────────────────────
#  Larger realistic scenario
# ──────────────────────────────────────────────────────────

def test_full_8_criteria_ranking():
    """
    5 servers with all 8 criteria. Verify that the server with the
    lowest overall cost metrics ranks first.
    """
    weights = {
        "cpu": 0.25, "ram": 0.15, "storage": 0.10, "network": 0.10,
        "temperature": 0.15, "power": 0.10, "humidity": 0.05,
        "workload_criticality": 0.10,
    }
    ctypes = {k: "cost" for k in weights}
    
    alts = [
        ServerTOPSISInput(server_id=1, criteria={
            "cpu": 90, "ram": 85, "storage": 70, "network": 60,
            "temperature": 35, "power": 80, "humidity": 70,
            "workload_criticality": 90,
        }),
        ServerTOPSISInput(server_id=2, criteria={
            "cpu": 40, "ram": 35, "storage": 30, "network": 25,
            "temperature": 22, "power": 30, "humidity": 45,
            "workload_criticality": 40,
        }),
        ServerTOPSISInput(server_id=3, criteria={
            "cpu": 10, "ram": 15, "storage": 10, "network": 5,
            "temperature": 21, "power": 15, "humidity": 50,
            "workload_criticality": 20,
        }),
        ServerTOPSISInput(server_id=4, criteria={
            "cpu": 70, "ram": 60, "storage": 55, "network": 45,
            "temperature": 28, "power": 60, "humidity": 55,
            "workload_criticality": 70,
        }),
        ServerTOPSISInput(server_id=5, criteria={
            "cpu": 55, "ram": 50, "storage": 45, "network": 35,
            "temperature": 25, "power": 45, "humidity": 48,
            "workload_criticality": 50,
        }),
    ]
    
    result = run_topsis(alts, weights=weights, criterion_types=ctypes)
    
    # Server 3 has the lowest values across the board → should rank 1
    assert result.results[0].server_id == 3
    # Server 1 has the highest values → should rank last
    assert result.results[-1].server_id == 1
    # All 5 servers present and uniquely ranked
    assert len(result.results) == 5
    assert sorted(r.rank for r in result.results) == [1, 2, 3, 4, 5]
