import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import duckdb
import boto3
import json

# Nalaganje okolijskih spremenljivk iz .env datoteke
load_dotenv()

# Inicializacija Firebase
key_path = os.getenv("FIREBASE_KEY_PATH")  # Pot do JSON ključa
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

# Firestore baza
db = firestore.client()

# Load AWS credentials from JSON
with open(os.getenv("AWS_CREDENTIALS_PATH")) as f:
    creds = json.load(f)

s3 = boto3.client(
    's3',
    aws_access_key_id=creds['aws_access_key_id'],
    aws_secret_access_key=creds['aws_secret_access_key'],
    region_name=creds['region_name']
)

# === Initialize DuckDB Connection Once ===
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"SET s3_region='{creds['region_name']}';")
# Optional if you need explicit creds (already set in env vars)
con.execute(f"SET s3_access_key_id='{creds['aws_access_key_id']}';")
con.execute(f"SET s3_secret_access_key='{creds['aws_secret_access_key']}';")


# BETTING
MICROSERVICE_URL = os.getenv("BETTING_SERVICE_URL", "http://localhost:3001")