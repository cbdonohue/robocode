# Debug Data for Robocode Bots

This document explains how to use the debug data functionality that has been added to the Robocode game.

## Overview

The game now automatically collects debug data for each bot, tracking:
- **Movement**: When and where bots move
- **Rotation**: When bots rotate and their new angle
- **Shooting**: When bots shoot and bullet details
- **Damage**: When bots take damage and their health
- **Hits**: When bots successfully hit other bots
- **Destruction**: When bots are destroyed

## How to Access Debug Data

### 1. Real-time Monitoring

Run the debug monitor script to see live debug data:

```bash
python debug_example.py
```

This will continuously display debug information for all bots every 2 seconds.

### 2. API Endpoint

Access debug data directly via the API:

```bash
curl http://localhost:5000/api/debug-data
```

Returns JSON with debug logs for all bots (last 100 events per bot).

### 3. Export to Files

Export debug data to JSON files for analysis:

```bash
python export_debug_data.py
```

This creates timestamped files in a `debug_exports/` directory.

## Debug Data Format

Each debug event contains:
```json
{
  "ts": 1234567890.123,  // Timestamp
  "event": "move",       // Event type
  "new_x": 100.5,        // Event-specific data
  "new_y": 200.3
}
```

### Event Types

- **`move`**: Bot moved to new position
  - `new_x`, `new_y`: New coordinates
- **`rotate`**: Bot rotated
  - `angle`: New angle in degrees
- **`shoot`**: Bot fired a bullet
  - `bullet`: Bullet object with position and velocity
- **`damage`**: Bot took damage
  - `damage`: Amount of damage taken
  - `new_health`: Health after damage
- **`hit`**: Bot was hit by another bot
  - `by`: Name of bot that hit this one
- **`successful_hit`**: Bot successfully hit another bot
  - `target`: Name of bot that was hit
- **`destroyed`**: Bot was destroyed

## Using Debug Data for Development

### 1. Analyze Bot Behavior

Use the export script to analyze how your bots behave:
- How often do they move vs shoot?
- Are they getting stuck in certain patterns?
- How effective is their targeting?

### 2. Debug AI Issues

Check the debug logs to see:
- If your bot is making the expected decisions
- If there are errors in movement calculations
- If the bot is responding to game events correctly

### 3. Performance Analysis

Track metrics like:
- Events per second (activity level)
- Hit accuracy (successful_hit vs shoot ratio)
- Survival time (time between creation and destruction)

## Example Usage

1. Start the game: `python app.py`
2. Add some bots and start a battle
3. In another terminal, run: `python debug_example.py`
4. Watch the real-time debug output
5. When done, export the data: `python export_debug_data.py`

## File Structure

```
robocode/
├── app.py                 # Main game with debug functionality
├── debug_example.py       # Real-time debug monitor
├── export_debug_data.py   # Debug data exporter
├── debug_exports/         # Generated debug files (created when exporting)
└── DEBUG_README.md        # This file
```

## Technical Details

- Debug logs are capped at 200 events per bot to prevent memory issues
- Events are stored in memory and lost when the game restarts
- The `/api/debug-data` endpoint returns the last 100 events per bot
- Timestamps are Unix timestamps (seconds since epoch) 