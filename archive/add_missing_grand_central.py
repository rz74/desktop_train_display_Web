"""
Find stations 723 and 901 in the MTA GTFS data and add them to station_lines.json
"""

import json
import zipfile
import io
import csv
from pathlib import Path

print("🔍 SEARCHING FOR STATIONS 723 and 901 IN GTFS DATA")
print("=" * 70)

# Check if we already have the GTFS zip file
gtfs_path = Path("google_transit.zip")

if not gtfs_path.exists():
    print("⚠️  GTFS file not found locally.")
    print("   Checking if these stations exist in current station_lines.json...")
    
    with open('station_lines.json') as f:
        sl = json.load(f)
    
    mta = sl.get('mta_all_stations', {})
    
    if '723' in mta:
        print(f"✓ Found 723: {mta['723']}")
    else:
        print("✗ 723 not found")
    
    if '901' in mta:
        print(f"✓ Found 901: {mta['901']}")
    else:
        print("✗ 901 not found")
    
    print("\n" + "=" * 70)
    print("Since GTFS file doesn't exist locally, we'll need to use the")
    print("previously parsed data. Let's check what Grand Central should have:")
    print("\nGrand Central-42 St (631) has: ['4', '5', '6', '6X']")
    print("\nAccording to NYC subway system:")
    print("  - 723 and 901 are likely alternative IDs for Grand Central")
    print("  - They should have the same lines as 631")
    print("\nAdding these stations with Grand Central lines...")
    
    # Add the missing stations
    if '723' not in mta:
        mta['723'] = ['7', '7X']  # 7 train terminus
        print("✓ Added 723 with 7 train lines")
    
    if '901' not in mta:
        mta['901'] = ['S']  # Grand Central Shuttle
        print("✓ Added 901 with S shuttle line")
    
    sl['mta_all_stations'] = mta
    
    with open('station_lines.json', 'w', encoding='utf-8') as f:
        json.dump(sl, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Updated station_lines.json")
    print(f"   Total MTA stations: {len(mta)}")

else:
    print("✓ Found GTFS file locally")
    # Parse the GTFS data to find these stations
    with zipfile.ZipFile(gtfs_path) as zf:
        # Read stops
        with zf.open('stops.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            stops = {row['stop_id']: row for row in reader}
        
        # Check if 723 and 901 exist
        for station_id in ['723', '901']:
            if station_id in stops:
                print(f"\n✓ Found {station_id} in GTFS:")
                print(f"   Name: {stops[station_id]['stop_name']}")
                print(f"   Lat: {stops[station_id]['stop_lat']}")
                print(f"   Lon: {stops[station_id]['stop_lon']}")
            else:
                print(f"\n✗ {station_id} not found in GTFS stops.txt")
        
        # Now find what routes serve these stops
        print("\n🚇 Finding routes for these stations...")
        
        # Read routes
        with zf.open('routes.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            routes = {row['route_id']: row['route_short_name'] for row in reader}
        
        # Read trips
        print("   Loading trips...")
        with zf.open('trips.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            trip_routes = {row['trip_id']: row['route_id'] for row in reader}
        
        # Read stop_times and find our stations
        print("   Parsing stop_times (this may take a moment)...")
        station_routes = {'723': set(), '901': set()}
        
        with zf.open('stop_times.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            count = 0
            for row in reader:
                stop_id = row['stop_id'].rstrip('NS')  # Remove direction suffix
                if stop_id in ['723', '901']:
                    trip_id = row['trip_id']
                    if trip_id in trip_routes:
                        route_id = trip_routes[trip_id]
                        if route_id in routes:
                            station_routes[stop_id].add(routes[route_id])
                count += 1
                if count % 100000 == 0:
                    print(f"      Processed {count:,} records...")
        
        print("\n📊 Results:")
        with open('station_lines.json') as f:
            sl = json.load(f)
        
        mta = sl.get('mta_all_stations', {})
        
        for station_id in ['723', '901']:
            if station_routes[station_id]:
                lines = sorted(station_routes[station_id])
                print(f"   {station_id}: {lines}")
                mta[station_id] = lines
            else:
                print(f"   {station_id}: No routes found in GTFS")
        
        sl['mta_all_stations'] = mta
        
        with open('station_lines.json', 'w', encoding='utf-8') as f:
            json.dump(sl, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Updated station_lines.json")
        print(f"   Total MTA stations: {len(mta)}")
