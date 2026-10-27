import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase only once
def initialize_firebase():
    if not firebase_admin._apps:
        # 1. Check for raw JSON string in environment variable (Render / Cloud production)
        firebase_cred_env = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_cred_env:
            try:
                cred_dict = json.loads(firebase_cred_env)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                return
            except Exception as e:
                print(f"Error parsing FIREBASE_CREDENTIALS environment variable: {e}")

        # 2. Check Render default secret file location (/etc/secrets/serviceAccountKey.json)
        render_secret_path = "/etc/secrets/serviceAccountKey.json"
        if os.path.exists(render_secret_path):
            cred = credentials.Certificate(render_secret_path)
            firebase_admin.initialize_app(cred)
            return

        # 3. Check local credentials file (Local development)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cred_path = os.path.join(base_dir, "credentials", "serviceAccountKey.json")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase service account key not found at {cred_path} or {render_secret_path}, "
                "and FIREBASE_CREDENTIALS environment variable is not set. "
                "Please set the FIREBASE_CREDENTIALS environment variable or add serviceAccountKey.json."
            )
            
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

initialize_firebase()
db = firestore.client()

