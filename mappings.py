"""
Comprehensive mapping system for MTA Subway and PATH transit data.
Provides station names, route information, and direction mappings.
"""

from underground import metadata

# ============================================================================
# MTA SUBWAY MAPPINGS
# ============================================================================

MTA_LINES = {
    '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
    'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G',
    'J': 'J', 'L': 'L', 'M': 'M', 'N': 'N', 'Q': 'Q', 'R': 'R', 'S': 'S',
    'W': 'W', 'Z': 'Z'
}

# Direction suffixes for MTA stations
# N = Northbound/Uptown, S = Southbound/Downtown
def get_mta_direction(stop_id, route_id):
    """
    Determine direction based on stop_id suffix.
    N suffix = Uptown/Northbound
    S suffix = Downtown/Southbound
    """
    if stop_id.endswith('N'):
        # Northbound routes
        if route_id in ['1', '2', '3', '4', '5', '6', '7']:
            return 'Uptown/Bronx'
        elif route_id in ['A', 'C', 'E', 'B', 'D', 'F', 'M']:
            return 'Uptown/Manhattan'
        elif route_id in ['G', 'L', 'J', 'Z']:
            return 'Manhattan Bound'
        elif route_id in ['N', 'Q', 'R', 'W']:
            return 'Manhattan/Queens'
        else:
            return 'Northbound'
    elif stop_id.endswith('S'):
        # Southbound routes
        if route_id in ['1', '2', '3', '4', '5', '6', '7']:
            return 'Downtown/Brooklyn'
        elif route_id in ['A', 'C', 'E', 'B', 'D', 'F', 'M']:
            return 'Downtown/Brooklyn'
        elif route_id in ['G', 'L', 'J', 'Z']:
            return 'Brooklyn/Queens'
        elif route_id in ['N', 'Q', 'R', 'W']:
            return 'Brooklyn/Queens'
        else:
            return 'Southbound'
    else:
        return 'Unknown Direction'

def get_mta_station_name(stop_id):
    """
    Get station name from underground library metadata.
    Returns cleaned station name without direction suffix.
    """
    # Remove directional suffix for lookup
    base_stop_id = stop_id.rstrip('NS')
    
    # Try to get from metadata
    try:
        station_info = metadata.stops.get(stop_id, {})
        if station_info and 'stop_name' in station_info:
            return station_info['stop_name']
        
        # Try without suffix
        station_info = metadata.stops.get(base_stop_id, {})
        if station_info and 'stop_name' in station_info:
            return station_info['stop_name']
    except:
        pass
    
    # Fallback to stop ID
    return f"Stop {stop_id}"

# ============================================================================
# PATH MAPPINGS
# ============================================================================

PATH_STATIONS = {
    "26722": "14th St",
    "26723": "23rd St",
    "26724": "33rd St",
    "26725": "9th St",
    "26726": "Christopher St",
    "26727": "Exchange Place",
    "26728": "Grove St",
    "26729": "Harrison",
    "26730": "Hoboken",
    "26731": "Journal Square",
    "26732": "Newark",
    "26733": "Newport",
    "26734": "World Trade Center"
}

PATH_ROUTES = {
    "859": "Green (HOB-WTC)",
    "860": "Red (NWK-WTC)",
    "861": "Yellow (JSQ-33)",
    "862": "Blue (JSQ-33 via HOB)",
    "1024": "Blue (JSQ-33 via HOB)"
}

def get_path_station_name(stop_id):
    """Get PATH station name from stop ID."""
    return PATH_STATIONS.get(stop_id, f"Stop {stop_id}")

def get_path_route_name(route_id):
    """Get PATH route name with color coding."""
    return PATH_ROUTES.get(route_id, f"Route {route_id}")

def get_path_direction(route_id):
    """Get general direction description for PATH route."""
    route_name = PATH_ROUTES.get(route_id, "")
    
    if "HOB-WTC" in route_name:
        return "Manhattan"
    elif "NWK-WTC" in route_name:
        return "Manhattan"
    elif "JSQ-33" in route_name:
        return "Manhattan"
    else:
        return "Various"

# ============================================================================
# TIMEZONE UTILITIES
# ============================================================================

from datetime import datetime
import pytz

def get_eastern_time():
    """Get current time in US/Eastern timezone."""
    eastern = pytz.timezone('America/New_York')
    return datetime.now(eastern)

def convert_to_eastern(timestamp):
    """Convert UTC timestamp to US/Eastern timezone."""
    eastern = pytz.timezone('America/New_York')
    
    if isinstance(timestamp, datetime):
        # If already a datetime object, ensure it has timezone
        if timestamp.tzinfo is None:
            timestamp = pytz.utc.localize(timestamp)
        return timestamp.astimezone(eastern)
    else:
        # If it's a Unix timestamp (int/float)
        utc_time = datetime.fromtimestamp(timestamp, tz=pytz.utc)
        return utc_time.astimezone(eastern)

def calculate_minutes_until(arrival_time):
    """
    Calculate minutes until arrival, properly handling US/Eastern timezone.
    
    Args:
        arrival_time: Either a datetime object or Unix timestamp
    
    Returns:
        Integer minutes until arrival
    """
    current_time = get_eastern_time()
    arrival_eastern = convert_to_eastern(arrival_time)
    
    time_diff = (arrival_eastern - current_time).total_seconds()
    return int(time_diff / 60)
