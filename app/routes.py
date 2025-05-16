from flask import Blueprint, Response, jsonify
from .utils import get_team_matches
import json
import requests
from .config import db

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

from .utils import get_team_squad

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
