from flask import Blueprint, Response, jsonify, request
from .utils import get_team_matches, get_team_squad,get_match_statistics
import json
import requests
from .config import db, s3, con
import pandas as pd
import io


main = Blueprint('main', __name__)


@main.route('/matches', methods=['GET'])
def fetch_matches():
    try:
        response = requests.get("http://localhost:3000/api/matches")  # Klic na mikrostoritev
        return Response(response.text, status=response.status_code, mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({'message': str(e)}, ensure_ascii=False), status=500, mimetype='application/json')

@main.route('/team-matches/<int:team_id>', methods=['GET'])
def fetch_team_matches(team_id):
    matches = get_team_matches(team_id)
    if "error" in matches:
        return Response(
            json.dumps({'message': matches["error"]}, ensure_ascii=False, indent=4),
            status=500,
            mimetype='application/json'
        )
    return Response(
        json.dumps(matches, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )

@main.route('/team-squad/<int:team_id>', methods=['GET'])
def fetch_team_squad(team_id):
    squad = get_team_squad(team_id)
    if "error" in squad:
        return Response(
            json.dumps({'message': squad["error"]}, ensure_ascii=False, indent=4),
            status=500,
            mimetype='application/json'
        )
    return Response(
        json.dumps(squad, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )

@main.route('/match-statistics/<int:match_id>', methods=['GET'])
def fetch_match_statistics(match_id):
    stats = get_match_statistics(match_id)
    if "error" in stats:
        return Response(
            json.dumps({'message': stats["error"]}, ensure_ascii=False, indent=4),
            status=500,
            mimetype='application/json'
        )
    return Response(
        json.dumps(stats, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )


@main.route('/test-firestore', methods=['GET'])
def test_firestore():
    try:
        users_ref = db.collection('users')
        docs = users_ref.stream()
        users = [doc.to_dict() for doc in docs]
        return Response(json.dumps(users, ensure_ascii=False), status=200, mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({'error': str(e)}, ensure_ascii=False), status=500, mimetype='application/json')
    
@main.route('/api/fpl/team/<int:team_id>', methods=['GET'])
def get_fpl_team(team_id):
    try:
        gw = 36  # ali dinamično iz frontend ali nastavitev

        # API-ji
        picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"
        elements_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        live_url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"

        # Fetch podatkov
        picks_res = requests.get(picks_url)
        if picks_res.status_code != 200:
            return jsonify({"error": "Team not found"}), 404
        picks_data = picks_res.json()

        elements = requests.get(elements_url).json()["elements"]
        live_stats = requests.get(live_url).json()["elements"]

        # Mape za lookup
        player_map = {player["id"]: player for player in elements}
        live_points_map = {player["id"]: player["stats"]["total_points"] for player in live_stats}

        starting_players = []
        bench_players = []
        total_points = 0

        for pick in picks_data["picks"]:
            player_id = pick["element"]
            player = player_map[player_id]

            player_data = {
                "id": player_id,
                "first_name": player["first_name"],
                "second_name": player["second_name"],
                "position": player["element_type"],
                "team": player["team"],
                "multiplier": pick["multiplier"],
                "is_captain": pick["is_captain"],
                "is_vice_captain": pick["is_vice_captain"],
                "points": live_points_map.get(player_id, 0)
            }

            if pick["position"] <= 11:
                starting_players.append(player_data)
                total_points += player_data["points"] * pick["multiplier"]
            else:
                bench_players.append(player_data)

        return jsonify({
            "starting_players": starting_players,
            "bench_players": bench_players,
            "total_points": total_points
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    

# GALOV DEL ZA ANALYSIS HUB
def load_parquet_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Load a parquet file from S3 and return it as a DataFrame."""
    response = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_parquet(io.BytesIO(response['Body'].read()))


@main.route("/api/teams", methods=['GET'])
def get_pass_clusters():
    """Returns clustered passes from the parquet file on S3."""
    try:
        df = load_parquet_from_s3("footlyiq-data", "gold/pass_clustering/parquet/teams.parquet")
        # Optional: reduce size before sending to frontend
        #limited = df.head(100)  # send only 100 rows for test
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/get_team_id", methods=['GET'])
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
    

@main.route("/api/passes/most-common", methods=['GET'])
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
    

@main.route("/api/passes/last-third", methods=['GET'])
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

        df_limited = top_6_clusters.head(50)
        
        return jsonify(df_limited.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    

@main.route("/api/passes/filters", methods=['GET'])
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


