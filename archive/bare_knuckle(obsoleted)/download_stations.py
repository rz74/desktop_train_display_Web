"""
Download and parse MTA GTFS Static data to get ALL station names and IDs
"""
import requests
import csv
from io import StringIO
import json

print("Downloading MTA GTFS Static station data...")

# MTA GTFS Static feed URL
GTFS_STATIC_URL = "http://web.mta.info/developers/data/nyct/subway/google_transit.zip"

# For now, use a direct link to stops.txt
STOPS_URL = "http://web.mta.info/developers/data/nyct/subway/Stations.csv"

try:
    response = requests.get(STOPS_URL, timeout=10)
    if response.status_code == 200:
        print(f"✓ Downloaded stations data")
        
        # Parse CSV
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        
        stations = {}
        for row in reader:
            gtfs_stop_id = row.get('GTFS Stop ID') or row.get('Stop ID')
            station_name = row.get('Stop Name') or row.get('Station Name')
            
            if gtfs_stop_id and station_name:
                # Determine which feed (rough mapping)
                feed = "1"  # Default
                if gtfs_stop_id:
                    first_char = gtfs_stop_id[0] if gtfs_stop_id else ""
                    if first_char in ['A', 'D', 'E', 'H']:
                        feed = "A"
                    elif first_char in ['R', 'Q', 'B']:
                        feed = "N"
                    elif first_char == 'L':
                        feed = "L"
                    elif first_char == 'G':
                        feed = "G"
                    elif first_char == 'J':
                        feed = "L"
                        
                # Normalize station name for dict key
                key = station_name.lower().replace("-", " ").replace("/", " ")
                
                if key not in stations:
                    stations[key] = []
                stations[key].append((gtfs_stop_id, feed, station_name))
        
        print(f"✓ Parsed {len(stations)} unique stations")
        
        # Save to JSON for easy import
        with open('all_mta_stations.json', 'w') as f:
            json.dump(stations, f, indent=2)
        
        print(f"✓ Saved to all_mta_stations.json")
        print(f"\nSample stations:")
        for i, (key, value) in enumerate(list(stations.items())[:10]):
            print(f"  {key}: {value}")
            
    else:
        print(f"✗ Failed to download: HTTP {response.status_code}")
        print("Using alternative: Build from feed analysis...")
        
        # Alternative: scan live feeds
        print("\nScanning live GTFS-RT feeds for all stops...")
        from underground import SubwayFeed
        
        all_stops = {}
        feeds_to_scan = ['1', 'A', 'N', 'L', 'G', 'SI']
        
        for feed_name in feeds_to_scan:
            print(f"  Scanning feed {feed_name}...")
            try:
                feed = SubwayFeed.get(feed_name)
                for entity in feed.entity:
                    if hasattr(entity, 'trip_update') and entity.trip_update:
                        for stop_time in entity.trip_update.stop_time_update:
                            stop_id = stop_time.stop_id.rstrip('NS')  # Remove direction suffix
                            if stop_id not in all_stops:
                                all_stops[stop_id] = feed_name
            except Exception as e:
                print(f"    Error: {e}")
        
        print(f"\n✓ Found {len(all_stops)} unique stop IDs from live feeds")
        
        # Save stop IDs
        with open('mta_stop_ids.json', 'w') as f:
            json.dump(all_stops, f, indent=2)
        
        print("✓ Saved to mta_stop_ids.json")
        print("\nNote: Stop IDs found but station names need manual mapping")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nFalling back to manual comprehensive list...")
