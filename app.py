from flask import Flask, render_template, jsonify, request
import random
import math
import time
import threading
import importlib.util
import os
import sys
from typing import Dict, List, Tuple, Optional
import json

app = Flask(__name__)

# Game configuration
ARENA_WIDTH = 800
ARENA_HEIGHT = 600
TANK_SIZE = 20
BULLET_SIZE = 4
BULLET_SPEED = 5
TANK_SPEED = 2
ROTATION_SPEED = 3
MAX_HEALTH = 100
DAMAGE_PER_HIT = 25
DEBUG_LOG_LIMIT = 200  # Max debug events to keep per tank

# List of safe phonetic names for default tank names
PHONETIC_NAMES = [
    'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf', 'Hotel',
    'India', 'Juliet', 'Kilo', 'Lima', 'Mike', 'November', 'Oscar', 'Papa',
    'Quebec', 'Romeo', 'Sierra', 'Tango', 'Uniform', 'Victor', 'Whiskey',
    'Xray', 'Yankee', 'Zulu'
]


def _next_phonetic_name(existing_names):
    """Return the first unused phonetic name. If all are taken, append a counter."""
    # First attempt exact phonetic names
    for n in PHONETIC_NAMES:
        if n not in existing_names:
            return n
    # If we've run out, append a numeric suffix to ensure uniqueness
    counter = 1
    while True:
        for base in PHONETIC_NAMES:
            candidate = f"{base}_{counter}"
            if candidate not in existing_names:
                return candidate
        counter += 1


class Tank:
    def __init__(self, x: float, y: float, color: str, name: str, brain_module=None):
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 360)  # Random starting direction
        self.color = color
        self.name = name
        self.health = MAX_HEALTH
        self.brain_module = brain_module
        self.bullets = []
        self.last_shot_time = 0
        self.shot_cooldown = 0.5  # Seconds between shots
        self.alive = True
        self.score = 0
        self.kills = 0
        self.debug_log = []  # Store recent debug events for this tank
        
    def _add_debug_event(self, event_type: str, **data):
        """Internal: append a debug event keeping list capped"""
        event = {'ts': time.time(), 'event': event_type}
        if data:
            event.update(data)
        self.debug_log.append(event)
        # Cap the log size
        if len(self.debug_log) > DEBUG_LOG_LIMIT:
            self.debug_log.pop(0)
    
    def move(self, dx: float, dy: float):
        """Move tank by given delta"""
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Keep tank within arena bounds
        if TANK_SIZE/2 <= new_x <= ARENA_WIDTH - TANK_SIZE/2:
            self.x = new_x
        if TANK_SIZE/2 <= new_y <= ARENA_HEIGHT - TANK_SIZE/2:
            self.y = new_y
        self._add_debug_event('move', new_x=self.x, new_y=self.y)
    
    def rotate(self, angle_delta: float):
        """Rotate tank by given angle"""
        self.angle += angle_delta
        self.angle %= 360
        self._add_debug_event('rotate', angle=self.angle)
    
    def shoot(self):
        """Fire a bullet if cooldown allows"""
        current_time = time.time()
        if current_time - self.last_shot_time >= self.shot_cooldown:
            # Calculate bullet starting position (front of tank)
            angle_rad = math.radians(self.angle)
            bullet_x = self.x + math.cos(angle_rad) * (TANK_SIZE/2 + 5)
            bullet_y = self.y + math.sin(angle_rad) * (TANK_SIZE/2 + 5)
            
            # Calculate bullet velocity
            bullet_dx = math.cos(angle_rad) * BULLET_SPEED
            bullet_dy = math.sin(angle_rad) * BULLET_SPEED
            
            bullet = {
                'x': bullet_x,
                'y': bullet_y,
                'dx': bullet_dx,
                'dy': bullet_dy,
                'owner': self.name,
                'lifetime': 0
            }
            
            self.bullets.append(bullet)
            self.last_shot_time = current_time
            self._add_debug_event('shoot', bullet=bullet)
    
    def take_damage(self, damage: int):
        """Take damage and check if tank is destroyed"""
        self.health -= damage
        self._add_debug_event('damage', new_health=self.health, damage=damage)
        if self.health <= 0:
            self.alive = False
            self.health = 0
            self._add_debug_event('destroyed')
    
    def get_state(self) -> dict:
        """Get tank state for brain AI"""
        return {
            'x': self.x,
            'y': self.y,
            'angle': self.angle,
            'health': self.health,
            'alive': self.alive,
            'bullets': self.bullets.copy()
        }
    
    def to_dict(self) -> dict:
        """Convert tank to dictionary for JSON serialization"""
        return {
            'x': self.x,
            'y': self.y,
            'angle': self.angle,
            'color': self.color,
            'name': self.name,
            'health': self.health,
            'alive': self.alive,
            'score': self.score,
            'kills': self.kills,
            'debug': self.debug_log[-100:]
        }

