from flask import Blueprint, Response, jsonify, request
from .utils import get_team_matches, get_team_squad,get_match_statistics, get_matches_from_api, get_player_details, get_player_matches, get_team_filters
import json
import requests
from .config import db

main = Blueprint('main', __name__)


@main.route('/matches', methods=['GET'])
def fetch_matches():
    try:
        # Get date from query parameters, but don't provide a default
        # Let the microservice handle the default case
        date = request.args.get('date')
        data = get_matches_from_api(date)
        
        if "error" in data:
            return jsonify(data), 500
            
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

@main.route('/team-matches/<int:team_id>', methods=['GET'])
def fetch_team_matches(team_id):
    season = request.args.get('season')
    competition = request.args.get('competition')
    matches = get_team_matches(team_id, season=season, competition=competition)
    if "error" in matches:
        return jsonify({"message": matches["error"]}), 500
    return jsonify(matches)

@main.route('/team-filters/<int:team_id>', methods=['GET'])
def fetch_team_filters(team_id):
    try:
        filters = get_team_filters(team_id)
        if "error" in filters:
            return jsonify({"message": filters["error"]}), 500
        return jsonify(filters)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/team-squad/<int:team_id>', methods=['GET'])
def fetch_team_squad(team_id):
    squad = get_team_squad(team_id)
    if "error" in squad:
        return jsonify({"message": squad["error"]}), 500
    return jsonify(squad)

@main.route('/match-statistics/<int:match_id>', methods=['GET'])
def fetch_match_statistics(match_id):
    stats = get_match_statistics(match_id)
    if "error" in stats:
        return jsonify({"message": stats["error"]}), 500
    return jsonify(stats)

@main.route('/player/<int:player_id>', methods=['GET'])
def fetch_player_details(player_id):
    try:
        data = get_player_details(player_id)
        if "error" in data:
            return jsonify(data), 500
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/player/<int:player_id>/matches', methods=['GET'])
def fetch_player_matches(player_id):
    try:
        limit = request.args.get('limit', default=50, type=int)
        season = request.args.get('season')
        competition = request.args.get('competition')
        data = get_player_matches(player_id, limit, season, competition)
        if "error" in data:
            return jsonify(data), 500
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
