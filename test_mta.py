"""
Test script for NYC Subway (MTA) real-time arrivals using the underground library.
Tests multiple stations on the ACE lines.
"""

from underground import metadata, SubwayFeed
from datetime import datetime, timezone

def get_station_arrivals(feed, stop_id, station_name):
    """Get arrivals for a specific station."""
    arrivals = []
    
    for entity in feed.entity:
        if hasattr(entity, 'trip_update') and entity.trip_update:
            trip = entity.trip_update
            route_id = trip.trip.route_id
            
            # Get destination (last stop)
            destination = "Unknown"
            if trip.stop_time_update and len(trip.stop_time_update) > 0:
                last_stop = trip.stop_time_update[-1].stop_id
                try:
                    destination = metadata.stops.get(last_stop, {}).get('stop_name', last_stop)
                except:
                    destination = last_stop
            
            # Check each stop time update for our target stop
            if trip.stop_time_update:
                for stop_update in trip.stop_time_update:
                    if stop_update.stop_id.startswith(stop_id):
                        if hasattr(stop_update, 'arrival') and stop_update.arrival:
                            arrival_time = stop_update.arrival.time
                            
                            # Handle both timestamp (int) and datetime objects
                            if isinstance(arrival_time, datetime):
                                now = datetime.now(timezone.utc)
                                if arrival_time.tzinfo is None:
                                    arrival_time = arrival_time.replace(tzinfo=timezone.utc)
                                minutes = int((arrival_time - now).total_seconds() / 60)
                            else:
                                now = int(datetime.now().timestamp())
                                minutes = int((arrival_time - now) / 60)
                            
                            if minutes >= 0:
                                sort_key = arrival_time.timestamp() if isinstance(arrival_time, datetime) else arrival_time
                                arrivals.append({
                                    'line': route_id,
                                    'destination': destination,
                                    'minutes': minutes,
                                    'time': sort_key
                                })
    
    # Sort by arrival time and get next 5
    arrivals.sort(key=lambda x: x['time'])
    next_arrivals = arrivals[:5]
    
    # Print results
    print(f"NYC SUBWAY - {station_name} ({stop_id})")
    print("-" * 60)
    
    if next_arrivals:
        for arrival in next_arrivals:
            dest = arrival['destination']
            if not any(char.isalpha() and char.islower() for char in dest):
                dest = f"Stop {dest}"
            print(f"  [{arrival['line']}] {dest[:28]:28s} - {arrival['minutes']} min")
        print(f"  Total: {len(arrivals)} arrivals")
    else:
        print("  No upcoming arrivals found.")
    print()

def get_mta_arrivals():
    # Initialize the ACE subway feed
    feed = SubwayFeed.get("A")
    
    # Test multiple stations
    stations = [
        ("A27", "Fulton St"),
        ("A32", "34 St-Penn Station"),
        ("A42", "42 St-Port Authority")
    ]
    
    print("=" * 60)
    print("NYC SUBWAY - Testing Multiple Stations")
    print("=" * 60)
    print()
    
    for stop_id, station_name in stations:
        get_station_arrivals(feed, stop_id, station_name)
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        get_mta_arrivals()
    except Exception as e:
        print(f"Error fetching MTA data: {e}")
        print("\nMake sure you have an active internet connection.")
