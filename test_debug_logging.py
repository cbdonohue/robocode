#!/usr/bin/env python3
"""
Test script to verify debug logging is working for the ChatGPT bot.
"""

import requests
import json
import time

def test_debug_logging():
    """Test if debug logging is working"""
    print("🧪 Testing Debug Logging System")
    
    # Check if game is running
    try:
        response = requests.get('http://localhost:5000/api/game-state')
        if response.status_code != 200:
            print("❌ Game server not responding")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to game server. Make sure it's running on localhost:5000")
        return False
    
    print("✅ Game server is running")
    
    # Get current debug data
    try:
        response = requests.get('http://localhost:5000/api/debug-data')
        if response.status_code == 200:
            debug_data = response.json()
            print(f"✅ Debug data API working")
            print(f"📊 Tanks with debug data: {list(debug_data.keys())}")
            
            for tank_name, events in debug_data.items():
                print(f"🤖 {tank_name}: {len(events)} events")
                if events:
                    print(f"   Latest event: {events[-1]}")
                else:
                    print(f"   No events recorded")
        else:
            print(f"❌ Debug data API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting debug data: {e}")
        return False
    
    return True

def check_chatgpt_bot():
    """Check if ChatGPT bot is properly configured"""
    print("\n🤖 Checking ChatGPT Bot Configuration")
    
    # Check if OpenAI is available
    try:
        import openai
        print("✅ OpenAI library available")
    except ImportError:
        print("❌ OpenAI library not available")
        return False
    
    # Check if API key is set
    import os
    if os.getenv('OPENAI_API_KEY'):
        print("✅ OpenAI API key configured")
    else:
        print("⚠️  OpenAI API key not set (bot will use fallback strategy)")
    
    return True

def main():
    """Main test function"""
    print("=" * 50)
    print("🧪 ROBOTANK DEBUG LOGGING TEST")
    print("=" * 50)
    
    # Test debug logging
    if not test_debug_logging():
        print("\n❌ Debug logging test failed")
        return
    
    # Check ChatGPT bot
    if not check_chatgpt_bot():
        print("\n❌ ChatGPT bot configuration issues")
        return
    
    print("\n✅ All tests passed!")
    print("\n📋 Next steps:")
    print("1. Make sure a tank with ChatGPT bot is added to the game")
    print("2. Start the battle")
    print("3. Run the export script: python export_debug_data.py")
    print("4. Check the generated JSON files for debug data")

if __name__ == "__main__":
    main() 