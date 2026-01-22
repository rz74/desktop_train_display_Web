"""
COORDINATE-BASED DISCOVERY
Maps MTA GTFS Stop IDs and PATH stations to HERE Station IDs using lat/lng proximity.
Bypasses name-matching issues by using exact coordinates.
"""
import httpx
import json
import time
from pathlib import Path
from typing import Dict, Optional

# Configuration
HERE_API_KEY = "3323Fg4PTSpFKcex0iIRwr7ECrOTi_InEZQ3zSpIzCg"
MTA_API_URL = "https://data.ny.gov/api/views/39hk-dx4f/rows.json?accessType=DOWNLOAD"
HERE_STATIONS_URL = "https://transit.hereapi.com/v8/stations"

# Proximity search radius (meters)
SEARCH_RADIUS = 100  # 100 meters

# PATH stations with coordinates
PATH_STATIONS = {
    "Newark Penn Station": (40.734346, -74.164101),
    "Harrison": (40.739462, -74.155836),
    "Journal Square": (40.733126, -74.062745),
    "Grove Street": (40.719742, -74.042482),
    "Hoboken": (40.735657, -74.029414),
    "Newport": (40.727127, -74.033818),
    "Exchange Place": (40.716306, -74.033355),
    "World Trade Center": (40.712582, -74.012147),
    "Christopher Street": (40.733021, -74.007135),
    "9th St": (40.734655, -73.999073),
    "14th St": (40.737466, -73.996782),
    "23rd St": (40.742878, -73.992821),
    "33rd St": (40.749013, -73.988466)
}


def fetch_mta_with_coordinates():
    """
    Fetch MTA stations with GTFS Stop ID, Stop Name, and coordinates.
    Returns list of dicts with stop_id, name, lat, lng.
    """
    print("="*80)
    print("FETCHING MTA STATION DATA WITH COORDINATES")
    print("="*80)
    print(f"Source: {MTA_API_URL}")
    print()
    
    try:
        with httpx.Client(timeout=60.0) as client:
            print("Downloading data...")
            response = client.get(MTA_API_URL)
            response.raise_for_status()
            data = response.json()
        
        stations = []
        seen_stop_ids = set()
        
        for row in data.get('data', []):
            if len(row) > 19:  # Need all columns up to longitude
                gtfs_stop_id = row[8]   # Column 8: GTFS Stop ID
                stop_name = row[13]     # Column 13: Stop Name
                lat = row[18]           # Column 18: GTFS Latitude
                lng = row[19]           # Column 19: GTFS Longitude
                
                # Validate data
                if all([gtfs_stop_id, stop_name, lat, lng]):
                    # Skip duplicates (same stop_id)
                    if gtfs_stop_id in seen_stop_ids:
                        continue
                    
                    try:
                        lat = float(lat)
                        lng = float(lng)
                        
                        stations.append({
                            'gtfs_stop_id': str(gtfs_stop_id),
                            'stop_name': str(stop_name).strip(),
                            'lat': lat,
                            'lng': lng
                        })
                        seen_stop_ids.add(gtfs_stop_id)
                    except (ValueError, TypeError):
                        continue
        
        print(f"[SUCCESS] Retrieved {len(stations)} unique MTA stops with coordinates")
        print()
        
        # Show first 10 as verification
        print("First 10 stops (verification):")
        for i, station in enumerate(stations[:10], 1):
            print(f"  {i:2d}. {station['gtfs_stop_id']:6s} - {station['stop_name']:40s} ({station['lat']:.6f}, {station['lng']:.6f})")
        print()
        
        return stations
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch MTA data: {e}")
        return []


