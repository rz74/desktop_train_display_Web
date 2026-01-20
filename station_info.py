"""
Unified station search and arrival information script.
Searches both MTA and PATH systems and displays combined arrivals.
"""

import sys
from underground import SubwayFeed
import httpx
from google.transit import gtfs_realtime_pb2

from mappings import (
    PATH_STATIONS,
    PATH_ROUTES,
    MTA_LINES,
    get_mta_station_name,
    get_mta_direction,
    get_path_route_name,
    calculate_minutes_until
)

# Common MTA stations with their stop IDs and primary feeds
MTA_COMMON_STATIONS = {
    "14th st": [("L03", "L", "14 St-Union Sq")],
    "14 st": [("L03", "L", "14 St-Union Sq")],
    "23rd st": [("A25", "A", "23 St"), ("L05", "L", "23 St")],
    "23 st": [("A25", "A", "23 St"), ("L05", "L", "23 St")],
    "34th st": [("A32", "A", "34 St-Penn Station")],
    "34 st": [("A32", "A", "34 St-Penn Station")],
    "42nd st": [("A42", "A", "42 St-Port Authority"), ("127", "1", "Times Sq-42 St")],
    "42 st": [("A42", "A", "42 St-Port Authority"), ("127", "1", "Times Sq-42 St")],
    "times square": [("127", "1", "Times Sq-42 St"), ("A42", "A", "42 St-Port Authority")],
    "times sq": [("127", "1", "Times Sq-42 St")],
    "fulton": [("A27", "A", "Fulton St")],
    "fulton st": [("A27", "A", "Fulton St")],
    "union square": [("L03", "L", "14 St-Union Sq"), ("R20", "N", "14 St-Union Sq")],
    "union sq": [("L03", "L", "14 St-Union Sq")],
    "penn station": [("A32", "A", "34 St-Penn Station")],
    "port authority": [("A42", "A", "42 St-Port Authority")],
}


def find_mta_stations(search_query):
    """
    Find MTA stations matching the search query.
    Returns list of (stop_id, feed, station_name) tuples.
    """
    matches = []
    search_lower = search_query.lower().strip()
    
    for station_key, station_data in MTA_COMMON_STATIONS.items():
        if search_lower in station_key or station_key in search_lower:
            matches.extend(station_data)
    
    return matches


def find_path_stations(search_query):
    """
    Find PATH stations matching the search query.
    Returns list of (stop_id, station_name) tuples.
    """
    matches = []
    search_lower = search_query.lower().strip()
    
    # Special aliases for PATH stations
    aliases = {
        'wtc': '26734',
        'hoboken': '26730',
        'hob': '26730',
        'journal square': '26731',
        'jsq': '26731',
        '33rd': '26724',
        '23rd': '26723',
        '14th': '26722',
    }
    
    # Check aliases first
    for alias, stop_id in aliases.items():
        if alias in search_lower:
            station_name = PATH_STATIONS.get(stop_id)
            if station_name and (stop_id, station_name) not in matches:
                matches.append((stop_id, station_name))
    
    # Also check station names
    for stop_id, station_name in PATH_STATIONS.items():
        if search_lower in station_name.lower():
            if (stop_id, station_name) not in matches:
                matches.append((stop_id, station_name))
    
    return matches


def get_mta_feed_for_lines(lines):
    """
    Determine which feed(s) to fetch based on lines.
    Returns list of feed names to fetch.
    """
    # Map lines to their feeds
    feed_map = {
        'A': ['A', 'C', 'E'],
        'B': ['B', 'D', 'F', 'M'],
        'G': ['G'],
        'J': ['J', 'Z'],
        'L': ['L'],
        'N': ['N', 'Q', 'R', 'W'],
        '1': ['1', '2', '3', '4', '5', '6', '7'],
        'S': ['S']
    }
    
    feeds_needed = set()
    for line in lines:
        for feed_key, feed_lines in feed_map.items():
            if line in feed_lines:
                feeds_needed.add(feed_key)
                break
    
    return list(feeds_needed)


def get_mta_arrivals(stop_id, feed_name, station_name):
    """
    Get MTA arrivals for a station from specific feed.
    Returns list of arrival dictionaries.
    """
    arrivals = []
    
    try:
        feed = SubwayFeed.get(feed_name)
        
        for entity in feed.entity:
            if hasattr(entity, 'trip_update') and entity.trip_update:
                trip = entity.trip_update
                route_id = trip.trip.route_id
                
                if route_id not in MTA_LINES:
                    continue
                
                if trip.stop_time_update:
                    for stop_update in trip.stop_time_update:
                        if stop_update.stop_id.startswith(stop_id):
                            if hasattr(stop_update, 'arrival') and stop_update.arrival:
                                arrival_time = stop_update.arrival.time
                                minutes = calculate_minutes_until(arrival_time)
                                
                                if minutes >= 0 and minutes < 60:  # Only show trains within an hour
                                    direction = get_mta_direction(stop_update.stop_id, route_id)
                                    arrivals.append({
                                        'agency': 'MTA',
                                        'line': route_id,
                                        'direction': direction,
                                        'minutes': minutes,
                                        'time': arrival_time
                                    })
    except Exception as e:
        print(f"  Error fetching MTA feed {feed_name}: {e}")
    
    return arrivals


