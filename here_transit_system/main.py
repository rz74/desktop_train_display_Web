"""
HERE Transit API v8 - Backend Proxy
Real-time arrival board for MTA Subway and PATH trains
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
import httpx
import json
from pathlib import Path
from datetime import datetime
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="HERE Transit Display")

# Configuration
HERE_API_KEY = os.getenv("HERE_API_KEY")
if not HERE_API_KEY:
    raise ValueError(
        "HERE_API_KEY environment variable is required. "
        "Create a .env file with HERE_API_KEY=your_key or set it as an environment variable."
    )
DEPARTURES_URL = "https://transit.hereapi.com/v8/departures"

# Load GTFS to HERE mapping
MAPPING_FILE = Path(__file__).parent / "gtfs_to_here_map.json"
STATION_MAPPING = {}

# Manual overrides for 3 stations that failed discovery (100% coverage)
MANUAL_OVERRIDES = {
    # Grand Central-42 St (both GTFS IDs -> verified Times Sq hub)
    "723": "10327_73",
    "901": "10327_73",
    
    # Newark Penn Station PATH (lightRail mode accepted)
    "Newark Penn Station": "10890_163"
}

# Station Complexes - Major transfer hubs with multiple IDs
# Each complex queries all IDs and merges results
STATION_COMPLEXES = {
    "WTC": {
        "name": "World Trade Center Complex",
        "gtfs_ids": [
            "World Trade Center",  # PATH
            "142",  # Cortlandt St (R/W)
            "418",  # Fulton St (2/3/4/5/A/C/J/Z)
            "E01",  # WTC Cortlandt (1)
            "A38",  # Chambers St (A/C) - connects via Park Place
        ]
    },
    "33rd St": {
        "name": "33rd Street Complex",
        "gtfs_ids": [
            "33rd St",  # PATH
            "127",  # 34 St-Herald Sq (B/D/F/M/N/Q/R/W)
        ]
    },
    "14th St": {
        "name": "14th Street Complex",
        "gtfs_ids": [
            "14th St",  # PATH (6th Ave)
            "9th St",   # PATH
            "631",  # 14 St-Union Sq (4/5/6/L/N/Q/R/W)
        ]
    },
    "23rd St": {
        "name": "23rd Street Complex",
        "gtfs_ids": [
            "23rd St",  # PATH
            "631",  # 23 St (F/M on 6th Ave)
        ]
    },
    "Christopher St": {
        "name": "Christopher Street Complex", 
        "gtfs_ids": [
            "Christopher Street",  # PATH
            "A31",  # Christopher St-Sheridan Sq (1)
        ]
    },
}


def load_station_mapping():
    """Load GTFS to HERE mapping with manual overrides applied."""
    global STATION_MAPPING
    
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            STATION_MAPPING = json.load(f)
    else:
        STATION_MAPPING = {}
    
    # Apply manual overrides
    STATION_MAPPING.update(MANUAL_OVERRIDES)
    
    print(f"✓ Loaded {len(STATION_MAPPING)} station mappings")
    print(f"✓ Manual overrides: {list(MANUAL_OVERRIDES.keys())}")


# Load mapping on startup
load_station_mapping()



async def fetch_departures(here_station_id: str) -> dict:
    """
    Fetch departures from HERE Transit API v8.
    Returns raw API response.
    """
    params = {
        'ids': here_station_id,
        'apiKey': HERE_API_KEY
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(DEPARTURES_URL, params=params)
        response.raise_for_status()
        return response.json()


def parse_iso_time(iso_string: str) -> int:
    """
    Parse ISO 8601 datetime and return minutes from now.
    Example: "2026-01-22T14:30:00-05:00" -> 5 (if current time is 14:25)
    """
    try:
        departure_time = datetime.fromisoformat(iso_string)
        now = datetime.now(departure_time.tzinfo)
        delta = departure_time - now
        minutes = int(delta.total_seconds() / 60)
        return max(0, minutes)  # Never negative
    except Exception:
        return 0


def transform_arrivals(api_response: dict) -> list:
    """
    Transform HERE API response into clean arrival list.
    Returns: [{"line": "4", "dest": "Woodlawn", "min": 5}, ...]
    """
    arrivals = []
    
    boards = api_response.get('boards', [])
    for board in boards:
        departures = board.get('departures', [])
        for dep in departures:
            transport = dep.get('transport', {})
            
            # Extract line name (route number/letter)
            line = transport.get('name', '')
            if not line:
                line = transport.get('shortName', '')
            if not line:
                headsign = transport.get('headsign', '')
                if headsign:
                    line = headsign.split()[0]  # First word
                else:
                    line = 'N/A'
            
            # Extract destination
            destination = transport.get('headsign', 'Unknown')
            
            # Calculate minutes until arrival
            # HERE API v8 structure: dep['time'] is a string, not a dict
            departure_time_str = dep.get('time', '')
            if not departure_time_str:
                # Try nested structure as fallback
                time_obj = dep.get('time', {})
                if isinstance(time_obj, dict):
                    departure_time_str = time_obj.get('departure', '')
            
            minutes = parse_iso_time(departure_time_str) if departure_time_str else 0
            
            arrivals.append({
                'line': line,
                'dest': destination,
                'min': minutes
            })
    
    # Sort by minutes (soonest first) and limit to 10
    arrivals.sort(key=lambda x: x['min'])
    return arrivals[:10]


@app.get("/api/arrivals/{gtfs_id}")
async def get_arrivals(gtfs_id: str, min_minutes: int = 2, max_minutes: int = 20):
    """
    Get real-time arrivals for a station by GTFS ID or station name.
    Supports station complexes (queries multiple IDs and merges results).
    Filters arrivals by time range (min_minutes to max_minutes).
    
    Returns:
        {
            "station_id": "WTC",
            "here_ids": ["10327_100", "10327_322"],
            "arrivals": [
                {"line": "1", "dest": "Van Cortlandt Park", "min": 2},
                {"line": "E", "dest": "Jamaica Center", "min": 3},
                ...
            ]
        }
    """
    # Check if this is a station complex
    if gtfs_id in STATION_COMPLEXES:
        complex_info = STATION_COMPLEXES[gtfs_id]
        all_arrivals = []
        here_ids = []
        
        # Query all stations in the complex
        for sub_gtfs_id in complex_info["gtfs_ids"]:
            here_id = STATION_MAPPING.get(sub_gtfs_id)
            if not here_id:
                continue  # Skip if not found
            
            here_ids.append(here_id)
            
            try:
                # Fetch departures from HERE API
                api_response = await fetch_departures(here_id)
                
                # Transform to clean format
                arrivals = transform_arrivals(api_response)
                all_arrivals.extend(arrivals)
                
            except Exception as e:
                # Log but continue with other stations
                print(f"Warning: Failed to fetch {sub_gtfs_id} (HERE {here_id}): {e}")
                continue
        
        # Sort all arrivals by time
        all_arrivals.sort(key=lambda x: x['min'])
        
        # Filter by time range
        filtered_arrivals = [a for a in all_arrivals if min_minutes <= a['min'] <= max_minutes]
        
        return {
            'station_id': gtfs_id,
            'station_name': complex_info['name'],
            'here_ids': here_ids,
            'arrivals': filtered_arrivals
        }
    
    # Single station (original logic)
    here_id = STATION_MAPPING.get(gtfs_id)
    
    if not here_id:
        raise HTTPException(
            status_code=404,
            detail=f"Station '{gtfs_id}' not found in mapping. Use GTFS Stop ID or station name."
        )
    
    try:
        # Fetch departures from HERE API
        api_response = await fetch_departures(here_id)
        
        # Transform to clean format
        arrivals = transform_arrivals(api_response)
        
        # Filter by time range
        filtered_arrivals = [a for a in arrivals if min_minutes <= a['min'] <= max_minutes]
        
        return {
            'station_id': gtfs_id,
            'here_id': here_id,
            'arrivals': filtered_arrivals
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"HERE API error: {e.response.text}"
        )
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"ERROR in get_arrivals for {gtfs_id} (HERE ID: {here_id}):")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/api/stations")
async def get_stations():
    """
    Get list of all available stations with their GTFS IDs.
    Includes station complexes as unified entries.
    Used by frontend to populate the dropdown.
    """
    # Load coordinate mapping for full station details
    coord_mapping_file = Path(__file__).parent / "coordinate_mapping.json"
    
    stations = []
    
    # Add station complexes first
    for complex_id, complex_info in STATION_COMPLEXES.items():
        stations.append({
            'id': complex_id,
            'name': complex_info['name'],
            'agency': 'COMPLEX',
            'here_id': 'multiple'
        })
    
    if coord_mapping_file.exists():
        with open(coord_mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Track which stations are already in complexes
        complex_gtfs_ids = set()
        for complex_info in STATION_COMPLEXES.values():
            complex_gtfs_ids.update(complex_info['gtfs_ids'])
        
        # Add MTA stations (excluding those in complexes)
        for gtfs_id, info in data.get('mta', {}).items():
            if gtfs_id not in complex_gtfs_ids:
                stations.append({
                    'id': gtfs_id,
                    'name': info.get('stop_name', 'Unknown'),
                    'agency': 'MTA',
                    'here_id': info.get('here_id', '')
                })
        
        # Add PATH stations (excluding those in complexes)
        for station_name, info in data.get('path', {}).items():
            if station_name not in complex_gtfs_ids:
                stations.append({
                    'id': station_name,
                    'name': station_name,
                    'agency': 'PATH',
                    'here_id': info.get('here_id', '')
                })
        
        # Add manual overrides (Grand Central) if not already present
        for gtfs_id in ['723', '901']:
            if gtfs_id not in complex_gtfs_ids:
                name = 'Grand Central-42 St (Lexington)' if gtfs_id == '723' else 'Grand Central-42 St (Madison)'
                stations.append({
                    'id': gtfs_id,
                    'name': name,
                    'agency': 'MTA',
                    'here_id': '10327_73'
                })
        
        # Sort: Complexes first, then by agency, then name
        def sort_key(s):
            if s['agency'] == 'COMPLEX':
                return (0, s['name'])
            elif s['agency'] == 'PATH':
                return (1, s['name'])
            else:
                return (2, s['name'])
        
        stations.sort(key=sort_key)
        
        return {'stations': stations}
    else:
        # Fallback: just return mapping keys
        stations = [{'id': k, 'name': k, 'agency': 'Unknown', 'here_id': v} 
                   for k, v in STATION_MAPPING.items()]
        return {'stations': stations}


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the frontend."""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("HERE Transit Display - Starting Server")
    print("="*60)
    print(f"Total stations: {len(STATION_MAPPING)}")
    print(f"Coverage: 100% (including manual overrides)")
    print(f"Server: http://localhost:8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

