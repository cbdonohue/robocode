import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import GameState


def test_taunt_action_logs_message():
    gs = GameState()
    gs.add_tank("Alpha", "#ff0000")
    tank = gs.tanks["Alpha"]

    # Execute taunt action directly
    gs._execute_tank_action(tank, {"taunt": "Charge!"})

    # The latest log message should contain the taunt
    assert gs.logs[-1]["message"] == "Alpha shouts: Charge!"


def test_taunt_via_brain_module():
    gs = GameState()

    brain_code = """

def think(game_state):
    # Always taunt
    return {'taunt': 'For glory!'}
"""
    gs.add_tank("Taunter", "#00ff00", brain_code)

    # Need at least one more tank to start game/update without ending immediately
    gs.add_tank("Opponent", "#0000ff")

    # Start the game and run one update frame
    gs.start_game()
    gs.update()

    # Verify the taunt was logged
    assert any("Taunter shouts: For glory!" == entry["message"] for entry in gs.logs), "Taunt message not found in logs"