class GameState:
    def __init__(self):
        self.tanks = {}
        self.bullets = []
        self.obstacles = []
        self.game_running = False
        self.round_number = 0
        self.max_rounds = 10
        self.round_time = 60  # seconds
        self.round_start_time = 0
        # Battle log entries (list of dicts with 'time' and 'message')
        self.logs = []

    def _log(self, message: str):
        """Append an entry to the battle log with a timestamp (keeps last 200)."""
        timestamp = time.time()
        self.logs.append({'time': timestamp, 'message': message})
        if len(self.logs) > 200:
            self.logs.pop(0)
    
    def add_tank(self, name: str, color: str, brain_code: str = None):
        """Add a tank to the game"""
        # Generate random starting position
        x = random.uniform(TANK_SIZE, ARENA_WIDTH - TANK_SIZE)
        y = random.uniform(TANK_SIZE, ARENA_HEIGHT - TANK_SIZE)
        
        brain_module = None
        if brain_code:
            brain_module = self._compile_brain(name, brain_code)
        
        tank = Tank(x, y, color, name, brain_module)
        self.tanks[name] = tank
        self._log(f"Tank {name} deployed.")
    
    def _compile_brain(self, tank_name: str, brain_code: str):
        """Compile tank brain code into a module"""
        try:
            # Create a unique module name
            module_name = f"brain_{tank_name}_{int(time.time())}"
            
            # Compile the code
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            module = importlib.util.module_from_spec(spec)
            
            # Add necessary imports to the module namespace
            module.__dict__.update({
                'math': math,
                'random': random,
                'time': time
            })
            
            # Execute the code in the module namespace
            exec(brain_code, module.__dict__)
            
            return module
        except Exception as e:
            print(f"Error compiling brain for {tank_name}: {e}")
            return None
    
    def update(self):
        """Update game state for one frame"""
        if not self.game_running:
            return
        
        # Update bullets
        self._update_bullets()
        
        # Update tanks (AI decisions)
        self._update_tanks()
        
        # Check for tank-tank overlap and separate overlapping tanks
        self._resolve_tank_collisions()
        
        # Check collisions
        self._check_collisions()
        
        # NEW: End round early if only one (or zero) tanks remain alive
        alive_tanks_count = sum(1 for t in self.tanks.values() if t.alive)
        if alive_tanks_count <= 1:
            self._log("Only one tank remaining. Ending round early.")
            self._end_round()
            return
        
        # Check if round should end due to time limit
        if time.time() - self.round_start_time > self.round_time:
            self._end_round()
    
    def _update_bullets(self):
        """Update bullet positions and lifetimes"""
        new_bullets = []
        
        for bullet in self.bullets:
            # Update position
            bullet['x'] += bullet['dx']
            bullet['y'] += bullet['dy']
            bullet['lifetime'] += 1
            
            # Remove bullets that are out of bounds or too old
            if (0 <= bullet['x'] <= ARENA_WIDTH and 
                0 <= bullet['y'] <= ARENA_HEIGHT and 
                bullet['lifetime'] < 120):  # 2 seconds at 60fps
                new_bullets.append(bullet)
        
        self.bullets = new_bullets
    
    def _update_tanks(self):
        """Update tank AI and actions"""
        for tank_name, tank in self.tanks.items():
            if not tank.alive:
                continue
            
            # Get game state for AI
            game_state = self._get_game_state_for_ai(tank_name)
            
            # Call tank brain if available
            if tank.brain_module and hasattr(tank.brain_module, 'think'):
                try:
                    action = tank.brain_module.think(game_state)
                    self._execute_tank_action(tank, action)
                except Exception as e:
                    print(f"Error in tank {tank_name} brain: {e}")
    
    def _get_game_state_for_ai(self, tank_name: str) -> dict:
        """Get game state from perspective of specific tank"""
        tank = self.tanks[tank_name]
        
        # Get other tanks
        other_tanks = []
        for name, other_tank in self.tanks.items():
            if name != tank_name and other_tank.alive:
                other_tanks.append({
                    'x': other_tank.x,
                    'y': other_tank.y,
                    'angle': other_tank.angle,
                    'name': other_tank.name
                })
        
        return {
            'my_tank': tank.get_state(),
            'other_tanks': other_tanks,
            'bullets': self.bullets.copy(),
            'obstacles': self.obstacles.copy(),
            'arena_width': ARENA_WIDTH,
            'arena_height': ARENA_HEIGHT
        }
    
    def _execute_tank_action(self, tank: Tank, action: dict):
        """Execute action from tank brain"""
        if not action:
            return
        
        # Movement
        if 'move' in action:
            move = action['move']
            if move == 'forward':
                angle_rad = math.radians(tank.angle)
                dx = math.cos(angle_rad) * TANK_SPEED
                dy = math.sin(angle_rad) * TANK_SPEED
                tank.move(dx, dy)
            elif move == 'backward':
                angle_rad = math.radians(tank.angle)
                dx = -math.cos(angle_rad) * TANK_SPEED
                dy = -math.sin(angle_rad) * TANK_SPEED
                tank.move(dx, dy)
        
        # Rotation
        if 'rotate' in action:
            tank.rotate(action['rotate'] * ROTATION_SPEED)
        
        # Shooting
        if action.get('shoot', False):
            tank.shoot()
            # Add bullets to global bullet list
            self.bullets.extend(tank.bullets)
            tank.bullets = []
    
    def _check_collisions(self):
        """Check for bullet-tank collisions"""
        for bullet in self.bullets:
            for tank_name, tank in self.tanks.items():
                if not tank.alive:
                    continue
                
                # Check if bullet hits tank
                distance = math.sqrt((bullet['x'] - tank.x)**2 + (bullet['y'] - tank.y)**2)
                if distance <= TANK_SIZE/2:
                    # Tank hit!
                    tank.take_damage(DAMAGE_PER_HIT)
                    self._log(f"{bullet['owner']} hit {tank_name}. Health: {tank.health}")
                    
                    # Award points to shooter
                    if bullet['owner'] in self.tanks:
                        shooter = self.tanks[bullet['owner']]
                        shooter.score += 10
                        
                        if not tank.alive:
                            shooter.kills += 1
                            shooter.score += 50  # Bonus for kill
                            self._log(f"{tank_name} was destroyed by {bullet['owner']}.")
                    
                    # Remove bullet
                    self.bullets.remove(bullet)
                    break
    
    def _end_round(self):
        """End current round and start new one"""
        # Log completion of the round that just finished
        self._log(f"Round {self.round_number} completed.")

        # If we've just finished the final round, end the battle
        if self.round_number >= self.max_rounds:
            self.game_running = False
            self._log("Battle finished!")
            return

        # Increment round counter for the next round
        self.round_number += 1
        
        # Reset tanks for new round
        for tank in self.tanks.values():
            tank.x = random.uniform(TANK_SIZE, ARENA_WIDTH - TANK_SIZE)
            tank.y = random.uniform(TANK_SIZE, ARENA_HEIGHT - TANK_SIZE)
            tank.angle = random.uniform(0, 360)
            tank.health = MAX_HEALTH
            tank.alive = True
            tank.bullets = []
        
        # Clear bullets
        self.bullets = []
        
        # Start new round
        self.round_start_time = time.time()
    
    def start_game(self):
        """Start the game"""
        self.game_running = True
        self.round_number = 1
        self.round_start_time = time.time()
        self._log("Battle started!")
        
        # Reset all tanks
        for tank in self.tanks.values():
            tank.health = MAX_HEALTH
            tank.alive = True
            tank.score = 0
            tank.kills = 0
            tank.bullets = []
        
        self.bullets = []
    
    def get_game_state(self) -> dict:
        """Get current game state for frontend"""
        return {
            'tanks': [tank.to_dict() for tank in self.tanks.values()],
            'bullets': self.bullets,
            'obstacles': self.obstacles,
            'game_running': self.game_running,
            'round_number': self.round_number,
            'max_rounds': self.max_rounds,
            'round_time': self.round_time,
            'time_remaining': max(0, self.round_time - (time.time() - self.round_start_time)),
            'logs': self.logs[-100:]
        }

    def _resolve_tank_collisions(self):
        """Prevent tanks from overlapping by separating any that collide."""
        # Create a list of alive tanks for easier iteration
        alive_tanks = [t for t in self.tanks.values() if t.alive]
        for i in range(len(alive_tanks)):
            for j in range(i + 1, len(alive_tanks)):
                t1 = alive_tanks[i]
                t2 = alive_tanks[j]
                dx = t2.x - t1.x
                dy = t2.y - t1.y
                distance = math.hypot(dx, dy)
                min_dist = TANK_SIZE  # Tanks are considered circles with radius TANK_SIZE/2
                if distance == 0:
                    # If both tanks are exactly on top of each other, nudge them apart slightly
                    angle = random.uniform(0, 2 * math.pi)
                    dx = math.cos(angle) * 0.1
                    dy = math.sin(angle) * 0.1
                    t1.x -= dx
                    t1.y -= dy
                    t2.x += dx
                    t2.y += dy
                    continue
                if distance < min_dist:
                    # Amount we need to separate the tanks so they just touch
                    overlap = min_dist - distance
                    # Normalised vector between the tanks
                    nx = dx / distance
                    ny = dy / distance
                    # Push each tank half the overlap distance in opposite directions
                    shift_x = nx * overlap / 2
                    shift_y = ny * overlap / 2
                    t1.x -= shift_x
                    t1.y -= shift_y
                    t2.x += shift_x
                    t2.y += shift_y
                    # Ensure tanks stay within arena bounds
                    for t in (t1, t2):
                        t.x = min(max(t.x, TANK_SIZE / 2), ARENA_WIDTH - TANK_SIZE / 2)
                        t.y = min(max(t.y, TANK_SIZE / 2), ARENA_HEIGHT - TANK_SIZE / 2)

