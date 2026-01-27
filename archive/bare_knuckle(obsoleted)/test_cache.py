"""Test the station cache building"""
import sys
sys.path.insert(0, '.')

# Simulate what happens in app.py
from underground import SubwayFeed
from mappings import get_mta_station_name
from collections import defaultdict

print("Testing cache building...")

stations = defaultdict(lambda: {"feeds": set(), "routes": set(), "name": None})

feeds_to_check = ['A', 'N', 'L', '1', 'G', 'SI']

for feed_name in feeds_to_check:
    try:
        print(f"\nFetching feed {feed_name}...")
        feed = SubwayFeed.get(feed_name)
        
        if not feed or not hasattr(feed, 'entity'):
            print(f"  Feed {feed_name} has no entity")
            continue
            
        entity_count = 0
        for entity in feed.entity:
            if hasattr(entity, 'trip_update') and entity.trip_update:
                entity_count += 1
                trip = entity.trip_update.trip
                route_id = trip.route_id
                
                if not hasattr(entity.trip_update, 'stop_time_update') or not entity.trip_update.stop_time_update:
                    continue
                
                for stop_time in entity.trip_update.stop_time_update:
                    stop_id = stop_time.stop_id
                    base_stop_id = stop_id.rstrip('NS')
                    
                    stations[base_stop_id]["feeds"].add(feed_name)
                    stations[base_stop_id]["routes"].add(route_id)
                    
                    if not stations[base_stop_id]["name"]:
                        name = get_mta_station_name(stop_id)
                        if name and not name.startswith("Stop "):
                            stations[base_stop_id]["name"] = name
        
        print(f"  Processed {entity_count} entities")
        print(f"  Total stations so far: {len(stations)}")
        
    except Exception as e:
        print(f"  Error with feed {feed_name}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n\nFinal count: {len(stations)} stations")

# Show some examples
print("\nSample stations:")
for i, (stop_id, info) in enumerate(list(stations.items())[:10]):
    print(f"  {stop_id}: {info['name']} - Routes: {info['routes']}")

# Search for "queens"
print("\n\nSearching for 'queens':")
query = "queens"
matches = []
for stop_id, info in stations.items():
    if info["name"]:
        if query.lower() in info["name"].lower():
            matches.append(f"  {info['name']} ({stop_id})")

if matches:
    for match in matches[:10]:
        print(match)
else:
    print("  No matches found")
