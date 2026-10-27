from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from app.services.firestore_service import FirestoreService
from app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/workloads", tags=["workloads"])
workloads_collection = FirestoreService("workloads")

class WorkloadCreate(BaseModel):
    workload_name: str
    application_type: str
    department: str
    priority: str
    criticality: str
    sensitivity: str
    preferred_server_id: Optional[str] = None
    status: str = "ACTIVE"

class WorkloadUpdate(BaseModel):
    workload_name: Optional[str] = None
    application_type: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None
    criticality: Optional[str] = None
    sensitivity: Optional[str] = None
    preferred_server_id: Optional[str] = None
    status: Optional[str] = None

@router.get("")
def get_workloads(current_user: dict = Depends(get_current_user)):
    return workloads_collection.list_documents()

@router.get("/{workload_id}")
def get_workload(workload_id: str, current_user: dict = Depends(get_current_user)):
    return workloads_collection.get_document(workload_id)

@router.post("")
def create_workload(workload_data: WorkloadCreate, current_user: dict = Depends(get_current_user)):
    data = workload_data.model_dump()
    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()
    doc_id = workloads_collection.create_document(data=data)
    return workloads_collection.get_document(doc_id)

@router.put("/{workload_id}")
def update_workload(workload_id: str, workload_data: WorkloadUpdate, current_user: dict = Depends(get_current_user)):
    data = workload_data.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow().isoformat()
    return workloads_collection.update_document(workload_id, data)

@router.delete("/{workload_id}")
def delete_workload(workload_id: str, current_user: dict = Depends(get_current_user)):
    workloads_collection.delete_document(workload_id)
    return {"detail": "Workload deleted successfully"}
