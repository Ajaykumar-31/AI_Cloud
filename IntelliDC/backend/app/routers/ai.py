import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.firestore_service import FirestoreService
from app.routers.auth import get_current_user
from app.ai.decision_engine import analyze_server

router = APIRouter(prefix="/api/ai", tags=["ai"])

server_collection = FirestoreService("servers")
ai_recommendations_collection = FirestoreService("ai_recommendations")

def _build_full_response(rec: dict) -> dict:
    server = server_collection.get_document(rec["server_id"])
    server_name = server.get("server_name", f"Server-{rec['server_id']}") if server else f"Server-{rec['server_id']}"

    return {
        "id": rec.get("id"),
        "server_id": rec["server_id"],
        "server_name": server_name,
        "risk_score": rec.get("risk_score"),
        "priority": rec.get("priority"),
        "severity": rec.get("severity", rec.get("risk_level")),
        "agent_scores": rec.get("agent_scores", {}),
        "contributing_factors": rec.get("contributing_factors", []),
        "summary": rec.get("summary", "Legacy Recommendation"),
        "observed_values": rec.get("observed_values", {}),
        "topsis_rank": rec.get("topsis_rank"),
        "recommendation": rec.get("recommendation", rec.get("suggested_action")),
        "suggested_action": rec.get("suggested_action", rec.get("recommendation")),
        "explanation": rec.get("explanation", ""),
        "expected_outcome": rec.get("expected_outcome", "(Estimate) General improvement"),
        "data_freshness": rec.get("data_freshness", "Unknown"),
        "confidence": rec.get("confidence", 0.0),
        "status": rec.get("status", "NEW"),
        "created_at": rec.get("created_at"),
    }

