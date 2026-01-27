"""
Verify that complexes in station_lines.json properly aggregate all lines
from their constituent stations according to main.py definitions.
"""

import json

# Load station_lines.json
with open('station_lines.json') as f:
    station_lines = json.load(f)

# Complex definitions from main.py
COMPLEXES_DEF = {
    "WTC": {
        "name": "World Trade Center Complex",
        "gtfs_ids": [
            "World Trade Center",  # PATH
            "142",  # Cortlandt St (R/W)
            "418",  # Fulton St (2/3/4/5/A/C/J/Z)
            "E01",  # WTC Cortlandt (1)
            "A38",  # Chambers St (A/C)
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
            "14th St",  # PATH
            "9th St",   # PATH
            "631",  # 14 St-Union Sq (4/5/6/L/N/Q/R/W)
        ]
    },
    "23rd St": {
        "name": "23rd Street Complex",
        "gtfs_ids": [
            "23rd St",  # PATH
            "631",  # 23 St (F/M)
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

print("🔍 VERIFYING COMPLEXES")
print("=" * 70)

path_stations = station_lines.get("path_stations", {})
mta_stations = station_lines.get("mta_major_stations", {})
complexes = station_lines.get("complexes", {})

for complex_id, complex_def in COMPLEXES_DEF.items():
    print(f"\n📍 {complex_def['name']} (ID: {complex_id})")
    print(f"   Constituent stations: {', '.join(complex_def['gtfs_ids'])}")
    
    # Collect all lines from constituent stations
    expected_lines = set()
    for gtfs_id in complex_def['gtfs_ids']:
        # Check PATH stations
        if gtfs_id in path_stations:
            lines = path_stations[gtfs_id]
            print(f"   - {gtfs_id} (PATH): {lines}")
            expected_lines.update(lines)
        # Check MTA stations
        elif gtfs_id in mta_stations:
            lines = mta_stations[gtfs_id]
            print(f"   - {gtfs_id} (MTA): {lines}")
            expected_lines.update(lines)
        else:
            print(f"   - {gtfs_id}: ⚠️  NOT FOUND in station_lines.json")
    
    # Check current complex entry
    current_lines = set(complexes.get(complex_id, []))
    print(f"\n   Expected lines: {sorted(expected_lines)}")
    print(f"   Current lines:  {sorted(current_lines)}")
    
    # Compare
    missing = expected_lines - current_lines
    extra = current_lines - expected_lines
    
    if missing:
        print(f"   ❌ MISSING: {sorted(missing)}")
    if extra:
        print(f"   ⚠️  EXTRA: {sorted(extra)}")
    if not missing and not extra:
        print(f"   ✅ CORRECT!")

print("\n" + "=" * 70)
print("📝 SUMMARY")
print(f"Total complexes defined in main.py: {len(COMPLEXES_DEF)}")
print(f"Total complexes in station_lines.json: {len(complexes)}")
