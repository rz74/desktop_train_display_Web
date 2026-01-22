"""Map direction_id to terminal stations for PATH routes"""
import httpx
from google.transit import gtfs_realtime_pb2
from mappings import PATH_STATIONS

PATH_FEED_URL = "https://path.transitdata.nyc/gtfsrt"

response = httpx.get(PATH_FEED_URL, timeout=10.0)
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

# Check terminal stations to understand direction_id mapping
terminals = {
    "26733": "Newark",      # Red terminal
    "26734": "WTC",         # Red/Green terminal
    "26731": "Journal Sq",  # Yellow terminal
    "26724": "33rd St",     # Yellow/Orange/Blue terminal
    "26730": "Hoboken"      # Green/Orange/Blue terminal
}

print("=== Direction ID Mapping at Terminal Stations ===\n")

for stop_id, name in terminals.items():
    print(f"\n{name} (Stop {stop_id}):")
    seen_routes = {}
    
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip = entity.trip_update.trip
            
            for stop_time in entity.trip_update.stop_time_update:
                if str(stop_time.stop_id) == stop_id:
                    if stop_time.HasField('arrival'):
                        route_id = trip.route_id
                        direction_id = trip.direction_id if trip.HasField('direction_id') else 'N/A'
                        
                        if route_id not in seen_routes:
                            seen_routes[route_id] = set()
                        seen_routes[route_id].add(direction_id)
    
    for route_id in sorted(seen_routes.keys()):
        directions = sorted(list(seen_routes[route_id]))
        print(f"  Route {route_id}: direction_id = {directions}")
