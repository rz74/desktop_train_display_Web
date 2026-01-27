#!/usr/bin/env python3
"""Test PATH arrivals at Journal Square"""

import httpx
from google.transit import gtfs_realtime_pb2
from mappings import calculate_minutes_until, PATH_ROUTES_ABBREV, get_path_direction

response = httpx.get('https://path.transitdata.nyc/gtfsrt')
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

print("=" * 60)
print("JOURNAL SQUARE (26731) ARRIVALS")
print("=" * 60)

arrivals = []
for entity in feed.entity:
    if entity.HasField('trip_update'):
        route_id = entity.trip_update.trip.route_id
        for st in entity.trip_update.stop_time_update:
            if str(st.stop_id) == "26731" and st.HasField('arrival'):
                minutes = calculate_minutes_until(st.arrival.time)
                if minutes >= 0:
                    route_abbrev = PATH_ROUTES_ABBREV.get(route_id, route_id)
                    direction = get_path_direction(route_id, "26731", None)
                    arrivals.append(f"{route_abbrev} {direction} - {minutes}min")

print(f"Found {len(arrivals)} arrivals:")
for a in sorted(arrivals)[:15]:
    print(f"  {a}")
