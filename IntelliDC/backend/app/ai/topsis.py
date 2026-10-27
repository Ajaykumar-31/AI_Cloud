"""
IntelliDC TOPSIS Implementation
(Technique for Order Preference by Similarity to Ideal Solution)

Ranks multiple server alternatives based on multiple decision criteria.

Each criterion is classified as either:
  - COST:    higher value = worse  (e.g., CPU usage, temperature, power)
  - BENEFIT: higher value = better (e.g., uptime, availability)

For the current risk-ranking use case all criteria are COST criteria
because high CPU, temperature, power, etc. represent higher risk.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel
import numpy as np

from app.ai.scoring_config import get_weights

CriterionType = Literal["cost", "benefit"]

DEFAULT_CRITERION_TYPES: Dict[str, CriterionType] = {
    "cpu":                  "cost",
    "ram":                  "cost",
    "storage":              "cost",
    "network":              "cost",
    "temperature":          "cost",
    "humidity":             "cost",
    "power":                "cost",
    "workload_criticality": "cost",
}

class ServerTOPSISInput(BaseModel):
    """Raw criteria values for one server alternative."""
    server_id: str
    criteria: Dict[str, Optional[float]]  # criterion_name → value (0–100)
    data_freshness: str = "Live"


class ServerTOPSISResult(BaseModel):
    """Full TOPSIS output for one server alternative."""
    server_id: str
    original_criteria: Dict[str, Optional[float]]
    normalized_criteria: Dict[str, float]
    weighted_criteria: Dict[str, float]
    distance_to_ideal: float
    distance_to_negative_ideal: float
    closeness_coefficient: float
    rank: int


class TOPSISOutput(BaseModel):
    """Complete output of a TOPSIS run."""
    criteria_names: List[str]
    excluded_criteria: List[str]
    coverage: float
    criterion_types: Dict[str, str]
    weights_used: Dict[str, float]
    ideal_solution: Dict[str, float]
    negative_ideal_solution: Dict[str, float]
    results: List[ServerTOPSISResult]
    explanation: str


def run_topsis(
    alternatives: List[ServerTOPSISInput],
    weights: Dict[str, float] | None = None,
    criterion_types: Dict[str, CriterionType] | None = None,
) -> TOPSISOutput:
    """
    Execute the full TOPSIS ranking process.
    Excludes criteria that are missing or invalid for any alternative.
    """
    if not alternatives or len(alternatives) < 2:
        raise ValueError("TOPSIS requires at least 2 alternatives to rank.")

    if weights is None:
        weights = get_weights()
    if criterion_types is None:
        criterion_types = dict(DEFAULT_CRITERION_TYPES)

    all_criteria = set(weights.keys())
    excluded_criteria = []
    included_criteria = []

    # Identify included vs excluded criteria
    for crit in all_criteria:
        is_valid = True
        for alt in alternatives:
            val = alt.criteria.get(crit)
            if val is None or val < 0.0:
                is_valid = False
                break
        
        # Also check for constant columns
        if is_valid:
            vals = [alt.criteria.get(crit) for alt in alternatives]
            # Wait, constant columns are mathematically valid in TOPSIS but they have 0 distance impact
            # if they are identical. Let's just let the math handle constant columns (col_norms will scale them).
            # But the prompt says "Handle constant-valued criteria safely." The existing col_norm handles zeros.
            pass

        if is_valid:
            included_criteria.append(crit)
        else:
            excluded_criteria.append(crit)

    if not included_criteria:
        raise ValueError("No valid criteria remaining across all alternatives to run TOPSIS.")

    criteria_names = sorted(included_criteria)
    coverage = sum(weights.get(c, 0.0) for c in criteria_names)

    m = len(alternatives)
    n = len(criteria_names)

    decision_matrix = np.zeros((m, n))
    server_ids = []

    for i, alt in enumerate(alternatives):
        server_ids.append(alt.server_id)
        for j, crit in enumerate(criteria_names):
            decision_matrix[i, j] = alt.criteria[crit]

    # Step 2: Normalize matrix (vector normalization)
    col_norms = np.sqrt(np.sum(decision_matrix ** 2, axis=0))
    col_norms[col_norms == 0] = 1.0  # Guard against division by zero (constant zero column)
    normalized_matrix = decision_matrix / col_norms

    # Step 3: Apply criterion weights
    # Normalize weights so they sum to 1 for the available criteria
    base_weight_vector = np.array([weights.get(c, 0.0) for c in criteria_names])
    weight_vector = base_weight_vector / coverage if coverage > 0 else base_weight_vector
    
    weighted_matrix = normalized_matrix * weight_vector

    # Step 4 & 5: Ideal and negative-ideal solutions
    ideal = np.zeros(n)
    negative_ideal = np.zeros(n)

    for j, crit in enumerate(criteria_names):
        ctype = criterion_types.get(crit, "cost")
        col = weighted_matrix[:, j]
        if ctype == "benefit":
            ideal[j] = np.max(col)
            negative_ideal[j] = np.min(col)
        else:  # cost
            ideal[j] = np.min(col)
            negative_ideal[j] = np.max(col)

    # Step 6 & 7: Euclidean distances
    dist_to_ideal = np.sqrt(np.sum((weighted_matrix - ideal) ** 2, axis=1))
    dist_to_neg   = np.sqrt(np.sum((weighted_matrix - negative_ideal) ** 2, axis=1))

    # Step 8: Closeness coefficient
    denominator = dist_to_ideal + dist_to_neg
    denominator[denominator == 0] = 1.0
    closeness = dist_to_neg / denominator

    # Step 9: Rank (higher CC = better = closer to ideal)
    # Negate closeness for descending sort
    # np.argsort on -closeness returns indices that would sort descending
    # However, if closeness is exactly the same, argsort might not be stable, but it's fine.
    ranking_order = np.argsort(-closeness)
    
    # Ranks
    ranks = np.empty_like(ranking_order)
    current_rank = 1
    for rank_idx, original_idx in enumerate(ranking_order):
        # Handle ties
        if rank_idx > 0 and abs(closeness[original_idx] - closeness[ranking_order[rank_idx - 1]]) < 1e-9:
            ranks[original_idx] = ranks[ranking_order[rank_idx - 1]]
        else:
            ranks[original_idx] = current_rank
        current_rank += 1

    # Assemble results
    results: List[ServerTOPSISResult] = []
    for i in range(m):
        results.append(ServerTOPSISResult(
            server_id=server_ids[i],
            original_criteria=alternatives[i].criteria,
            normalized_criteria={
                criteria_names[j]: round(float(normalized_matrix[i, j]), 6)
                for j in range(n)
            },
            weighted_criteria={
                criteria_names[j]: round(float(weighted_matrix[i, j]), 6)
                for j in range(n)
            },
            distance_to_ideal=round(float(dist_to_ideal[i]), 6),
            distance_to_negative_ideal=round(float(dist_to_neg[i]), 6),
            closeness_coefficient=round(float(closeness[i]), 6),
            rank=int(ranks[i]),
        ))

    results.sort(key=lambda r: r.rank)

    explanation = f"TOPSIS ranking completed over {m} servers using {n} criteria. Data coverage: {coverage*100:.1f}%. Excluded criteria due to missing data: {', '.join(excluded_criteria) if excluded_criteria else 'None'}."

    return TOPSISOutput(
        criteria_names=criteria_names,
        excluded_criteria=excluded_criteria,
        coverage=round(coverage, 4),
        criterion_types={c: criterion_types.get(c, "cost") for c in criteria_names},
        weights_used={c: round(float(weight_vector[j]), 6) for j, c in enumerate(criteria_names)},
        ideal_solution={
            criteria_names[j]: round(float(ideal[j]), 6) for j in range(n)
        },
        negative_ideal_solution={
            criteria_names[j]: round(float(negative_ideal[j]), 6) for j in range(n)
        },
        results=results,
        explanation=explanation,
    )
