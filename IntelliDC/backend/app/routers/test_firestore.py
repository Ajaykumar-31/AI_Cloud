from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.config.firebase import db
from firebase_admin import firestore

router = APIRouter(prefix="/api/test/firestore", tags=["test"])

class TestData(BaseModel):
    message: str
    value: int

@router.post("")
def create_test_document(data: TestData):
    try:
        doc_ref = db.collection("test").document("intellidc_test")
        doc_ref.set({
            "message": data.message,
            "value": data.value,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return {"status": "success", "message": "Document created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firestore write failed: {str(e)}")

@router.get("")
def read_test_document():
    try:
        doc_ref = db.collection("test").document("intellidc_test")
        doc = doc_ref.get()
        if doc.exists:
            return {"status": "success", "data": doc.to_dict()}
        else:
            raise HTTPException(status_code=404, detail="Test document not found")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Firestore read failed: {str(e)}")
