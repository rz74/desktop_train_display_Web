"""
Test script for PATH real-time arrivals using GTFS-RT feed.
Tests multiple PATH stations.
"""

import httpx
from datetime import datetime
from google.transit import gtfs_realtime_pb2

def get_station_arrivals(feed, stop_id, station_name):
    """Get arrivals for a specific station."""
    trains = []
    
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip = entity.trip_update
            route_id = trip.trip.route_id if hasattr(trip.trip, 'route_id') else 'PATH'
            
            for stop_update in trip.stop_time_update:
                if stop_update.stop_id == stop_id:
                    if stop_update.HasField('arrival'):
                        arrival_time = stop_update.arrival.time
                        now = int(datetime.now().timestamp())
                        minutes = int((arrival_time - now) / 60)
                        
                        if minutes >= 0:
                            trains.append({
                                'route': route_id,
                                'minutes': minutes,
                                'time': arrival_time
                            })
    
    trains.sort(key=lambda x: x['time'])
    
    print(f"PATH TRAIN - {station_name} (Stop {stop_id})")
    print("-" * 60)
    
    if trains:
        for train in trains[:5]:
            time_str = "Now" if train['minutes'] == 0 else f"{train['minutes']} min"
            print(f"  Route {train['route']} - {time_str}")
        print(f"  Total: {len(trains)} trains")
    else:
        print("  No data available")
    print()

def get_path_arrivals():
    url = "https://path.transitdata.nyc/gtfsrt"
    
    try:
        print("Fetching data from PATH GTFS-RT feed...")
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        print("=" * 60)
        print("PATH TRAIN - Testing Multiple Stations")
        print("=" * 60)
        print()
        
        stations = [
            ("26734", "World Trade Center"),
            ("26722", "14th Street"),
            ("26731", "Journal Square")
        ]
        
        for stop_id, station_name in stations:
            get_station_arrivals(feed, stop_id, station_name)
        
        print("=" * 60)
        
    except httpx.HTTPStatusError as e:
        print("=" * 60)
        print("PATH TRAIN - Connection Error")
        print("=" * 60)
        print(f"HTTP Error {e.response.status_code}: {e.response.reason_phrase}")
        print("`nNo data available")
        print("=" * 60)
    except Exception as e:
        print("=" * 60)
        print("PATH TRAIN - Error")
        print("=" * 60)
        print(f"Error: {e}")
        print("`nNo data available")
        print("=" * 60)

if __name__ == "__main__":
    get_path_arrivals()
