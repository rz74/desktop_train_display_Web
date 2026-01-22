#!/usr/bin/env python3
"""
Unified arrival script for NYC/NJ transit.
Intelligently routes queries to MTA, PATH, or both systems.
"""

import sys
import difflib
import httpx
from underground import SubwayFeed
from google.transit import gtfs_realtime_pb2

from mappings import (
    PATH_STATIONS,
    PATH_ROUTES,
    MTA_LINES,
    get_mta_direction,
    calculate_minutes_until,
    get_eastern_time
)

# Comprehensive MTA station mappings
# Format: {search_key: [(stop_id, feed_name, display_name), ...]}
MTA_STATIONS = {
    "world trade center": [("E01", "A", "World Trade Center")],
    "wtc": [("E01", "A", "World Trade Center")],
    "fulton": [("A27", "A", "Fulton St")],
    "fulton st": [("A27", "A", "Fulton St")],
    "14th st": [("L03", "L", "14 St-Union Sq"), ("R20", "N", "14 St-Union Sq")],
    "14 st": [("L03", "L", "14 St-Union Sq")],
    "union square": [("L03", "L", "14 St-Union Sq"), ("R20", "N", "14 St-Union Sq")],
    "union sq": [("L03", "L", "14 St-Union Sq")],
    "23rd st": [("A25", "A", "23 St"), ("L05", "L", "23 St")],
    "23 st": [("A25", "A", "23 St"), ("L05", "L", "23 St")],
    "34th st": [("A32", "A", "34 St-Penn Station")],
    "34 st": [("A32", "A", "34 St-Penn Station")],
    "penn station": [("A32", "A", "34 St-Penn Station")],
    "33rd st": [("A32", "A", "34 St-Penn Station")],
    "33 st": [("A32", "A", "34 St-Penn Station")],
    "42nd st": [("A42", "A", "42 St-Port Authority"), ("127", "1", "Times Sq-42 St")],
    "42 st": [("A42", "A", "42 St-Port Authority"), ("127", "1", "Times Sq-42 St")],
    "times square": [("127", "1", "Times Sq-42 St"), ("A42", "A", "42 St-Port Authority")],
    "times sq": [("127", "1", "Times Sq-42 St")],
    "port authority": [("A42", "A", "42 St-Port Authority")],
}

# Dual-system station mappings
DUAL_SYSTEM_STATIONS = {
    "world trade center": {
        "mta": [("E01", "A", "World Trade Center")],
        "path": (26734, "World Trade Center")
    },
    "wtc": {
        "mta": [("E01", "A", "World Trade Center")],
        "path": (26734, "World Trade Center")
    },
    "14th st": {
        "mta": [("L03", "L", "14 St-Union Sq")],
        "path": (26722, "14th Street")
    },
    "14 st": {
        "mta": [("L03", "L", "14 St-Union Sq")],
        "path": (26722, "14th Street")
    },
    "23rd st": {
        "mta": [("A25", "A", "23 St"), ("L05", "L", "23 St")],
        "path": (26723, "23rd Street")
    },
    "23 st": {
        "mta": [("A25", "A", "23 St")],
        "path": (26723, "23rd Street")
    },
    "33rd st": {
        "mta": [("A32", "A", "34 St-Penn Station")],
        "path": (26724, "33rd Street")
    },
    "33 st": {
        "mta": [("A32", "A", "34 St-Penn Station")],
        "path": (26724, "33rd Street")
    },
}

PATH_FEED_URL = "https://path.transitdata.nyc/gtfsrt"

def fuzzy_match_station(query, station_dict):
    """Use fuzzy matching to find station in dictionary"""
    query_lower = query.lower().strip()
    
    # Exact match first
    if query_lower in station_dict:
        return query_lower, station_dict[query_lower]
    
    # Substring match
    for key in station_dict:
        if query_lower in key or key in query_lower:
            return key, station_dict[key]
    
    # Fuzzy match
    matches = difflib.get_close_matches(query_lower, station_dict.keys(), n=1, cutoff=0.6)
    if matches:
        return matches[0], station_dict[matches[0]]
    
    return None, None

def get_mta_arrivals(stop_id, feed_name, station_name):
    """Fetch MTA arrivals for a specific station"""
    arrivals = []
    
    try:
        feed = SubwayFeed.get(feed_name)
        
        if not feed or not hasattr(feed, 'entity'):
            return arrivals
        
        for entity in feed.entity:
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
                            
                            if minutes >= 0:
                                route_name = MTA_LINES.get(route_id, route_id)
                                direction = get_mta_direction(stop_time.stop_id, route_id)
                                
                                arrivals.append({
                                    'agency': 'MTA',
                                    'route': route_name,
                                    'destination': direction,
                                    'minutes': minutes,
                                    'time': arrival_time
                                })
    except Exception as e:
        print(f"  ⚠️  MTA Error: {e}")
    
    return arrivals

def get_path_arrivals(stop_id, station_name):
    """Fetch PATH arrivals for a specific station"""
    arrivals = []
    
    try:
        response = httpx.get(PATH_FEED_URL, timeout=10.0)
        response.raise_for_status()
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip = entity.trip_update.trip
                route_id = trip.route_id
                
                for stop_time in entity.trip_update.stop_time_update:
                    if str(stop_time.stop_id) == str(stop_id):
                        if stop_time.HasField('arrival'):
                            arrival_time = stop_time.arrival.time
                            minutes = calculate_minutes_until(arrival_time)
                            
                            if minutes >= 0:
                                route_name = PATH_ROUTES.get(route_id, route_id)
                                
                                arrivals.append({
                                    'agency': 'PATH',
                                    'route': route_name,
                                    'destination': '',
                                    'minutes': minutes,
                                    'time': arrival_time
                                })
    except Exception as e:
        print(f"  ⚠️  PATH Error: {e}")
    
    return arrivals

