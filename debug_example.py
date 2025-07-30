#!/usr/bin/env python3
"""
Example script showing how to access debug data for each bot.
Run this while the game is running to see debug information.
"""

import requests
import json
import time
from datetime import datetime

def get_debug_data():
    """Fetch debug data from the running game"""
    try:
        response = requests.get('http://localhost:5000/api/debug-data')
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to game server. Make sure the game is running on localhost:5000")
        return None

def format_timestamp(ts):
    """Convert timestamp to readable format"""
    return datetime.fromtimestamp(ts).strftime('%H:%M:%S.%f')[:-3]

def display_debug_data(debug_data):
    """Display debug data in a readable format"""
    if not debug_data:
        print("No debug data available")
        return
    
    print(f"\n=== DEBUG DATA ({datetime.now().strftime('%H:%M:%S')}) ===\n")
    
    for tank_name, events in debug_data.items():
        print(f"🤖 {tank_name}:")
        if not events:
            print("  No recent events")
            continue
            
        # Group events by type for better readability
        event_counts = {}
        for event in events:
            event_type = event['event']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Show event summary
        for event_type, count in event_counts.items():
            print(f"  {event_type}: {count} times")
        
        # Show most recent 5 events in detail
        print("  Recent events:")
        for event in events[-5:]:
            ts = format_timestamp(event['ts'])
            event_type = event['event']
            
            if event_type == 'move':
                print(f"    {ts} - Moved to ({event.get('new_x', 'N/A'):.1f}, {event.get('new_y', 'N/A'):.1f})")
            elif event_type == 'rotate':
                print(f"    {ts} - Rotated to {event.get('angle', 'N/A'):.1f}°")
            elif event_type == 'shoot':
                bullet = event.get('bullet', {})
                print(f"    {ts} - Shot bullet at ({bullet.get('x', 'N/A'):.1f}, {bullet.get('y', 'N/A'):.1f})")
            elif event_type == 'damage':
                print(f"    {ts} - Took {event.get('damage', 'N/A')} damage (health: {event.get('new_health', 'N/A')})")
            elif event_type == 'hit':
                print(f"    {ts} - Hit by {event.get('by', 'unknown')}")
            elif event_type == 'successful_hit':
                print(f"    {ts} - Successfully hit {event.get('target', 'unknown')}")
            elif event_type == 'destroyed':
                print(f"    {ts} - DESTROYED!")
            else:
                print(f"    {ts} - {event_type}: {event}")
        
        print()

def main():
    """Main function to continuously monitor debug data"""
    print("🔍 Robocode Debug Data Monitor")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            debug_data = get_debug_data()
            if debug_data:
                display_debug_data(debug_data)
            else:
                print("Waiting for game to start...")
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Debug monitor stopped")

if __name__ == "__main__":
    main() 