"""
Discovery script to find HERE Transit Station IDs for our required hubs.
Run this once to identify the correct station IDs.
"""
import requests
import json

# HERE API Configuration
HERE_API_KEY = "YOUR_HERE_API_KEY"  # Replace with your actual API key
BASE_URL = "https://transit.hereapi.com/v8/stations"

# NYC/NJ center point
CENTER_LAT = 40.7306
CENTER_LNG = -73.9352
RADIUS = 5000  # 5km search radius

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
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        stations = data.get('stations', [])
        print(f"Found {len(stations)} total stations\n")
        
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
        
    except requests.exceptions.RequestException as e:
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
