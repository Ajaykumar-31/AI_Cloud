import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase only once
def initialize_firebase():
    if not firebase_admin._apps:
        # Resolve the absolute path to the credentials file
        # Assuming this script is in backend/app/config/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cred_path = os.path.join(base_dir, "credentials", "serviceAccountKey.json")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase service account key not found at {cred_path}. "
                "Please add serviceAccountKey.json to the credentials/ directory."
            )
            
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

initialize_firebase()
db = firestore.client()
