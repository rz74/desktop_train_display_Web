"""Find the real stop IDs for major stations"""
from underground import SubwayFeed

# Try different feeds
feeds_to_check = ['1', 'A', 'N', 'L']

print("Searching for stations with '66' in stop ID...")

for feed_name in feeds_to_check:
    try:
        print(f"\n=== Feed {feed_name} ===")
        feed = SubwayFeed.get(feed_name)
        
        stops_found = {}
        for entity in feed.entity:
            if hasattr(entity, 'trip_update') and entity.trip_update:
                for stop_time in entity.trip_update.stop_time_update:
                    stop = stop_time.stop_id
                    if '66' in stop or stop.startswith('1') or stop.startswith('2'):
                        if stop not in stops_found:
                            stops_found[stop] = set()
                        stops_found[stop].add(entity.trip_update.trip.route_id)
        
        # Show results
        for stop, routes in sorted(stops_found.items())[:10]:
            print(f"  {stop}: Routes {routes}")
            
    except Exception as e:
        print(f"Error with feed {feed_name}: {e}")