# Global game state
game_state = GameState()

# Game update thread
def game_loop():
    """Main game loop running in background"""
    while True:
        if game_state.game_running:
            game_state.update()
        time.sleep(1/60)  # 60 FPS

# Start game loop in background thread
game_thread = threading.Thread(target=game_loop, daemon=True)
game_thread.start()

@app.route('/')
def index():
    """Main game page"""
    return render_template('index.html')

@app.route('/api/game-state')
def get_game_state():
    """Get current game state"""
    return jsonify(game_state.get_game_state())

@app.route('/api/add-tank', methods=['POST'])
def add_tank():
    """Add a new tank to the game"""
    data = request.get_json()
    raw_name = (data.get('name') or '').strip()
    # Use provided name if non-empty, else pick the next safe phonetic name
    if raw_name:
        name = raw_name
    else:
        name = _next_phonetic_name(game_state.tanks.keys())
    color = data.get('color', f'#{random.randint(0, 0xFFFFFF):06x}')
    brain_code = data.get('brain_code')
    
    game_state.add_tank(name, color, brain_code)
    return jsonify({'success': True, 'tank_name': name})

@app.route('/api/start-game', methods=['POST'])
def start_game():
    """Start the game"""
    if len(game_state.tanks) < 2:
        return jsonify({'error': 'Need at least 2 tanks to start'})
    # Allow optional configuration of rounds and time per round
    data = request.get_json(silent=True) or {}

    # Validate and apply custom settings if provided
    max_rounds = data.get('max_rounds')
    round_time = data.get('round_time')

    try:
        if max_rounds is not None:
            max_rounds = int(max_rounds)
            if max_rounds > 0:
                game_state.max_rounds = max_rounds
        if round_time is not None:
            round_time = int(round_time)
            if round_time > 0:
                game_state.round_time = round_time
    except ValueError:
        # Ignore invalid values and keep defaults
        pass

    game_state.start_game()
    return jsonify({'success': True, 'max_rounds': game_state.max_rounds, 'round_time': game_state.round_time})

