"""
IntelliDC Weighted Scoring Model

Calculates transparent and explainable risk scores from normalized criteria.
All input values must be normalized to the 0-100 range.

Risk Levels:
    0 – 30  →  Healthy
   31 – 50  →  Low
   51 – 70  →  Medium
   71 – 85  →  High
   86 – 100 →  Critical
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from app.ai.scoring_config import get_weights


class CriterionContribution(BaseModel):
    """Explainability output for a single criterion."""
    criterion: str
    raw_value: float
    weight: float
    weighted_value: float
    contribution_pct: float


class WeightedScoringResult(BaseModel):
    """Full result of the weighted scoring model."""
    overall_score: float
    risk_level: str
    individual_contributions: List[CriterionContribution]
    coverage: float
    unavailable_criteria: List[str]


def classify_risk(score: float) -> str:
    """Map a numeric score to a human-readable risk level."""
    if score <= 30:
        return "Healthy"
    elif score <= 50:
        return "Low"
    elif score <= 70:
        return "Medium"
    elif score <= 85:
        return "High"
    else:
        return "Critical"


def normalize_criterion(key: str, value: Optional[float], thresholds: Optional[Dict[str, float]] = None) -> Optional[float]:
    """
    Normalize raw criterion value to a 0-100 risk scale.
    """
    if value is None or value < 0:
        return None
        
    if thresholds is None:
        thresholds = {
            "temperature_max": 35.0,
            "humidity_max": 85.0,
            "power_max": 3500.0,
        }
        
    if key in ["cpu", "ram", "storage", "network"]:
        return min(max(value, 0.0), 100.0)
    elif key == "temperature":
        return min((value / thresholds.get("temperature_max", 35.0)) * 100.0, 100.0)
    elif key == "humidity":
        return min((value / thresholds.get("humidity_max", 85.0)) * 100.0, 100.0)
    elif key == "power":
        return min((value / thresholds.get("power_max", 3500.0)) * 100.0, 100.0)
    elif key == "workload_criticality":
        return min(max(value, 0.0), 100.0)
    
    return min(max(value, 0.0), 100.0)


def calculate_weighted_score(
    criteria_values: Dict[str, Optional[float]],
    weights: Dict[str, float] | None = None,
) -> WeightedScoringResult:
    """
    Calculate a transparent, explainable risk score.
    Handles missing values by re-weighting the available criteria.
    """
    if weights is None:
        weights = get_weights()

    available_criteria = {}
    unavailable_criteria = []
    
    for key, weight in weights.items():
        val = criteria_values.get(key)
        if val is None or val < 0.0:  # Invalid or missing
            unavailable_criteria.append(key)
        else:
            if val > 100.0:
                val = 100.0
            available_criteria[key] = val
            
    total_available_weight = sum(weights[k] for k in available_criteria.keys())
    
    if total_available_weight == 0.0:
        return WeightedScoringResult(
            overall_score=0.0,
            risk_level="Unknown",
            individual_contributions=[],
            coverage=0.0,
            unavailable_criteria=unavailable_criteria
        )
        
    overall_score = 0.0
    contributions: List[CriterionContribution] = []

    for criterion, raw_value in available_criteria.items():
        # Re-weight to sum to 1.0 across available criteria
        effective_weight = weights[criterion] / total_available_weight
        weighted_value = effective_weight * raw_value
        overall_score += weighted_value

        contributions.append(CriterionContribution(
            criterion=criterion,
            raw_value=raw_value,
            weight=effective_weight,
            weighted_value=round(weighted_value, 4),
            contribution_pct=0.0,
        ))

    overall_score = round(overall_score, 4)

    if overall_score > 0:
        for c in contributions:
            c.contribution_pct = round(
                (c.weighted_value / overall_score) * 100.0, 2
            )

    contributions.sort(key=lambda c: c.weighted_value, reverse=True)

    return WeightedScoringResult(
        overall_score=overall_score,
        risk_level=classify_risk(overall_score),
        individual_contributions=contributions,
        coverage=round(total_available_weight, 4),
        unavailable_criteria=unavailable_criteria,
    )

