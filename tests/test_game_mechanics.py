import os
import sys
import math
import time

import pytest

# Ensure the application root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import GameState, Tank, TANK_SIZE, TANK_SPEED, ROTATION_SPEED


@pytest.fixture()

def fresh_gamestate():
    """Return a fresh GameState instance for each test."""
    return GameState()


def test_execute_tank_action_move_forward(fresh_gamestate):
    gs = fresh_gamestate
    tank = Tank(100, 100, "#ffffff", "Mover")
    # Facing right (0°) so forward should increase x
    tank.angle = 0

    gs._execute_tank_action(tank, {"move": "forward"})

    assert tank.x == pytest.approx(100 + TANK_SPEED)
    assert tank.y == pytest.approx(100)


def test_execute_tank_action_rotate(fresh_gamestate):
    gs = fresh_gamestate
    tank = Tank(0, 0, "#ffffff", "Spinner")

    original_angle = tank.angle
    gs._execute_tank_action(tank, {"rotate": 1})  # Positive rotate should add ROTATION_SPEED
    expected = (original_angle + ROTATION_SPEED) % 360

    assert tank.angle == pytest.approx(expected)


def test_execute_tank_action_shoot(fresh_gamestate):
    gs = fresh_gamestate
    tank = Tank(200, 200, "#ffffff", "Shooter")
    tank.last_shot_time = 0  # Ensure cooldown has passed
    tank.angle = 0  # Facing right

    gs._execute_tank_action(tank, {"shoot": True})

    # Bullet should be transferred to GameState and cleared from tank
    assert len(gs.bullets) == 1
    assert len(tank.bullets) == 0

    bullet = gs.bullets[0]
    # Basic sanity checks on bullet direction
    assert bullet["dx"] > 0  # Moving right
    assert bullet["dy"] == pytest.approx(0)
    assert bullet["owner"] == "Shooter"


def test_resolve_tank_collisions(fresh_gamestate):
    """Tanks starting too close should be separated so they no longer overlap."""
    gs = fresh_gamestate

    # Position two tanks partially overlapping (distance < TANK_SIZE)
    tank1 = Tank(100, 100, "#ff0000", "Alpha")
    tank2 = Tank(100 + TANK_SIZE / 4, 100, "#00ff00", "Beta")

    gs.tanks = {"Alpha": tank1, "Beta": tank2}

    # Initial distance is intentionally < TANK_SIZE
    initial_distance = math.hypot(tank2.x - tank1.x, tank2.y - tank1.y)
    assert initial_distance < TANK_SIZE

    gs._resolve_tank_collisions()

    # After resolution, tanks should be at least TANK_SIZE apart
    resolved_distance = math.hypot(tank2.x - tank1.x, tank2.y - tank1.y)
    assert resolved_distance >= pytest.approx(TANK_SIZE, rel=0.05)


def test_log_keeps_max_entries(fresh_gamestate):
    gs = fresh_gamestate

    # Add more than 200 log entries
    for i in range(250):
        gs._log(f"Event {i}")

    assert len(gs.logs) == 200
    # The earliest retained log should be Event 50 (0-indexed)
    assert gs.logs[0]["message"] == "Event 50"