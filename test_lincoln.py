"""Test why Lincoln Center shows no lines"""
from underground import SubwayFeed

station_id = "lincoln center"
stop_id = "D12"
feed_name = "1"

print(f"Testing station: {station_id}")
print(f"Stop ID: {stop_id}")
print(f"Feed: {feed_name}")

try:
    feed = SubwayFeed.get(feed_name)
    print(f"\nFeed fetched successfully")
    print(f"Number of entities: {len(feed.entity)}")
    
    routes_found = set()
    stops_found = set()
    
    for entity in feed.entity:
        if hasattr(entity, 'trip_update') and entity.trip_update:
            trip = entity.trip_update.trip
            route_id = trip.route_id
            
            for stop_time in entity.trip_update.stop_time_update:
                stop = stop_time.stop_id
                stops_found.add(stop)
                
                if stop.startswith(stop_id):
                    routes_found.add(route_id)
                    print(f"  Found route {route_id} at stop {stop}")
    
    print(f"\nTotal routes found: {routes_found}")
    print(f"\nAll stops in feed (first 20): {list(stops_found)[:20]}")
    
    # Check if D12 appears anywhere
    d12_stops = [s for s in stops_found if 'D12' in s]
    print(f"\nStops containing 'D12': {d12_stops}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