def detect_station_type(query):
    """Determine if station is MTA, PATH, or dual-system"""
    query_lower = query.lower().strip()
    
    # Check dual-system first
    dual_key, dual_info = fuzzy_match_station(query, DUAL_SYSTEM_STATIONS)
    if dual_key:
        return "DUAL", dual_info
    
    # Check MTA
    mta_key, mta_info = fuzzy_match_station(query, MTA_STATIONS)
    
    # Check PATH
    path_key = None
    path_info = None
    for stop_id, name in PATH_STATIONS.items():
        name_lower = name.lower()
        if query_lower in name_lower or name_lower in query_lower:
            path_key = name_lower
            path_info = (stop_id, name)
            break
    
    # Also check PATH aliases
    path_aliases = {
        "wtc": (26734, "World Trade Center"),
        "hob": (26730, "Hoboken"),
        "hoboken": (26730, "Hoboken"),
        "jsq": (26731, "Journal Square"),
        "journal square": (26731, "Journal Square"),
        "grove": (26732, "Grove Street"),
        "newport": (26733, "Newport"),
        "exchange place": (26735, "Exchange Place"),
        "christopher": (26727, "Christopher Street"),
        "9th": (26728, "9th Street"),
        "14th": (26722, "14th Street"),
        "23rd": (26723, "23rd Street"),
        "33rd": (26724, "33rd Street")
    }
    
    if not path_info:
        path_key, path_info = fuzzy_match_station(query, path_aliases)
    
    # Determine type
    if mta_info and path_info:
        return "DUAL", {"mta": mta_info, "path": path_info}
    elif mta_info:
        return "MTA", mta_info
    elif path_info:
        return "PATH", path_info
    else:
        return "NONE", None

def format_arrival(arrival):
    """Format a single arrival for e-ink display"""
    minutes_str = "Due" if arrival['minutes'] == 0 else f"{arrival['minutes']} min"
    
    if arrival['agency'] == 'MTA':
        route = f"MTA-{arrival['route']}"
        dest = arrival['destination'][:20]
        return f"[{route:<8}] {dest:<20} - {minutes_str}"
    else:  # PATH
        route_name = arrival['route'][:20]
        return f"[PATH    ] {route_name:<20} - {minutes_str}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python unified_arrival.py <station_name>")
        print("\nExamples:")
        print("  python unified_arrival.py \"WTC\"")
        print("  python unified_arrival.py \"14th St\"")
        print("  python unified_arrival.py \"Times Square\"")
        print("  python unified_arrival.py \"Hoboken\"")
        return
    
    query = " ".join(sys.argv[1:])
    
    print("=" * 60)
    print(f"UNIFIED ARRIVAL LOOKUP")
    print(f"Current time: {get_eastern_time().strftime('%I:%M:%S %p ET')}")
    print("=" * 60)
    print(f"Searching for: {query}")
    print()
    
    # Detect station type
    station_type, station_info = detect_station_type(query)
    
    if station_type == "NONE":
        print("❌ No station found matching your query.")
        print("\nDid you mean one of these?")
        
        # Show close matches
        all_stations = list(MTA_STATIONS.keys()) + list(PATH_STATIONS.values())
        close = difflib.get_close_matches(query.lower(), 
                                         [s.lower() for s in all_stations], 
                                         n=5, cutoff=0.4)
        for match in close:
            print(f"  - {match}")
        return
    
    # Display station mode
    print(f"Station Mode: {station_type}")
    print("-" * 60)
    
    all_arrivals = []
    station_display_name = query
    
    # Fetch arrivals based on type
    if station_type == "DUAL":
        print("Fetching from both MTA and PATH systems...")
        
        # Get MTA arrivals
        mta_stations = station_info.get("mta", [])
        for stop_id, feed_name, name in mta_stations:
            station_display_name = name
            print(f"  → MTA: {name} (Stop {stop_id}, Feed {feed_name})")
            arrivals = get_mta_arrivals(stop_id, feed_name, name)
            all_arrivals.extend(arrivals)
        
        # Get PATH arrivals
        if "path" in station_info:
            path_stop_id, path_name = station_info["path"]
            print(f"  → PATH: {path_name} (Stop {path_stop_id})")
            arrivals = get_path_arrivals(path_stop_id, path_name)
            all_arrivals.extend(arrivals)
    
    elif station_type == "MTA":
        print("Fetching from MTA system...")
        for stop_id, feed_name, name in station_info:
            station_display_name = name
            print(f"  → {name} (Stop {stop_id}, Feed {feed_name})")
            arrivals = get_mta_arrivals(stop_id, feed_name, name)
            all_arrivals.extend(arrivals)
    
    elif station_type == "PATH":
        print("Fetching from PATH system...")
        stop_id, name = station_info
        station_display_name = name
        print(f"  → {name} (Stop {stop_id})")
        arrivals = get_path_arrivals(stop_id, name)
        all_arrivals.extend(arrivals)
    
    # Sort arrivals chronologically
    all_arrivals = sorted(all_arrivals, key=lambda x: x['minutes'])
    
    print()
    print("=" * 60)
    print(f"ARRIVALS: {station_display_name.upper()}")
    print("=" * 60)
    
    if all_arrivals:
        display_count = min(15, len(all_arrivals))
        for i, arrival in enumerate(all_arrivals[:display_count], 1):
            print(f"{i:2d}. {format_arrival(arrival)}")
        
        if len(all_arrivals) > display_count:
            print(f"\n... and {len(all_arrivals) - display_count} more arrivals")
        
        print("=" * 60)
        print(f"Total: {len(all_arrivals)} arrivals")
    else:
        print("⚠️  No arrivals found at this time")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
