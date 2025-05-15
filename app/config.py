import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os

# Nalaganje okolijskih spremenljivk iz .env datoteke
load_dotenv()

# Inicializacija Firebase
key_path = os.getenv("FIREBASE_KEY_PATH")  # Pot do JSON ključa
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

# Firestore baza
db = firestore.client()