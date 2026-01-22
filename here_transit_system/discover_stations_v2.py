"""
Discovery script v2 - Search for stations by proximity to known coordinates
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

# Known station coordinates
STATIONS_TO_FIND = {
    'jsq': {
        'name': 'Journal Square',
        'lat': 40.7334,
        'lng': -74.0631,
        'search_terms': ['journal square', 'jsq']
    },
    'wtc': {
        'name': 'World Trade Center (PATH)',
        'lat': 40.7126,
        'lng': -74.0099,
        'search_terms': ['world trade center', 'wtc']
    },
    'fulton': {
        'name': 'Fulton St',
        'lat': 40.7101,
        'lng': -74.0070,
        'search_terms': ['fulton']
    },
    'cortlandt': {
        'name': 'WTC Cortlandt',
        'lat': 40.7107,
        'lng': -74.0116,
        'search_terms': ['cortlandt', 'wtc cortlandt']
    }
}

def search_near_location(key, station_info, radius=500):
    """Search for stations near a specific coordinate."""
    params = {
        'apiKey': HERE_API_KEY,
        'in': f'{station_info["lat"]},{station_info["lng"]};r={radius}',
        'return': 'transport'
    }
    
    print(f"\n{'='*60}")
    print(f"Searching for: {station_info['name']}")
    print(f"Location: {station_info['lat']}, {station_info['lng']}")
    print(f"Radius: {radius}m")
    print('='*60)
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        stations = data.get('stations', [])
        print(f"\nFound {len(stations)} stations nearby:\n")
        
        matches = []
        for station in stations:
            place = station.get('place', {})
            station_name = place.get('name', '')
            station_id = place.get('id', '')
            location = place.get('location', {})
            
            print(f"  • {station_name}")
            print(f"    ID: {station_id}")
            print(f"    Lat/Lng: {location.get('lat')}, {location.get('lng')}")
            
            # Check if this matches our search terms
            name_lower = station_name.lower()
            for search_term in station_info['search_terms']:
                if search_term.lower() in name_lower:
                    print(f"    ✓ MATCH for '{search_term}'")
                    matches.append({
                        'id': station_id,
                        'name': station_name
                    })
                    break
            print()
        
        return matches
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        return []
    except httpx.RequestError as e:
        print(f"Request Error: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print("\n" + "="*60)
    print("HERE Transit Station Discovery v2")
    print("Searching by proximity to known station coordinates")
    print("="*60)
    
    if HERE_API_KEY == "YOUR_HERE_API_KEY":
        print("\n⚠️  WARNING: Please set your HERE API key!")
        return
    
    all_results = {}
    
    # Search for each station
    for key, station_info in STATIONS_TO_FIND.items():
        matches = search_near_location(key, station_info)
        
        if matches:
            # Use the first match
            all_results[key] = matches[0]['id']
            print(f"✓ Selected for '{key}': {matches[0]['name']} ({matches[0]['id']})")
        else:
            print(f"✗ No match found for '{key}'")
            all_results[key] = f"NOT_FOUND_{key.upper()}"
    
    # Print summary
    print("\n" + "="*60)
    print("FINAL SUMMARY - stations.json format:")
    print("="*60)
    print(json.dumps(all_results, indent=2))
    
    # Optionally write to file
    output_file = Path(__file__).parent / "stations_discovered.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ Saved to: {output_file}")

if __name__ == "__main__":
    main()
