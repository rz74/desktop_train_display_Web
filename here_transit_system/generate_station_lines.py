"""
Generate station_lines.json by fetching live arrivals from all stations.
This script analyzes which lines actually serve each station.
"""
import json
import asyncio
from pathlib import Path
import sys

# Add parent directory to path to import from main.py
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from main import (
    STATION_MAPPING, 
    STATION_COMPLEXES, 
    STATION_AGENCY,
    DEPARTURES_URL,
    HERE_API_KEY,
    MTA_FEED_AVAILABLE,
    get_mta_arrivals
)


async def fetch_departures(here_id: str):
    """Fetch departures from HERE Transit API."""
    params = {
        'apiKey': HERE_API_KEY,
        'id': here_id,
        'maxPerBoard': 40
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(DEPARTURES_URL, params=params, timeout=15.0)
        response.raise_for_status()
        return response.json()


def transform_arrivals(api_response: dict) -> list:
    """Extract line identifiers from HERE API response."""
    lines = set()
    
    boards = api_response.get('boards', [])
    for board in boards:
        departures = board.get('departures', [])
        for dep in departures:
            transport = dep.get('transport', {})
            
            # Extract line name
            line = transport.get('shortName', '').strip()
            if not line:
                line = transport.get('name', '').strip()
                if len(line) > 4:
                    # Try to extract route from longer name
                    words = line.split()
                    for word in words:
                        if len(word) <= 3 and word[0].isalnum():
                            line = word
                            break
            
            if line and line != '?':
                lines.add(line)
    
    return list(lines)


async def fetch_station_lines(gtfs_id: str, here_id: str) -> list:
    """Fetch lines for a single station from multiple sources."""
    lines = set()
    
    # Try HERE API
    try:
        api_response = await fetch_departures(here_id)
        here_lines = transform_arrivals(api_response)
        lines.update(here_lines)
        print(f"  HERE API: {len(here_lines)} lines for {gtfs_id}")
    except Exception as e:
        print(f"  HERE API failed for {gtfs_id}: {e}")
    
    # Try MTA real-time feed if available
    if STATION_AGENCY.get(gtfs_id) == 'MTA' and MTA_FEED_AVAILABLE:
        try:
            mta_arrivals = get_mta_arrivals(gtfs_id)
            mta_lines = set([a['line'] for a in mta_arrivals if a['line'] != '?'])
            lines.update(mta_lines)
            print(f"  MTA GTFS: {len(mta_lines)} lines for {gtfs_id}")
        except Exception as e:
            print(f"  MTA GTFS failed for {gtfs_id}: {e}")
    
    return sorted(list(lines))


async def generate_all_station_lines():
    """Generate comprehensive station_lines.json from live data."""
    print("=" * 60)
    print("Generating station_lines.json from live data")
    print("=" * 60)
    
    station_lines_data = {
        "metadata": {
            "version": "2.0",
            "last_updated": "auto-generated",
            "description": "Automatically generated from live arrival data",
            "method": "HERE API + MTA Real-time feeds"
        },
        "path_stations": {},
        "complexes": {},
        "mta_stations": {}
    }
    
    # Get all stations that are part of complexes (to exclude from individual listing)
    complex_station_ids = set()
    for complex_id, complex_info in STATION_COMPLEXES.items():
        complex_station_ids.update(complex_info['gtfs_ids'])
    
    print(f"\nFound {len(STATION_COMPLEXES)} complexes with {len(complex_station_ids)} constituent stations")
    
    # Process station complexes first
    print("\n" + "=" * 60)
    print("Processing Station Complexes")
    print("=" * 60)
    
    for complex_id, complex_info in STATION_COMPLEXES.items():
        print(f"\nProcessing complex: {complex_info['name']}")
        all_lines = set()
        
        for gtfs_id in complex_info['gtfs_ids']:
            here_id = STATION_MAPPING.get(gtfs_id)
            if not here_id:
                print(f"  Skipping {gtfs_id} (no HERE mapping)")
                continue
            
            lines = await fetch_station_lines(gtfs_id, here_id)
            all_lines.update(lines)
            await asyncio.sleep(0.5)  # Rate limiting
        
        if all_lines:
            station_lines_data['complexes'][complex_id] = sorted(list(all_lines))
            print(f"  Complex {complex_id}: {len(all_lines)} unique lines - {sorted(all_lines)}")
    
    # Process individual MTA stations (excluding complex members)
    print("\n" + "=" * 60)
    print("Processing Individual MTA Stations")
    print("=" * 60)
    
    mta_count = 0
    mta_with_lines = 0
    
    for gtfs_id, here_id in STATION_MAPPING.items():
        # Skip if part of a complex
        if gtfs_id in complex_station_ids:
            continue
        
        # Only process MTA stations
        if STATION_AGENCY.get(gtfs_id) != 'MTA':
            continue
        
        mta_count += 1
        print(f"\n[{mta_count}] Processing MTA station: {gtfs_id}")
        
        lines = await fetch_station_lines(gtfs_id, here_id)
        
        if lines:
            station_lines_data['mta_stations'][gtfs_id] = lines
            mta_with_lines += 1
            print(f"  ✓ Found {len(lines)} lines: {lines}")
        else:
            print(f"  ✗ No lines found")
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Process PATH stations
    print("\n" + "=" * 60)
    print("Processing PATH Stations")
    print("=" * 60)
    
    path_count = 0
    
    for gtfs_id, here_id in STATION_MAPPING.items():
        # Skip if part of a complex
        if gtfs_id in complex_station_ids:
            continue
        
        # Only process PATH stations
        if STATION_AGENCY.get(gtfs_id) != 'PATH':
            continue
        
        path_count += 1
        print(f"\n[{path_count}] Processing PATH station: {gtfs_id}")
        
        lines = await fetch_station_lines(gtfs_id, here_id)
        
        if lines:
            station_lines_data['path_stations'][gtfs_id] = lines
            print(f"  ✓ Found {len(lines)} lines: {lines}")
        else:
            print(f"  ✗ No lines found")
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Save results
    output_file = Path(__file__).parent / "station_lines.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(station_lines_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Complexes processed: {len(station_lines_data['complexes'])}")
    print(f"MTA stations processed: {mta_count}")
    print(f"MTA stations with lines: {mta_with_lines}")
    print(f"PATH stations processed: {path_count}")
    print(f"PATH stations with lines: {len(station_lines_data['path_stations'])}")
    print(f"\nOutput saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(generate_all_station_lines())
