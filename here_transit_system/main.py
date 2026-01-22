"""
Minimalist FastAPI proxy for HERE Transit API v8.
No GTFS, no Protobuf, no underground - just clean HTTP requests.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import httpx
import json
from pathlib import Path
from datetime import datetime
import os

app = FastAPI(title="HERE Transit Proxy")

# Load station mappings
STATIONS_FILE = Path(__file__).parent / "stations.json"
with open(STATIONS_FILE, 'r') as f:
    STATIONS = json.load(f)

# HERE API Configuration
HERE_API_KEY = os.getenv("HERE_API_KEY", "YOUR_HERE_API_KEY")
DEPARTURES_URL = "https://transit.hereapi.com/v8/departures"

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Redirect to static frontend."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/api/stations")
async def get_stations():
    """Return available station keys and names."""
    return {"stations": list(STATIONS.keys())}


@app.get("/api/arrivals/{station_key}")
async def get_arrivals(station_key: str):
    """
    Get next arrivals for a station.
    
    Args:
        station_key: Key from stations.json (e.g., 'jsq', 'wtc')
    
    Returns:
        List of arrivals with line, destination, and minutes away
    """
    # Validate station key
    if station_key not in STATIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Station '{station_key}' not found. Available: {list(STATIONS.keys())}"
        )
    
    station_id = STATIONS[station_key]
    
    # Check for placeholder IDs
    if station_id.startswith("HERE_STATION_ID_"):
        raise HTTPException(
            status_code=503,
            detail="Station ID not configured. Run discover_stations.py to get actual IDs."
        )
    
    # Check API key
    if HERE_API_KEY == "YOUR_HERE_API_KEY":
        raise HTTPException(
            status_code=503,
            detail="HERE API key not configured. Set HERE_API_KEY environment variable."
        )
    
    try:
        # Call HERE Transit API
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                'ids': station_id,
                'apiKey': HERE_API_KEY,
                'return': 'transport,time'
            }
            
            response = await client.get(DEPARTURES_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Parse and transform data
        arrivals = []
        current_time = datetime.now()
        
        # Extract departures from response
        boards = data.get('boards', [])
        for board in boards:
            departures = board.get('departures', [])
            
            for dep in departures:
                transport = dep.get('transport', {})
                time_info = dep.get('time', {})
                
                # Extract key fields
                line = transport.get('name', 'Unknown')
                headsign = transport.get('headsign', 'Unknown')
                
                # Parse departure time
                dep_time_str = time_info.get('expected') or time_info.get('timetabled')
                if not dep_time_str:
                    continue
                
                try:
                    # Parse ISO 8601 timestamp
                    dep_time = datetime.fromisoformat(dep_time_str.replace('Z', '+00:00'))
                    # Convert to local time if needed (HERE returns UTC)
                    minutes_away = int((dep_time - current_time.astimezone()).total_seconds() / 60)
                    
                    # Only include future arrivals
                    if minutes_away < 0:
                        continue
                    
                    arrivals.append({
                        'line': line,
                        'destination': headsign,
                        'minutes': minutes_away,
                        'time': dep_time_str
                    })
                except (ValueError, TypeError):
                    # Skip if time parsing fails
                    continue
        
        # Sort by time and return top 10
        arrivals.sort(key=lambda x: x['minutes'])
        arrivals = arrivals[:10]
        
        return {
            'station': station_key,
            'station_id': station_id,
            'updated': datetime.now().isoformat(),
            'arrivals': arrivals,
            'count': len(arrivals)
        }
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"HERE API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Network error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        'status': 'ok',
        'api_key_configured': HERE_API_KEY != "YOUR_HERE_API_KEY",
        'stations_loaded': len(STATIONS),
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
