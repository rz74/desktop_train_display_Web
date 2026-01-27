"""
Debug script to check why some stations have no lines.
Tests the actual station lookup and line detection logic.
"""

import json
from underground import SubwayFeed

# Load stations
with open('all_mta_stations.json', 'r') as f:
    stations = json.load(f)

# Test station
test_station = "8th st-nyu"

print("="*80)
print("DEBUGGING STATION LINE DETECTION")
print("="*80)

# Find the station
matches = [k for k in stations.keys() if "8th" in k.lower() and "nyu" in k.lower()]
print(f"\nSearching for stations with '8th' and 'nyu':")
print(f"Matches: {matches}")

if matches:
    station_key = matches[0]
    print(f"\nFound station: {station_key}")
    print(f"Data: {stations[station_key]}")
    
    # Try to get lines for this station
    for stop_id, feed, display_name in stations[station_key]:
        print(f"\n  Stop ID: {stop_id}")
        print(f"  Feed: {feed}")
        print(f"  Display Name: {display_name}")
        
        # Try to query the feed
        try:
            print(f"  Testing feed '{feed}'...")
            
            # The issue might be with how we're querying
            # Let's check what stop IDs the feed actually knows about
            subway_feed = SubwayFeed.get(feed)
            
            # Get all stop IDs in the feed
            all_stops = set()
            for train in subway_feed.extract_stop_dict().values():
                for stop in train:
                    all_stops.add(stop[0])  # stop_id
            
            print(f"  Feed has {len(all_stops)} stops")
            
            # Check if our stop_id is in the feed
            # The issue might be N/S suffix
            if stop_id in all_stops:
                print(f"  ✓ Stop ID '{stop_id}' found in feed")
            elif stop_id + "N" in all_stops:
                print(f"  ⚠ Stop ID needs 'N' suffix: '{stop_id}N'")
            elif stop_id + "S" in all_stops:
                print(f"  ⚠ Stop ID needs 'S' suffix: '{stop_id}S'")
            else:
                print(f"  ✗ Stop ID '{stop_id}' NOT in feed")
                # Show similar IDs
                similar = [s for s in all_stops if stop_id in s or s in stop_id]
                if similar:
                    print(f"    Similar stop IDs in feed: {similar[:5]}")
                    
        except Exception as e:
            print(f"  ✗ Error: {e}")

# Test a few more problematic stations
print("\n" + "="*80)
print("TESTING OTHER STATIONS")
print("="*80)

test_stations = ["canal st", "houston st", "bleecker st", "astor", "union"]

for test in test_stations:
    matches = [k for k in stations.keys() if test in k.lower()]
    if matches:
        station_key = matches[0]
        print(f"\n{station_key}:")
        for stop_id, feed, display_name in stations[station_key]:
            print(f"  {stop_id} (Feed: {feed})")
