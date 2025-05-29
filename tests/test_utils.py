import pytest
from unittest.mock import Mock, patch
from app.utils import (
    get_matches_from_api,
    get_team_matches,
    get_team_squad,
    get_match_statistics
)

def test_get_matches_from_api_success():
    mock_response = Mock()
    mock_response.json.return_value = [{"id": 1, "home_team": "Team A", "away_team": "Team B"}]
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):
        result = get_matches_from_api()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["home_team"] == "Team A"

def test_get_matches_from_api_error():
    with patch('requests.get', side_effect=Exception("API Error")):
        result = get_matches_from_api()
        assert isinstance(result, dict)
        assert "error" in result
        assert "Neuspešen klic mikrostoritve" in result["error"]

def test_get_team_matches_success():
    mock_response = Mock()
    mock_response.json.return_value = [
        {"match_id": 1, "home_team": "Team A", "away_team": "Team B"}
    ]
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):
        result = get_team_matches(1)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["match_id"] == 1

def test_get_team_matches_error():
    with patch('requests.get', side_effect=Exception("API Error")):
        result = get_team_matches(1)
        assert isinstance(result, dict)
        assert "error" in result
        assert "Neuspešen klic mikrostoritve za team matches" in result["error"]

def test_get_team_squad_success():
    mock_response = Mock()
    mock_response.json.return_value = [
        {"player_id": 1, "name": "Player A", "position": "Forward"}
    ]
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):
        result = get_team_squad(1)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["player_id"] == 1

def test_get_team_squad_error():
    with patch('requests.get', side_effect=Exception("API Error")):
        result = get_team_squad(1)
        assert isinstance(result, dict)
        assert "error" in result
        assert "Neuspešen klic mikrostoritve za team squad" in result["error"]

def test_get_match_statistics_success():
    mock_response = Mock()
    mock_response.json.return_value = {"possession": {"home": 60, "away": 40}}
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):
        result = get_match_statistics(1)
        assert isinstance(result, dict)
        assert "possession" in result
        assert result["possession"]["home"] == 60

def test_get_match_statistics_error():
    with patch('requests.get', side_effect=Exception("API Error")):
        result = get_match_statistics(1)
        assert isinstance(result, dict)
        assert "error" in result
        assert "Neuspešen klic mikrostoritve za statistiko tekme" in result["error"] 