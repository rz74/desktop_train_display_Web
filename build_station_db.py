"""Build comprehensive MTA station database from live feeds"""
from underground import SubwayFeed
import pytz
from collections import defaultdict
import time

# Get all unique stations from all feeds
all_stations = defaultdict(set)  # stop_id -> set of (route_id, stop_name)

feeds_to_check = ['A', 'N', 'L', '1', 'G', 'SI']  # Representative feeds

print("Scanning MTA feeds for all stations...")

for feed_name in feeds_to_check:
    try:
        print(f"\nChecking feed {feed_name}...")
        feed = SubwayFeed.get(feed_name)
        
        for entity in feed.entity:
            if hasattr(entity, 'trip_update') and entity.trip_update:
                trip = entity.trip_update.trip
                route_id = trip.route_id
                
                for stop_time in entity.trip_update.stop_time_update:
                    stop_id = stop_time.stop_id
                    # Remove directional suffix
                    base_stop_id = stop_id.rstrip('NS')
                    
                    # Try to get stop name (we'll need to fetch from somewhere)
                    all_stations[base_stop_id].add(route_id)
        
        print(f"  Found {len(all_stations)} unique stations so far")
        time.sleep(1)  # Rate limit
        
    except Exception as e:
        print(f"  Error with feed {feed_name}: {e}")

print(f"\n\nTotal unique stations found: {len(all_stations)}")
print("\nSample stations:")
for i, (stop_id, routes) in enumerate(list(all_stations.items())[:20]):
    print(f"{stop_id}: Routes {sorted(routes)}")
