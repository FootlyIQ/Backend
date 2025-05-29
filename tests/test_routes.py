import json
import pytest
from unittest.mock import Mock

def test_fetch_matches(client, mock_requests):
    # Mock the response from the microservice
    mock_response = Mock()
    mock_response.text = json.dumps([{"id": 1, "home_team": "Team A", "away_team": "Team B"}])
    mock_response.status_code = 200
    mock_requests.return_value = mock_response

    response = client.get('/matches')
    assert response.status_code == 200
    assert json.loads(response.data) == [{"id": 1, "home_team": "Team A", "away_team": "Team B"}]

def test_fetch_matches_error(client, mock_requests):
    # Mock an error response
    mock_requests.side_effect = Exception("Connection error")
    
    response = client.get('/matches')
    assert response.status_code == 500
    assert "Connection error" in response.data.decode()

def test_fetch_team_matches(client, mock_requests):
    # Mock the response for team matches
    mock_response = Mock()
    mock_response.json.return_value = [{"match_id": 1, "home_team": "Team A", "away_team": "Team B"}]
    mock_response.status_code = 200
    mock_requests.return_value = mock_response

    response = client.get('/team-matches/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "match_id" in data[0]

def test_fetch_team_squad(client, mock_requests):
    # Mock the response for team squad
    mock_response = Mock()
    mock_response.json.return_value = [{"player_id": 1, "name": "Player A", "position": "Forward"}]
    mock_response.status_code = 200
    mock_requests.return_value = mock_response

    response = client.get('/team-squad/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "player_id" in data[0]

def test_fetch_match_statistics(client, mock_requests):
    # Mock the response for match statistics
    mock_response = Mock()
    mock_response.json.return_value = {"possession": {"home": 60, "away": 40}}
    mock_response.status_code = 200
    mock_requests.return_value = mock_response

    response = client.get('/match-statistics/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert "possession" in data

def test_test_firestore(client, mock_db):
    # Mock Firestore users collection
    mock_docs = [
        Mock(to_dict=lambda: {"id": 1, "name": "User A"}),
        Mock(to_dict=lambda: {"id": 2, "name": "User B"})
    ]
    mock_collection = Mock()
    mock_collection.stream.return_value = mock_docs
    mock_db.collection.return_value = mock_collection

    response = client.get('/test-firestore')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "User A"

def test_get_fpl_team(client, mock_requests):
    # Mock responses for all required API calls
    def mock_responses(url):
        if "picks" in url:
            return Mock(
                status_code=200,
                json=lambda: {"picks": [
                    {"element": 1, "position": 1, "multiplier": 1, "is_captain": False, "is_vice_captain": False}
                ]}
            )
        elif "bootstrap-static" in url:
            return Mock(
                status_code=200,
                json=lambda: {"elements": [{
                    "id": 1,
                    "first_name": "John",
                    "second_name": "Doe",
                    "element_type": 1,
                    "team": 1
                }]}
            )
        else:  # live url
            return Mock(
                status_code=200,
                json=lambda: {"elements": [{"id": 1, "stats": {"total_points": 10}}]}
            )

    mock_requests.side_effect = mock_responses

    response = client.get('/api/fpl/team/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "starting_players" in data
    assert "bench_players" in data
    assert "total_points" in data 