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


def get_team_matches(team_id):
    try:
        response = requests.get(f"{EXPRESS_API_URL}/team/{team_id}/matches")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Napaka pri klicu mikrostoritve za team matches: {e}")
        return {"error": "Neuspešen klic mikrostoritve za team matches"}

def get_team_squad(team_id):
    try:
        response = requests.get(f"{EXPRESS_API_URL}/team/{team_id}/squad")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Napaka pri klicu mikrostoritve za team squad: {e}")
        return {"error": "Neuspešen klic mikrostoritve za team squad"}
    
def get_match_statistics(match_id):
    try:
        response = requests.get(f"http://localhost:3000/match/{match_id}/statistics")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Napaka pri klicu mikrostoritve za statistiko tekme: {e}")
        return {"error": "Neuspešen klic mikrostoritve za statistiko tekme"}
