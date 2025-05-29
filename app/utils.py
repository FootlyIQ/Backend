import requests

EXPRESS_API_URL = "http://localhost:3000/api"

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