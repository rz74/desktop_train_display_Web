"""
Discovery script to find HERE Transit Station IDs for our required hubs.
Run this once to identify the correct station IDs.
"""
import httpx
import json
import os
from pathlib import Path

# Load API key from .env file
env_file = Path(__file__).parent / ".env.example"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('HERE_API_KEY='):
                HERE_API_KEY = line.split('=', 1)[1].strip()
                break
else:
    HERE_API_KEY = os.getenv("HERE_API_KEY", "YOUR_HERE_API_KEY")

BASE_URL = "https://transit.hereapi.com/v8/stations"

# NYC/NJ center point
CENTER_LAT = 40.7306
CENTER_LNG = -73.9352
RADIUS = 20000  # 20km search radius as specified

# Stations we're looking for
TARGET_STATIONS = [
    'Journal Square',
    'World Trade Center',
    'Fulton St',
    'WTC Cortlandt'
]

def search_stations():
    """Search for stations near the center point."""
    params = {
        'apiKey': HERE_API_KEY,
        'in': f'{CENTER_LAT},{CENTER_LNG};r={RADIUS}',
        'return': 'transport'
    }
    
    print(f"Searching for stations near {CENTER_LAT},{CENTER_LNG}...")
    print(f"Radius: {RADIUS}m\n")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        stations = data.get('stations', [])
        print(f"Found {len(stations)} total stations\n")
        
        # Show all stations first
        print("All stations found:")
        print("-" * 60)
        for station in stations:
            station_name = station.get('place', {}).get('name', '')
            station_id = station.get('id', '')
            location = station.get('place', {}).get('location', {})
            print(f"  {station_name}")
            print(f"    ID: {station_id}")
            print(f"    Lat/Lng: {location.get('lat')}, {location.get('lng')}")
            print()
        
        print("\n" + "="*60)
        print("Searching for target stations...")
        print("="*60 + "\n")
        
        # Filter and display relevant stations
        matches = {}
        for station in stations:
            station_name = station.get('place', {}).get('name', '')
            station_id = station.get('id', '')
            
            # Check if this matches any of our target stations
            for target in TARGET_STATIONS:
                if target.lower() in station_name.lower():
                    print(f"✓ Match found!")
                    print(f"  Name: {station_name}")
                    print(f"  ID: {station_id}")
                    print(f"  Location: {station.get('place', {}).get('location', {})}")
                    print()
                    
                    # Store for JSON output
                    key = target.lower().replace(' ', '_')
                    matches[key] = {
                        'id': station_id,
                        'name': station_name
                    }
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY - Station IDs for stations.json:")
        print("="*60)
        for key, info in matches.items():
            print(f'{key}: {info["id"]}  # {info["name"]}')
        
        return matches
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        return {}
    except httpx.RequestError as e:
        print(f"Request Error: {e}")
        return {}
    except Exception as e:
        print(f"Error fetching stations: {e}")
        return {}

if __name__ == "__main__":
    print("HERE Transit Station Discovery")
    print("="*60)
    print()
    
    if HERE_API_KEY == "YOUR_HERE_API_KEY":
        print("⚠️  WARNING: Please set your HERE API key in the script!")
        print("   Get one at: https://platform.here.com/")
        print()
        print("   Replace 'YOUR_HERE_API_KEY' with your actual key.")
    else:
        matches = search_stations()
        
        if matches:
            print("\n✓ Discovery complete!")
            print(f"  Found {len(matches)} matching stations")
        else:
            print("\n⚠️  No matching stations found")
            print("  Try adjusting the search radius or station names")
