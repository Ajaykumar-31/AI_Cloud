from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.services.firestore_service import FirestoreService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
alerts_collection = FirestoreService("alerts")

VALID_TRANSITIONS = {
    "NEW": ["ACKNOWLEDGED", "RESOLVED", "DISMISSED"],
    "ACKNOWLEDGED": ["RESOLVED", "DISMISSED"],
    "RESOLVED": ["NEW"],
    "DISMISSED": ["NEW"]
}

@router.get("")
def get_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    server_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    alerts = alerts_collection.list_documents()
    
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    if status:
        alerts = [a for a in alerts if a.get("status") == status]
    if server_id:
        alerts = [a for a in alerts if a.get("server_id") == server_id]
        
    alerts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return alerts

@router.get("/{alert_id}")
def get_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    return alerts_collection.get_document(alert_id)


def _update_status(alert_id: str, new_status: str) -> dict:
    alert = alerts_collection.get_document(alert_id)
    current_status = alert.get("status", "NEW").upper()
    if current_status == "ACTIVE":
        current_status = "NEW"
        
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise HTTPException(status_code=400, detail=f"Invalid transition from {current_status} to {new_status}")
        
    updates = {
        "status": new_status,
        "updated_at": datetime.utcnow().isoformat()
    }
    if new_status == "ACKNOWLEDGED":
        updates["acknowledged_at"] = updates["updated_at"]
    elif new_status == "RESOLVED":
        updates["resolved_at"] = updates["updated_at"]
        
    alerts_collection.update_document(alert_id, updates)
    alert.update(updates)
    return alert

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    return _update_status(alert_id, "ACKNOWLEDGED")

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    return _update_status(alert_id, "RESOLVED")

@router.post("/{alert_id}/dismiss")
def dismiss_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    return _update_status(alert_id, "DISMISSED")
