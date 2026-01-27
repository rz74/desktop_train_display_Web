"""
Download and parse MTA Static GTFS data to build station_lines.json.
Uses the official MTA GTFS feed (static, not real-time).
"""

import json
import csv
import io
import zipfile
from collections import defaultdict
import httpx

GTFS_URL = "http://web.mta.info/developers/data/nyct/subway/google_transit.zip"

def load_existing_station_lines():
    """Load existing station_lines.json to preserve PATH stations and complexes."""
    try:
        with open('station_lines.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "path_stations": {},
            "complexes": {},
            "mta_major_stations": {}
        }

def load_coordinate_mapping():
    """Load coordinate_mapping.json to get all station IDs we care about."""
    with open('coordinate_mapping.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def download_and_parse_gtfs():
    """
    Download MTA Static GTFS and extract route information for each station.
    Returns: dict mapping stop_id -> list of route_ids
    """
    print("📥 Downloading MTA Static GTFS data...")
    print(f"   URL: {GTFS_URL}")
    
    response = httpx.get(GTFS_URL, timeout=30.0, follow_redirects=True)
    response.raise_for_status()
    
    print(f"✓ Downloaded {len(response.content) / 1024 / 1024:.1f} MB")
    
    # Parse the ZIP file
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        print("\n📂 Files in GTFS archive:")
        for name in zf.namelist():
            print(f"   - {name}")
        
        # Read stops.txt to get parent stations
        print("\n📍 Parsing stops.txt...")
        stops_data = {}
        with zf.open('stops.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            for row in reader:
                stop_id = row['stop_id']
                parent_station = row.get('parent_station', '') or stop_id
                stops_data[stop_id] = {
                    'stop_name': row.get('stop_name', ''),
                    'parent_station': parent_station
                }
        
        print(f"✓ Loaded {len(stops_data)} stops")
        
        # Read routes.txt to get route information
        print("\n🚇 Parsing routes.txt...")
        routes_data = {}
        with zf.open('routes.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            for row in reader:
                route_id = row['route_id']
                routes_data[route_id] = {
                    'route_short_name': row.get('route_short_name', ''),
                    'route_long_name': row.get('route_long_name', '')
                }
        
        print(f"✓ Loaded {len(routes_data)} routes")
        
        # Read trips.txt to link routes to trips
        print("\n🚃 Parsing trips.txt...")
        trip_routes = {}
        with zf.open('trips.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            for row in reader:
                trip_id = row['trip_id']
                route_id = row['route_id']
                trip_routes[trip_id] = route_id
        
        print(f"✓ Loaded {len(trip_routes)} trips")
        
        # Read stop_times.txt to link trips to stops
        print("\n⏱️  Parsing stop_times.txt (this may take a minute)...")
        station_routes = defaultdict(set)
        
        with zf.open('stop_times.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            count = 0
            for row in reader:
                trip_id = row['trip_id']
                stop_id = row['stop_id']
                
                if trip_id in trip_routes:
                    route_id = trip_routes[trip_id]
                    
                    # Get parent station
                    if stop_id in stops_data:
                        parent_station = stops_data[stop_id]['parent_station']
                        station_routes[parent_station].add(route_id)
                
                count += 1
                if count % 50000 == 0:
                    print(f"   Processed {count:,} stop times...")
        
        print(f"✓ Processed {count:,} stop times")
    
    # Convert sets to sorted lists and use route short names
    result = {}
    for station_id, route_ids in station_routes.items():
        route_names = []
        for route_id in route_ids:
            if route_id in routes_data:
                short_name = routes_data[route_id]['route_short_name']
                if short_name:
                    route_names.append(short_name)
        result[station_id] = sorted(route_names)
    
    return result

def main():
    print("🚇 Building station_lines.json from MTA STATIC GTFS")
    print("=" * 70)
    
    # Load existing data
    existing_data = load_existing_station_lines()
    print(f"✓ Loaded existing data:")
    print(f"  - PATH stations: {len(existing_data.get('path_stations', {}))}")
    print(f"  - Complexes: {len(existing_data.get('complexes', {}))}")
    print(f"  - MTA stations: {len(existing_data.get('mta_major_stations', {}))}")
    
    # Load coordinate mapping
    coord_data = load_coordinate_mapping()
    mta_stations = coord_data.get('mta', {})
    print(f"\n✓ Loaded {len(mta_stations)} MTA stations from coordinate_mapping.json")
    
    # Download and parse GTFS
    try:
        all_routes = download_and_parse_gtfs()
        print(f"\n✓ Extracted routes for {len(all_routes)} stations from GTFS")
        
        # Match with our coordinate mapping
        updated_mta_stations = {}
        found_count = 0
        missing_count = 0
        
        for gtfs_id in mta_stations.keys():
            if gtfs_id in all_routes and all_routes[gtfs_id]:
                updated_mta_stations[gtfs_id] = all_routes[gtfs_id]
                found_count += 1
            else:
                missing_count += 1
        
        print(f"\n📊 Results:")
        print(f"  ✓ Matched: {found_count} stations")
        if missing_count > 0:
            print(f"  ⚠️  Missing: {missing_count} stations")
        
    except Exception as e:
        print(f"\n❌ Error downloading/parsing GTFS: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Merge with existing data
    final_data = {
        "path_stations": existing_data.get("path_stations", {}),
        "complexes": existing_data.get("complexes", {}),
        "mta_major_stations": updated_mta_stations
    }
    
    # Save to file
    output_file = 'station_lines.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ SUCCESS! Saved to {output_file}")
    print(f"  - PATH stations: {len(final_data['path_stations'])}")
    print(f"  - Complexes: {len(final_data['complexes'])}")
    print(f"  - MTA stations: {len(final_data['mta_major_stations'])}")
    total = len(final_data['path_stations']) + len(final_data['complexes']) + len(final_data['mta_major_stations'])
    print(f"  - Total entries: {total}")
    
    # Show sample entries
    print(f"\n📝 Sample entries:")
    sample_count = 0
    for station_id, routes in list(updated_mta_stations.items())[:5]:
        station_name = mta_stations.get(station_id, {}).get('stop_name', 'Unknown')
        print(f"  - {station_id} ({station_name}): {', '.join(routes)}")
        sample_count += 1

if __name__ == "__main__":
    main()
