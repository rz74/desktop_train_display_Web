"""
Comprehensive discovery script to find all PATH and MTA stations in NYC/JC.
This will search for stations by name and coordinates.
"""
import httpx
import json
from pathlib import Path
from typing import Dict, List

# Load API key
env_file = Path(__file__).parent / ".env.example"
with open(env_file, 'r') as f:
    for line in f:
        if line.startswith('HERE_API_KEY='):
            HERE_API_KEY = line.split('=', 1)[1].strip()
            break

BASE_URL = "https://transit.hereapi.com/v8/stations"

# Comprehensive list of PATH stations
PATH_STATIONS = {
    # Newark Line
    'newark': {'name': 'Newark Penn Station', 'lat': 40.7347, 'lng': -74.1644, 'search': ['newark']},
    'harrison': {'name': 'Harrison', 'lat': 40.7394, 'lng': -74.1558, 'search': ['harrison']},
    
    # JSQ-33rd Line
    'jsq': {'name': 'Journal Square', 'lat': 40.7334, 'lng': -74.0631, 'search': ['journal square', 'jsq']},
    'grove': {'name': 'Grove Street', 'lat': 40.7196, 'lng': -74.0426, 'search': ['grove street', 'grove st']},
    'exchange': {'name': 'Exchange Place', 'lat': 40.7167, 'lng': -74.0331, 'search': ['exchange place']},
    'wtc_path': {'name': 'World Trade Center PATH', 'lat': 40.7126, 'lng': -74.0099, 'search': ['world trade center']},
    'christopher': {'name': 'Christopher Street', 'lat': 40.7329, 'lng': -74.0070, 'search': ['christopher', 'christopher street']},
    '9th_street': {'name': '9th Street', 'lat': 40.7342, 'lng': -73.9991, 'search': ['9th street', '9th st']},
    '14th_street': {'name': '14th Street', 'lat': 40.7375, 'lng': -73.9968, 'search': ['14th street', '14th st']},
    '23rd_street': {'name': '23rd Street', 'lat': 40.7429, 'lng': -73.9925, 'search': ['23rd street', '23rd st']},
    '33rd_street': {'name': '33rd Street', 'lat': 40.7495, 'lng': -73.9881, 'search': ['33rd street', '33rd st']},
    
    # Hoboken Line
    'hoboken': {'name': 'Hoboken', 'lat': 40.7363, 'lng': -74.0290, 'search': ['hoboken']},
}

# Major MTA subway hubs in Manhattan and nearby
MTA_STATIONS = {
    # Lower Manhattan
    'fulton': {'name': 'Fulton St', 'lat': 40.7101, 'lng': -74.0070, 'search': ['fulton']},
    'cortlandt': {'name': 'WTC Cortlandt', 'lat': 40.7107, 'lng': -74.0116, 'search': ['cortlandt']},
    'chambers': {'name': 'Chambers St', 'lat': 40.7130, 'lng': -74.0094, 'search': ['chambers']},
    'city_hall': {'name': 'City Hall', 'lat': 40.7132, 'lng': -74.0066, 'search': ['city hall']},
    'canal': {'name': 'Canal St', 'lat': 40.7188, 'lng': -74.0062, 'search': ['canal']},
    
    # Midtown West
    'penn_station': {'name': 'Penn Station (34th St)', 'lat': 40.7505, 'lng': -73.9935, 'search': ['penn station', '34th street']},
    'times_square': {'name': 'Times Square-42nd St', 'lat': 40.7557, 'lng': -73.9871, 'search': ['times square', '42nd street']},
    'port_authority': {'name': 'Port Authority', 'lat': 40.7571, 'lng': -73.9897, 'search': ['port authority']},
    'herald_square': {'name': 'Herald Square-34th St', 'lat': 40.7495, 'lng': -73.9878, 'search': ['herald square']},
    
    # Midtown East
    'grand_central': {'name': 'Grand Central-42nd St', 'lat': 40.7527, 'lng': -73.9772, 'search': ['grand central']},
    'lexington_53': {'name': 'Lexington Ave/53rd St', 'lat': 40.7575, 'lng': -73.9691, 'search': ['lexington', '53rd']},
    'lexington_59': {'name': 'Lexington Ave/59th St', 'lat': 40.7625, 'lng': -73.9675, 'search': ['59th', 'lexington']},
    
    # Union Square area
    'union_square': {'name': 'Union Square-14th St', 'lat': 40.7347, 'lng': -73.9906, 'search': ['union square']},
    'astor_place': {'name': 'Astor Place', 'lat': 40.7300, 'lng': -73.9912, 'search': ['astor']},
    
    # Upper West Side
    'columbus_circle': {'name': 'Columbus Circle-59th St', 'lat': 40.7681, 'lng': -73.9819, 'search': ['columbus circle']},
    '72nd_street': {'name': '72nd St', 'lat': 40.7782, 'lng': -73.9816, 'search': ['72nd']},
    '96th_street': {'name': '96th St', 'lat': 40.7937, 'lng': -73.9722, 'search': ['96th']},
    
    # Upper East Side
    '86th_street': {'name': '86th St', 'lat': 40.7795, 'lng': -73.9554, 'search': ['86th']},
    
    # Brooklyn major hubs
    'atlantic_terminal': {'name': 'Atlantic Terminal-Barclays', 'lat': 40.6844, 'lng': -73.9766, 'search': ['atlantic', 'barclays']},
    'jay_street': {'name': 'Jay St-MetroTech', 'lat': 40.6923, 'lng': -73.9868, 'search': ['jay street', 'metrotech']},
    
    # Queens major hubs
    'queensboro': {'name': 'Queensboro Plaza', 'lat': 40.7508, 'lng': -73.9400, 'search': ['queensboro']},
    'jackson_heights': {'name': 'Jackson Heights-Roosevelt Ave', 'lat': 40.7465, 'lng': -73.8911, 'search': ['jackson heights', 'roosevelt']},
}

