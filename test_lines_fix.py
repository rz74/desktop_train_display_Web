"""
Test that stations now show lines even when real-time feed is empty.
"""

import urllib.request
import json
import time

def test_station_lines(station_name):
    """Test if a station returns lines."""
    station_encoded = station_name.replace(' ', '%20')
    url = f"http://127.0.0.1:8000/api/lines?station_id={station_encoded}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        return {"error": str(e)}

print("="*80)
print("TESTING STATION LINES WITH STATIC FALLBACK")
print("="*80)

time.sleep(2)  # Wait for server

# Test stations that previously had issues
test_stations = [
    "8 st-nyu",
    "prince st",
    "canal st",
    "houston st",
    "bleecker st",
    "astor pl",
    "times sq-42 st",
    "union sq",
    "astoria-ditmars blvd",
]

results = {"has_lines": 0, "no_lines": 0, "errors": 0}

for station in test_stations:
    print(f"\nTesting: {station}")
    lines_data = test_station_lines(station)
    
    if "error" in lines_data:
        print(f"  ✗ Error: {lines_data['error']}")
        results["errors"] += 1
    elif isinstance(lines_data, list):
        if len(lines_data) > 0:
            print(f"  ✓ Found {len(lines_data)} line(s):")
            for line in lines_data:
                print(f"    - {line.get('line_name', line.get('line_id', 'Unknown'))}")
            results["has_lines"] += 1
        else:
            print(f"  ⚠ No lines returned (empty list)")
            results["no_lines"] += 1
    else:
        print(f"  ⚠ Unexpected response: {lines_data}")
        results["no_lines"] += 1

print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"✓ Stations with lines: {results['has_lines']}/{len(test_stations)}")
print(f"⚠ Stations without lines: {results['no_lines']}/{len(test_stations)}")
print(f"✗ Errors: {results['errors']}/{len(test_stations)}")

if results['has_lines'] == len(test_stations):
    print("\n✓ ALL STATIONS NOW SHOW LINES!")
elif results['has_lines'] >= len(test_stations) * 0.9:
    print("\n⚠ Most stations working, but some issues remain")
else:
    print("\n✗ Many stations still showing no lines")

print("="*80)
