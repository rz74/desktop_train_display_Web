#!/usr/bin/env python3
"""
Debug script to see actual PATH route IDs in the feed
"""

import httpx
from google.transit import gtfs_realtime_pb2

PATH_FEED_URL = "https://path.transitdata.nyc/gtfsrt"

def debug_path_feed():
    try:
        response = httpx.get(PATH_FEED_URL, timeout=10.0)
        response.raise_for_status()
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        route_ids = set()
        stop_ids = set()
        
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update.trip
                route_id = trip.route_id
                route_ids.add(route_id)
                
                for stop_time in entity.trip_update.stop_time_update:
                    stop_id = str(stop_time.stop_id)
                    stop_ids.add(stop_id)
        
        print("=" * 60)
        print("PATH FEED DEBUG INFO")
        print("=" * 60)
        print(f"\nFound {len(route_ids)} unique route IDs:")
        for rid in sorted(route_ids):
            print(f"  - {rid}")
        
        print(f"\nFound {len(stop_ids)} unique stop IDs:")
        for sid in sorted(stop_ids):
            print(f"  - {sid}")
        
        print("\n" + "=" * 60)
        print("Sample arrivals at Grove St (26732):")
        print("=" * 60)
        
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update.trip
                route_id = trip.route_id
                
                for stop_time in entity.trip_update.stop_time_update:
                    if str(stop_time.stop_id) == "26732":
                        if stop_time.HasField('arrival'):
                            print(f"Route ID: {route_id}, Trip ID: {trip.trip_id}")
                            break
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_path_feed()
