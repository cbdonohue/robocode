#!/usr/bin/env python3
"""
Utility to export debug data from the game to JSON files for analysis.
This creates timestamped files with all debug data for each bot.
"""

import requests
import json
import time
import os
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

def export_debug_data(debug_data, output_dir="debug_exports"):
    """Export debug data to JSON files"""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export individual bot data
    for tank_name, events in debug_data.items():
        filename = f"{output_dir}/{tank_name}_{timestamp}.json"
        
        export_data = {
            "tank_name": tank_name,
            "export_timestamp": datetime.now().isoformat(),
            "total_events": len(events),
            "events": events
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Exported {len(events)} events for {tank_name} to {filename}")
    
    # Export combined data
    combined_filename = f"{output_dir}/all_bots_{timestamp}.json"
    combined_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_bots": len(debug_data),
        "bot_data": debug_data
    }
    
    with open(combined_filename, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"Exported combined data to {combined_filename}")

def analyze_debug_data(debug_data):
    """Provide a quick analysis of the debug data"""
    print("\n=== DEBUG DATA ANALYSIS ===")
    
    for tank_name, events in debug_data.items():
        print(f"\n🤖 {tank_name}:")
        
        if not events:
            print("  No events recorded")
            continue
        
        # Count event types
        event_counts = {}
        for event in events:
            event_type = event['event']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Show statistics
        total_events = len(events)
        print(f"  Total events: {total_events}")
        
        for event_type, count in event_counts.items():
            percentage = (count / total_events) * 100
            print(f"  {event_type}: {count} ({percentage:.1f}%)")
        
        # Time span
        if events:
            first_time = events[0]['ts']
            last_time = events[-1]['ts']
            duration = last_time - first_time
            print(f"  Time span: {duration:.1f} seconds")
            print(f"  Events per second: {total_events/duration:.1f}")

def main():
    """Main function"""
    print("📊 Robocode Debug Data Exporter")
    print("This will export debug data for all bots to JSON files.\n")
    
    # Get current debug data
    debug_data = get_debug_data()
    
    if not debug_data:
        print("No debug data available. Make sure the game is running and has some activity.")
        return
    
    # Show analysis
    analyze_debug_data(debug_data)
    
    # Ask user if they want to export
    response = input("\nExport debug data to files? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        export_debug_data(debug_data)
        print("\n✅ Export complete!")
    else:
        print("Export cancelled.")

if __name__ == "__main__":
    main() 