def search_here_by_coordinates(lat: float, lng: float, retry: int = 3) -> Optional[Dict]:
    """
    Search HERE Transit API using coordinates (proximity search).
    Returns the nearest rail/subway station within SEARCH_RADIUS.
    """
    params = {
        'apiKey': HERE_API_KEY,
        'in': f'{lat},{lng};r={SEARCH_RADIUS}',
        'return': 'transport'
    }
    
    for attempt in range(retry):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(HERE_STATIONS_URL, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = 2 ** attempt
                    print(f"      [RATE LIMIT] Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
            
            stations = data.get('stations', [])
            if not stations:
                return None
            
            # Filter for rail/subway/regionalTrain stations only
            for station in stations:
                place = station.get('place', {})
                transports = station.get('transports', [])
                
                # Check if it's a rail/subway station
                modes = [t.get('mode', '') for t in transports]
                if any(mode in ['subway', 'rail', 'regionalTrain'] for mode in modes):
                    return {
                        'here_id': place.get('id', ''),
                        'here_name': place.get('name', ''),
                        'modes': list(set(modes)),
                        'location': place.get('location', {})
                    }
            
            return None
            
        except httpx.HTTPStatusError as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            return None
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            return None
    
    return None


def discover_by_coordinates():
    """
    Main discovery logic using coordinate-based proximity search.
    """
    print("="*80)
    print("COORDINATE-BASED DISCOVERY - NYC/NJ METRO AREA")
    print("="*80)
    print("Target: Map every MTA GTFS Stop ID and PATH station to HERE Station ID")
    print("Method: Proximity search using official coordinates")
    print(f"Search Radius: {SEARCH_RADIUS} meters")
    print()
    
    # Step 1: Fetch MTA stations with coordinates
    mta_stations = fetch_mta_with_coordinates()
    if not mta_stations:
        print("[FATAL] Failed to fetch MTA stations. Aborting.")
        return
    
    # Step 2: Map MTA stations by coordinates
    print("="*80)
    print(f"MAPPING {len(mta_stations)} MTA STOPS BY COORDINATES")
    print("="*80)
    print()
    
    mta_mapping = {}
    mta_found = {}
    mta_not_found = []
    
    for i, station in enumerate(mta_stations, 1):
        gtfs_id = station['gtfs_stop_id']
        name = station['stop_name']
        lat = station['lat']
        lng = station['lng']
        
        print(f"[{i:4d}/{len(mta_stations)}] {gtfs_id:6s} {name:45s} ", end='', flush=True)
        
        result = search_here_by_coordinates(lat, lng)
        
        if result:
            mta_mapping[gtfs_id] = result['here_id']
            mta_found[gtfs_id] = {
                'gtfs_stop_id': gtfs_id,
                'stop_name': name,
                'here_id': result['here_id'],
                'here_name': result['here_name'],
                'agency': 'MTA',
                'modes': result['modes'],
                'coordinates': {'lat': lat, 'lng': lng}
            }
            print(f"[OK] -> {result['here_id']}")
        else:
            mta_not_found.append(station)
            print("[NOT FOUND]")
        
        # Rate limiting: 0.3 seconds per request (faster)
        if i < len(mta_stations):
            time.sleep(0.3)
    
    print()
    
    # Step 3: Map PATH stations by coordinates
    print("="*80)
    print(f"MAPPING {len(PATH_STATIONS)} PATH STATIONS BY COORDINATES")
    print("="*80)
    print()
    
    path_mapping = {}
    path_found = {}
    path_not_found = []
    
    for i, (station_name, (lat, lng)) in enumerate(PATH_STATIONS.items(), 1):
        print(f"[{i:2d}/{len(PATH_STATIONS)}] {station_name:30s} ", end='', flush=True)
        
        result = search_here_by_coordinates(lat, lng)
        
        if result:
            path_mapping[station_name] = result['here_id']
            path_found[station_name] = {
                'station_name': station_name,
                'here_id': result['here_id'],
                'here_name': result['here_name'],
                'agency': 'PATH',
                'modes': result['modes'],
                'coordinates': {'lat': lat, 'lng': lng}
            }
            print(f"[OK] -> {result['here_id']}")
        else:
            path_not_found.append(station_name)
            print("[NOT FOUND]")
        
        if i < len(PATH_STATIONS):
            time.sleep(0.3)
    
    print()
    print("[INFO] Saving results...")
    
    # Step 4: Generate results
    print("="*80)
    print("DISCOVERY RESULTS")
    print("="*80)
    print(f"MTA Stops: {len(mta_found)}/{len(mta_stations)} mapped ({len(mta_found)*100//len(mta_stations)}%)")
    print(f"PATH Stations: {len(path_found)}/{len(PATH_STATIONS)} mapped ({len(path_found)*100//len(PATH_STATIONS)}%)")
    print(f"Total: {len(mta_found) + len(path_found)}/{len(mta_stations) + len(PATH_STATIONS)} stations")
    print()
    
    # Save comprehensive results
    output = {
        'metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'coordinate-based proximity search',
            'search_radius_meters': SEARCH_RADIUS,
            'mta_total': len(mta_stations),
            'mta_found': len(mta_found),
            'mta_not_found': len(mta_not_found),
            'path_total': len(PATH_STATIONS),
            'path_found': len(path_found),
            'path_not_found': len(path_not_found),
            'coverage_percent': (len(mta_found) + len(path_found)) * 100 // (len(mta_stations) + len(PATH_STATIONS))
        },
        'mta': mta_found,
        'path': path_found,
        'not_found': {
            'mta': [s['gtfs_stop_id'] for s in mta_not_found[:50]],
            'path': path_not_found
        }
    }
    
    output_file = Path(__file__).parent / 'coordinate_mapping.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[SAVED] Complete mapping: {output_file}")
    print()
    
    # Generate simplified GTFS-to-HERE mapping for API use
    gtfs_to_here = {}
    gtfs_to_here.update(mta_mapping)
    gtfs_to_here.update(path_mapping)
    
    mapping_file = Path(__file__).parent / 'gtfs_to_here_map.json'
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(gtfs_to_here, f, indent=2)
    
    print(f"[SAVED] GTFS-to-HERE mapping: {mapping_file}")
    print()
    
    # Show first 20 successful MTA mappings
    if mta_found:
        print("="*80)
        print("FIRST 20 SUCCESSFUL MTA MAPPINGS:")
        print("="*80)
        for i, (gtfs_id, info) in enumerate(list(mta_found.items())[:20], 1):
            print(f"{i:2d}. {gtfs_id:6s} -> {info['here_id']:15s} | {info['stop_name']:40s} -> {info['here_name']}")
        print()
    
    # Show sample of not found
    if mta_not_found:
        print("="*80)
        print(f"SAMPLE NOT FOUND (first 10 of {len(mta_not_found)}):")
        print("="*80)
        for station in mta_not_found[:10]:
            print(f"  {station['gtfs_stop_id']:6s} - {station['stop_name']:40s} ({station['lat']:.6f}, {station['lng']:.6f})")
        print()
    
    if path_not_found:
        print("="*80)
        print("PATH STATIONS NOT FOUND:")
        print("="*80)
        for station in path_not_found:
            print(f"  - {station}")
        print()
    
    print("="*80)
    print("COORDINATE-BASED DISCOVERY COMPLETE")
    print("="*80)


if __name__ == '__main__':
    discover_by_coordinates()
