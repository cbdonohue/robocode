# 🤖 Tank Battle Arena

A competitive tank battle arena where programmers write Python code to control their tanks! Watch Code-driven tanks battle it out in real-time with custom strategies and tactics.

[video.mp4](https://github.com/user-attachments/assets/641ff54d-9aaf-4c52-9362-3c62504665b0)

## 🎮 Game Features

- **AI Programming**: Write Python code to control your tank's behavior
- **Real-time Battles**: Watch tanks battle in a dynamic arena
- **Multiple Rounds**: 10 rounds of intense combat
- **Scoring System**: Points for hits, kills, and survival
- **Sample Brains**: Pre-built code examples to get started
- **Beautiful UI**: Modern interface with real-time visualization
- **Health System**: Tanks have health and can be destroyed
- **Bullet Physics**: Realistic projectile movement and collision detection

## 🧠 How Tank Brains Work

Each tank has a "brain" - a Python function that receives game state and returns actions:

```python
def think(game_state):
    my_tank = game_state['my_tank']
    other_tanks = game_state['other_tanks']
    bullets = game_state['bullets']
    
    # Your logic here
    return {
        'move': 'forward',      # 'forward', 'backward', or None
        'rotate': 1,           # -1 (left), 0, or 1 (right)
        'shoot': True          # True to fire, False to not
    }
```

### Available Actions:
- **Movement**: `'forward'` or `'backward'` to move in tank's current direction
- **Rotation**: `-1` (turn left), `0` (no turn), or `1` (turn right)
- **Shooting**: `True` to fire a bullet, `False` to not shoot

### Game State Information:
- **my_tank**: Your tank's position, angle, health, and status
- **other_tanks**: List of enemy tanks with positions and angles
- **bullets**: All active bullets in the arena
- **obstacles**: Arena obstacles (future feature)
- **arena_width/height**: Arena dimensions

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Steps

1. **Clone or download the project files**

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game:**
   ```bash
   python app.py
   ```

5. **Open your web browser and go to:**
   ```
   http://localhost:5000
   ```

## 🎯 How to Play

1. **Add Tanks**: Create tanks with custom names, colors, and code brains
2. **Write Code**: Program your tank's behavior using Python
3. **Start Battle**: Begin the arena battle with at least 2 tanks
4. **Watch & Learn**: Observe how different strategies perform
5. **Iterate**: Modify your tank's brain and try again!

## 🧠 Sample Code Strategies

### Simple Chaser
```python
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
    
    # Rotate towards enemy and shoot
    angle_diff = (target_angle - my_tank['angle']) % 360
    if angle_diff > 180:
        angle_diff -= 360
    
    if abs(angle_diff) > 5:
        return {'rotate': 1 if angle_diff > 0 else -1}
    else:
        return {'move': 'forward', 'shoot': True}
```

### Coward (Defensive)
```python
def think(game_state):
    my_tank = game_state['my_tank']
    other_tanks = game_state['other_tanks']
    
    if other_tanks:
        closest = min(other_tanks, key=lambda t: 
            (t['x'] - my_tank['x'])**2 + (t['y'] - my_tank['y'])**2)
        
        distance = math.sqrt((closest['x'] - my_tank['x'])**2 + (closest['y'] - my_tank['y'])**2)
        
        # Run away if too close
        if distance < 100:
            dx = my_tank['x'] - closest['x']
            dy = my_tank['y'] - closest['y']
            target_angle = math.degrees(math.atan2(dy, dx))
            
            angle_diff = (target_angle - my_tank['angle']) % 360
            if angle_diff > 180:
                angle_diff -= 360
            
            if abs(angle_diff) > 5:
                return {'rotate': 1 if angle_diff > 0 else -1}
            else:
                return {'move': 'forward'}
    
    return {'move': 'forward', 'rotate': random.choice([-1, 0, 1])}
```

## 🏆 Scoring System

- **Hit**: +10 points for hitting an enemy
- **Kill**: +50 bonus points for destroying an enemy
- **Survival**: Points for staying alive longer
- **Final Score**: Total points across all rounds

## 🎨 Game Mechanics

- **Arena Size**: 800x600 pixels
- **Tank Speed**: 2 pixels per frame
- **Rotation Speed**: 3 degrees per frame
- **Bullet Speed**: 5 pixels per frame
- **Health**: 100 HP per tank
- **Damage**: 25 HP per hit
- **Shot Cooldown**: 0.5 seconds between shots
- **Rounds**: 10 rounds, 60 seconds each

## 🛠️ Technical Details

- **Backend**: Python Flask with real-time game loop
- **Frontend**: HTML5, CSS3, JavaScript with modern UI
- **Execution**: Safe Python code execution with error handling and configurable timeouts
- **Real-time Updates**: 60 FPS game loop with 20 FPS display updates
- **Multi-threading**: Background game processing with per-tank execution timeouts

## 📁 File Structure

```
tank-battle-arena/
├── app.py              # Main Flask application with game logic
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── venv/              # Virtual environment
└── templates/
    └── index.html     # Main game interface
```

## 🚀 Advanced Features

### Configurable Brain Timeouts
Prevent slow code from freezing the game:
- **Environment Variable**: Set `BRAIN_THINK_TIMEOUT=0.1` for 100ms timeout
- **API Configuration**: Pass `think_timeout` parameter when starting games
- **Default**: 50ms timeout prevents one slow brain from affecting others
- **Safety**: Timeouts are logged and don't crash the game

### Custom Strategies
Create sophisticated tank behaviors:
- **Predictive Shooting**: Lead moving targets
- **Formation Tactics**: Coordinate with multiple tanks
- **Terrain Awareness**: Use arena boundaries strategically
- **Bullet Dodging**: Avoid incoming projectiles
- **Resource Management**: Balance aggression vs. survival

### Competition Ideas
- **Tournament Mode**: Bracket-style elimination
- **League System**: Ranked matches with ELO ratings
- **Code Sharing**: Share and rate tank brains
- **Replay System**: Watch and analyze past battles

## 🔧 Customization

You can easily modify:
- **Arena Size**: Change `ARENA_WIDTH` and `ARENA_HEIGHT`
- **Game Speed**: Adjust `TANK_SPEED`, `BULLET_SPEED`, etc.
- **Scoring**: Modify point values in the collision detection
- **Round Settings**: Change `max_rounds` and `round_time`
- **Brain Timeout**: Configure per-tank execution time limit via environment variable `BRAIN_THINK_TIMEOUT` or API parameter `think_timeout`
- **Visual Effects**: Update CSS for different themes

## 🐛 Troubleshooting

- **Tank not moving**: Check your `think()` function returns valid actions
- **Code errors**: Look for Python syntax errors in the browser console
- **Performance issues**: Reduce the number of tanks or simplify AI logic
- **Connection problems**: Ensure Flask server is running on port 5000

## 🤝 Contributing

Feel free to contribute:
- New sample strategies
- UI improvements
- Game mechanics enhancements
- Bug fixes and optimizations

## 📄 License

This project is open source. Feel free to use, modify, and distribute!

---

**Ready to program your tank and dominate the arena? Let the battles begin!** 🎮⚔️ 
