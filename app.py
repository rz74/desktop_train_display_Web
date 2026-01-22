"""
FastAPI web server for e-ink transit dashboard.
Provides API endpoints for station search, line selection, and live arrivals.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import difflib
import httpx
import json
import os
from underground import SubwayFeed
from google.transit import gtfs_realtime_pb2

from mappings import (
    PATH_STATIONS,
    PATH_ROUTES,
    PATH_ROUTES_ABBREV,
    PATH_STATION_ROUTES,
    get_path_direction,
    MTA_LINES,
    get_mta_direction,
    get_mta_station_name,
    calculate_minutes_until,
    get_eastern_time
)

app = FastAPI(title="E-Ink Transit Dashboard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load comprehensive MTA station database
MTA_STATIONS = {}
json_path = os.path.join(os.path.dirname(__file__), 'all_mta_stations.json')
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        loaded_data = json.load(f)
        # Convert from JSON format to tuple format
        for key, value in loaded_data.items():
            MTA_STATIONS[key] = [tuple(item) for item in value]
    print(f"✓ Loaded {len(MTA_STATIONS)} MTA stations from all_mta_stations.json")
else:
    print("⚠ all_mta_stations.json not found, using fallback stations")
    # Fallback to minimal set if JSON not available
    MTA_STATIONS = {
        "times square": [("725", "1", "Times Sq-42 St")],
        "union square": [("635", "1", "14 St-Union Sq")],
        "grand central": [("631", "1", "Grand Central-42 St")],
    }

# Load static station-to-lines mapping (fallback for when real-time feed is empty)
STATION_LINES_MAP = {}
lines_map_path = os.path.join(os.path.dirname(__file__), 'station_lines_map.json')
if os.path.exists(lines_map_path):
    with open(lines_map_path, 'r') as f:
        STATION_LINES_MAP = json.load(f)
    print(f"✓ Loaded static lines mapping for {len(STATION_LINES_MAP)} stations")

DUAL_SYSTEM_STATIONS = {
    "world trade center": {
        "mta": [
            ("E01", "A", "World Trade Center"),  # E train
            ("138", "1", "WTC Cortlandt"),  # 1 train
            ("R25", "N", "Cortlandt St")  # N, R, W trains
        ],
        "path": (26734, "World Trade Center")
    },
    "wtc": {
        "mta": [
            ("E01", "A", "World Trade Center"),  # E train
            ("138", "1", "WTC Cortlandt"),  # 1 train
            ("R25", "N", "Cortlandt St")  # N, R, W trains
        ],
        "path": (26734, "World Trade Center")
    },
    "christopher st": {
        "mta": [("133", "1", "Christopher St")],
        "path": (26726, "Christopher Street")
    },
    "christopher street": {
        "mta": [("133", "1", "Christopher St")],
        "path": (26726, "Christopher Street")
    },
    "14th st": {
        "mta": [
            ("128", "1", "14 St"),  # 1, 2, 3 trains
            ("A31", "A", "14 St"),  # A, C, E trains
            ("D14", "D", "14 St")  # B, D, F, M trains
        ],
        "path": (26722, "14th Street")
    },
    "14 st": {
        "mta": [
            ("128", "1", "14 St"),  # 1, 2, 3 trains
            ("A31", "A", "14 St"),  # A, C, E trains
            ("D14", "D", "14 St")  # B, D, F, M trains
        ],
        "path": (26722, "14th Street")
    },
    "23rd st": {
        "mta": [("D18", "D", "23 St")],  # B, D, F, M trains
        "path": (26723, "23rd Street")
    },
    "23 st": {
        "mta": [("D18", "D", "23 St")],  # B, D, F, M trains
        "path": (26723, "23rd Street")
    },
    "33rd st": {
        "mta": [
            ("D17", "D", "34 St-Herald Sq"),  # B, D, F, M trains
            ("R17", "N", "34 St-Herald Sq")  # N, Q, R, W trains
        ],
        "path": (26724, "33rd Street")
    },
    "33 st": {
        "mta": [
            ("D17", "D", "34 St-Herald Sq"),  # B, D, F, M trains
            ("R17", "N", "34 St-Herald Sq")  # N, Q, R, W trains
        ],
        "path": (26724, "33rd Street")
    },
    "34 st-herald sq": {
        "mta": [
            ("D17", "D", "34 St-Herald Sq"),  # B, D, F, M trains
            ("R17", "N", "34 St-Herald Sq")  # N, Q, R, W trains
        ],
        "path": (26724, "33rd Street")
    },
    "christopher st-stonewall": {
        "mta": [("133", "1", "Christopher St-Stonewall")],
        "path": (26726, "Christopher Street")
    }
}

PATH_FEED_URL = "https://path.transitdata.nyc/gtfsrt"

# Request/Response models
class ArrivalRequest(BaseModel):
    station_id: str
    selected_lines: List[str]
    max_minutes: Optional[int] = 20  # Default to 20 minutes

class StationResult(BaseModel):
    id: str
    name: str
    type: str  # "MTA", "PATH", or "DUAL"

class LineInfo(BaseModel):
    line_id: str
    line_name: str
    agency: str  # "MTA" or "PATH"

class Arrival(BaseModel):
    agency: str
    route: str
    destination: str
    minutes: int

def fuzzy_match_station(query):
    """Find matching stations using fuzzy matching"""
    query_lower = query.lower().strip()
    results = []
    seen = set()
    
    # Check dual-system stations first (priority)
    for key, info in DUAL_SYSTEM_STATIONS.items():
        if query_lower in key or key in query_lower:
            if "mta" in info:
                station_name = info["mta"][0][2]
            else:
                station_name = info["path"][1]
            if station_name not in seen:
                results.append(StationResult(
                    id=key,
                    name=station_name,
                    type="DUAL"
                ))
                seen.add(station_name)
    
    # Check MTA stations
    for key, stations in MTA_STATIONS.items():
        if query_lower in key or key in query_lower:
            for stop_id, feed, name in stations:
                if name not in seen:
                    results.append(StationResult(
                        id=key,
                        name=name,
                        type="MTA"
                    ))
                    seen.add(name)
                    break
    
    # Check PATH stations
    for stop_id, name in PATH_STATIONS.items():
        name_lower = name.lower()
        if query_lower in name_lower or name_lower in query_lower:
            if name not in seen:
                results.append(StationResult(
                    id=name_lower.replace(" ", "_"),
                    name=name,
                    type="PATH"
                ))
                seen.add(name)
    
    return results[:10]  # Return top 10 matches

def get_station_lines(station_id: str):
    """Get all lines available at a station"""
    lines = []
    station_id_lower = station_id.lower().replace("_", " ")
    routes_seen = set()
    
    # Check if dual-system
    if station_id_lower in DUAL_SYSTEM_STATIONS:
        info = DUAL_SYSTEM_STATIONS[station_id_lower]
        
        # Add MTA lines
        if "mta" in info:
            # First try real-time feed
            for stop_id, feed_name, name in info["mta"]:
                try:
                    feed = SubwayFeed.get(feed_name)
                    for entity in feed.entity:
                        if hasattr(entity, 'trip_update') and entity.trip_update:
                            trip = entity.trip_update.trip
                            route_id = trip.route_id
                            for stop_time in entity.trip_update.stop_time_update:
                                if stop_time.stop_id.startswith(stop_id):
                                    if route_id in MTA_LINES and route_id not in routes_seen:
                                        routes_seen.add(route_id)
                                        lines.append(LineInfo(
                                            line_id=f"MTA-{route_id}",
                                            line_name=f"MTA {route_id}",
                                            agency="MTA"
                                        ))
                                    break
                except:
                    pass
            
            # Always add static mapping for dual-system stations to ensure complete line list
            # Try station_id_lower first, then try the display name from mta info
            lookup_keys = [station_id_lower]
            if info["mta"]:
                # Also try the display name from the first MTA entry
                display_name = info["mta"][0][2].lower()  # "World Trade Center" -> "world trade center"
                if display_name not in lookup_keys:
                    lookup_keys.append(display_name)
            
            for lookup_key in lookup_keys:
                if lookup_key in STATION_LINES_MAP:
                    station_data = STATION_LINES_MAP[lookup_key]
                    for route_id in station_data.get('routes', []):
                        if route_id in MTA_LINES and route_id not in routes_seen:
                            routes_seen.add(route_id)
                            lines.append(LineInfo(
                                line_id=f"MTA-{route_id}",
                                line_name=f"MTA {route_id}",
                                agency="MTA"
                            ))
                    break  # Found it, stop looking
        
        # Add PATH routes - also use static fallback
        if "path" in info:
            path_stop_id = str(info["path"][0])
            path_routes_seen = set()
            # Check which routes actually serve this station from real-time
            try:
                import httpx
                response = httpx.get(PATH_FEED_URL, timeout=10.0)
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)
                
                for entity in feed.entity:
                    if entity.HasField('trip_update'):
                        route_id = entity.trip_update.trip.route_id
                        for stop_time in entity.trip_update.stop_time_update:
                            if str(stop_time.stop_id) == path_stop_id:
                                if route_id not in path_routes_seen:
                                    path_routes_seen.add(route_id)
                                    route_abbrev = PATH_ROUTES_ABBREV.get(route_id, route_id)
                                    lines.append(LineInfo(
                                        line_id=f"PATH-{route_id}",
                                        line_name=f"PATH {route_abbrev}",
                                        agency="PATH"
                                    ))
                                break
            except:
                pass
            
            # Always add static mapping for PATH at dual-system stations
            if path_stop_id in PATH_STATION_ROUTES:
                for route_id in PATH_STATION_ROUTES[path_stop_id]:
                    if route_id not in path_routes_seen:
                        route_abbrev = PATH_ROUTES_ABBREV.get(route_id, route_id)
                        lines.append(LineInfo(
                            line_id=f"PATH-{route_id}",
                            line_name=f"PATH {route_abbrev}",
                            agency="PATH"
                        ))
    
    # Check if MTA station
    elif station_id_lower in MTA_STATIONS:
        # First try real-time feed
        for stop_id, feed_name, name in MTA_STATIONS[station_id_lower]:
            try:
                feed = SubwayFeed.get(feed_name)
                for entity in feed.entity:
                    if hasattr(entity, 'trip_update') and entity.trip_update:
                        trip = entity.trip_update.trip
                        route_id = trip.route_id
                        for stop_time in entity.trip_update.stop_time_update:
                            if stop_time.stop_id.startswith(stop_id):
                                if route_id in MTA_LINES and route_id not in routes_seen:
                                    routes_seen.add(route_id)
                                    lines.append(LineInfo(
                                        line_id=f"MTA-{route_id}",
                                        line_name=f"MTA {route_id}",
                                        agency="MTA"
                                    ))
                                break
            except:
                pass
        
        # Always add static mapping to ensure complete line list
        if station_id_lower in STATION_LINES_MAP:
            station_data = STATION_LINES_MAP[station_id_lower]
            for route_id in station_data.get('routes', []):
                if route_id in MTA_LINES and route_id not in routes_seen:
                    routes_seen.add(route_id)
                    lines.append(LineInfo(
                        line_id=f"MTA-{route_id}",
                        line_name=f"MTA {route_id}",
                        agency="MTA"
                    ))
    
    # Check if PATH station
    else:
        # Try to match PATH station by name
        for path_stop_id, path_name in PATH_STATIONS.items():
            # Compare normalized names (both with spaces, no underscores)
            if station_id_lower == path_name.lower():
                path_routes_seen = set()
                # First try real-time feed
                try:
                    import httpx
                    response = httpx.get(PATH_FEED_URL, timeout=10.0)
                    feed = gtfs_realtime_pb2.FeedMessage()
                    feed.ParseFromString(response.content)
                    
                    for entity in feed.entity:
                        if entity.HasField('trip_update'):
                            route_id = entity.trip_update.trip.route_id
                            for stop_time in entity.trip_update.stop_time_update:
                                if str(stop_time.stop_id) == path_stop_id:
                                    if route_id not in path_routes_seen:
                                        path_routes_seen.add(route_id)
                                        route_abbrev = PATH_ROUTES_ABBREV.get(route_id, route_id)
                                        lines.append(LineInfo(
                                            line_id=f"PATH-{route_id}",
                                            line_name=f"PATH {route_abbrev}",
                                            agency="PATH"
                                        ))
                                    break
                except:
                    pass
                
                # Always add static mapping to ensure complete line list
                if path_stop_id in PATH_STATION_ROUTES:
                    for route_id in PATH_STATION_ROUTES[path_stop_id]:
                        if route_id not in path_routes_seen:
                            route_abbrev = PATH_ROUTES_ABBREV.get(route_id, route_id)
                            lines.append(LineInfo(
                                line_id=f"PATH-{route_id}",
                                line_name=f"PATH {route_abbrev}",
                                agency="PATH"
                            ))
                break
    
    return lines

def get_mta_arrivals(stop_id, feed_name, selected_lines):
    """Fetch MTA arrivals for specific lines"""
    arrivals = []
    
    try:
        feed = SubwayFeed.get(feed_name)
        
        if not feed or not hasattr(feed, 'entity'):
            return arrivals
        
        for entity in feed.entity:
            if hasattr(entity, 'trip_update') and entity.trip_update:
                trip = entity.trip_update.trip
                route_id = trip.route_id
                
                # Filter by selected lines
                if selected_lines and f"MTA-{route_id}" not in selected_lines:
                    continue
                
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
                                
                                arrivals.append(Arrival(
                                    agency='MTA',
                                    route=route_name,
                                    destination=direction,
                                    minutes=minutes
                                ))
    except Exception as e:
        print(f"MTA Error: {e}")
    
    return arrivals

def get_path_arrivals(stop_id, selected_lines):
    """Fetch PATH arrivals for specific lines"""
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
                direction_id = trip.direction_id if trip.HasField('direction_id') else 0
                
                # Filter by selected lines
                if selected_lines and f"PATH-{route_id}" not in selected_lines:
                    continue
                
                for stop_time in entity.trip_update.stop_time_update:
                    if str(stop_time.stop_id) == str(stop_id):
                        if stop_time.HasField('arrival'):
                            arrival_time = stop_time.arrival.time
                            minutes = calculate_minutes_until(arrival_time)
                            
                            if minutes >= 0:
                                route_abbrev = PATH_ROUTES_ABBREV.get(route_id, route_id)
                                direction = get_path_direction(route_id, direction_id)
                                
                                arrivals.append(Arrival(
                                    agency='PATH',
                                    route=route_abbrev,
                                    destination=direction,
                                    minutes=minutes
                                ))
    except Exception as e:
        print(f"PATH Error: {e}")
    
    return arrivals

# API Endpoints
@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/api/search")
async def search_stations(q: str):
    """Search for stations by query string"""
    if not q or len(q) < 2:
        return []
    
    results = fuzzy_match_station(q)
    return results

@app.get("/api/lines")
async def get_lines(station_id: str):
    """Get all lines available at a station"""
    lines = get_station_lines(station_id)
    return lines

@app.post("/api/arrivals")
async def get_arrivals(request: ArrivalRequest):
    """Get live arrivals for selected lines at a station"""
    station_id = request.station_id.lower().replace("_", " ")
    selected_lines = request.selected_lines
    max_minutes = request.max_minutes or 20
    
    all_arrivals = []
    
    # Check if dual-system
    if station_id in DUAL_SYSTEM_STATIONS:
        info = DUAL_SYSTEM_STATIONS[station_id]
        
        # Get MTA arrivals
        if "mta" in info:
            for stop_id, feed_name, name in info["mta"]:
                arrivals = get_mta_arrivals(stop_id, feed_name, selected_lines)
                all_arrivals.extend(arrivals)
        
        # Get PATH arrivals
        if "path" in info:
            path_stop_id, path_name = info["path"]
            arrivals = get_path_arrivals(path_stop_id, selected_lines)
            all_arrivals.extend(arrivals)
    
    # Check if MTA station
    elif station_id in MTA_STATIONS:
        for stop_id, feed_name, name in MTA_STATIONS[station_id]:
            arrivals = get_mta_arrivals(stop_id, feed_name, selected_lines)
            all_arrivals.extend(arrivals)
    
    # Check if PATH station
    else:
        # Find PATH stop ID
        for stop_id, name in PATH_STATIONS.items():
            if station_id.replace("_", " ") == name.lower():
                arrivals = get_path_arrivals(stop_id, selected_lines)
                all_arrivals.extend(arrivals)
                break
    
    # Filter by max_minutes
    all_arrivals = [a for a in all_arrivals if a.minutes <= max_minutes]
    
    # Sort by minutes
    all_arrivals = sorted(all_arrivals, key=lambda x: x.minutes)
    
    return {
        "timestamp": get_eastern_time().strftime('%I:%M %p ET'),
        "arrivals": all_arrivals
    }

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
