from flask import Flask, jsonify
from flask_cors import CORS
import boto3
import pandas as pd
import io
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app) #ZAENKRAT DOVOLIMO ALL ORIGINS - PRED PRODUKCIJO POPRAVIT

# Load AWS credentials from JSON
with open(os.getenv("AWS_CREDENTIALS_PATH")) as f:
    creds = json.load(f)

s3 = boto3.client(
    's3',
    aws_access_key_id=creds['aws_access_key_id'],
    aws_secret_access_key=creds['aws_secret_access_key'],
    region_name=creds['region_name']
)

def load_parquet_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Load a parquet file from S3 and return it as a DataFrame."""
    response = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_parquet(io.BytesIO(response['Body'].read()))


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route("/test", methods=['GET'])
def test_be():
    return "Backend deluje"

@app.route("/api/teams", methods=['GET'])
def get_pass_clusters():
    """Returns clustered passes from the parquet file on S3."""
    try:
        df = load_parquet_from_s3("footlyiq-data", "teams.parquet")
        # Optional: reduce size before sending to frontend
        #limited = df.head(100)  # send only 100 rows for test
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run()
