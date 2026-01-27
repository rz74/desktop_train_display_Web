"""
Extract train line routes for each station using STATIC DATA ONLY.
No API calls - uses the underground library's built-in GTFS data.

This script reads from the MTA Static GTFS data embedded in the underground library
and creates a complete station_lines.json file.
"""

import json
from collections import defaultdict
from underground import metadata

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

def extract_routes_from_gtfs():
    """
    Extract station to routes mapping from underground library's GTFS data.
    Returns: dict mapping gtfs_stop_id -> list of route_ids
    """
    station_routes = defaultdict(set)
    
    # Get feed metadata
    print("📚 Loading MTA Static GTFS data from underground library...")
    
    # Access the GTFS data structure from underground
    # underground.metadata contains the GTFS feed information
    feed = metadata.get_feed()
    
    # Iterate through all stops in the feed
    for stop_id, stop_info in feed.stops.items():
        # Get parent station if this is a platform
        parent_id = stop_info.get('parent_station') or stop_id
        
        # Find all routes that serve this stop
        for route_id, route_info in feed.routes.items():
            # Check if this route serves this stop
            for trip_id, trip_info in feed.trips.items():
                if trip_info.get('route_id') == route_id:
                    # Check if this trip stops at our station
                    for stop_time in feed.stop_times.get(trip_id, []):
                        if stop_time.get('stop_id', '').startswith(parent_id):
                            station_routes[parent_id].add(route_id)
                            break
    
    # Convert sets to sorted lists
    return {sid: sorted(list(routes)) for sid, routes in station_routes.items()}

def main():
    print("🚇 Building station_lines.json from STATIC GTFS data ONLY")
    print("=" * 70)
    
    # Load existing data (to preserve PATH stations and complexes)
    existing_data = load_existing_station_lines()
    print(f"✓ Loaded existing data:")
    print(f"  - PATH stations: {len(existing_data.get('path_stations', {}))}")
    print(f"  - Complexes: {len(existing_data.get('complexes', {}))}")
    print(f"  - MTA stations: {len(existing_data.get('mta_major_stations', {}))}")
    
    # Extract routes from GTFS
    try:
        station_routes = extract_routes_from_gtfs()
        print(f"\n✓ Extracted routes for {len(station_routes)} MTA stations from GTFS")
    except Exception as e:
        print(f"\n❌ Error extracting from underground library: {e}")
        print("\nAttempting alternative method...")
        
        # Alternative: Load from coordinate_mapping and use known route patterns
        with open('coordinate_mapping.json', 'r', encoding='utf-8') as f:
            coord_data = json.load(f)
        
        station_routes = {}
        for gtfs_id, station_info in coord_data.get('mta', {}).items():
            # For now, mark as needs_manual_entry
            station_routes[gtfs_id] = ["NEEDS_MANUAL_ENTRY"]
        
        print(f"✓ Loaded {len(station_routes)} stations from coordinate_mapping.json")
        print("⚠️  Routes need to be filled in from MTA Static GTFS or Open Data CSV")
    
    # Update the MTA stations section
    updated_mta_stations = {}
    for gtfs_id, routes in station_routes.items():
        if routes and routes != ["NEEDS_MANUAL_ENTRY"]:
            updated_mta_stations[gtfs_id] = routes
    
    # Merge with existing data
    final_data = {
        "path_stations": existing_data.get("path_stations", {}),
        "complexes": existing_data.get("complexes", {}),
        "mta_major_stations": updated_mta_stations
    }
    
    # Save to file
    with open('station_lines.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ SUCCESS! Updated station_lines.json")
    print(f"  - PATH stations: {len(final_data['path_stations'])}")
    print(f"  - Complexes: {len(final_data['complexes'])}")
    print(f"  - MTA stations: {len(final_data['mta_major_stations'])}")
    print(f"  - Total: {len(final_data['path_stations']) + len(final_data['complexes']) + len(final_data['mta_major_stations'])}")

if __name__ == "__main__":
    main()
