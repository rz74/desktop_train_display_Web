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

app = FastAPI(title="E-Ink Transit Dashboard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Station mappings
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

# Request/Response models
class ArrivalRequest(BaseModel):
    station_id: str
    selected_lines: List[str]

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
    
    # Check dual-system stations
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
    
    # Check if dual-system
    if station_id_lower in DUAL_SYSTEM_STATIONS:
        info = DUAL_SYSTEM_STATIONS[station_id_lower]
        
        # Add MTA lines
        if "mta" in info:
            for stop_id, feed_name, name in info["mta"]:
                # Get lines from feed
                try:
                    feed = SubwayFeed.get(feed_name)
                    routes_seen = set()
                    for entity in feed.entity:
                        if hasattr(entity, 'trip_update') and entity.trip_update:
                            route_id = entity.trip_update.trip.route_id
                            if route_id in MTA_LINES and route_id not in routes_seen:
                                routes_seen.add(route_id)
                                lines.append(LineInfo(
                                    line_id=f"MTA-{route_id}",
                                    line_name=f"MTA {route_id}",
                                    agency="MTA"
                                ))
                except:
                    pass
        
        # Add PATH routes
        if "path" in info:
            for route_id, route_name in PATH_ROUTES.items():
                lines.append(LineInfo(
                    line_id=f"PATH-{route_id}",
                    line_name=route_name,
                    agency="PATH"
                ))
    
    # Check if MTA only
    elif station_id_lower in MTA_STATIONS:
        for stop_id, feed_name, name in MTA_STATIONS[station_id_lower]:
            try:
                feed = SubwayFeed.get(feed_name)
                routes_seen = set()
                for entity in feed.entity:
                    if hasattr(entity, 'trip_update') and entity.trip_update:
                        route_id = entity.trip_update.trip.route_id
                        if route_id in MTA_LINES and route_id not in routes_seen:
                            routes_seen.add(route_id)
                            lines.append(LineInfo(
                                line_id=f"MTA-{route_id}",
                                line_name=f"MTA {route_id}",
                                agency="MTA"
                            ))
            except:
                pass
    
    # Check if PATH only
    else:
        for route_id, route_name in PATH_ROUTES.items():
            lines.append(LineInfo(
                line_id=f"PATH-{route_id}",
                line_name=route_name,
                agency="PATH"
            ))
    
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
                
                # Filter by selected lines
                if selected_lines and f"PATH-{route_id}" not in selected_lines:
                    continue
                
                for stop_time in entity.trip_update.stop_time_update:
                    if str(stop_time.stop_id) == str(stop_id):
                        if stop_time.HasField('arrival'):
                            arrival_time = stop_time.arrival.time
                            minutes = calculate_minutes_until(arrival_time)
                            
                            if minutes >= 0:
                                route_name = PATH_ROUTES.get(route_id, route_id)
                                
                                arrivals.append(Arrival(
                                    agency='PATH',
                                    route=route_name,
                                    destination='',
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
    
    # Check if MTA only
    elif station_id in MTA_STATIONS:
        for stop_id, feed_name, name in MTA_STATIONS[station_id]:
            arrivals = get_mta_arrivals(stop_id, feed_name, selected_lines)
            all_arrivals.extend(arrivals)
    
    # Check if PATH only
    else:
        # Find PATH stop ID
        for stop_id, name in PATH_STATIONS.items():
            if station_id.replace("_", " ") == name.lower():
                arrivals = get_path_arrivals(stop_id, selected_lines)
                all_arrivals.extend(arrivals)
                break
    
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
