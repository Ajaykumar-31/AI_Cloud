from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.services.firestore_service import FirestoreService
import hashlib

alerts_collection = FirestoreService("alerts")

def map_risk_to_severity(score: float) -> str:
    """
    Mapping from risk scores to severity:
    0-30: INFO
    31-50: LOW
    51-70: MEDIUM
    71-85: HIGH
    86-100: CRITICAL
    """
    if score <= 30: return "INFO"
    if score <= 50: return "LOW"
    if score <= 70: return "MEDIUM"
    if score <= 85: return "HIGH"
    return "CRITICAL"


class Alert(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    severity: str
    priority: int
    server_id: str
    source_recommendation_id: Optional[str] = None
    observed_values: Dict[str, Any]
    threshold: Optional[float] = None
    status: str = "NEW"
    fingerprint: str
    created_at: str
    updated_at: str


def compute_priority(severity: str, risk_score: float, workload_criticality: str, is_stale: bool) -> int:
    """
    Prioritize alerts by severity, risk score, critical workload context, and data freshness.
    Lower number means higher priority.
    """
    if is_stale:
        # Do not treat stale telemetry as a confirmed live fault. Give it lower priority.
        return 100
        
    sev_map = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4, "INFO": 5}
    base = sev_map.get(severity, 5) * 10
    
    workload_map = {"CRITICAL": 0, "HIGH": 2, "MEDIUM": 4, "LOW": 6}
    wl = workload_map.get(workload_criticality.upper(), 6)
    
    # Priority = (Severity Base) + (Workload Adjustment) - (Risk Score / 100)
    # The higher the risk score, the lower the number (higher priority).
    return int(base + wl - (risk_score / 20.0))


def generate_alerts(
    server_id: str,
    agent_results: List[Dict[str, Any]],
    workload_criticality: str = "LOW",
    is_stale: bool = False,
    source_rec_id: Optional[str] = None
) -> List[Alert]:
    
    generated = []
    
    # 1. Analyze findings
    for res in agent_results:
        risk_level = res.get("risk_level", "UNKNOWN")
        score = float(res.get("score", 0.0))
        agent = res.get("agent_name", "")
        
        # We only alert on HIGH/CRITICAL or if score > 70
        if score > 70 and not is_stale:
            title = f"{agent} Alert"
            description = f"Agent '{agent}' reported elevated risk."
            if "factors" in res and res["factors"]:
                description += f" Findings: {', '.join(res['factors'])}"
                
            severity = map_risk_to_severity(score)
            priority = compute_priority(severity, score, workload_criticality, is_stale)
            
            fingerprint_raw = f"{server_id}_{agent}_{title}"
            fingerprint = hashlib.sha256(fingerprint_raw.encode()).hexdigest()
            
            alert = Alert(
                title=title,
                description=description,
                severity=severity,
                priority=priority,
                server_id=server_id,
                source_recommendation_id=source_rec_id,
                observed_values={"score": score},
                threshold=70.0,
                fingerprint=fingerprint,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            generated.append(alert)
            
    # Also generate a specific alert if stale
    if is_stale:
        fingerprint = hashlib.sha256(f"{server_id}_STALE_DATA".encode()).hexdigest()
        alert = Alert(
            title="Stale Telemetry Data",
            description="Telemetry for this server is stale or missing.",
            severity="INFO",
            priority=100,
            server_id=server_id,
            source_recommendation_id=source_rec_id,
            observed_values={"stale": True},
            fingerprint=fingerprint,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        generated.append(alert)
        
    saved_alerts = []
    
    for alert in generated:
        # Deduplicate
        existing = alerts_collection.query_documents("fingerprint", "==", alert.fingerprint)
        unresolved = [e for e in existing if e.get("status") in ["NEW", "ACKNOWLEDGED"]]
        
        if unresolved:
            # Update the first unresolved one
            target = unresolved[0]
            updates = {
                "updated_at": datetime.utcnow().isoformat(),
                "priority": alert.priority,
                "severity": alert.severity,
                "observed_values": alert.observed_values,
                "description": alert.description
            }
            alerts_collection.update_document(target["id"], updates)
            target.update(updates)
            
            # Map back to Alert object
            alert.id = target["id"]
            alert.status = target["status"]
            alert.created_at = target["created_at"]
            saved_alerts.append(alert)
        else:
            # Create new
            doc = alert.dict(exclude={"id"})
            doc_id = alerts_collection.create_document(data=doc)
            alert.id = doc_id
            saved_alerts.append(alert)
            
    # Sort by priority
    saved_alerts.sort(key=lambda a: a.priority)
    return saved_alerts
