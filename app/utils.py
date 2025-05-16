import requests

EXPRESS_API_URL = "http://localhost:3000/api"

def get_matches_from_api():
    try:
        response = requests.get(f"{EXPRESS_API_URL}/matches")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Napaka pri klicu mikrostoritve: {e}")
        return {"error": "Neuspešen klic mikrostoritve"}

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
