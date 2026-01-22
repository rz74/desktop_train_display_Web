from underground import SubwayFeed

# Check Feed A for A, C, E line stops near WTC
try:
    feed = SubwayFeed.get('A')
    
    wtc_stops = set()
    
    for entity in feed.entity:
        if hasattr(entity, 'trip_update') and entity.trip_update:
            trip = entity.trip_update.trip
            route_id = trip.route_id
            
            if route_id in ['A', 'C', 'E']:
                for stop_time in entity.trip_update.stop_time_update:
                    stop_id = stop_time.stop_id
                    # Look for stops that might be WTC (E01, A41, etc)
                    if stop_id.startswith('E01') or stop_id.startswith('A4') or 'Cortlandt' in str(stop_id):
                        wtc_stops.add((route_id, stop_id))
    
    print("A/C/E stops found in Feed A:")
    for route, stop in sorted(wtc_stops):
        print(f"  Route {route}: {stop}")
        
except Exception as e:
    print(f"Error: {e}")