@app.route('/api/reset-game', methods=['POST'])
def reset_game():
    """Reset the game"""
    global game_state
    game_state = GameState()
    return jsonify({'success': True})

@app.route('/api/sample-brains')
def get_sample_brains():
    """Get sample tank brain code for competitors"""
    samples = {
        'simple_chaser': '''
import math

def think(game_state):
    my_tank = game_state['my_tank']
    other_tanks = game_state['other_tanks']
    
    if not other_tanks:
        return {'move': 'forward'}
    
    # Find closest enemy
    closest = min(other_tanks, key=lambda t: 
        (t['x'] - my_tank['x'])**2 + (t['y'] - my_tank['y'])**2)
    
    # Calculate angle to enemy
    dx = closest['x'] - my_tank['x']
    dy = closest['y'] - my_tank['y']
    target_angle = math.degrees(math.atan2(dy, dx))
    
    # Calculate angle difference
    angle_diff = (target_angle - my_tank['angle']) % 360
    if angle_diff > 180:
        angle_diff -= 360
    
    action = {}
    
    # Rotate towards enemy
    if abs(angle_diff) > 5:
        action['rotate'] = 1 if angle_diff > 0 else -1
    else:
        action['move'] = 'forward'
        action['shoot'] = True
    
    return action
''',
        'coward': '''
import math
import random

def think(game_state):
    my_tank = game_state['my_tank']
    other_tanks = game_state['other_tanks']
    bullets = game_state['bullets']
    
    # Find closest enemy
    if other_tanks:
        closest = min(other_tanks, key=lambda t: 
            (t['x'] - my_tank['x'])**2 + (t['y'] - my_tank['y'])**2)
        
        # Calculate distance to enemy
        distance = math.sqrt((closest['x'] - my_tank['x'])**2 + (closest['y'] - my_tank['y'])**2)
        
        # If too close, move away
        if distance < 100:
            dx = my_tank['x'] - closest['x']
            dy = my_tank['y'] - closest['y']
            target_angle = math.degrees(math.atan2(dy, dx))
            
            angle_diff = (target_angle - my_tank['angle']) % 360
            if angle_diff > 180:
                angle_diff -= 360
            
            action = {}
            if abs(angle_diff) > 5:
                action['rotate'] = 1 if angle_diff > 0 else -1
            else:
                action['move'] = 'forward'
            
            return action
    
    # Default: move randomly
    return {'move': 'forward', 'rotate': random.choice([-1, 0, 1])}
''',
        'aggressive_shooter': '''
import math

def think(game_state):
    my_tank = game_state['my_tank']
    other_tanks = game_state['other_tanks']
    
    action = {'shoot': True}  # Always try to shoot
    
    if other_tanks:
        # Find closest enemy
        closest = min(other_tanks, key=lambda t: 
            (t['x'] - my_tank['x'])**2 + (t['y'] - my_tank['y'])**2)
        
        # Calculate angle to enemy
        dx = closest['x'] - my_tank['x']
        dy = closest['y'] - my_tank['y']
        target_angle = math.degrees(math.atan2(dy, dx))
        
        # Calculate angle difference
        angle_diff = (target_angle - my_tank['angle']) % 360
        if angle_diff > 180:
            angle_diff -= 360
        
        # Rotate towards enemy
        if abs(angle_diff) > 5:
            action['rotate'] = 1 if angle_diff > 0 else -1
        else:
            action['move'] = 'forward'
    
    return action
'''
    }
    
    return jsonify(samples)

@app.route('/api/debug-data')
def get_debug_data():
    """Return recent debug logs for all tanks (capped)"""
    return jsonify({name: tank.debug_log[-100:] for name, tank in game_state.tanks.items()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 