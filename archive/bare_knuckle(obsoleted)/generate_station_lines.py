"""
Generate a comprehensive station-to-lines mapping from MTA GTFS Static data.
This will provide fallback line information even when real-time feed is empty.
"""

import requests
import csv
import json
from io import StringIO

def download_and_parse():
    """Download station data and create station-to-lines mapping."""
    
    print("Downloading MTA GTFS Static station data...")
    
    url = "http://web.mta.info/developers/data/nyct/subway/Stations.csv"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    print("✓ Downloaded stations data")
    
    # Parse CSV
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    
    # Build station to lines mapping
    station_lines = {}
    
    for row in reader:
        stop_id = row.get('GTFS Stop ID', '').strip()
        station_name = row.get('Stop Name', '').strip()
        routes = row.get('Daytime Routes', '').strip()
        
        if not stop_id or not station_name or not routes:
            continue
        
        # Normalize station name
        search_name = station_name.lower().replace(' station', '')
        
        # Parse routes (space-separated)
        route_list = routes.split()
        
        if search_name in station_lines:
            # Add routes to existing station
            station_lines[search_name]['routes'].update(route_list)
            station_lines[search_name]['stop_ids'].append(stop_id)
        else:
            station_lines[search_name] = {
                'display_name': station_name,
                'routes': set(route_list),
                'stop_ids': [stop_id]
            }
    
    # Convert sets to sorted lists
    for station_data in station_lines.values():
        station_data['routes'] = sorted(list(station_data['routes']))
    
    return station_lines

def main():
    station_lines = download_and_parse()
    
    print(f"✓ Parsed {len(station_lines)} stations")
    
    # Save to JSON
    with open('station_lines_map.json', 'w') as f:
        json.dump(station_lines, f, indent=2)
    
    print(f"✓ Saved to station_lines_map.json")
    
    # Test a few stations
    print("\n" + "="*60)
    print("SAMPLE STATION LINES")
    print("="*60)
    
    test_stations = ["8 st-nyu", "times sq-42 st", "canal st", "union sq"]
    
    for test in test_stations:
        matches = [k for k in station_lines.keys() if test in k]
        if matches:
            station_key = matches[0]
            data = station_lines[station_key]
            print(f"\n{data['display_name']}:")
            print(f"  Routes: {', '.join(data['routes'])}")
            print(f"  Stop IDs: {', '.join(data['stop_ids'][:3])}")
        else:
            print(f"\n✗ '{test}' not found")

if __name__ == "__main__":
    main()
