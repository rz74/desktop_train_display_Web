#!/usr/bin/env python3
"""Check what routes actually serve Journal Square"""

import httpx
from google.transit import gtfs_realtime_pb2

response = httpx.get('https://path.transitdata.nyc/gtfsrt')
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

routes_at_jsq = set()
for entity in feed.entity:
    if entity.HasField('trip_update'):
        route_id = entity.trip_update.trip.route_id
        for st in entity.trip_update.stop_time_update:
            if str(st.stop_id) == "26731":
                routes_at_jsq.add(route_id)

print("Routes serving Journal Square (26731):")
for r in sorted(routes_at_jsq):
    print(f"  Route {r}")

# Now check all unique route/stop combinations
print("\nAll route 860 (Red) stops:")
for entity in feed.entity:
    if entity.HasField('trip_update'):
        if entity.trip_update.trip.route_id == "860":
            stops = [str(st.stop_id) for st in entity.trip_update.stop_time_update]
            print(f"  Stops: {stops}")
            break
