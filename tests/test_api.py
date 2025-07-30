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