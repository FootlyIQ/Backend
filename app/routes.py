from flask import Blueprint, Response
from .utils import get_matches_from_api  # Uvoz funkcije iz utils.py
import json

main = Blueprint('main', __name__)

@main.route('/matches', methods=['GET'])
def fetch_matches():
    matches = get_matches_from_api()  # Pridobivanje tekem iz API-ja iz utils.py
    if "error" in matches:  # Preverjanje, če je prišlo do napake
        return Response(
            json.dumps({'message': matches["error"]}, ensure_ascii=False, indent=4),  # Formatiran JSON
            status=500,
            mimetype='application/json'
        )
    return Response(
        json.dumps(matches, ensure_ascii=False, indent=4),  # Formatiran JSON
        status=200,
        mimetype='application/json'
    )