"""
Build station_lines.json using the underground library's static GTFS data.
This script queries the local GTFS data (no API calls) to determine which routes serve each station.
"""

import json
from collections import defaultdict
from underground import SubwayFeed

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
    """Load coordinate_mapping.json to get all station IDs."""
    with open('coordinate_mapping.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_routes_from_underground():
    """
    Use the underground library to access static GTFS data.
    Returns: dict mapping gtfs_stop_id -> list of route_ids
    """
    print("📚 Accessing MTA Static GTFS via underground library...")
    
    station_routes = defaultdict(set)
    
    # The underground library has embedded GTFS data
    # We can access it through the SubwayFeed class
    feed = SubwayFeed.get('gtfs')
    
    # Get the stops data
    stops = feed.stops
    
    # Get route information
    routes = feed.routes
    
    # Get trip information to link routes to stops
    trips = feed.trips
    stop_times = feed.stop_times
    
    # Build mapping
    for trip_id, trip in trips.items():
        route_id = trip.route_id
        
        # Get all stops for this trip
        if trip_id in stop_times:
            for stop_time in stop_times[trip_id]:
                stop_id = stop_time.stop_id
                
                # Get parent station (remove direction suffix like 'N' or 'S')
                parent_id = stop_id.rstrip('NS')
                
                # Add route to this station
                station_routes[parent_id].add(route_id)
    
    # Convert sets to sorted lists
    return {sid: sorted(list(routes)) for sid, routes in station_routes.items()}

def main():
    print("🚇 Building station_lines.json from UNDERGROUND LIBRARY (Static GTFS)")
    print("=" * 70)
    
    # Load existing data
    existing_data = load_existing_station_lines()
    print(f"✓ Loaded existing data:")
    print(f"  - PATH stations: {len(existing_data.get('path_stations', {}))}")
    print(f"  - Complexes: {len(existing_data.get('complexes', {}))}")
    print(f"  - MTA stations: {len(existing_data.get('mta_major_stations', {}))}")
    
    # Load coordinate mapping to know which stations we care about
    coord_data = load_coordinate_mapping()
    mta_stations = coord_data.get('mta', {})
    print(f"\n✓ Loaded {len(mta_stations)} MTA stations from coordinate_mapping.json")
    
    # Try to extract routes from underground library
    try:
        all_routes = extract_routes_from_underground()
        print(f"✓ Extracted routes from underground GTFS data")
        
        # Filter to only stations in our coordinate mapping
        updated_mta_stations = {}
        missing_count = 0
        
        for gtfs_id in mta_stations.keys():
            if gtfs_id in all_routes:
                updated_mta_stations[gtfs_id] = all_routes[gtfs_id]
            else:
                missing_count += 1
        
        print(f"✓ Matched {len(updated_mta_stations)} stations with routes")
        if missing_count > 0:
            print(f"⚠️  {missing_count} stations missing route data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n📝 Need to use alternative approach:")
        print("   1. Download MTA Static GTFS from: http://web.mta.info/developers/data/nyct/subway/google_transit.zip")
        print("   2. Extract stops.txt and parse routes manually")
        return
    
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
    total = len(final_data['path_stations']) + len(final_data['complexes']) + len(final_data['mta_major_stations'])
    print(f"  - Total entries: {total}")

if __name__ == "__main__":
    main()
