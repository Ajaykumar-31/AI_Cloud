from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException
from app.config.settings import settings
from app.services.firestore_service import FirestoreService
import os

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
admin_collection = FirestoreService("admins")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def authenticate_admin(email, password):
    # Ensure there's a default admin if it doesn't exist
    admin_users = admin_collection.query_documents("email", "==", email)
    
    if not admin_users:
        if email == os.environ.get("ADMIN_EMAIL", "admin@intellidc.com"):
            # Create the initial admin dynamically
            admin_data = {
                "email": email,
                "name": "IntelliDC Admin",
                "role": "ADMIN",
                "password_hash": get_password_hash(os.environ.get("ADMIN_PASSWORD", "admin123")),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            admin_collection.create_document(data=admin_data)
            admin_users = [admin_data]
        else:
            return None
            
    user = admin_users[0]
    if not verify_password(password, user["password_hash"]):
        return None
    return user
