from flask import Blueprint, Response
from .utils import get_team_matches
import json
import requests

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
