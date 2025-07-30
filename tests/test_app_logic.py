import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import math
import pytest
import time

from app import Tank, GameState, TANK_SIZE, ARENA_WIDTH, ARENA_HEIGHT, BULLET_SPEED


def test_tank_move_within_bounds():
    tank = Tank(400, 300, "#ff0000", "Alpha")
    tank.move(100, 0)
    assert tank.x == 500
    assert tank.y == 300


def test_tank_move_out_of_bounds():
    tank = Tank(TANK_SIZE / 2, TANK_SIZE / 2, "#00ff00", "Beta")
    # Attempt to move tank beyond the left/top boundaries – it should be clamped
    tank.move(-100, -100)
    assert tank.x == pytest.approx(TANK_SIZE / 2)
    assert tank.y == pytest.approx(TANK_SIZE / 2)


def test_tank_rotation():
    tank = Tank(0, 0, "#0000ff", "Gamma")
    original_angle = tank.angle
    tank.rotate(90)
    expected = (original_angle + 90) % 360
    assert tank.angle == pytest.approx(expected)


def test_tank_shoot():
    tank = Tank(100, 100, "#abcdef", "Shooter")
    tank.last_shot_time = 0  # force cooldown to allow shooting
    tank.angle = 0  # facing right
    tank.shoot()
    assert len(tank.bullets) == 1
    bullet = tank.bullets[0]
    # Bullet should start to the right of the tank and travel horizontally
    assert bullet["dx"] > 0
    assert bullet["dy"] == pytest.approx(0)


def test_tank_take_damage_and_death():
    tank = Tank(100, 100, "#123456", "Target")
    tank.take_damage(150)  # more than MAX_HEALTH
    assert tank.health == 0
    assert tank.alive is False


def test_tank_shoot_cooldown():
    tank = Tank(100, 100, "#abcdef", "Shooter")
    tank.angle = 0
    
    # First shot should work
    tank.shoot()
    assert len(tank.bullets) == 1
    
    # Second shot immediately should not work due to cooldown
    tank.shoot()
    assert len(tank.bullets) == 1  # Still only one bullet


def test_tank_get_state():
    tank = Tank(100, 100, "#ff0000", "TestTank")
    state = tank.get_state()
    assert state['x'] == 100
    assert state['y'] == 100
    assert state['alive'] is True
    assert 'bullets' in state


def test_tank_to_dict():
    tank = Tank(100, 100, "#ff0000", "TestTank")
    tank.score = 50
    tank.kills = 3
    tank_dict = tank.to_dict()
    assert tank_dict['x'] == 100
    assert tank_dict['y'] == 100
    assert tank_dict['score'] == 50
    assert tank_dict['kills'] == 3


# ---------------- GameState ----------------

def test_game_state_add_tank():
    gs = GameState()
    gs.add_tank("Alpha", "#ff0000")
    assert "Alpha" in gs.tanks
    assert len(gs.tanks) == 1
    tank = gs.tanks["Alpha"]
    assert tank.color == "#ff0000"


def test_game_state_compile_brain():
    gs = GameState()
    brain_code = """
def think(game_state):
    return {'move': 'forward'}
"""
    gs.add_tank("SmartTank", "#00ff00", brain_code)
    tank = gs.tanks["SmartTank"]
    assert tank.brain_module is not None
    assert hasattr(tank.brain_module, 'think')


def test_game_state_compile_invalid_brain():
    gs = GameState()
    invalid_brain_code = "this is not valid python code"
    gs.add_tank("BrokenTank", "#ff0000", invalid_brain_code)
    tank = gs.tanks["BrokenTank"]
    assert tank.brain_module is None  # Should handle compilation errors gracefully


def test_game_state_start_game():
    gs = GameState()
    gs.add_tank("Alpha", "#ff0000")
    gs.add_tank("Beta", "#00ff00")
    
    gs.start_game()
    assert gs.game_running is True
    assert gs.round_number == 1
    assert gs.round_start_time > 0
    
    # All tanks should be reset to full health
    for tank in gs.tanks.values():
        assert tank.health == 100
        assert tank.alive is True
        assert tank.score == 0
        assert tank.kills == 0


def test_game_state_get_game_state():
    gs = GameState()
    gs.add_tank("Alpha", "#ff0000")
    gs.add_tank("Beta", "#00ff00")
    gs.start_game()
    
    state = gs.get_game_state()
    assert 'tanks' in state
    assert 'bullets' in state
    assert 'game_running' in state
    assert 'round_number' in state
    assert 'time_remaining' in state
    assert len(state['tanks']) == 2


def test_bullet_physics():
    gs = GameState()
    gs.add_tank("Shooter", "#ff0000")
    tank = gs.tanks["Shooter"]
    
    # Position tank and shoot
    tank.x, tank.y = 100, 100
    tank.angle = 0  # facing right
    tank.last_shot_time = 0
    tank.shoot()
    
    # Add bullet to game state
    gs.bullets = tank.bullets.copy()
    
    # Update bullets
    gs._update_bullets()
    
    # Bullet should have moved
    assert len(gs.bullets) == 1
    bullet = gs.bullets[0]
    assert bullet['x'] > 100  # Should have moved right
    assert bullet['y'] == pytest.approx(100)  # Should stay at same y


def test_bullet_lifetime():
    gs = GameState()
    gs.add_tank("Shooter", "#ff0000")
    tank = gs.tanks["Shooter"]
    
    # Create a bullet with high lifetime
    bullet = {
        'x': 100, 'y': 100, 'dx': 0, 'dy': 0,
        'owner': 'Shooter', 'lifetime': 150  # Over the 120 limit
    }
    gs.bullets = [bullet]
    
    # Update should remove the old bullet
    gs._update_bullets()
    assert len(gs.bullets) == 0


def test_bullet_out_of_bounds():
    gs = GameState()
    gs.add_tank("Shooter", "#ff0000")
    tank = gs.tanks["Shooter"]
    
    # Create a bullet outside the arena
    bullet = {
        'x': -10, 'y': 100, 'dx': 0, 'dy': 0,
        'owner': 'Shooter', 'lifetime': 0
    }
    gs.bullets = [bullet]
    
    # Update should remove the out-of-bounds bullet
    gs._update_bullets()
    assert len(gs.bullets) == 0