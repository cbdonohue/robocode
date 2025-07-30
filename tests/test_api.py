import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Ensure a fresh game state before each test
        client.post("/api/reset-game")
        yield client
        # Clean up afterwards
        client.post("/api/reset-game")


def test_get_game_state(client):
    res = client.get("/api/game-state")
    assert res.status_code == 200
    data = res.get_json()
    assert "tanks" in data
    assert "bullets" in data


def test_add_tank_endpoint(client):
    res = client.post("/api/add-tank", json={"name": "Alpha", "color": "#f00"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["tank_name"] == "Alpha"

    # Tank should now show up in game state
    state = client.get("/api/game-state").get_json()
    assert any(t["name"] == "Alpha" for t in state["tanks"])


def test_start_game_requires_two_tanks(client):
    # Only one tank present
    client.post("/api/add-tank", json={"name": "Alpha", "color": "#f00"})
    res = client.post("/api/start-game")
    assert res.status_code == 200
    assert "error" in res.get_json()

    # Add a second tank and try again
    client.post("/api/add-tank", json={"name": "Beta", "color": "#0f0"})
    res = client.post("/api/start-game")
    assert res.status_code == 200
    assert res.get_json().get("success") is True


def test_add_tank_with_brain_code(client):
    brain_code = """
def think(game_state):
    return {'move': 'forward'}
"""
    res = client.post("/api/add-tank", json={
        "name": "SmartTank", 
        "color": "#00f", 
        "brain_code": brain_code
    })
    assert res.status_code == 200
    assert res.get_json()["success"] is True


def test_add_tank_without_name(client):
    res = client.post("/api/add-tank", json={"color": "#f00"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    # Should use phonetic name instead of Tank_ prefix
    assert data["tank_name"] in ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel",
                                "India", "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa",
                                "Quebec", "Romeo", "Sierra", "Tango", "Uniform", "Victor", "Whiskey",
                                "Xray", "Yankee", "Zulu"]


def test_add_tank_without_color(client):
    res = client.post("/api/add-tank", json={"name": "TestTank"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    
    # Should have generated a random color
    state = client.get("/api/game-state").get_json()
    tank = next(t for t in state["tanks"] if t["name"] == "TestTank")
    assert tank["color"].startswith("#")


def test_phonetic_naming_sequence(client):
    """Test that multiple tanks without names get sequential phonetic names"""
    # Add first tank without name
    res1 = client.post("/api/add-tank", json={"color": "#f00"})
    assert res1.status_code == 200
    data1 = res1.get_json()
    assert data1["success"] is True
    assert data1["tank_name"] == "Alpha"
    
    # Add second tank without name
    res2 = client.post("/api/add-tank", json={"color": "#0f0"})
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["success"] is True
    assert data2["tank_name"] == "Bravo"
    
    # Add third tank without name
    res3 = client.post("/api/add-tank", json={"color": "#00f"})
    assert res3.status_code == 200
    data3 = res3.get_json()
    assert data3["success"] is True
    assert data3["tank_name"] == "Charlie"


def test_reset_game_endpoint(client):
    # Add some tanks first
    client.post("/api/add-tank", json={"name": "Alpha", "color": "#f00"})
    client.post("/api/add-tank", json={"name": "Beta", "color": "#0f0"})
    
    # Start the game
    client.post("/api/start-game")
    
    # Check that game is running
    state = client.get("/api/game-state").get_json()
    assert state["game_running"] is True
    
    # Reset the game
    res = client.post("/api/reset-game")
    assert res.status_code == 200
    assert res.get_json()["success"] is True
    
    # Check that game is no longer running
    state = client.get("/api/game-state").get_json()
    assert state["game_running"] is False
    assert len(state["tanks"]) == 0


def test_sample_brains_endpoint(client):
    res = client.get("/api/sample-brains")
    assert res.status_code == 200
    data = res.get_json()
    assert "simple_chaser" in data
    assert "coward" in data


def test_add_tank_invalid_json(client):
    res = client.post("/api/add-tank", data="invalid json", content_type="application/json")
    assert res.status_code == 400


def test_start_game_no_tanks(client):
    res = client.post("/api/start-game")
    assert res.status_code == 200
    data = res.get_json()
    assert "error" in data
    assert "Need at least 2 tanks" in data["error"]


def test_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    # Should return the HTML template
    assert b"<!DOCTYPE html>" in res.data or b"<html" in res.data