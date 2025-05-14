import requests

import requests

EXPRESS_API_URL = "http://localhost:3000/api/matches"

def get_matches_from_api():
    try:
        response = requests.get(EXPRESS_API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Napaka pri klicu mikrostoritve: {e}")
        return {"error": "Neuspešen klic mikrostoritve"}

def get_team_matches(team_id):
    try:
        url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {"error": f"API Error: {response.status_code}"}

        data = response.json()
        matches = []

        for match in data.get('matches', []):
            home_team = match.get('homeTeam', {}).get('name', 'Unknown')
            away_team = match.get('awayTeam', {}).get('name', 'Unknown')
            score = "Match not played yet"
            if match.get('score', {}).get('fullTime', {}).get('home') is not None:
                score = f"{match['score']['fullTime']['home']} - {match['score']['fullTime']['away']}"
            date = match.get('utcDate', 'Unknown')
            if date != 'Unknown':
                date = datetime.fromisoformat(date.replace('Z', '')).strftime('%d %B %Y at %H:%M')

            matches.append({
                "home_team": home_team,
                "away_team": away_team,
                "score": score,
                "date": date
            })

        return matches

    except Exception as e:
        print(f"Error: {e}")
        return {"error": "Internal Server Error"}
    
def get_team_squad(team_id):
    try:
        url = f"https://api.football-data.org/v4/teams/{team_id}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {"error": f"API Error: {response.status_code}"}

        data = response.json()
        squad = []

        # Pridobimo glavnega trenerja
        coach = data.get('coach', {})
        coach_name = coach.get('name', 'Unknown') if coach else 'No Coach'

        # Dodamo glavnega trenerja kot prvo osebo v seznam
        squad.append({
            "name": coach_name,
            "position": "Manager",
            "dateOfBirth": coach.get('dateOfBirth', 'Unknown'),
            "nationality": coach.get('nationality', 'Unknown')
            # Trenerju ne dodajamo shirtNumber
        })

        # Pridobimo igralce
        for player in data.get('squad', []):

            squad.append({
                "name": player.get('name', 'Unknown'),
                "position": player.get('position', 'Unknown'),
                "dateOfBirth": player.get('dateOfBirth', 'Unknown'),
                "nationality": player.get('nationality', 'Unknown'),
            })

        return {
            "team": data.get("name", "Unknown"),
            "squad": squad
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"error": "Internal Server Error"}



