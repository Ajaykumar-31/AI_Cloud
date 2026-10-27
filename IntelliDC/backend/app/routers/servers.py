from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from app.services.firestore_service import FirestoreService
from app.routers.auth import get_current_user
from datetime import datetime, timezone
from app.schemas.server import ServerCreate, ServerUpdate, MetricCreate

router = APIRouter(prefix="/api/servers", tags=["servers"])
server_collection = FirestoreService("servers")
metrics_collection = FirestoreService("infrastructure_metrics")

@router.get("")
def get_servers(current_user: dict = Depends(get_current_user)):
    servers = server_collection.list_documents()
    return {"servers": servers}

@router.get("/{server_id}")
def get_server(server_id: str, current_user: dict = Depends(get_current_user)):
    return server_collection.get_document(server_id)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_server(server_data: ServerCreate, current_user: dict = Depends(get_current_user)):
    data = server_data.model_dump()
    timestamp = datetime.now(timezone.utc).isoformat()
    data["created_at"] = timestamp
    data["updated_at"] = timestamp
    doc_id = server_collection.create_document(data=data)
    return server_collection.get_document(doc_id)

@router.put("/{server_id}")
def update_server(server_id: str, server_data: ServerUpdate, current_user: dict = Depends(get_current_user)):
    data = server_data.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    return server_collection.update_document(server_id, data)

@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: str, current_user: dict = Depends(get_current_user)):
    server_collection.delete_document(server_id)
    # Delete metrics as well
    metrics = metrics_collection.query_documents("server_id", "==", server_id)
    for m in metrics:
        metrics_collection.delete_document(m["id"])
    return None

@router.get("/{server_id}/metrics")
def get_server_metrics(server_id: str, limit: int = 50, current_user: dict = Depends(get_current_user)):
    # Verify server exists
    server_collection.get_document(server_id)
    
    metrics = metrics_collection.query_documents("server_id", "==", server_id)
    # Sort locally by timestamp descending, take limit
    metrics.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    metrics = metrics[:limit]
    return {
        "server_id": server_id,
        "metrics": list(reversed(metrics))
    }

@router.post("/{server_id}/metrics", status_code=status.HTTP_201_CREATED)
def add_server_metric(server_id: str, metric_data: MetricCreate, current_user: dict = Depends(get_current_user)):
    # Verify server exists
    server = server_collection.get_document(server_id)
    
    data = metric_data.model_dump()
    data["server_id"] = server_id
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    doc_id = metrics_collection.create_document(data=data)
    
    return metrics_collection.get_document(doc_id)
