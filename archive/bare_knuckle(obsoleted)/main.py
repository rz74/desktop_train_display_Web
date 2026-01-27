from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
from datetime import datetime
from underground import SubwayFeed

app = FastAPI()

# Load stations configuration
with open("stations.json", "r", encoding="utf-8") as f:
    STATIONS = json.load(f)

# PATH API Configuration
PATH_API_URL = "https://path.api.razza.dev/v1/stations/{stop_id}/realtime"

# PATH Route Names
PATH_ROUTES = {
    "860": "Red (HOB-WTC)",
    "861": "Yellow (JSQ-33)",
    "862": "Red (NWK-WTC)",
    "1024": "Orange (JSQ-33 HOB)"
}

# MTA Route Names
MTA_LINES = {
    "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6",
    "A": "A", "C": "C", "E": "E", "B": "B", "D": "D", "F": "F", "M": "M",
    "N": "N", "Q": "Q", "R": "R", "W": "W", "J": "J", "Z": "Z",
    "L": "L", "G": "G", "S": "S", "GS": "GS", "FS": "FS"
}

class ArrivalRequest(BaseModel):
    station_id: str
    selected_lines: Optional[List[str]] = None

class Arrival(BaseModel):
    agency: str
    route: str
    destination: str
    minutes: int

def calculate_minutes_until(timestamp):
    """Calculate minutes until arrival from Unix timestamp"""
    now = datetime.now().timestamp()
    diff = timestamp - now
    return max(0, int(diff / 60))

def get_mta_direction(stop_id: str, route_id: str) -> str:
    """Get direction based on stop_id suffix (N/S for uptown/downtown)"""
    if stop_id.endswith('N'):
        return "Uptown"
    elif stop_id.endswith('S'):
        return "Downtown"
    return "Unknown"

def get_path_arrivals(stop_id: int, selected_lines: Optional[List[str]] = None) -> List[Arrival]:
    """Fetch PATH arrivals using razza.dev API"""
    arrivals = []
    
    try:
        url = PATH_API_URL.format(stop_id=stop_id)
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        # API returns: {"upcomingTrains": [{"lineName": "Newark - World Trade Center", "projectedArrival": "2024-01-21T12:34:56-05:00", ...}]}
        for train in data.get("upcomingTrains", []):
            line_name = train.get("lineName", "")
            route_id = train.get("route", "")
            
            # Filter by selected lines if specified
            if selected_lines:
                line_filter = f"PATH-{route_id}"
                if line_filter not in selected_lines:
                    continue
            
            # Parse ISO timestamp
            arrival_str = train.get("projectedArrival", "")
            if arrival_str:
                arrival_time = datetime.fromisoformat(arrival_str.replace('Z', '+00:00'))
                minutes = calculate_minutes_until(arrival_time.timestamp())
                
                route_name = PATH_ROUTES.get(route_id, route_id)
                
                arrivals.append(Arrival(
                    agency="PATH",
                    route=route_name,
                    destination=train.get("headsign", ""),
                    minutes=minutes
                ))
                
    except Exception as e:
        print(f"PATH API Error for stop {stop_id}: {e}")
    
    return arrivals

def get_mta_arrivals(stop_id: str, feed_group: str, selected_lines: Optional[List[str]] = None) -> List[Arrival]:
    """Fetch MTA arrivals using underground library"""
    arrivals = []
    
    try:
        feed = SubwayFeed.get(feed_group)
        
        if not feed or not hasattr(feed, 'entity'):
            return arrivals
        
        for entity in feed.entity:
            if hasattr(entity, 'trip_update') and entity.trip_update:
                trip = entity.trip_update.trip
                route_id = trip.route_id
                
                # Filter by selected lines
                if selected_lines:
                    line_filter = f"MTA-{route_id}"
                    if line_filter not in selected_lines:
                        continue
                
                if not entity.trip_update.stop_time_update:
                    continue
                
                for stop_time in entity.trip_update.stop_time_update:
                    # Match base stop_id (ignoring N/S suffix)
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
        print(f"MTA Error for stop {stop_id} feed {feed_group}: {e}")
    
    return arrivals

@app.get("/api/stations")
async def get_stations():
    """Return all available stations"""
    return {"stations": STATIONS}

@app.get("/api/lines/{station_id}")
async def get_station_lines(station_id: str):
    """Get available lines for a station"""
    station = STATIONS.get(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    lines = []
    
    # Add MTA lines
    if "mta" in station:
        for stop_info in station["mta"]:
            for route in stop_info.get("routes", []):
                lines.append({
                    "line_id": f"MTA-{route}",
                    "line_name": route,
                    "agency": "MTA"
                })
    
    # Add PATH lines
    if "path" in station:
        for route_id, route_name in PATH_ROUTES.items():
            lines.append({
                "line_id": f"PATH-{route_id}",
                "line_name": route_name,
                "agency": "PATH"
            })
    
    return {"lines": lines}

@app.post("/api/arrivals")
async def get_arrivals(request: ArrivalRequest):
    """Get arrivals for a station"""
    print(f"DEBUG: Received arrivals request for station: {request.station_id}")
    station = STATIONS.get(request.station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    all_arrivals = []
    
    # Fetch MTA arrivals from all stops
    if "mta" in station:
        for stop_info in station["mta"]:
            stop_id = stop_info["stop_id"]
            feed_group = stop_info["feed_group"]
            arrivals = get_mta_arrivals(stop_id, feed_group, request.selected_lines)
            all_arrivals.extend(arrivals)
    
    # Fetch PATH arrivals
    if "path" in station:
        path_stop_id = station["path"]["stop_id"]
        arrivals = get_path_arrivals(path_stop_id, request.selected_lines)
        all_arrivals.extend(arrivals)
    
    # Sort by arrival time
    all_arrivals.sort(key=lambda x: x.minutes)
    
    # Limit to 20 arrivals
    all_arrivals = all_arrivals[:20]
    
    return {"arrivals": all_arrivals}

# Mount static files at root for CSS/JS, but API routes take precedence
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("✓ Loaded stations.json")
    print(f"Registered routes: {[route.path for route in app.routes]}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
