from typing import List, Dict, Any, Optional
from google.cloud import firestore
from app.config.firebase import db
from fastapi import HTTPException

class FirestoreService:
    def __init__(self, collection_name: str):
        self.collection = db.collection(collection_name)

    def create_document(self, document_id: Optional[str] = None, data: Dict[str, Any] = {}) -> str:
        """Create a new document, with or without a specific ID."""
        try:
            if document_id:
                doc_ref = self.collection.document(document_id)
                # Check if it already exists
                if doc_ref.get().exists:
                    raise HTTPException(status_code=400, detail=f"Document with ID {document_id} already exists.")
                doc_ref.set(data)
                return document_id
            else:
                _, doc_ref = self.collection.add(data)
                return doc_ref.id
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Firestore create failed: {str(e)}")

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve a specific document by ID."""
        try:
            doc = self.collection.document(document_id).get()
            if not doc.exists:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Firestore get failed: {str(e)}")

    def update_document(self, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific document."""
        try:
            doc_ref = self.collection.document(document_id)
            if not doc_ref.get().exists:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
            doc_ref.update(data)
            return self.get_document(document_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Firestore update failed: {str(e)}")

    def delete_document(self, document_id: str) -> bool:
        """Delete a specific document."""
        try:
            doc_ref = self.collection.document(document_id)
            if not doc_ref.get().exists:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
            doc_ref.delete()
            return True
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Firestore delete failed: {str(e)}")

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the collection."""
        try:
            docs = self.collection.stream()
            result = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                result.append(data)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Firestore list failed: {str(e)}")

    def query_documents(self, field: str, operator: str, value: Any) -> List[Dict[str, Any]]:
        """Query documents based on a condition."""
        try:
            query = self.collection.where(field, operator, value).stream()
            result = []
            for doc in query:
                data = doc.to_dict()
                data['id'] = doc.id
                result.append(data)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Firestore query failed: {str(e)}")
