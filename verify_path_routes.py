#!/usr/bin/env python3
"""
Verify complete PATH route structure by analyzing all trips in the feed
"""

import httpx
from google.transit import gtfs_realtime_pb2
from collections import defaultdict

PATH_FEED_URL = "https://path.transitdata.nyc/gtfsrt"

def verify_routes():
    try:
        response = httpx.get(PATH_FEED_URL, timeout=10.0)
        response.raise_for_status()
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        # Track which routes serve which stops
        route_stops = defaultdict(set)
        
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update.trip
                route_id = trip.route_id
                
                for stop_time in entity.trip_update.stop_time_update:
                    stop_id = str(stop_time.stop_id)
                    route_stops[route_id].add(stop_id)
        
        route_names = {
            "859": "Green (HOB-WTC)",
            "860": "Red (NWK-WTC)",
            "861": "Yellow (JSQ-33)",
            "862": "Blue (JSQ-33 via HOB)"
        }
        
        print("=" * 70)
        print("COMPLETE PATH ROUTE STRUCTURE (from current feed)")
        print("=" * 70)
        
        for route_id in sorted(route_stops.keys()):
            route_name = route_names.get(route_id, f"Route {route_id}")
            stops = sorted(route_stops[route_id])
            print(f"\n{route_name} (ID: {route_id})")
            print(f"  Serves {len(stops)} stops: {', '.join(stops)}")
        
        # Check specifically for Journal Square
        print("\n" + "=" * 70)
        print("JOURNAL SQUARE (26731) - Which routes serve this station?")
        print("=" * 70)
        
        for route_id, stops in route_stops.items():
            if "26731" in stops:
                route_name = route_names.get(route_id, f"Route {route_id}")
                print(f"  ✓ {route_name}")
        
        print("\n")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_routes()