def get_path_arrivals(stop_id, station_name):
    """
    Get PATH arrivals for a station.
    Returns list of arrival dictionaries.
    """
    arrivals = []
    url = "https://path.transitdata.nyc/gtfsrt"
    
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update
                route_id = trip.trip.route_id if hasattr(trip.trip, 'route_id') else 'PATH'
                
                for stop_update in trip.stop_time_update:
                    if stop_update.stop_id == stop_id:
                        if stop_update.HasField('arrival'):
                            arrival_time = stop_update.arrival.time
                            minutes = calculate_minutes_until(arrival_time)
                            
                            if minutes >= 0:
                                route_name = get_path_route_name(route_id)
                                arrivals.append({
                                    'agency': 'PATH',
                                    'line': route_name,
                                    'direction': '',
                                    'minutes': minutes,
                                    'time': arrival_time
                                })
    except Exception as e:
        print(f"Error fetching PATH data: {e}")
    
    return arrivals


def format_time(minutes):
    """Format minutes into display string."""
    if minutes == 0:
        return "Due"
    elif minutes == 1:
        return "1 min"
    else:
        return f"{minutes} min"


def display_arrivals(station_name, arrivals):
    """
    Display arrivals in a clean e-ink friendly format.
    """
    print("=" * 50)
    print(f"STATION: {station_name.upper()}")
    print("=" * 50)
    
    if not arrivals:
        print("No arrivals found at this time.")
    else:
        # Sort by minutes
        arrivals.sort(key=lambda x: x['minutes'])
        
        # Display up to 10 arrivals
        for arrival in arrivals[:10]:
            if arrival['agency'] == 'MTA':
                line_display = f"MTA-{arrival['line']}"
                direction = arrival['direction'][:15]  # Truncate long directions
                print(f"[{line_display:8s}] {direction:20s} - {format_time(arrival['minutes'])}")
            else:  # PATH
                line_display = f"PATH"
                route_info = arrival['line'][:20]
                print(f"[{line_display:8s}] {route_info:20s} - {format_time(arrival['minutes'])}")
        
        if len(arrivals) > 10:
            print(f"\n... and {len(arrivals) - 10} more arrivals")
    
    print("=" * 50)


def search_station(query):
    """
    Main search function - finds and displays arrivals for a station.
    """
    if not query:
        print("Usage: python station_info.py \"<station name>\"")
        print("Example: python station_info.py \"14th St\"")
        return
    
    print(f"Searching for: {query}")
    print()
    
    # Search both systems
    mta_matches = find_mta_stations(query)
    path_matches = find_path_stations(query)
    
    if not mta_matches and not path_matches:
        print(f"No stations found matching '{query}'")
        print("\nTry searching for:")
        print("  - MTA: 'Fulton', '14th St', '42nd St', 'Times Sq'")
        print("  - PATH: 'WTC', 'Hoboken', 'Journal Square', '33rd St'")
        return
    
    # Process all matches
    all_arrivals = []
    station_display_name = query
    
    # Get MTA arrivals
    if mta_matches:
        print(f"Found {len(mta_matches)} MTA match(es)")
        for stop_id, feed_name, station_name in mta_matches:
            station_display_name = station_name
            print(f"  Fetching MTA arrivals for {station_name}...")
            mta_arrivals = get_mta_arrivals(stop_id, feed_name, station_name)
            all_arrivals.extend(mta_arrivals)
    
    # Get PATH arrivals
    if path_matches:
        print(f"Found {len(path_matches)} PATH station(s)")
        for stop_id, station_name in path_matches:
            if not mta_matches:  # Only update if we didn't find MTA
                station_display_name = station_name
            else:
                station_display_name += " / " + station_name
            print(f"  Fetching PATH arrivals for {station_name}...")
            path_arrivals = get_path_arrivals(stop_id, station_name)
            all_arrivals.extend(path_arrivals)
    
    print()
    
    # Display combined results
    display_arrivals(station_display_name, all_arrivals)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python station_info.py \"<station name>\"")
        print("\nExamples:")
        print("  python station_info.py \"14th St\"")
        print("  python station_info.py \"WTC\"")
        print("  python station_info.py \"Times Square\"")
        print("  python station_info.py \"Fulton\"")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    search_station(query)
