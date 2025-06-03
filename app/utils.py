import requests
import time
from .config import RESULTS_URL

player_history_cache = {}
CACHE_TTL = 60 * 180  # 3 hours

EXPRESS_API_URL = "http://localhost:3000/api"   #RESULTS_URL to bi naj blo tu

def get_matches_from_api(date=None):
    try:
        url = f"{EXPRESS_API_URL}/matches"
        # If no date is provided, don't add the query parameter
        # The microservice will use current date by default
        if date:
            url += f"?date={date}"
        
        print(f"Sending request to URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        print(f"Successfully fetched {sum(len(league['matches']) for country in data for league in country['leagues'])} matches")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error calling microservice: {str(e)}")
        return {"error": "Failed to fetch matches from microservice"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": "An unexpected error occurred"} 


def get_team_matches(team_id, season=None, competition=None):
    try:
        url = f"{EXPRESS_API_URL}/team/{team_id}/matches"
        params = {}
        if season:
            params['season'] = season
        if competition:
            params['competition'] = competition
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling microservice for team matches: {e}")
        return {"error": "Failed to call microservice for team matches"}

def get_team_squad(team_id):
    try:
        response = requests.get(f"{EXPRESS_API_URL}/team/{team_id}/squad")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling microservice for team squad: {e}")
        return {"error": "Failed to call microservice for team squad"}

def get_match_statistics(match_id):
    try:
        response = requests.get(f"http://localhost:3000/match/{match_id}/statistics")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling microservice for match statistics: {e}")
        return {"error": "Failed to call microservice for match statistics"}

def get_player_details(player_id):
    try:
        response = requests.get(f"{EXPRESS_API_URL}/player/{player_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling microservice for player details: {e}")
        return {"error": "Failed to call microservice for player details"}

def get_player_matches(player_id, limit=50, season=None, competition=None):
    try:
        url = f"{EXPRESS_API_URL}/player/{player_id}/matches"
        params = {'limit': limit}
        if season:
            params['season'] = season
        if competition:
            params['competition'] = competition
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling microservice for player matches: {e}")
        return {"error": "Failed to call microservice for player matches"}

def get_team_filters(team_id):
    try:
        response = requests.get(f"{EXPRESS_API_URL}/team/{team_id}/filters")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching team filters from microservice: {e}")
        return {"error": "Failed to fetch team filters"}

def get_competition_details(competition_code, season=None):
    try:
        url = f"{EXPRESS_API_URL}/competition/{competition_code}"
        params = {}
        if season:
            params['season'] = season
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check if the response contains an error
        if "error" in data:
            print(f"Error from microservice: {data['error']}")
            return data
            
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error calling microservice for competition details: {e}")
        return {"error": f"Failed to fetch competition details: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error in get_competition_details: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
#FANTASY DEL OLIVER
def get_player_history(player_id):
    now = time.time()
    if player_id in player_history_cache:
        ts, history = player_history_cache[player_id]
        if now - ts < CACHE_TTL:
            return history
    url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
    res = requests.get(url)
    if res.status_code == 200:
        history = res.json().get("history", [])
        player_history_cache[player_id] = (now, history)
        return history
    return []

def get_upcoming_fixtures():
    fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
    res = requests.get(fixtures_url)
    if res.status_code == 200:
        return res.json()
    return []

def get_next_fixture(player, fixtures, selected_gw):
    team_id = player["team"]
    # Find the first fixture after the selected_gw where the team plays and the fixture is not finished
    future_fixtures = sorted(
        [f for f in fixtures if f["event"] and f["event"] > selected_gw and (f["team_h"] == team_id or f["team_a"] == team_id)],
        key=lambda x: x["event"]
    )
    for fixture in future_fixtures:
        is_home = fixture["team_h"] == team_id
        opponent_team = fixture["team_a"] if is_home else fixture["team_h"]
        fdr = fixture["team_h_difficulty"] if is_home else fixture["team_a_difficulty"]
        return {
            "opponent_team": opponent_team,
            "is_home": is_home,
            "fdr": fdr,
            "event": fixture["event"]
        }
    return None

def predict_points(player, recent_history, next_fixture):
    avg_recent = sum(gw["total_points"] for gw in recent_history) / len(recent_history) if recent_history else 0
    form = float(player.get("form", 0))
    fdr = next_fixture.get("fdr", 3) if next_fixture else 3
    fixture_factor = max(0.5, 6 - fdr) / 5
    predicted = 0.5 * avg_recent + 0.3 * form + 0.2 * fixture_factor * avg_recent
    return round(predicted, 2)