@router.post("/analyze/{server_id}")
def trigger_analysis(
    server_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        server = server_collection.get_document(server_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        rec = analyze_server(server_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return _build_full_response(rec)

from app.ai.weighted_scoring import calculate_weighted_score, normalize_criterion
from app.ai.decision_engine import _get_latest_sensor_data, _get_workload_context
from datetime import datetime

@router.post("/score/{server_id}")
def trigger_weighted_score(
    server_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        server = server_collection.get_document(server_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Server not found")

    cpu = server.get("cpu_usage")
    ram = server.get("memory_usage")
    storage = server.get("storage_usage")
    network = server.get("network_usage")
    
    temperature, humidity, current, power, timestamp = _get_latest_sensor_data(server)
    w_priority, w_criticality, w_sensitivity = _get_workload_context(server_id)
    
    crit_map = {"LOW": 25, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 100}
    workload_crit = crit_map.get(w_criticality, 25)

    raw_values = {
        "cpu": cpu,
        "ram": ram,
        "storage": storage,
        "network": network,
        "temperature": temperature,
        "power": power,
        "humidity": humidity,
        "workload_criticality": workload_crit
    }
    
    normalized_values = {
        k: normalize_criterion(k, v) for k, v in raw_values.items()
    }
    
    score_result = calculate_weighted_score(normalized_values)
    
    rec_data = {
        "server_id": server_id,
        "risk_score": score_result.overall_score,
        "risk_level": score_result.risk_level.upper() if score_result.risk_level != "Unknown" else "UNKNOWN",
        "priority": "HIGH" if score_result.risk_level in ["High", "Critical", "Unknown"] else "LOW",
        "topsis_rank": None,
        "topsis_score": None,
        "coverage": score_result.coverage,
        "unavailable_criteria": score_result.unavailable_criteria,
        "agent_scores": {
            "WeightedScoring": {
                "score": score_result.overall_score,
                "risk_level": score_result.risk_level,
                "findings": [
                    f"{c.criterion}: {c.raw_value:.2f} (weight {c.weight:.2f}, contribution {c.contribution_pct}%)"
                    for c in score_result.individual_contributions
                ]
            }
        },
        "contributing_factors": [
            f"Coverage: {score_result.coverage*100:.1f}%. Unavailable: {', '.join(score_result.unavailable_criteria) if score_result.unavailable_criteria else 'None'}"
        ],
        "recommendation": "Review individual metrics." if score_result.risk_level != "Unknown" else "Resolve missing telemetry.",
        "explanation": f"Weighted score {score_result.overall_score:.1f}/100",
        "status": "ADMINISTRATOR_REVIEW_REQUIRED",
        "created_at": datetime.utcnow().isoformat()
    }
    doc_id = ai_recommendations_collection.create_document(data=rec_data)
    rec = ai_recommendations_collection.get_document(doc_id)
    return _build_full_response(rec)

from app.ai.topsis import run_topsis, ServerTOPSISInput

@router.post("/rank")
def trigger_topsis_ranking(
    current_user: dict = Depends(get_current_user),
):
    all_servers = server_collection.list_documents()
    if len(all_servers) < 2:
        raise HTTPException(status_code=400, detail="Not enough servers to perform TOPSIS ranking. Minimum 2 required.")
        
    alternatives = []
    for s in all_servers:
        cpu = s.get("cpu_usage")
        ram = s.get("memory_usage")
        storage = s.get("storage_usage")
        network = s.get("network_usage")
        
        temperature, humidity, current, power, timestamp = _get_latest_sensor_data(s)
        w_priority, w_criticality, w_sensitivity = _get_workload_context(s["id"])
        
        crit_map = {"LOW": 25, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 100}
        workload_crit = crit_map.get(w_criticality, 25)
        
        raw_values = {
            "cpu": cpu,
            "ram": ram,
            "storage": storage,
            "network": network,
            "temperature": temperature,
            "power": power,
            "humidity": humidity,
            "workload_criticality": workload_crit
        }
        
        normalized_values = {
            k: normalize_criterion(k, v) for k, v in raw_values.items()
        }
        
        alternatives.append(ServerTOPSISInput(
            server_id=str(s["id"]),
            criteria=normalized_values,
            data_freshness=timestamp if timestamp else "Unknown"
        ))
        
    try:
        topsis_output = run_topsis(alternatives)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Store ranking results in agent_results
    import datetime
    for res in topsis_output.results:
        from app.ai.decision_engine import agent_results_collection
        agent_results_collection.create_document(data={
            "server_id": res.server_id,
            "agent_name": "TOPSIS_Ranking",
            "score": res.closeness_coefficient * 100,
            "risk_level": "N/A",
            "factors": [
                f"Rank: {res.rank} out of {len(all_servers)}",
                f"Closeness to negative-ideal risk: {res.closeness_coefficient:.4f}"
            ],
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        
    return topsis_output.dict()

@router.get("/recommendations")
def get_recommendations(
    current_user: dict = Depends(get_current_user),
):
    recs = ai_recommendations_collection.list_documents()
    recs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    results = []
    for rec in recs:
        try:
            server = server_collection.get_document(rec["server_id"])
            server_name = server.get("server_name", f"Server-{rec['server_id']}")
        except:
            server_name = f"Server-{rec['server_id']}"
            
        results.append({
            "id": rec.get("id"),
            "server_id": rec["server_id"],
            "server_name": server_name,
            "risk_score": rec.get("risk_score"),
            "priority": rec.get("priority"),
            "topsis_rank": rec.get("topsis_rank"),
            "recommendation": rec.get("recommendation"),
            "status": rec.get("status"),
            "created_at": rec.get("created_at"),
        })
    return results

@router.get("/recommendations/{rec_id}")
def get_recommendation(
    rec_id: str,
    current_user: dict = Depends(get_current_user),
):
    rec = ai_recommendations_collection.get_document(rec_id)
    return _build_full_response(rec)

from pydantic import BaseModel
class StatusUpdate(BaseModel):
    status: str

@router.patch("/recommendations/{rec_id}/status")
def update_rec_status(
    rec_id: str,
    update_data: StatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    from app.ai.recommendation_engine import update_recommendation_status
    try:
        updated = update_recommendation_status(rec_id, update_data.status.upper())
        return _build_full_response(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
