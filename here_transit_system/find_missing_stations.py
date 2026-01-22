"""
Find the missing stations with broader search patterns
"""
import httpx
import json
from pathlib import Path

# Load API key
env_file = Path(__file__).parent / ".env.example"
with open(env_file, 'r') as f:
    for line in f:
        if line.startswith('HERE_API_KEY='):
            HERE_API_KEY = line.split('=', 1)[1].strip()
            break

BASE_URL = "https://transit.hereapi.com/v8/stations"

# Missing stations with expanded search
MISSING_STATIONS = {
    'chambers': {'name': 'Chambers St', 'lat': 40.7130, 'lng': -74.0094, 'search': ['chamber', 'park place']},
    'canal': {'name': 'Canal St', 'lat': 40.7188, 'lng': -74.0062, 'search': ['canal']},
    'times_square': {'name': 'Times Square', 'lat': 40.7557, 'lng': -73.9871, 'search': ['times sq', '42 st', '42nd st']},
    'herald_square': {'name': 'Herald Square', 'lat': 40.7495, 'lng': -73.9878, 'search': ['34 st', '34th st', 'herald']},
    'grand_central': {'name': 'Grand Central', 'lat': 40.7527, 'lng': -73.9772, 'search': ['grand central', '42 st']},
    'union_square': {'name': 'Union Square', 'lat': 40.7347, 'lng': -73.9906, 'search': ['union sq', '14 st']},
    '72nd_street': {'name': '72nd St', 'lat': 40.7782, 'lng': -73.9816, 'search': ['72 st', '72nd st']},
    '96th_street': {'name': '96th St', 'lat': 40.7937, 'lng': -73.9722, 'search': ['96 st', '96th st']},
    '86th_street': {'name': '86th St', 'lat': 40.7795, 'lng': -73.9554, 'search': ['86 st', '86th st']},
}

def search_station(key, info, radius=800):
    """Search for a station with larger radius."""
    params = {
        'apiKey': HERE_API_KEY,
        'in': f'{info["lat"]},{info["lng"]};r={radius}',
        'return': 'transport'
    }
    
    print(f"\nSearching: {info['name']} ({key})")
    print(f"  Location: {info['lat']}, {info['lng']}, Radius: {radius}m")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        stations = data.get('stations', [])
        print(f"  Found {len(stations)} stations nearby")
        
        # Show all rail/subway stations found
        rail_stations = []
        for station in stations:
            place = station.get('place', {})
            station_name = place.get('name', '')
            station_id = place.get('id', '')
            transports = station.get('transports', [])
            
            has_rail = any(
                t.get('mode') in ['regionalTrain', 'highSpeedTrain', 'rail', 'subway']
                for t in transports
            )
            
            if has_rail:
                rail_stations.append({
                    'id': station_id,
                    'name': station_name,
                    'transports': [t.get('name', 'Unknown') for t in transports if t.get('mode') in ['regionalTrain', 'subway']][:3]
                })
        
        if rail_stations:
            print(f"  Rail/Subway stations found ({len(rail_stations)}):")
            for i, rs in enumerate(rail_stations[:5], 1):  # Show first 5
                print(f"    {i}. {rs['name']} (ID: {rs['id']})")
                print(f"       Services: {', '.join(rs['transports'])}")
        
        # Try to match with search terms
        matches = []
        for rs in rail_stations:
            name_lower = rs['name'].lower()
            for search_term in info['search']:
                if search_term.lower() in name_lower:
                    matches.append(rs)
                    break
        
        if matches:
            print(f"\n  ✓ Best match: {matches[0]['name']} ({matches[0]['id']})")
            return matches[0]
        elif rail_stations:
            print(f"\n  ⚠ No exact match, best guess: {rail_stations[0]['name']} ({rail_stations[0]['id']})")
            return rail_stations[0]
        else:
            print(f"\n  ✗ No rail stations found")
            return None
            
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("="*80)
    print("FINDING MISSING STATIONS")
    print("="*80)
    
    results = {}
    for key, info in MISSING_STATIONS.items():
        result = search_station(key, info)
        if result:
            results[key] = result['id']
        else:
            results[key] = f'NOT_FOUND_{key.upper()}'
    
    print("\n" + "="*80)
    print("MISSING STATIONS SUMMARY")
    print("="*80)
    found = sum(1 for v in results.values() if not v.startswith('NOT_FOUND'))
    print(f"\nFound: {found}/{len(results)}")
    print("\nResults:")
    for key, station_id in results.items():
        status = "✓" if not station_id.startswith('NOT_FOUND') else "✗"
        print(f"  {status} {key}: {station_id}")
    
    # Save to file
    output_file = Path(__file__).parent / "missing_stations_found.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved to: {output_file}")

if __name__ == "__main__":
    main()
