import json
from typing import List, Optional, Tuple
from datetime import datetime

from app.services.firestore_service import FirestoreService
from app.ai.infrastructure_agent import InfrastructureAgent
from app.ai.environmental_agent import EnvironmentalAgent
from app.ai.energy_agent import EnergyAgent
from app.ai.workload_agent import WorkloadContextAgent
from app.ai.coordinator_agent import CoordinatorAgent
from app.ai.base_agent import AgentResult

server_collection = FirestoreService("servers")
iot_devices_collection = FirestoreService("iot_devices")
sensor_readings_collection = FirestoreService("sensor_readings")
workloads_collection = FirestoreService("workloads")
agent_results_collection = FirestoreService("agent_results")
ai_recommendations_collection = FirestoreService("ai_recommendations")

def _generate_recommendation_text(risk_level: str, findings: List[str]) -> str:
    advice_parts = []
    has_cpu = any("CPU" in f.upper() for f in findings)
    has_temp = any("TEMPERATURE" in f.upper() or "TEMP" in f.upper() for f in findings)
    has_power = any("POWER" in f.upper() or "CURRENT" in f.upper() or "ENERGY" in f.upper() for f in findings)
    has_memory = any("RAM" in f.upper() or "MEMORY" in f.upper() for f in findings)
    has_storage = any("STORAGE" in f.upper() for f in findings)
    has_humidity = any("HUMIDITY" in f.upper() for f in findings)
    has_workload = any("WORKLOAD" in f.upper() or "CRITICALITY" in f.upper() or "PRIORITY" in f.upper() for f in findings)
    has_missing = any("MISSING" in f.upper() or "STALE" in f.upper() or "INVALID" in f.upper() for f in findings)

    if has_missing: advice_parts.append("Investigate and resolve missing or invalid sensor telemetry.")
    if has_temp: advice_parts.append("Inspect the cooling system and verify airflow in the server rack.")
    if has_cpu: advice_parts.append("Avoid assigning additional workloads until CPU load stabilizes.")
    if has_memory: advice_parts.append("Review memory allocation and consider scaling or migrating low-priority workloads.")
    if has_power: advice_parts.append("Monitor power draw closely; consider load redistribution across racks.")
    if has_storage: advice_parts.append("Plan storage capacity expansion or archive old data.")
    if has_humidity: advice_parts.append("Check environmental controls for humidity regulation.")
    if has_workload: advice_parts.append("This server hosts high-priority workloads; ensure redundancy and failover readiness.")

    if not advice_parts:
        if risk_level in ("HIGH", "CRITICAL"):
            advice_parts.append("Perform a comprehensive review of this server's operating conditions.")
        elif risk_level == "UNKNOWN":
            advice_parts.append("Resolve data availability issues before making operational decisions.")
        else:
            advice_parts.append("No immediate action required. Continue routine monitoring.")
    return " ".join(advice_parts)

def _generate_explanation(coordinator_output: dict, risk_level: str) -> str:
    score = coordinator_output["overall_health_score"]
    lines = [
        f"The Multi-Agent Decision Engine evaluated this server across infrastructure, environmental, energy, and workload dimensions.",
        f"The overall health score is {score:.1f}/100 with an aggregate risk level of {risk_level}."
    ]
    if risk_level == "UNKNOWN":
        lines.append("Assessment is incomplete due to missing, stale, or invalid telemetry.")
    elif coordinator_output["action_required"]:
        lines.append("Administrator review is required before any operational changes.")
    else:
        lines.append("No urgent issues detected at this time.")
    return " ".join(lines)

def _map_priority(risk_level: str) -> str:
    return {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW", "UNKNOWN": "HIGH"}.get(risk_level, "LOW")

def _get_latest_sensor_data(server: dict) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[str]]:
    devices = iot_devices_collection.list_documents()
    latest_temp, latest_hum, latest_current, latest_power, latest_ts = None, None, None, None, None
    
    for device in devices:
        readings = sensor_readings_collection.query_documents("device_id", "==", device["id"])
        if readings:
            readings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            r = readings[0]
            if r.get("temperature") is not None: latest_temp = r.get("temperature")
            if r.get("humidity") is not None: latest_hum = r.get("humidity")
            if r.get("current") is not None: latest_current = r.get("current")
            if r.get("power") is not None: latest_power = r.get("power")
            if r.get("timestamp") is not None: latest_ts = r.get("timestamp")
            break
    return latest_temp, latest_hum, latest_current, latest_power, latest_ts

def _get_workload_context(server_id: str) -> Tuple[str, str, str]:
    priority_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    workloads = workloads_collection.query_documents("preferred_server_id", "==", server_id)
    if not workloads:
        return "LOW", "LOW", "PUBLIC"
    most_critical = max(workloads, key=lambda w: priority_order.get(w.get("criticality", "LOW"), 0))
    return (
        most_critical.get("priority", "LOW"),
        most_critical.get("criticality", "LOW"),
        most_critical.get("sensitivity", "PUBLIC")
    )

def analyze_server(server_id: str) -> dict:
    server = server_collection.get_document(server_id)
    
    cpu = server.get("cpu_usage")
    ram = server.get("memory_usage")
    storage = server.get("storage_usage")
    network = server.get("network_usage")

    temperature, humidity, current, power, timestamp = _get_latest_sensor_data(server)
    w_priority, w_criticality, w_sensitivity = _get_workload_context(server_id)

    infra_agent = InfrastructureAgent()
    env_agent = EnvironmentalAgent()
    energy_agent = EnergyAgent()
    workload_agent = WorkloadContextAgent()

    infra_result = infra_agent.evaluate(cpu=cpu, ram=ram, storage=storage, network=network)
    env_result = env_agent.evaluate(temperature=temperature, humidity=humidity, timestamp=timestamp)
    energy_result = energy_agent.evaluate(current=current, power=power)
    workload_result = workload_agent.evaluate(priority=w_priority, criticality=w_criticality, sensitivity=w_sensitivity)

    agent_results = [infra_result, env_result, energy_result, workload_result]
    
    for ar in agent_results:
        agent_results_collection.create_document(data={
            "server_id": server_id,
            "agent_name": ar.agent_name,
            "score": ar.score,
            "risk_level": ar.risk_level,
            "factors": ar.findings,
            "timestamp": datetime.utcnow().isoformat()
        })

    coordinator = CoordinatorAgent()
    coordinator_output = coordinator.compile_decision_input(agent_results)

    overall_risk_score = coordinator_output["overall_health_score"]
    risk_level = coordinator_output["aggregate_risk_level"]

    recommendation_text = _generate_recommendation_text(risk_level, coordinator_output["combined_findings"])
    explanation_text = _generate_explanation(coordinator_output, risk_level)
    priority = _map_priority(risk_level)

    agent_scores_dict = {
        ar.agent_name: {"score": ar.score, "risk_level": ar.risk_level, "findings": ar.findings}
        for ar in agent_results
    }
    
    rec_data = {
        "server_id": server_id,
        "risk_score": round(overall_risk_score, 2),
        "risk_level": risk_level,
        "priority": priority,
        "topsis_rank": None,
        "topsis_score": None,
        "agent_scores": agent_scores_dict,
        "contributing_factors": coordinator_output["combined_findings"],
        "recommendation": recommendation_text,
        "explanation": explanation_text,
        "status": "ADMINISTRATOR_REVIEW_REQUIRED",
        "created_at": datetime.utcnow().isoformat()
    }
    doc_id = ai_recommendations_collection.create_document(data=rec_data)
    return ai_recommendations_collection.get_document(doc_id)
