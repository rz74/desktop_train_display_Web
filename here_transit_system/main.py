"""
HERE Transit API v8 - Multi-Tenant Backend
Real-time arrival board for MTA Subway and PATH trains
"""
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import httpx
import json
import re
from pathlib import Path
from datetime import datetime
import os
import asyncio
from io import BytesIO

try:
    from underground import SubwayFeed
    MTA_FEED_AVAILABLE = True
except ImportError:
    MTA_FEED_AVAILABLE = False
    print("Warning: underground library not installed. MTA real-time data unavailable.")

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: playwright library not installed. Screenshot rendering unavailable.")

# Load environment variables
load_dotenv()

# Initialize FastAPI with dynamic root_path for deployment flexibility
ROOT_PATH = os.getenv("ROOT_PATH", "/einktrain")
app = FastAPI(
    title="HERE Transit Display - Multi-Tenant",
    root_path=ROOT_PATH
)

# Add session middleware for authentication
import secrets
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    # Auto-generate a random secret key for this session
    SESSION_SECRET_KEY = secrets.token_hex(32)
    print("Warning: SESSION_SECRET_KEY not set in .env. Using auto-generated key (will change on restart).")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Configuration
HERE_API_KEY = os.getenv("HERE_API_KEY")
if not HERE_API_KEY:
    raise ValueError(
        "HERE_API_KEY environment variable is required. "
        "Create a .env file with HERE_API_KEY=your_key or set it as an environment variable."
    )
ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE")
if not ADMIN_PASSCODE:
    raise ValueError(
        "ADMIN_PASSCODE environment variable is required. "
        "Set it in your .env file for admin access."
    )
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    print("Warning: OPENWEATHER_API_KEY not set. Weather data will not be updated automatically.")

DEPARTURES_URL = "https://transit.hereapi.com/v8/departures"
WEATHER_URL = "https://api.openweathermap.org/data/3.0/onecall"
# NYC coordinates
NYC_LAT = 40.7128
NYC_LON = -74.0060

# User configurations file
USER_CONFIGS_FILE = Path(__file__).parent / "user_configs.json"

