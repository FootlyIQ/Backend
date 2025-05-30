from flask import Blueprint, Response, jsonify, request
from .utils import get_team_matches, get_team_squad,get_match_statistics, get_matches_from_api, get_player_details, get_player_matches, get_team_filters, get_competition_details
import json
import requests
from .config import db, s3, con
import pandas as pd
import numpy as np
import io


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
    
@main.route('/competition/<competition_code>', methods=['GET'])
def fetch_competition_details(competition_code):
    try:
        season = request.args.get('season')  # Get season from query parameters
        data = get_competition_details(competition_code, season)
        if "error" in data:
            return jsonify({"error": data["error"]}), 500
        return jsonify(data)
    except Exception as e:
        print(f"Error in competition route: {str(e)}")
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
        gw = request.args.get("gameweek", type=int)
        if not gw:
            return jsonify({"error": "Missing gameweek parameter"}), 400

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

            # Določi osnovne točke
            base_points = live_points_map.get(player_id, 0)
            # Če je kapetan, podvoji točke
            points = base_points * 2 if pick["is_captain"] else base_points

            player_data = {
                "id": player_id,
                "first_name": player["first_name"],
                "second_name": player["second_name"],
                "position": player["element_type"],
                "team": player["team"],
                "multiplier": pick["multiplier"],
                "is_captain": pick["is_captain"],
                "is_vice_captain": pick["is_vice_captain"],
                "points": points
            }

            if pick["position"] <= 11:
                starting_players.append(player_data)
                total_points += points
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

