import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import time
import threading
from unittest.mock import patch

from app import GameState


def test_default_timeout():
    """Test that default timeout is 0.05 seconds when no env var is set"""
    with patch.dict(os.environ, {}, clear=True):
        gs = GameState()
        assert gs.think_timeout == 0.05


def test_env_var_timeout():
    """Test that timeout can be set via environment variable"""
    with patch.dict(os.environ, {'BRAIN_THINK_TIMEOUT': '0.1'}):
        gs = GameState()
        assert gs.think_timeout == 0.1


def test_env_var_invalid_timeout():
    """Test that invalid env var falls back to default"""
    with patch.dict(os.environ, {'BRAIN_THINK_TIMEOUT': 'invalid'}):
        gs = GameState()
        assert gs.think_timeout == 0.05


def test_timeout_via_api():
    """Test that timeout can be set via start-game API"""
    # Import the global game_state
    from app import app, game_state
    original_timeout = game_state.think_timeout
    
    # Simulate API call with custom timeout
    with app.test_client() as client:
        # First add some tanks
        client.post('/api/add-tank', json={'name': 'Tank1', 'color': '#ff0000'})
        client.post('/api/add-tank', json={'name': 'Tank2', 'color': '#00ff00'})
        
        # Now start game with custom timeout
        response = client.post('/api/start-game', 
                             json={'think_timeout': 0.2})
        assert response.status_code == 200
        data = response.get_json()
        assert data['think_timeout'] == 0.2
        assert game_state.think_timeout == 0.2


def test_timeout_prevents_slow_brain():
    """Test that slow brain code is actually timed out"""
    gs = GameState()
    gs.think_timeout = 0.01  # Very short timeout for testing
    
    # Create a brain that sleeps longer than the timeout
    slow_brain_code = """
import time

def think(game_state):
    time.sleep(0.1)  # Sleep for 100ms, longer than 10ms timeout
    return {'move': 'forward'}
"""
    
    # Add tank with slow brain
    gs.add_tank("SlowTank", "#ff0000", slow_brain_code)
    gs.add_tank("FastTank", "#00ff00")  # Need at least 2 tanks
    
    # Start game
    gs.start_game()
    
    # Run one update cycle
    start_time = time.time()
    gs.update()
    update_time = time.time() - start_time
    
    # The update should complete quickly despite the slow brain
    assert update_time < 0.05  # Should complete in less than 50ms
    
    # Check that timeout was logged
    timeout_logged = any("timed out" in log['message'] for log in gs.logs)
    assert timeout_logged, "Timeout should be logged when brain takes too long"


def test_fast_brain_works():
    """Test that fast brain code works normally"""
    gs = GameState()
    gs.think_timeout = 0.1  # Generous timeout
    
    # Create a brain that returns quickly
    fast_brain_code = """
def think(game_state):
    return {'move': 'forward'}
"""
    
    # Add tank with fast brain
    gs.add_tank("FastTank", "#ff0000", fast_brain_code)
    gs.add_tank("OtherTank", "#00ff00")  # Need at least 2 tanks
    
    # Start game
    gs.start_game()
    
    # Run one update cycle
    start_time = time.time()
    gs.update()
    update_time = time.time() - start_time
    
    # The update should complete quickly
    assert update_time < 0.05  # Should complete quickly
    
    # Check that no timeout was logged
    timeout_logged = any("timed out" in log['message'] for log in gs.logs)
    assert not timeout_logged, "No timeout should be logged for fast brain"


def test_timeout_with_multiple_tanks():
    """Test timeout behavior with multiple tanks having different brain speeds"""
    gs = GameState()
    gs.think_timeout = 0.02  # 20ms timeout
    
    # Add a fast tank
    fast_brain = """
def think(game_state):
    return {'move': 'forward'}
"""
    
    # Add a slow tank
    slow_brain = """
import time

def think(game_state):
    time.sleep(0.1)  # 100ms sleep
    return {'move': 'forward'}
"""
    
    # Add a medium tank
    medium_brain = """
import time

def think(game_state):
    time.sleep(0.01)  # 10ms sleep, should be fine
    return {'move': 'forward'}
"""
    
    gs.add_tank("FastTank", "#ff0000", fast_brain)
    gs.add_tank("SlowTank", "#00ff00", slow_brain)
    gs.add_tank("MediumTank", "#0000ff", medium_brain)
    
    # Start game
    gs.start_game()
    
    # Run one update cycle
    start_time = time.time()
    gs.update()
    update_time = time.time() - start_time
    
    # Should complete quickly despite one slow tank
    assert update_time < 0.05
    
    # Check that only the slow tank timed out
    timeout_logs = [log for log in gs.logs if "timed out" in log['message']]
    assert len(timeout_logs) == 1, "Only one tank should timeout"
    assert "SlowTank" in timeout_logs[0]['message'], "SlowTank should be the one timing out"


if __name__ == "__main__":
    # Run tests manually if needed
    pytest.main([__file__, "-v"]) 