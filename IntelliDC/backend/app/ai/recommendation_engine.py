from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.services.firestore_service import FirestoreService

ai_recommendations_collection = FirestoreService("ai_recommendations")

VALID_STATUS_TRANSITIONS = {
    "NEW": ["REVIEWED", "ACCEPTED", "DISMISSED", "RESOLVED"],
    "REVIEWED": ["ACCEPTED", "DISMISSED", "RESOLVED"],
    "ACCEPTED": ["RESOLVED", "DISMISSED"],
    "DISMISSED": ["NEW"],
    "RESOLVED": ["NEW"]
}

class Recommendation(BaseModel):
    id: Optional[str] = None
    server_id: str
    severity: str
    priority: str
    summary: str
    contributing_factors: List[str]
    observed_values: Dict[str, Any]
    explanation: str
    suggested_action: str
    expected_outcome: str
    data_freshness: str
    confidence: float
    status: str = "NEW"
    created_at: str
    
    # Legacy fields mapping
    @property
    def recommendation(self) -> str:
        return self.suggested_action
        
    @property
    def risk_score(self) -> float:
        return self.confidence * 100.0
        
    @property
    def risk_level(self) -> str:
        return self.severity


def generate_recommendations(
    server_id: str, 
    agent_results: List[Dict[str, Any]], 
    weighted_score: Optional[Dict[str, Any]] = None,
    topsis_rank: Optional[int] = None
) -> List[Recommendation]:
    """
    Generate actionable recommendations based on agent evidence.
    Prevents duplicating NEW/REVIEWED recommendations.
    """
    existing = ai_recommendations_collection.query_documents("server_id", "==", server_id)
    active_summaries = {
        r.get("summary") for r in existing 
        if r.get("status") in ["NEW", "REVIEWED", "ACCEPTED", "ADMINISTRATOR_REVIEW_REQUIRED"]
    }
    
    new_recs = []
    
    # 1. Parse infra evidence
    cpu = None
    temp = None
    for res in agent_results:
        if res.get("agent_name") == "InfrastructureAgent":
            factors = res.get("factors", [])
            for f in factors:
                if "CPU" in f:
                    cpu = "high"
        if res.get("agent_name") == "EnvironmentalAgent":
            factors = res.get("factors", [])
            for f in factors:
                if "Temperature" in f:
                    temp = "high"
                if "MISSING" in f.upper() or "STALE" in f.upper():
                    temp = "missing"

    if cpu == "high" and "High CPU Utilization" not in active_summaries:
        new_recs.append(Recommendation(
            server_id=server_id,
            severity="HIGH",
            priority="HIGH",
            summary="High CPU Utilization",
            contributing_factors=["InfrastructureAgent detected elevated CPU."],
            observed_values={"cpu_status": "Elevated"},
            explanation="Sustained high CPU increases the risk of thermal throttling and workload degradation.",
            suggested_action="Review and migrate low-priority workloads to healthy nodes.",
            expected_outcome="(Estimate) 30% reduction in peak load within 1 hour.",
            data_freshness="Live",
            confidence=0.85,
            created_at=datetime.utcnow().isoformat()
        ))
        
    if temp == "high" and "Thermal Warning" not in active_summaries:
        new_recs.append(Recommendation(
            server_id=server_id,
            severity="CRITICAL",
            priority="CRITICAL",
            summary="Thermal Warning",
            contributing_factors=["EnvironmentalAgent detected dangerous temperature levels."],
            observed_values={"temperature_status": "Elevated"},
            explanation="Operating above thermal thresholds drastically degrades hardware lifespan and risks shutdown.",
            suggested_action="Inspect cooling infrastructure immediately.",
            expected_outcome="(Estimate) Temperature stabilization within 15 minutes of cooling correction.",
            data_freshness="Live",
            confidence=0.95,
            created_at=datetime.utcnow().isoformat()
        ))
        
    if temp == "missing" and "Missing Telemetry" not in active_summaries:
        new_recs.append(Recommendation(
            server_id=server_id,
            severity="UNKNOWN",
            priority="LOW",
            summary="Missing Telemetry",
            contributing_factors=["EnvironmentalAgent reported missing or stale data."],
            observed_values={},
            explanation="The engine cannot assess environmental risk without valid telemetry.",
            suggested_action="Restore sensor connections and verify IoT device health.",
            expected_outcome="(Estimate) Visibility restored; accurate risk scores computable.",
            data_freshness="Stale/Missing",
            confidence=0.0,
            created_at=datetime.utcnow().isoformat()
        ))

    # Save them
    saved = []
    for rec in new_recs:
        doc = rec.dict(exclude={"id"})
        doc["recommendation"] = rec.recommendation
        doc["risk_score"] = rec.risk_score
        doc["risk_level"] = rec.risk_level
        doc_id = ai_recommendations_collection.create_document(data=doc)
        rec.id = doc_id
        saved.append(rec)
        
    return saved


def update_recommendation_status(rec_id: str, new_status: str) -> Dict[str, Any]:
    rec = ai_recommendations_collection.get_document(rec_id)
    if not rec:
        raise ValueError(f"Recommendation {rec_id} not found")
        
    current = rec.get("status", "NEW")
    # Also handle legacy status
    if current == "ADMINISTRATOR_REVIEW_REQUIRED":
        current = "NEW"
        
    if new_status not in VALID_STATUS_TRANSITIONS.get(current, []):
        raise ValueError(f"Invalid transition from {current} to {new_status}")
        
    ai_recommendations_collection.update_document(rec_id, {"status": new_status})
    rec["status"] = new_status
    return rec