# Load GTFS to HERE mapping
MAPPING_FILE = Path(__file__).parent / "gtfs_to_here_map.json"
COORDINATE_MAPPING_FILE = Path(__file__).parent / "coordinate_mapping.json"
STATION_LINES_FILE = Path(__file__).parent / "station_lines.json"
STATION_MAPPING = {}
STATION_NAMES = {}  # Maps GTFS ID to station name
STATION_AGENCY = {}  # Maps GTFS ID to agency (MTA or PATH)
STATION_LINES_METADATA = {}  # Maps station ID to available lines

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
    "Times Sq-42 St": {
        "name": "Times Sq-42 St",
        "gtfs_ids": [
            "127",  # Times Sq-42 St (1/2/3)
            "725",  # Times Sq-42 St (7)
            "R16",  # Times Sq-42 St (N/Q/R/W)
            "902",  # Times Sq-42 St (A/C/E)
        ]
    },
    "Grand Central-42 St": {
        "name": "Grand Central-42 St",
        "gtfs_ids": [
            "631",  # Grand Central-42 St (4/5/6/7/S)
            "723",  # Grand Central-42 St (Lexington)
            "901",  # Grand Central-42 St (Madison)
        ]
    },
    "Atlantic Av-Barclays Ctr": {
        "name": "Atlantic Av-Barclays Ctr",
        "gtfs_ids": [
            "D24",  # Atlantic Av-Barclays Ctr (B/D)
            "R31",  # Atlantic Av-Barclays Ctr (N/Q/R/W)
            "235",  # Atlantic Av-Barclays Ctr (2/3/4/5)
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
    """Load GTFS to HERE mapping with manual overrides and station names."""
    global STATION_MAPPING, STATION_NAMES, STATION_AGENCY, STATION_AGENCY
    
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            STATION_MAPPING = json.load(f)
    else:
        STATION_MAPPING = {}
    
    # Apply manual overrides
    STATION_MAPPING.update(MANUAL_OVERRIDES)
    
    # Load station names from coordinate mapping
    if COORDINATE_MAPPING_FILE.exists():
        with open(COORDINATE_MAPPING_FILE, 'r', encoding='utf-8') as f:
            coord_data = json.load(f)
            
            # Load MTA station names
            if 'mta' in coord_data:
                for gtfs_id, station_info in coord_data['mta'].items():
                    if 'stop_name' in station_info:
                        STATION_NAMES[gtfs_id] = station_info['stop_name']
                    STATION_AGENCY[gtfs_id] = 'MTA'
            
            # Load PATH station names (use station_name for PATH)
            if 'path' in coord_data:
                for gtfs_id, station_info in coord_data['path'].items():
                    if 'station_name' in station_info:
                        STATION_NAMES[gtfs_id] = station_info['station_name']
                    STATION_AGENCY[gtfs_id] = 'PATH'
    
    # Load station lines metadata
    if STATION_LINES_FILE.exists():
        with open(STATION_LINES_FILE, 'r', encoding='utf-8') as f:
            lines_data = json.load(f)
            # Flatten all station types into one dictionary
            for category in ['path_stations', 'complexes', 'mta_all_stations']:
                if category in lines_data:
                    STATION_LINES_METADATA.update(lines_data[category])
            print(f"✓ Loaded line metadata for {len(STATION_LINES_METADATA)} stations")
    else:
        print("⚠ station_lines.json not found, will fetch lines dynamically")
    
    # Add manual override names
    STATION_NAMES['723'] = 'Grand Central-42 St'
    STATION_NAMES['901'] = 'Grand Central-42 St'
    STATION_NAMES['Newark Penn Station'] = 'Newark Penn Station'
    
    print(f"✓ Loaded {len(STATION_MAPPING)} station mappings")
    print(f"✓ Manual overrides: {list(MANUAL_OVERRIDES.keys())}")


# Load mapping on startup
load_station_mapping()


# ============================================================
# Screenshot Service - Persistent Browser Manager
# ============================================================
class BrowserManager:
    """Manages a single persistent headless browser instance for screenshots."""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def start(self):
        """Initialize the browser instance."""
        if not PLAYWRIGHT_AVAILABLE:
            print("Warning: Playwright not available. Screenshot rendering disabled.")
            return
        
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page(viewport={'width': 800, 'height': 480})
            print("✓ Browser manager initialized")
        except Exception as e:
            print(f"Error initializing browser: {e}")
    
    async def close(self):
        """Close the browser instance."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("✓ Browser manager closed")
    
    async def capture_screenshot(self, url: str) -> bytes:
        """
        Navigate to URL and capture screenshot.
        Returns PNG image bytes.
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.goto(url, wait_until='networkidle')
        screenshot_bytes = await self.page.screenshot(type='png')
        return screenshot_bytes


# Initialize browser manager
browser_manager = BrowserManager()

# Weather update task
weather_task = None


# Icon mapping for OpenWeather conditions/icon codes to Lucide icons
ICON_MAP = {
    # OpenWeather icon codes
    '01d': 'sun',           # clear sky day
    '01n': 'moon',          # clear sky night
    '02d': 'cloud-sun',     # few clouds day
    '02n': 'cloud-moon',    # few clouds night
    '03d': 'cloud',         # scattered clouds
    '03n': 'cloud',
    '04d': 'cloudy',        # broken clouds
    '04n': 'cloudy',
    '09d': 'cloud-drizzle', # shower rain
    '09n': 'cloud-drizzle',
    '10d': 'cloud-rain',    # rain day
    '10n': 'cloud-rain',    # rain night
    '11d': 'cloud-lightning', # thunderstorm
    '11n': 'cloud-lightning',
    '13d': 'snowflake',     # snow
    '13n': 'snowflake',
    '50d': 'cloud-fog',     # mist
    '50n': 'cloud-fog',
    # OpenWeather main conditions (fallback)
    'Clear': 'sun',
    'Clouds': 'cloud',
    'Rain': 'cloud-rain',
    'Drizzle': 'cloud-drizzle',
    'Thunderstorm': 'cloud-lightning',
    'Snow': 'snowflake',
    'Mist': 'cloud-fog',
    'Smoke': 'cloud-fog',
    'Haze': 'cloud-fog',
    'Dust': 'cloud-fog',
    'Fog': 'cloud-fog',
    'Sand': 'cloud-fog',
    'Ash': 'cloud-fog',
    'Squall': 'wind',
    'Tornado': 'tornado'
}


async def fetch_nyc_weather():
    """Fetch current weather data for NYC from OpenWeatherMap One Call API 3.0."""
    if not OPENWEATHER_API_KEY:
        return None
    
    try:
        params = {
            'lat': NYC_LAT,
            'lon': NYC_LON,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'  # Get temperature in Celsius
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(WEATHER_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Extract weather information from One Call API 3.0 response
            current = data['current']
            daily = data['daily'][0]  # Today's forecast for high/low
            
            # Get icon code and map to Lucide icon
            icon_code = current['weather'][0].get('icon', '')
            condition = current['weather'][0]['main']
            lucide_icon = ICON_MAP.get(icon_code, ICON_MAP.get(condition, 'cloud'))
            
            weather_data = {
                'temp_c': str(round(current['temp'])),
                'temp_f': str(round(current['temp'] * 9/5 + 32)),
                'condition': condition,
                'icon': lucide_icon,
                'high_c': str(round(daily['temp']['max'])),
                'low_c': str(round(daily['temp']['min']))
            }
            
            print(f"Weather updated: {weather_data['temp_c']}°C / {weather_data['temp_f']}°F - {weather_data['condition']}")
            return weather_data
            
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None


async def update_all_user_weather():
    """Update weather data for all users in config file."""
    weather_data = await fetch_nyc_weather()
    if not weather_data:
        return
    
    if not USER_CONFIGS_FILE.exists():
        return
    
    try:
        with open(USER_CONFIGS_FILE, 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        # Update weather for all users
        for user_id in configs:
            configs[user_id]['weather_data'] = weather_data
        
        with open(USER_CONFIGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(configs, f, indent=2, ensure_ascii=False)
            
        print(f"Updated weather data for {len(configs)} user(s)")
        
    except Exception as e:
        print(f"Error updating user configs with weather: {e}")


async def weather_update_loop():
    """Background task to update weather every hour."""
    while True:
        try:
            await update_all_user_weather()
            # Wait 1 hour before next update
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"Error in weather update loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error before retrying


@app.on_event("startup")
async def startup_event():
    """Initialize browser and start weather updates on startup."""
    global weather_task
    await browser_manager.start()
    
    # Initial weather update
    if OPENWEATHER_API_KEY:
        await update_all_user_weather()
        # Start background task for hourly updates
        weather_task = asyncio.create_task(weather_update_loop())
        print("Weather update task started (updates every hour)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close browser and stop weather updates on shutdown."""
    global weather_task
    if weather_task:
        weather_task.cancel()
        try:
            await weather_task
        except asyncio.CancelledError:
            pass
    await browser_manager.close()


def load_user_config(display_id: str):
    """Load configuration for a specific display ID. Returns dict or None."""
    if not USER_CONFIGS_FILE.exists():
        return None
    
    with open(USER_CONFIGS_FILE, 'r', encoding='utf-8') as f:
        configs = json.load(f)
    
    return configs.get(display_id)


def save_user_config(display_id: str, config: dict):
    """Save configuration for a specific display ID."""
    configs = {}
    if USER_CONFIGS_FILE.exists():
        with open(USER_CONFIGS_FILE, 'r', encoding='utf-8') as f:
            configs = json.load(f)
    
    configs[display_id] = config
    
    with open(USER_CONFIGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(configs, f, indent=2)


def get_all_stations() -> list:
    """Get all stations for dropdown (includes complexes, PATH, and MTA)."""
    stations = []
    complex_gtfs_ids = set()
    
    # Add station complexes first
    for complex_id, info in STATION_COMPLEXES.items():
        stations.append({
            'id': complex_id,
            'name': info['name'],
            'agency': 'COMPLEX',
            'here_id': 'complex'
        })
        complex_gtfs_ids.update(info['gtfs_ids'])
    
    # Add regular stations (skip those in complexes)
    for gtfs_id, here_id in STATION_MAPPING.items():
        if gtfs_id not in complex_gtfs_ids:
            # Get proper station name
            station_name = STATION_NAMES.get(gtfs_id, gtfs_id)
            
            # Get agency from STATION_AGENCY dict (default to MTA if not found)
            agency = STATION_AGENCY.get(gtfs_id, 'MTA')
            
            stations.append({
                'id': gtfs_id,
                'name': station_name,
                'agency': agency,
                'here_id': here_id
            })
    
    # Sort: Complexes first, then PATH, then MTA, all alphabetically
    def sort_key(s):
        if s['agency'] == 'COMPLEX':
            return (0, s['name'])
        elif s['agency'] == 'PATH':
            return (1, s['name'])
        else:
            return (2, s['name'])
    
    stations.sort(key=sort_key)
    return stations


async def fetch_departures(here_station_id: str) -> dict:
    """
    Fetch departures from HERE Transit API v8.
    Returns raw API response.
    """
    params = {
        'ids': here_station_id,
        'apiKey': HERE_API_KEY,
        'maxPerBoard': 40,  # Max departures per platform/board (default is 5)
        'maxBoards': 10,    # Max platforms/boards to return
        'lang': 'en-US'
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


def get_mta_arrivals(gtfs_id: str) -> list:
    """
    Get real-time MTA subway arrivals using underground library.
    Returns: [{"line": "F", "dest": "Coney Island", "min": 3}, ...]
    """
    if not MTA_FEED_AVAILABLE:
        return []
    
    try:
        # underground library needs route letters/numbers, not stop IDs
        # Query all major routes and filter by stop_id
        routes = ['A', 'C', 'E', 'B', 'D', 'F', 'M', 'G', 'L', 'J', 'Z',
                  'N', 'Q', 'R', 'W', '1', '2', '3', '4', '5', '6', '7', 'S']
        
        arrivals = []
        
        for route in routes:
            try:
                feed = SubwayFeed.get(route)
                for train in feed:
                    # The stop_id in GTFS has N/S suffix for direction, our IDs don't
                    # Match if either the exact ID matches or the base ID matches
                    train_stop_id = getattr(train, 'stop_id', None)
                    if not train_stop_id:
                        continue
                    
                    # Remove direction suffix (N/S) if present
                    base_stop_id = train_stop_id.rstrip('NS')
                    target_base = gtfs_id.rstrip('NS')
                    
                    # Check if this train stops at our station
                    if train_stop_id == gtfs_id or base_stop_id == target_base:
                        # Extract route/line
                        line = route
                        
                        # Extract destination
                        dest = getattr(train, 'headsign', None) or getattr(train, 'direction', 'Unknown')
                        
                        # Calculate minutes until arrival
                        if hasattr(train, 'time'):
                            time_obj = train.time
                            try:
                                if isinstance(time_obj, datetime):
                                    now = datetime.now(time_obj.tzinfo if time_obj.tzinfo else None)
                                    delta = time_obj - now
                                    minutes = int(delta.total_seconds() / 60)
                                elif isinstance(time_obj, (int, float)):
                                    # Assume it's a timestamp
                                    from datetime import timezone
                                    now = datetime.now(timezone.utc)
                                    arrival_time = datetime.fromtimestamp(time_obj, tz=timezone.utc)
                                    delta = arrival_time - now
                                    minutes = int(delta.total_seconds() / 60)
                                else:
                                    continue
                                
                                if minutes >= 0:  # Only include future arrivals
                                    arrivals.append({
                                        'line': line,
                                        'dest': dest,
                                        'min': minutes
                                    })
                            except Exception:
                                continue
            except Exception as e:
                # Route might not exist or have errors, skip it silently
                pass
        
        return arrivals
    except Exception as e:
        print(f"MTA GTFS error for {gtfs_id}: {e}")
        return []


def transform_arrivals(api_response: dict) -> list:
    """
    Transform HERE API response into clean arrival list.
    Returns: [{"line": "4", "dest": "Woodlawn", "min": 5}, ...]
    """
    # PATH route name mapping (HERE API longName -> our abbreviated format)
    PATH_ROUTE_MAP = {
        "Hoboken - 33rd Street": "HOB-33",
        "Journal Square - 33rd Street": "JSQ-33",
        "Newark - World Trade Center": "NWK-WTC",
        "Journal Square - World Trade Center": "JSQ-WTC",
        "Hoboken - World Trade Center": "HOB-WTC"
    }
    
    arrivals = []
    
    boards = api_response.get('boards', [])
    for board in boards:
        departures = board.get('departures', [])
        for dep in departures:
            transport = dep.get('transport', {})
            
            # Extract line name - try multiple fields aggressively
            line = None
            
            # PATH-specific handling: Use longName to get the full route name
            if transport.get('shortName') == 'PATH' and transport.get('longName'):
                long_name = transport.get('longName').strip()
                # Convert full name to abbreviated format
                line = PATH_ROUTE_MAP.get(long_name, 'PATH')
            
            # Try shortName first (usually the route letter/number) for MTA
            if not line and transport.get('shortName'):
                line = transport.get('shortName').strip()
            
            # Try name as fallback
            if not line and transport.get('name'):
                name = transport.get('name').strip()
                # If name is short (1-4 chars), it's probably the route
                if len(name) <= 4:
                    line = name
                else:
                    # Try to extract route from longer name (e.g., "Subway D")
                    words = name.split()
                    for word in words:
                        if len(word) <= 3 and word[0].isalnum():
                            line = word
                            break
            
            # Try headsign as last resort
            if not line:
                headsign = transport.get('headsign', '')
                if headsign:
                    # Look for single letter/number patterns
                    match = re.search(r'\b([A-Z0-9]{1,3})\b', headsign)
                    if match:
                        line = match.group(1)
            
            # If still no line, use placeholder instead of skipping
            if not line:
                line = '?'
            
            # Extract destination
            destination = transport.get('headsign', 'Unknown')
            
            # Calculate minutes until arrival
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
    
    # Sort by minutes (soonest first) - don't limit here, let caller decide
    arrivals.sort(key=lambda x: x['min'])
    return arrivals


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


@app.get("/api/station-lines/{gtfs_id}")
async def get_station_lines(gtfs_id: str):
    """
    Get available lines/routes for a specific station from metadata.
    Returns a list of unique line identifiers.
    """
    lines = set()
    
    # Check if it's a station complex
    if gtfs_id in STATION_COMPLEXES:
        complex_info = STATION_COMPLEXES[gtfs_id]
        # Merge lines from all GTFS IDs in the complex
        for complex_gtfs_id in complex_info['gtfs_ids']:
            if complex_gtfs_id in STATION_LINES_METADATA:
                lines.update(STATION_LINES_METADATA[complex_gtfs_id])
        
        # Also check if complex itself has metadata
        if gtfs_id in STATION_LINES_METADATA:
            lines.update(STATION_LINES_METADATA[gtfs_id])
    else:
        # Single station - check metadata
        if gtfs_id in STATION_LINES_METADATA:
            lines.update(STATION_LINES_METADATA[gtfs_id])
        else:
            # Fallback: try to fetch lines dynamically from live data
            try:
                station_lines = await _fetch_station_lines(gtfs_id)
                lines.update(station_lines)
            except Exception as e:
                return JSONResponse(
                    status_code=404,
                    content={"error": f"No line metadata found for station: {gtfs_id}"}
                )
    
    if not lines:
        return JSONResponse(
            status_code=404,
            content={"error": f"No lines found for station: {gtfs_id}"}
        )
    
    return {"lines": sorted(list(lines))}


async def _fetch_station_lines(gtfs_id: str) -> set:
    """
    Helper function to fetch lines for a single station.
    Returns a set of line identifiers.
    """
    lines = set()
    
    # Try to get lines from HERE API by fetching current arrivals
    here_id = STATION_MAPPING.get(gtfs_id)
    if here_id:
        try:
            api_response = await fetch_departures(here_id)
            arrivals = transform_arrivals(api_response)
            lines.update([a['line'] for a in arrivals if a['line'] != '?'])
        except:
            pass
    
    # For MTA stations, also try to get from real-time feed
    if STATION_AGENCY.get(gtfs_id) == 'MTA' and MTA_FEED_AVAILABLE:
        try:
            mta_arrivals = get_mta_arrivals(gtfs_id)
            lines.update([a['line'] for a in mta_arrivals if a['line'] != '?'])
        except:
            pass
    
    return lines


@app.get("/debug/{gtfs_id}")
async def debug_station(gtfs_id: str):
    """Debug endpoint to see raw API response for a station."""
    here_id = STATION_MAPPING.get(gtfs_id)
    if not here_id:
        return {"error": f"Station {gtfs_id} not found in mapping"}
    
    try:
        api_response = await fetch_departures(here_id)
        return {
            "gtfs_id": gtfs_id,
            "here_id": here_id,
            "station_name": STATION_NAMES.get(gtfs_id, gtfs_id),
            "raw_api_response": api_response
        }
    except Exception as e:
        return {"error": str(e)}


# ===== Authentication Routes (must be defined before parametrized routes) =====

@app.get("/login")
async def login_page(request: Request, redirect_to: str = None):
    """
    Display the login page.
    """
    return templates.TemplateResponse("login.html", {
        "request": request,
        "display_id": None,
        "message": None,
        "message_type": None,
        "redirect_to": redirect_to,
        "root_path": request.app.root_path
    })


@app.post("/login")
async def login(
    request: Request,
    display_id: str = Form(...),
    password: str = Form(...),
    redirect_to: str = Form(None)
):
    """
    Authenticate user and create session.
    """
    # Load user config to verify password
    user_config = load_user_config(display_id)
    
    if not user_config:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "display_id": display_id,
            "message": "Display ID not found. Please check your username.",
            "message_type": "error",
            "redirect_to": redirect_to,
            "root_path": request.app.root_path
        })
    
    # Verify password from environment variable
    expected_password = os.getenv(f"{display_id.upper()}_PW")
    if not expected_password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "display_id": display_id,
            "message": f"Password not configured for {display_id}. Please contact administrator.",
            "message_type": "error",
            "redirect_to": redirect_to,
            "root_path": request.app.root_path
        })
    
    if password != expected_password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "display_id": display_id,
            "message": "Invalid password. Please try again.",
            "message_type": "error",
            "redirect_to": redirect_to,
            "root_path": request.app.root_path
        })
    
    # Authentication successful - create session
    request.session['display_id'] = display_id
    
    # Redirect to requested page or config page
    if redirect_to:
        return RedirectResponse(url=redirect_to, status_code=303)
    else:
        return RedirectResponse(url=f"/{display_id}/config", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    """
    Clear session and redirect to login.
    """
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ===== Display Routes =====

@app.get("/{display_id}")
async def display_page(request: Request, display_id: str):
    """
    Render the e-ink display page for a specific display ID.
    If no config exists, redirect to config page.
    """
    config = load_user_config(display_id)
    
    if not config:
        # No config found, redirect to config page
        return RedirectResponse(url=f"/{display_id}/config")
    
    # Get arrivals for configured station
    gtfs_id = config['gtfs_id']
    min_minutes = config.get('min_minutes', 2)
    max_minutes = config.get('max_minutes', 20)
    
    # Parse display resolution
    display_res = config.get('display_res', '800x600')
    width, height = map(int, display_res.split('x'))
    
    # Check if station complex
    if gtfs_id in STATION_COMPLEXES:
        complex_info = STATION_COMPLEXES[gtfs_id]
        all_arrivals = []
        
        for sub_gtfs_id in complex_info["gtfs_ids"]:
            here_id = STATION_MAPPING.get(sub_gtfs_id)
            if not here_id:
                continue
            
            try:
                api_response = await fetch_departures(here_id)
                arrivals = transform_arrivals(api_response)
                all_arrivals.extend(arrivals)
            except Exception as e:
                print(f"Warning: Failed to fetch {sub_gtfs_id}: {e}")
                continue
        
        # Filter and sort based on user's time window
        filtered = [a for a in all_arrivals if min_minutes <= a['min'] <= max_minutes]
        
        # Apply line filtering if selected_lines is configured (case-insensitive, whitespace-resilient)
        selected_lines = config.get('selected_lines', [])
        if selected_lines:
            # Normalize selected lines: strip whitespace and uppercase
            selected_lines_upper = [s.strip().upper() for s in selected_lines]
            # Debug: Show what we're comparing
            print(f"Complex Filter: Selected lines (normalized): {selected_lines_upper}")
            
            filtered_with_debug = []
            for a in filtered:
                arrival_line_normalized = a['line'].strip().upper()
                is_match = arrival_line_normalized in selected_lines_upper
                print(f"  Comparing Arrival Line: '{a['line']}' (normalized: '{arrival_line_normalized}') against Filter: {selected_lines_upper} → Match: {is_match}")
                if is_match:
                    filtered_with_debug.append(a)
            
            filtered = filtered_with_debug
            print(f"Complex: After line filtering: {len(filtered)} arrivals")
        
        filtered.sort(key=lambda x: x['min'])
        # Limit to 12 trains to fit 480px screen perfectly
        arrivals = filtered[:12]
        station_name = complex_info['name']
        
    else:
        # Single station
        here_id = STATION_MAPPING.get(gtfs_id)
        if not here_id:
            return {"error": f"Station {gtfs_id} not found"}
        
        station_name = STATION_NAMES.get(gtfs_id, gtfs_id)
        agency = STATION_AGENCY.get(gtfs_id, 'MTA')
        
        try:
            # Get HERE API data
            api_response = await fetch_departures(here_id)
            here_arrivals = transform_arrivals(api_response)
            print(f"HERE API: {len(here_arrivals)} arrivals")
            
            # Get MTA GTFS data if this is an MTA station
            mta_arrivals = []
            if agency == 'MTA' and MTA_FEED_AVAILABLE:
                mta_arrivals = get_mta_arrivals(gtfs_id)
                print(f"MTA GTFS: {len(mta_arrivals)} arrivals")
            
            # Combine and deduplicate arrivals
            all_arrivals = here_arrivals + mta_arrivals
            print(f"Combined total: {len(all_arrivals)} arrivals")
            
            # Filter and sort based on user's time window
            filtered = [a for a in all_arrivals if min_minutes <= a['min'] <= max_minutes]
            print(f"After filtering {min_minutes}-{max_minutes} min: {len(filtered)} arrivals")
            
            # Apply line filtering if selected_lines is configured (case-insensitive, whitespace-resilient)
            selected_lines = config.get('selected_lines', [])
            if selected_lines:
                # Normalize selected lines: strip whitespace and uppercase
                selected_lines_upper = [s.strip().upper() for s in selected_lines]
                # Debug: Show what we're comparing
                print(f"Single Station Filter: Selected lines (normalized): {selected_lines_upper}")
                
                filtered_with_debug = []
                for a in filtered:
                    arrival_line_normalized = a['line'].strip().upper()
                    is_match = arrival_line_normalized in selected_lines_upper
                    print(f"  Comparing Arrival Line: '{a['line']}' (normalized: '{arrival_line_normalized}') against Filter: {selected_lines_upper} → Match: {is_match}")
                    if is_match:
                        filtered_with_debug.append(a)
                
                filtered = filtered_with_debug
                print(f"Single Station: After line filtering: {len(filtered)} arrivals")
            
            filtered.sort(key=lambda x: (x['min'], x['line']))
            # Limit to 12 trains to fit 480px screen perfectly
            arrivals = filtered[:12]
            
        except Exception as e:
            return {"error": str(e)}
    
    # Get current time
    from datetime import datetime
    current_time = datetime.now().strftime("%I:%M %p")
    
    # Get weather data and custom note from config
    weather_data = config.get('weather_data', {
        'temp_c': '--',
        'temp_f': '--',
        'condition': 'N/A',
        'icon': 'cloud',
        'high_c': '--',
        'low_c': '--'
    })
    custom_note = config.get('custom_note', '')
    
    return templates.TemplateResponse("display.html", {
        "request": request,
        "display_id": display_id,
        "width": width,
        "height": height,
        "current_time": current_time,
        "station_name": station_name,
        "arrivals": arrivals,
        "weather_data": weather_data,
        "custom_note": custom_note
    })


@app.get("/{display_id}/config")
async def config_page(request: Request, display_id: str):
    """
    Render the configuration form for a specific display ID.
    Requires authentication - user must be logged in as this display_id.
    """
    # Check authentication
    session_display_id = request.session.get('display_id')
    if not session_display_id or session_display_id != display_id:
        # Redirect to login with return URL
        return RedirectResponse(
            url=f"/login?redirect_to=/{display_id}/config",
            status_code=303
        )
    
    config = load_user_config(display_id) or {
        'gtfs_id': '',
        'min_minutes': 2,
        'max_minutes': 20,
        'display_res': '800x480'
    }
    
    stations = get_all_stations()
    
    return templates.TemplateResponse("config.html", {
        "request": request,
        "display_id": display_id,
        "stations": stations,
        "config": config,
        "message": None,
        "message_type": None,
        "root_path": request.app.root_path
    })


@app.post("/{display_id}/config")
async def save_config(
    request: Request,
    display_id: str,
    gtfs_id: str = Form(...),
    min_minutes: int = Form(...),
    max_minutes: int = Form(...),
    display_res: str = Form(...),
    custom_note: str = Form("")
):
    """
    Save configuration for a specific display ID.
    Requires authentication - user must be logged in as this display_id.
    Password is no longer required in the form since user is already authenticated.
    """
    # Check authentication
    session_display_id = request.session.get('display_id')
    if not session_display_id or session_display_id != display_id:
        # Redirect to login
        return RedirectResponse(
            url=f"/login?redirect_to=/{display_id}/config",
            status_code=303
        )
    
    # Load existing config to preserve password and weather data
    existing_config = load_user_config(display_id)
    if not existing_config:
        # Should not happen if user is logged in, but handle gracefully
        stations = get_all_stations()
        return templates.TemplateResponse("config.html", {
            "request": request,
            "display_id": display_id,
            "stations": stations,
            "config": {
                'gtfs_id': gtfs_id,
                'min_minutes': min_minutes,
                'max_minutes': max_minutes,
                'display_res': display_res,
                'custom_note': custom_note
            },
            "message": "Configuration not found. Please contact administrator.",
            "message_type": "error",
            "root_path": request.app.root_path
        })
    
    # Get selected lines from form data
    form_data = await request.form()
    selected_lines = form_data.getlist('selected_lines')
    
    # Save configuration (keep existing password and weather data)
    config = {
        'gtfs_id': gtfs_id,
        'min_minutes': min_minutes,
        'max_minutes': max_minutes,
        'display_res': display_res,
        'custom_note': custom_note[:200],  # Enforce 200 char limit
        'selected_lines': selected_lines,
        'password': existing_config['password'],
        'weather_data': existing_config.get('weather_data', {'temp_c': '--', 'temp_f': '--', 'condition': 'N/A', 'icon': 'cloud', 'high_c': '--', 'low_c': '--'})
    }
    save_user_config(display_id, config)
    
    # Redirect to display page
    return RedirectResponse(
        url=f"/{display_id}",
        status_code=303
    )


@app.get("/render/{display_id}")
async def render_display(display_id: str):
    """
    Server-side screenshot rendering endpoint.
    Returns a PNG image of the display page at 800x480 resolution.
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Screenshot service unavailable. Playwright not installed."
        )
    
    if not browser_manager.page:
        raise HTTPException(
            status_code=503,
            detail="Browser not initialized"
        )
    
    try:
        # Construct URL to local display page
        url = f"http://localhost:8000/{display_id}"
        
        # Capture screenshot
        screenshot_bytes = await browser_manager.capture_screenshot(url)
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(screenshot_bytes),
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Screenshot capture failed: {str(e)}"
        )


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

