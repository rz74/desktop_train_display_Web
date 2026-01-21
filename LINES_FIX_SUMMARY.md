# Station Lines Fix - Summary

## Problem
Some stations showed no lines to watch, even though they should have service. For example, "8th St-NYU" showed empty lines despite being served by R and W trains.

## Root Cause
The `/api/lines` endpoint only checked the real-time GTFS-RT feed for active trains. When:
- No trains were currently running to that station
- Service was suspended or reduced
- Time of day had no scheduled service
- Feed had temporary issues

...the endpoint would return empty results.

## Solution
Added a **static fallback system** that provides line information even when real-time data is unavailable:

### 1. Generated Static Station-Lines Mapping
Created `station_lines_map.json` from MTA's GTFS Static data (Stations.csv):
- Maps each station to all lines that serve it
- 378 stations mapped
- Example: "8 st-nyu" → ["R", "W"]

### 2. Updated `app.py` Line Detection
Modified `get_station_lines()` function to:
1. **First**: Try to get lines from real-time GTFS-RT feed
2. **Fallback**: If no lines found, use static mapping from `station_lines_map.json`

This ensures every station always shows its lines, regardless of real-time service status.

## Files Modified

### 1. `generate_station_lines.py` (NEW)
- Downloads MTA Stations.csv
- Parses "Daytime Routes" column for each station
- Creates `station_lines_map.json` with station→lines mapping

### 2. `station_lines_map.json` (NEW - Generated)
Format:
```json
{
  "8 st-nyu": {
    "display_name": "8 St-NYU",
    "routes": ["R", "W"],
    "stop_ids": ["R21"]
  },
  "times sq-42 st": {
    "display_name": "Times Sq-42 St",
    "routes": ["1", "2", "3", "7", "N", "Q", "R", "S", "W"],
    "stop_ids": ["R16", "127", "725"]
  }
}
```

### 3. `app.py` (MODIFIED)
Added at startup:
```python
# Load static station-to-lines mapping (fallback for when real-time feed is empty)
STATION_LINES_MAP = {}
lines_map_path = os.path.join(os.path.dirname(__file__), 'station_lines_map.json')
if os.path.exists(lines_map_path):
    with open(lines_map_path, 'r') as f:
        STATION_LINES_MAP = json.load(f)
    print(f"✓ Loaded static lines mapping for {len(STATION_LINES_MAP)} stations")
```

Modified `get_station_lines()`:
```python
# After checking real-time feed...
# Fallback to static mapping if no lines found from real-time feed
if not routes_seen and station_id_lower in STATION_LINES_MAP:
    station_data = STATION_LINES_MAP[station_id_lower]
    for route_id in station_data.get('routes', []):
        if route_id in MTA_LINES:
            routes_seen.add(route_id)
            lines.append(LineInfo(
                line_id=f"MTA-{route_id}",
                line_name=f"MTA {route_id}",
                agency="MTA"
            ))
```

## Test Results

### Before Fix
```
8 St-NYU: [] (empty - no lines)
Prince St: [] (empty - no lines)
...many stations affected
```

### After Fix
```
8 St-NYU: [R, W]
Prince St: [N, R, W]
Canal St: [1, 6, A, C, E, J, N, Q, R, W, Z]
Houston St: [1]
Times Sq-42 St: [1, 2, 3, 7, N, Q, R, S, W]
```

## Server Status
```
✓ Loaded 380 MTA stations from all_mta_stations.json
✓ Loaded static lines mapping for 378 stations
INFO: Uvicorn running on http://127.0.0.1:8000
```

## How It Works

### Real-Time (Preferred)
1. User searches for station → finds "8 st-nyu"
2. Frontend calls `/api/lines?station_id=8 st-nyu`
3. Backend queries GTFS-RT feed for active trains at stop R21
4. If trains found → returns active lines (e.g., R train currently running)

### Static Fallback (When Real-Time Empty)
1. User searches for station → finds "8 st-nyu"
2. Frontend calls `/api/lines?station_id=8 st-nyu`
3. Backend queries GTFS-RT feed → finds no active trains
4. **Fallback triggers** → looks up "8 st-nyu" in static mapping
5. Returns all lines that serve the station: [R, W]

### Benefits
- ✓ Stations always show available lines
- ✓ Users can select lines even during service gaps
- ✓ Works during late night hours with reduced service
- ✓ Handles temporary feed outages gracefully
- ✓ Real-time data still preferred when available

## Maintenance

To update the static mapping when MTA adds/changes stations:
```bash
python generate_station_lines.py
```
This will:
1. Download latest Stations.csv from MTA
2. Regenerate station_lines_map.json
3. Restart server to load new mapping

## Verification

Test any station that previously showed no lines:
1. Open http://127.0.0.1:8000
2. Search for "8th nyu" or "prince" or "canal"
3. Station should show checkboxes for all serving lines
4. Select lines and view arrivals

**Expected**: All 378 MTA stations now show their lines, even when no trains are currently active.

---

*Fix implemented: January 21, 2026*
