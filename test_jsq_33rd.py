#!/usr/bin/env python3
"""
Test script for all stations on PATH JSQ-33rd (Blue) line
Shows both MTA and PATH trains at dual-system stations
"""

import httpx
from google.transit import gtfs_realtime_pb2
from underground import SubwayFeed
from mappings import PATH_ROUTES, MTA_LINES, calculate_minutes_until, get_eastern_time, get_mta_direction

PATH_FEED_URL = "https://path.transitdata.nyc/gtfsrt"

# JSQ-33rd (Blue) line stations in order
# Format: (path_stop_id, station_name, mta_stop_id, mta_feed)
JSQ_33RD_STATIONS = [
    (26731, "Journal Square", None, None),
    (26732, "Grove Street", None, None),
    (26733, "Newport", None, None),
    (26735, "Exchange Place", None, None),
    (26734, "World Trade Center", "E01", "A"),  # Has MTA A/C/E trains
    (26727, "Christopher Street", None, None),
    (26728, "9th Street", None, None),
    (26722, "14th Street", "L03", "L"),  # Has MTA L train
    (26723, "23rd Street", "A25", "A"),  # Has MTA C/E trains (using A feed which includes C/E)
    (26724, "33rd Street", None, None)
]

def get_mta_arrivals(feed, stop_id, station_name):
    """Get arrival times for a specific MTA station"""
    arrivals = []
    
    if not feed or not hasattr(feed, 'entity'):
        return arrivals
    
    for entity in feed.entity:  # Use feed.entity instead of just feed
        if hasattr(entity, 'trip_update') and entity.trip_update:
            trip = entity.trip_update.trip
            route_id = trip.route_id
            
            if not entity.trip_update.stop_time_update:
                continue
                
            for stop_time in entity.trip_update.stop_time_update:
                if stop_time.stop_id.startswith(stop_id):
                    if hasattr(stop_time, 'arrival') and stop_time.arrival:
                        arrival_time = stop_time.arrival.time
                        minutes = calculate_minutes_until(arrival_time)
                        
                        if minutes >= 0:  # Only show future arrivals
                            route_name = MTA_LINES.get(route_id, route_id)
                            direction = get_mta_direction(stop_time.stop_id, route_id)
                            
                            arrivals.append({
                                'system': 'MTA',
                                'route': route_name,
                                'direction': direction,
                                'minutes': minutes,
                                'time': arrival_time
                            })
    
    return arrivals

def get_path_arrivals(feed, stop_id):
    """Get arrival times for a specific PATH station"""
    arrivals = []
    
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip = entity.trip_update.trip
            route_id = trip.route_id
            
            for stop_time in entity.trip_update.stop_time_update:
                if str(stop_time.stop_id) == str(stop_id):
                    if stop_time.HasField('arrival'):
                        arrival_time = stop_time.arrival.time
                        minutes = calculate_minutes_until(arrival_time)
                        
                        route_name = PATH_ROUTES.get(route_id, route_id)
                        
                        arrivals.append({
                            'system': 'PATH',
                            'route': route_name,
                            'direction': '',
                            'minutes': minutes,
                            'time': arrival_time
                        })
    
    return arrivals

def main():
    print("=" * 60)
    print("PATH JSQ-33rd (BLUE LINE) - ALL STATIONS TEST")
    print(f"Current time: {get_eastern_time().strftime('%I:%M:%S %p ET')}")
    print("=" * 60)
    print()
    
    try:
        # Fetch the PATH GTFS-RT feed
        response = httpx.get(PATH_FEED_URL, timeout=10.0)
        response.raise_for_status()
        
        path_feed = gtfs_realtime_pb2.FeedMessage()
        path_feed.ParseFromString(response.content)
        
        # Cache for MTA feeds
        mta_feeds = {}
        
        # Test each station on the JSQ-33rd line
        for path_stop_id, station_name, mta_stop_id, mta_feed_name in JSQ_33RD_STATIONS:
            all_arrivals = []
            
            # Get PATH arrivals
            path_arrivals = get_path_arrivals(path_feed, path_stop_id)
            all_arrivals.extend(path_arrivals)
            
            # Get MTA arrivals if this station has MTA service
            if mta_stop_id and mta_feed_name:
                if mta_feed_name not in mta_feeds:
                    mta_feeds[mta_feed_name] = SubwayFeed.get(mta_feed_name)
                
                mta_arrivals = get_mta_arrivals(mta_feeds[mta_feed_name], mta_stop_id, station_name)
                all_arrivals.extend(mta_arrivals)
            
            # Sort all arrivals by time
            all_arrivals = sorted(all_arrivals, key=lambda x: x['minutes'])
            
            # Display station info
            system_info = ""
            if mta_stop_id:
                system_info = " [MTA + PATH]"
            else:
                system_info = " [PATH only]"
            
            print(f"📍 {station_name}{system_info} (PATH: {path_stop_id})")
            print("-" * 60)
            
            if all_arrivals:
                print(f"  Found {len(all_arrivals)} arrival(s):")
                for i, arrival in enumerate(all_arrivals[:10], 1):  # Show up to 10 trains
                    minutes_str = "Due" if arrival['minutes'] == 0 else f"{arrival['minutes']} min"
                    
                    if arrival['system'] == 'MTA':
                        system_route = f"MTA-{arrival['route']}"
                        direction = arrival['direction'][:20]
                        print(f"    {i}. [{system_route:<8}] {direction:<20} - {minutes_str}")
                    else:
                        route_name = arrival['route']
                        print(f"    {i}. [PATH    ] {route_name:<20} - {minutes_str}")
                
                if len(all_arrivals) > 10:
                    print(f"    ... and {len(all_arrivals) - 10} more")
            else:
                print("  ⚠️  No arrivals found")
            
            print()
        
        print("=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        
    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