@main.route("/api/fpl/current-gameweek", methods=["GET"])
def get_current_gameweek():
    try:
        res = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
        res.raise_for_status()
        events = res.json()["events"]
        current = next((e for e in events if e["is_current"]), None)
        if not current:
            # fallback: next event or last event
            current = next((e for e in events if e["is_next"]), events[-1])
        return jsonify({"current_gameweek": current["id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@main.route("/api/fpl/player-details/<int:player_id>", methods=["GET"])
def get_fpl_player_details(player_id):
    
    gameweek = request.args.get("gameweek", type=int)
    if not gameweek:
        return jsonify({"error": "Missing gameweek parameter"}), 400

    # Preberi ali je kapetan iz query param
    is_captain = request.args.get("is_captain", "false").lower() == "true"

    # Fetch player history and static info
    player_url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
    elements_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        response = requests.get(player_url)
        response.raise_for_status()
        data = response.json()
        bootstrap = requests.get(elements_url).json()
        elements = bootstrap["elements"]
        teams = bootstrap["teams"]
        player_info = next((el for el in elements if el["id"] == player_id), None)
        if not player_info:
            return jsonify({"error": "Player info not found"}), 404
        position = player_info["element_type"]  # 1=GK, 2=DEF, 3=MID, 4=FWD
    except Exception as e:
        return jsonify({"error": "Failed to fetch player data", "details": str(e)}), 500

    # Najdi podatke za gameweek 36
    gameweek_data = next((gw for gw in data["history"] if gw["round"] == gameweek), None)
    if not gameweek_data:
        return jsonify({"error": f"No data for gameweek {gameweek}"}), 404
    
    print("gameweek_data:", gameweek_data)
    
    # Determine home and away team IDs
    player_team_id = player_info["team"]
    opponent_team_id = gameweek_data["opponent_team"]
    
    if gameweek_data["was_home"]:
        home_team_id = player_team_id
        away_team_id = opponent_team_id
        home_score = gameweek_data["team_h_score"]
        away_score = gameweek_data["team_a_score"]
    else:
        home_team_id = opponent_team_id
        away_team_id = player_team_id
        home_score = gameweek_data["team_h_score"]
        away_score = gameweek_data["team_a_score"]
    
    # Get team short names
    home_team = next((t for t in teams if t["id"] == home_team_id), None)
    away_team = next((t for t in teams if t["id"] == away_team_id), None)
    home_short = home_team["short_name"] if home_team else "HOME"
    away_short = away_team["short_name"] if away_team else "AWAY"
    score = f"{home_score}–{away_score}"
    
    # Fixture string with short names and score
    fixture = f"{home_short} {score} {away_short}"

    # Points logic by position
    if position == 1:  # Goalkeeper
        points_map = {
            "minutes": 2 if gameweek_data["minutes"] > 59 else 1 if gameweek_data["minutes"] > 0 else 0,
            "goals_scored": gameweek_data["goals_scored"] * 6,
            "assists": gameweek_data["assists"] * 3,
            "clean_sheets": gameweek_data["clean_sheets"] * 4,
            "goals_conceded": -1 * (gameweek_data["goals_conceded"] // 2),
            "own_goals": -2 * gameweek_data["own_goals"],
            "penalties_saved": gameweek_data["penalties_saved"] * 5,
            "penalties_missed": -2 * gameweek_data["penalties_missed"],
            "yellow_cards": -1 * gameweek_data["yellow_cards"],
            "red_cards": -3 * gameweek_data["red_cards"],
            "saves": (gameweek_data["saves"] // 3),  # 1 point for every 3 saves
            "bonus": gameweek_data["bonus"],
        }
    elif position == 2:  # Defender
        points_map = {
            "minutes": 2 if gameweek_data["minutes"] > 59 else 1 if gameweek_data["minutes"] > 0 else 0,
            "goals_scored": gameweek_data["goals_scored"] * 6,
            "assists": gameweek_data["assists"] * 3,
            "clean_sheets": gameweek_data["clean_sheets"] * 4,
            "goals_conceded": -1 * (gameweek_data["goals_conceded"] // 2),
            "own_goals": -2 * gameweek_data["own_goals"],
            "penalties_saved": 0,
            "penalties_missed": -2 * gameweek_data["penalties_missed"],
            "yellow_cards": -1 * gameweek_data["yellow_cards"],
            "red_cards": -3 * gameweek_data["red_cards"],
            "saves": 0,
            "bonus": gameweek_data["bonus"],
        }
    elif position == 3:  # Midfielder
        points_map = {
            "minutes": 2 if gameweek_data["minutes"] > 59 else 1 if gameweek_data["minutes"] > 0 else 0,
            "goals_scored": gameweek_data["goals_scored"] * 5,
            "assists": gameweek_data["assists"] * 3,
            "clean_sheets": gameweek_data["clean_sheets"] * 1,
            "goals_conceded": 0,
            "own_goals": -2 * gameweek_data["own_goals"],
            "penalties_saved": 0,
            "penalties_missed": -2 * gameweek_data["penalties_missed"],
            "yellow_cards": -1 * gameweek_data["yellow_cards"],
            "red_cards": -3 * gameweek_data["red_cards"],
            "saves": 0,
            "bonus": gameweek_data["bonus"],
        }
    else:  # Forward
        points_map = {
            "minutes": 2 if gameweek_data["minutes"] > 59 else 1 if gameweek_data["minutes"] > 0 else 0,
            "goals_scored": gameweek_data["goals_scored"] * 4,
            "assists": gameweek_data["assists"] * 3,
            "clean_sheets": 0,
            "goals_conceded": 0,
            "own_goals": -2 * gameweek_data["own_goals"],
            "penalties_saved": 0,
            "penalties_missed": -2 * gameweek_data["penalties_missed"],
            "yellow_cards": -1 * gameweek_data["yellow_cards"],
            "red_cards": -3 * gameweek_data["red_cards"],
            "saves": 0,
            "bonus": gameweek_data["bonus"],
        }

    label_map = {
        "minutes": "Minutes Played",
        "goals_scored": "Goals Scored",
        "assists": "Assists",
        "clean_sheets": "Clean Sheets",
        "goals_conceded": "Goals Conceded",
        "own_goals": "Own Goals",
        "penalties_saved": "Penalties Saved",
        "penalties_missed": "Penalties Missed",
        "yellow_cards": "Yellow Cards",
        "red_cards": "Red Cards",
        "saves": "Saves",
        "bonus": "Bonus",
    }

    stats = []
    for key, points in points_map.items():
        if points != 0:
            stats.append({
                "label": label_map[key],
                "value": gameweek_data[key],
                "points": points
            })

    # Only double the total points if captain
    total_points = gameweek_data["total_points"] * 2 if is_captain else gameweek_data["total_points"]
    stats.append({
        "label": "Total Points",
        "value": "",
        "points": total_points
    })

    return jsonify({
        "fixture": fixture,
        "stats": stats
    })

@main.route("/api/fpl/captaincy/<int:team_id>", methods=["GET"])
def get_fpl_captaincy(team_id):
    try:
        # Fetch static data
        bootstrap = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
        elements = bootstrap["elements"]
        teams = {team["id"]: team for team in bootstrap["teams"]}
        events = bootstrap["events"]

        gw = request.args.get("gameweek", type=int)
        if gw:
            selected_gw = gw
        else:
            current_event = next((e for e in events if e["is_current"]), None)
            selected_gw = (current_event["id"] + 1) if current_event else 38

        picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{selected_gw}/picks/"
        picks_res = requests.get(picks_url)
        if picks_res.status_code != 200:
            current = next((e for e in events if e["is_current"]), None)
            picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{current['id']}/picks/"
            picks_res = requests.get(picks_url)
            if picks_res.status_code != 200:
                return jsonify({"error": "Team not found"}), 404
        picks_data = picks_res.json()
        user_player_ids = [pick["element"] for pick in picks_data["picks"]]
        player_map = {el["id"]: el for el in elements}
        user_players = [player_map[pid] for pid in user_player_ids if pid in player_map]

        def get_player_history(player_id):
            url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
            res = requests.get(url)
            if res.status_code == 200:
                return res.json().get("history", [])
            return []

        def get_upcoming_fixtures():
            fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
            res = requests.get(fixtures_url)
            if res.status_code == 200:
                return res.json()
            return []

        fixtures = get_upcoming_fixtures()

        def get_next_fixture(player, fixtures, selected_gw):
            team_id = player["team"]
            for fixture in fixtures:
                if fixture["event"] == selected_gw:
                    if fixture["team_h"] == team_id or fixture["team_a"] == team_id:
                        is_home = fixture["team_h"] == team_id
                        opponent_team = fixture["team_a"] if is_home else fixture["team_h"]
                        fdr = fixture["team_h_difficulty"] if is_home else fixture["team_a_difficulty"]
                        return {
                            "opponent_team": opponent_team,
                            "is_home": is_home,
                            "fdr": fdr
                        }
            return None

        captain_candidates = []
        for player in user_players:
            history = get_player_history(player["id"])
            recent_history = [gw for gw in history if selected_gw - 3 <= gw["round"] <= selected_gw]
            if not recent_history:
                continue
            avg_points = sum(gw["total_points"] for gw in recent_history) / len(recent_history)
            next_fixture = get_next_fixture(player, fixtures, selected_gw)
            if not next_fixture:
                continue
            fdr = next_fixture["fdr"]
            is_home = next_fixture["is_home"]

            position = player["element_type"]
            if position == 3:
                bias = 1.20
            elif position == 4:
                bias = 1.15
            else:
                bias = 1.0

            score = avg_points * (6 - fdr) * bias + (1 if is_home else 0)
            captain_candidates.append({
                "id": player["id"],
                "first_name": player["first_name"],
                "second_name": player["second_name"],
                "team": teams[player["team"]]["name"],
                "team_id": player["team"],
                "form": player["form"],
                "score": score,
                "avg_points": avg_points,
                "position": position,
                "next_fixture": {
                    "opponent": teams[next_fixture["opponent_team"]]["name"],
                    "is_home": is_home,
                    "fdr": fdr
                }
            })

        suggested_captains = sorted(captain_candidates, key=lambda x: x["score"], reverse=True)[:6]

        return jsonify({
            "suggested_captains": suggested_captains
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/fpl/transfers/<int:team_id>", methods=["GET"])
def get_fpl_transfers(team_id):
    try:
        bootstrap = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
        elements = bootstrap["elements"]
        teams = {team["id"]: team for team in bootstrap["teams"]}
        events = bootstrap["events"]

        gw = request.args.get("gameweek", type=int)
        if gw:
            selected_gw = gw
        else:
            current_event = next((e for e in events if e["is_current"]), None)
            selected_gw = (current_event["id"] + 1) if current_event else 38

        picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{selected_gw}/picks/"
        picks_res = requests.get(picks_url)
        if picks_res.status_code != 200:
            current = next((e for e in events if e["is_current"]), None)
            picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{current['id']}/picks/"
            picks_res = requests.get(picks_url)
            if picks_res.status_code != 200:
                return jsonify({"error": "Team not found"}), 404
        picks_data = picks_res.json()
        user_player_ids = [pick["element"] for pick in picks_data["picks"]]
        player_map = {el["id"]: el for el in elements}
        user_players = [player_map[pid] for pid in user_player_ids if pid in player_map]

        def get_player_history(player_id):
            url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
            res = requests.get(url)
            if res.status_code == 200:
                return res.json().get("history", [])
            return []

        def get_upcoming_fixtures():
            fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
            res = requests.get(fixtures_url)
            if res.status_code == 200:
                return res.json()
            return []

        fixtures = get_upcoming_fixtures()

        def get_next_fixture(player, fixtures, selected_gw):
            team_id = player["team"]
            for fixture in fixtures:
                if fixture["event"] == selected_gw:
                    if fixture["team_h"] == team_id or fixture["team_a"] == team_id:
                        is_home = fixture["team_h"] == team_id
                        opponent_team = fixture["team_a"] if is_home else fixture["team_h"]
                        fdr = fixture["team_h_difficulty"] if is_home else fixture["team_a_difficulty"]
                        return {
                            "opponent_team": opponent_team,
                            "is_home": is_home,
                            "fdr": fdr
                        }
            return None
        
        # Determine the budget using the picks endpoint for the selected gameweek
        picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{selected_gw}/picks/"
        picks_res = requests.get(picks_url)
        if picks_res.status_code == 200:
            picks_data = picks_res.json()
            budget = picks_data.get("entry_history", {}).get("bank", 0) / 10
        else:
            entry_history_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/history/"
            entry_history_res = requests.get(entry_history_url)
            if entry_history_res.status_code == 200:
                history_data = entry_history_res.json()
                finished_gws = [gw for gw in history_data["current"] if gw.get("points") is not None]
                if finished_gws:
                    latest_gw = max(finished_gws, key=lambda gw: gw["event"])
                    budget = latest_gw.get("bank", 0) / 10
                else:
                    budget = 0
            else:
                budget = 0


        # Sort user players by lowest form (worst performers)
        user_players_sorted = sorted(user_players, key=lambda x: float(x.get("form", 0)))
        transfer_out_candidates = user_players_sorted[:3]

        transfer_suggestions = []
        for out_player in transfer_out_candidates:
            out_position = out_player["element_type"]
            out_cost = out_player["now_cost"] / 10
            max_price = out_cost + budget
            # Candidates for transfer in (same position, not already in team, within budget)
            candidates = [
                p for p in elements
                if p["id"] not in user_player_ids
                and p["element_type"] == out_position
                and p["now_cost"] / 10 <= max_price
            ]
            scored_candidates = []
            for candidate in candidates:
                history = get_player_history(candidate["id"])
                recent_history = [gw for gw in history if gw["round"] < selected_gw][-3:]
                if not recent_history:
                    continue
                avg_points = sum(gw["total_points"] for gw in recent_history) / len(recent_history)
                next_fixture = get_next_fixture(candidate, fixtures, selected_gw)
                if not next_fixture:
                    continue
                fdr = next_fixture["fdr"]
                is_home = next_fixture["is_home"]
                score = avg_points * (6 - fdr) + (1 if is_home else 0)
                scored_candidates.append({
                    "id": candidate["id"],
                    "first_name": candidate["first_name"],
                    "second_name": candidate["second_name"],
                    "team": teams[candidate["team"]]["name"],
                    "team_id": candidate["team"],
                    "form": candidate["form"],
                    "now_cost": candidate["now_cost"] / 10,
                    "score": score,
                    "next_fixture": {
                        "opponent": teams[next_fixture["opponent_team"]]["name"],
                        "is_home": is_home,
                        "fdr": fdr
                    }
                })
            # Sort by score and take top 3 for this out_player
            best_in = sorted(scored_candidates, key=lambda x: x["score"], reverse=True)[:3]
            for in_player in best_in:
                transfer_suggestions.append({
                    "out": {
                        "id": out_player["id"],
                        "first_name": out_player["first_name"],
                        "second_name": out_player["second_name"],
                        "team": teams[out_player["team"]]["name"],
                        "team_id": out_player["team"],
                        "form": out_player["form"],
                        "now_cost": out_cost,
                        "next_fixture": {
                            "opponent": None,
                            "is_home": None,
                            "fdr": None
                        }
                    },
                    "in": in_player
                })

        # Sort all possible transfers by in-player score and take top 3 overall
        top_transfers = sorted(transfer_suggestions, key=lambda x: x["in"]["score"], reverse=True)[:3]

        return jsonify({
            "budget": budget,
            "top_transfers": top_transfers
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/fpl/entry-history/<int:team_id>")
def get_entry_history(team_id):
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/history/"
    res = requests.get(url)
    return jsonify(res.json()), res.status_code


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
    
# PASS

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


# XG

@main.route("/api/xG", methods=['GET'])
def get_xG():
    """Returns dataframe for xG for certain team"""
    team_name = request.args.get("team_name")
    print(team_name)
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400
    
    try:
        df = load_parquet_from_s3("footlyiq-data", "gold/xG/parquet/xG_done_filtered.parquet")
        team_id = inside_get_team_id(team_name)

        if team_id is None:
            return jsonify({"error": "Team not found"}), 404
        
        print(f"team_id: {team_id}")

        df_xG = df[df["team_id"] == team_id]
        print(df_xG.shape)

        df_limited = df_xG.head(50)
        
        return jsonify(df_limited.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@main.route("/api/xG/heatmap", methods=['GET'])
def get_xG_heatmap():
    team_name = request.args.get("team_name")
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400

    try:
        df = load_parquet_from_s3("footlyiq-data", "gold/xG/parquet/xG_done_filtered.parquet")
        team_id = inside_get_team_id(team_name)
        if team_id is None:
            return jsonify({"error": "Team not found"}), 404

        df = df[df["team_id"] == team_id]

        bins = 11  # or 17 depending on smoothness you want
        x_bins = np.linspace(0, 105, bins)
        y_bins = np.linspace(0, 68, bins)

        heatmap_data = []
        shot_grid = np.zeros((bins - 1, bins - 1))
        xg_grid = np.zeros((bins - 1, bins - 1))

        for _, shot in df.iterrows():
            x_idx = np.digitize(shot['X'], x_bins) - 1
            y_idx = np.digitize(shot['Y'], y_bins) - 1
            if 0 <= x_idx < bins - 1 and 0 <= y_idx < bins - 1:
                shot_grid[x_idx, y_idx] += 1
                xg_grid[x_idx, y_idx] += shot['xG']

        avg_xg_grid = np.divide(xg_grid, shot_grid, where=shot_grid != 0)
        avg_xg_grid = np.nan_to_num(avg_xg_grid)

        for i in range(bins - 1):
            for j in range(bins - 1):
                heatmap_data.append({
                    "x": (x_bins[i] + x_bins[i+1]) / 2,
                    "y": (y_bins[j] + y_bins[j+1]) / 2,
                    "xG": float(avg_xg_grid[i][j])
                })

        return jsonify(heatmap_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# XT

@main.route("/api/xT/moving", methods=['GET'])
def get_xT_moving():
    team_name = request.args.get("team_name")
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400
    print(team_name)

    try:
        df = load_parquet_from_s3("footlyiq-data", "gold/xT/parquet/moving_small.parquet")
        team_id = inside_get_team_id(team_name)
        if team_id is None:
            return jsonify({"error": "Team not found"}), 404
        
        print(f"team_id: {team_id}")

        df = df[df["team_id"] == team_id]

        counts, x_edges, y_edges = np.histogram2d(
            df["start_x"],
            df["start_y"],
            bins=[16,12],
            range=[[0, 105], [0, 68]]
        )

        # Convert to plain Python list for JSON
        counts_list = counts.T.tolist() # Transpose so it's rows by columns (y by x)

        return jsonify({
            "counts": counts_list,
            "x_bins": 16,
            "y_bins": 12,
            "pitch_width": 105,
            "pitch_height": 68
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@main.route("/api/xT/shots", methods=['GET'])
def get_xT_shots():
    team_name = request.args.get("team_name")
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400
    print(team_name)

    try:
        df = load_parquet_from_s3("footlyiq-data", "gold/xT/parquet/shots_small.parquet")
        team_id = inside_get_team_id(team_name)
        if team_id is None:
            return jsonify({"error": "Team not found"}), 404
        
        print(f"team_id: {team_id}")

        df = df[df["team_id"] == team_id]

        counts, x_edges, y_edges = np.histogram2d(
            df["start_x"],
            df["start_y"],
            bins=[16,12],
            range=[[0, 105], [0, 68]]
        )

        # Convert to plain Python list for JSON
        counts_list = counts.T.tolist() # Transpose so it's rows by columns (y by x)

        return jsonify({
            "counts": counts_list,
            "x_bins": 16,
            "y_bins": 12,
            "pitch_width": 105,
            "pitch_height": 68
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route("/api/xT/shot-probability", methods=['GET'])
def get_shot_probability():
    team_name = request.args.get("team_name")
    if not team_name:
        return jsonify({"error": "team_name is required"}), 400

    try:
        df_move = load_parquet_from_s3("footlyiq-data", "gold/xT/parquet/moving_small.parquet")
        df_shots = load_parquet_from_s3("footlyiq-data", "gold/xT/parquet/shots_small.parquet")
        team_id = inside_get_team_id(team_name)
        if team_id is None:
            return jsonify({"error": "Team not found"}), 404

        df_move = df_move[df_move["team_id"] == team_id]
        df_shots = df_shots[df_shots["team_id"] == team_id]

        # Define bins and range
        bins_x, bins_y = 16, 12
        range_x, range_y = [0, 105], [0, 68]

        # Binned counts for movement
        move_counts, _, _ = np.histogram2d(
            df_move["start_x"], df_move["start_y"],
            bins=[bins_x, bins_y],
            range=[range_x, range_y]
        )

        # Binned counts for shots
        shot_counts, _, _ = np.histogram2d(
            df_shots["start_x"], df_shots["start_y"],
            bins=[bins_x, bins_y],
            range=[range_x, range_y]
        )
        

        # Shot probability
        with np.errstate(divide='ignore', invalid='ignore'):
            prob = np.divide(shot_counts, move_counts + shot_counts)
            prob[np.isnan(prob)] = 0.0  # Avoid NaNs

        return jsonify({
            "probability": prob.T.tolist(),  # Transposed to match (y,x) layout
            "x_bins": bins_x,
            "y_bins": bins_y,
            "pitch_width": 105,
            "pitch_height": 68
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500