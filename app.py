from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
import pandas as pd
import io
import os
import json
import duckdb
import urllib.parse
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

# === Initialize DuckDB Connection Once ===
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"SET s3_region='{creds['region_name']}';")
# Optional if you need explicit creds (already set in env vars)
con.execute(f"SET s3_access_key_id='{creds['aws_access_key_id']}';")
con.execute(f"SET s3_secret_access_key='{creds['aws_secret_access_key']}';")


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
        df = load_parquet_from_s3("footlyiq-data", "gold/pass_clustering/parquet/teams.parquet")
        # Optional: reduce size before sending to frontend
        #limited = df.head(100)  # send only 100 rows for test
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/get_team_id", methods=['GET'])
def get_team_id():
    """Returns team_id from teams dataframe based on the team name."""
    team_name = request.args.get("team_name")
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400
    
    try:
        s3_path = "s3://footlyiq-data/bronze/teams.parquet"

        result = con.execute("""
            SELECT team_id, name, country
            FROM read_parquet(?)
            WHERE name = ?
        """, [s3_path, team_name]).fetchdf()

        if result.empty:
            return jsonify({"error": "Team not found"}), 404
        
        return jsonify(result.to_dict(orient="records"))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def inside_get_team_id(name):
    """Returns team_id from teams dataframe based on the team name."""
    try:
        s3_path = "s3://footlyiq-data/bronze/teams.parquet"

        result = con.execute("""
            SELECT team_id
            FROM read_parquet(?)
            WHERE name = ?
        """, [s3_path, name]).fetchdf()

        if result.empty:
            return None
        
        return result.iloc[0]["team_id"] # Return the scalar team_id
    
    except Exception as e:
        print(f"Error in inside_get_team_id: {e}")
        return None
    

@app.route("/api/passes/most-common", methods=['GET'])
def get_most_common_pass_clusters():
    #POMEBNO: funkcija vraca 0-based cluster labels (0-59), torej pri vizualizaciji moreš offsetat za 1 kot pri MOS-u (cluster+1) !!!!!!!!
    """Returns clustered passes from the parquet file on S3."""
    team_name = request.args.get("team_name")
    print(team_name)
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400
    
    try:
        df = load_parquet_from_s3("footlyiq-data", "gold/pass_clustering/parquet/ALL_clustered_passes_1_colab.parquet")
        team_id = inside_get_team_id(team_name)

        if team_id is None:
            return jsonify({"error": "Team not found"}), 404
        
        print(f"team_id: {team_id}")

        df_passes = df[df["team_id"] == team_id]
        top_6 = df_passes["label"].value_counts().head(6).index
        top_6_clusters = df_passes[df_passes["label"].isin(top_6)]

        df_limited = top_6_clusters.head(50)
        
        return jsonify(df_limited.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/passes/last-third/most-common", methods=['GET'])
def get_most_common_pass_clusters_last_third():
    #POMEBNO: funkcija vraca 0-based cluster labels (0-59), torej pri vizualizaciji moreš offsetat za 1 kot pri MOS-u (cluster+1) !!!!!!!!
    """Returns clustered passes penetrating in the last 3 from the parquet file on S3."""
    team_name = request.args.get("team_name")
    print(team_name)
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400
    
    try:
        df = load_parquet_from_s3("footlyiq-data", "gold/pass_clustering/parquet/FINAL-3rd_clustered_passes_1.parquet")
        team_id = inside_get_team_id(team_name)

        if team_id is None:
            return jsonify({"error": "Team not found"}), 404
        
        print(f"team_id: {team_id}")

        df_passes = df[df["team_id"] == team_id]
        top_6 = df_passes["label"].value_counts().head(6).index
        top_6_clusters = df_passes[df_passes["label"].isin(top_6)]

        df_limited = top_6_clusters.head(100)
        
        return jsonify(df_limited.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    

@app.route("/api/passes/filters", methods=['GET'])
def filter_pass_clusters():
    """
    Returns clustered passes from the parquet file on S3,
    optionally filtered by parameters like successful, pass_high, long_pass, and pass_length.
    """
    team_name = request.args.get("team_name")
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400

    try:
        # Load the full dataset
        df = load_parquet_from_s3("footlyiq-data", "gold/pass_clustering/parquet/ALL_clustered_passes_1_colab.parquet")
        team_id = inside_get_team_id(team_name)

        if team_id is None:
            return jsonify({"error": "Team not found"}), 404

        # Filter by team
        df_passes = df[df["team_id"] == team_id]

        # Optional filters
        filter_fields = {
            "successful": lambda x: x.lower() in ["true", "1"],
            "pass_high": lambda x: x.lower() in ["true", "1"],
            "long_pass": lambda x: x.lower() in ["true", "1"],
            "pass_length": float  # This is numeric
        }

        for field, parser in filter_fields.items():
            if field in request.args:
                value = request.args.get(field)
                try:
                    parsed_value = parser(value)
                    if field == "pass_length":
                        df_passes = df_passes[df_passes[field] >= parsed_value]
                    else:
                        df_passes = df_passes[df_passes[field] == parsed_value]
                except Exception as parse_err:
                    return jsonify({"error": f"Invalid value for {field}: {value}"}), 400

        # Top 6 clusters by frequency
        top_6 = df_passes["label"].value_counts().head(6).index
        top_6_clusters = df_passes[df_passes["label"].isin(top_6)]

        # Optional: limit result size
        df_limited = top_6_clusters.head(50)

        return jsonify(df_limited.to_dict(orient="records"))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# NE POZABI VKLOPIT VENV KO ZAČNEŠ ZAGANJAT !!!!!!!!!!!!!!!!!!!!!    

if __name__ == '__main__':
    app.run()
