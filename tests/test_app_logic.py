import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import math
import pytest

from app import Tank, GameState, TANK_SIZE


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


# ---------------- GameState ----------------

def test_game_state_add_tank():
    gs = GameState()
    gs.add_tank("Alpha", "#ff0000")
    assert "Alpha" in gs.tanks
    assert len(gs.tanks) == 1
    tank = gs.tanks["Alpha"]
    assert tank.color == "#ff0000"