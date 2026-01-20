"""Check if PATH GTFS-RT provides direction_id"""
import httpx
from google.transit import gtfs_realtime_pb2
from mappings import PATH_STATIONS

PATH_FEED_URL = "https://path.transitdata.nyc/gtfsrt"

# Grove Street = 26728
grove_st = "26728"

response = httpx.get(PATH_FEED_URL, timeout=10.0)
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

print(f"\n=== Checking arrivals at Grove Street (26728) ===\n")

for entity in feed.entity:
    if entity.HasField('trip_update'):
        trip = entity.trip_update.trip
        
        for stop_time in entity.trip_update.stop_time_update:
            if str(stop_time.stop_id) == grove_st:
                if stop_time.HasField('arrival'):
                    route_id = trip.route_id
                    trip_id = trip.trip_id if trip.HasField('trip_id') else 'N/A'
                    direction_id = trip.direction_id if trip.HasField('direction_id') else 'N/A'
                    
                    print(f"Route: {route_id} | Trip ID: {trip_id} | Direction ID: {direction_id}")
                    
                    # Check all fields available in trip
                    print(f"  Available trip fields: {[f.name for f, v in trip.ListFields()]}")
                    print()
