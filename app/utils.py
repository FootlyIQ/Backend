import requests
from flask import jsonify
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")

# Preveri, če sta ključ in URL dejansko bila naložena
if not API_KEY or not API_URL:
    raise EnvironmentError("API_KEY ali API_URL nista definirana v .env datoteki.")

headers = {
    'X-Auth-Token': API_KEY  # Glava, ki vsebuje tvoj API ključ
}

def get_matches_from_api():
    try:
        response = requests.get(API_URL, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code} - {response.text}")
            return {"error": "Failed to fetch data"}
        
        print("API Response:", response.json())
        data = response.json()
        
        leagues = {}
        for match in data.get('matches', []):
            league_name = match.get('competition', {}).get('name', 'Unknown league')
            home_team = match.get('homeTeam', {}).get('name', 'Unknown team')
            away_team = match.get('awayTeam', {}).get('name', 'Unknown team')
            home_crest = match.get('homeTeam', {}).get('crest', '')  # URL of home team crest
            away_crest = match.get('awayTeam', {}).get('crest', '')  # URL of away team crest
            score = "Match not played yet"
            if match.get('score', {}).get('fullTime', {}).get('home') is not None:
                score = f"{match['score']['fullTime']['home']} - {match['score']['fullTime']['away']}"
            date = match.get('utcDate', 'Unknown date')
            if date != 'Unknown date':
                date = datetime.fromisoformat(date.replace('Z', '')).strftime('%d %B %Y at %H:%M')
            
            match_data = {
                "home_team": home_team,
                "away_team": away_team,
                "home_crest": home_crest,
                "away_crest": away_crest,
                "score": score,
                "date": date
            }
            
            if league_name not in leagues:
                leagues[league_name] = []
            leagues[league_name].append(match_data)
        
        result = [{"league": league, "matches": matches} for league, matches in leagues.items()]
        return result
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"error": "An error occurred"}

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