def search_station(key: str, info: dict, radius: int = 500) -> List[dict]:
    """Search for a station near coordinates."""
    params = {
        'apiKey': HERE_API_KEY,
        'in': f'{info["lat"]},{info["lng"]};r={radius}',
        'return': 'transport'
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        stations = data.get('stations', [])
        matches = []
        
        for station in stations:
            place = station.get('place', {})
            station_name = place.get('name', '')
            station_id = place.get('id', '')
            transports = station.get('transports', [])
            
            # Check if this matches our search terms
            name_lower = station_name.lower()
            for search_term in info['search']:
                if search_term.lower() in name_lower:
                    # Check for rail/subway transport
                    has_rail = any(
                        t.get('mode') in ['regionalTrain', 'highSpeedTrain', 'rail', 'subway']
                        for t in transports
                    )
                    
                    if has_rail:
                        matches.append({
                            'id': station_id,
                            'name': station_name,
                            'transports': [
                                f"{t.get('name', 'Unknown')} ({t.get('mode', 'unknown')})"
                                for t in transports[:3]  # Show first 3
                            ]
                        })
                    break
        
        return matches
        
    except Exception as e:
        print(f"  Error searching {key}: {e}")
        return []

def discover_all_stations():
    """Discover all PATH and MTA stations."""
    print("="*80)
    print("COMPREHENSIVE STATION DISCOVERY - PATH & MTA")
    print("="*80)
    print()
    
    all_results = {}
    
    # Discover PATH stations
    print("\n" + "="*80)
    print("PATH STATIONS")
    print("="*80)
    
    for key, info in PATH_STATIONS.items():
        print(f"\nSearching: {info['name']} ({key})")
        print(f"  Location: {info['lat']}, {info['lng']}")
        
        matches = search_station(key, info)
        
        if matches:
            match = matches[0]
            all_results[key] = {
                'id': match['id'],
                'name': match['name'],
                'type': 'PATH',
                'transports': match['transports']
            }
            print(f"  ✓ Found: {match['name']}")
            print(f"    ID: {match['id']}")
            print(f"    Services: {', '.join(match['transports'][:2])}")
        else:
            print(f"  ✗ Not found")
            all_results[key] = {
                'id': f'NOT_FOUND_{key.upper()}',
                'name': info['name'],
                'type': 'PATH',
                'transports': []
            }
    
    # Discover MTA stations
    print("\n" + "="*80)
    print("MTA SUBWAY STATIONS")
    print("="*80)
    
    for key, info in MTA_STATIONS.items():
        print(f"\nSearching: {info['name']} ({key})")
        print(f"  Location: {info['lat']}, {info['lng']}")
        
        matches = search_station(key, info)
        
        if matches:
            match = matches[0]
            all_results[key] = {
                'id': match['id'],
                'name': match['name'],
                'type': 'MTA',
                'transports': match['transports']
            }
            print(f"  ✓ Found: {match['name']}")
            print(f"    ID: {match['id']}")
            print(f"    Services: {', '.join(match['transports'][:2])}")
        else:
            print(f"  ✗ Not found")
            all_results[key] = {
                'id': f'NOT_FOUND_{key.upper()}',
                'name': info['name'],
                'type': 'MTA',
                'transports': []
            }
    
    return all_results

def main():
    results = discover_all_stations()
    
    # Summary
    print("\n" + "="*80)
    print("DISCOVERY SUMMARY")
    print("="*80)
    
    path_found = sum(1 for r in results.values() if r['type'] == 'PATH' and not r['id'].startswith('NOT_FOUND'))
    mta_found = sum(1 for r in results.values() if r['type'] == 'MTA' and not r['id'].startswith('NOT_FOUND'))
    total_found = path_found + mta_found
    
    print(f"\nPATH Stations: {path_found}/{len(PATH_STATIONS)} found")
    print(f"MTA Stations: {mta_found}/{len(MTA_STATIONS)} found")
    print(f"Total: {total_found}/{len(results)} found")
    
    # Save full results
    output_file = Path(__file__).parent / "all_stations_discovered.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Full results saved to: {output_file}")
    
    # Create simplified stations.json format
    stations_map = {k: v['id'] for k, v in results.items() if not v['id'].startswith('NOT_FOUND')}
    
    stations_file = Path(__file__).parent / "stations_complete.json"
    with open(stations_file, 'w') as f:
        json.dump(stations_map, f, indent=2)
    print(f"✓ Station IDs map saved to: {stations_file}")
    
    # Print stations that weren't found
    not_found = [k for k, v in results.items() if v['id'].startswith('NOT_FOUND')]
    if not_found:
        print(f"\n⚠ Stations not found ({len(not_found)}):")
        for key in not_found:
            print(f"  - {key}: {results[key]['name']}")

if __name__ == "__main__":
    main()
