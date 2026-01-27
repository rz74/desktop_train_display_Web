"""
Fix complexes in station_lines.json to properly aggregate all lines
from constituent stations according to main.py definitions.
"""

import json

# Load station_lines.json
with open('station_lines.json') as f:
    station_lines = json.load(f)

# Complex definitions from main.py with proper aggregation
COMPLEXES_FIX = {
    "WTC": {
        "name": "World Trade Center Complex",
        "constituent_stations": {
            "World Trade Center": "PATH",  # NWK-WTC
            "142": "MTA",  # Cortlandt St (R/W) -- but MTA data shows only 1
            "418": "MTA",  # Fulton St (2/3/4/5/A/C/J/Z) -- but MTA data shows 4,5
            "E01": "MTA",  # WTC Cortlandt (1) -- but MTA data shows E
            "A38": "MTA",  # Chambers St (A/C)
        },
        # Let's check what the GTFS actually has for these stations
    },
    "33rd St": {
        "name": "33rd Street Complex",
        "constituent_stations": {
            "33rd St": "PATH",  # JSQ-33, HOB-33
            "127": "MTA",  # 34 St-Herald Sq -- but this is Times Sq-42 St
        },
        # 127 is Times Sq-42 St (1/2/3), not Herald Sq
        # Herald Sq should be station 633
    },
}

print("🔍 INVESTIGATING STATION IDs")
print("=" * 70)

path_stations = station_lines.get("path_stations", {})
mta_stations = station_lines.get("mta_major_stations", {})

# Check what these stations actually are
stations_to_check = ["127", "142", "418", "E01", "A38", "631", "633", "A31"]

for station_id in stations_to_check:
    if station_id in mta_stations:
        lines = mta_stations[station_id]
        print(f"{station_id}: {lines}")

print("\n🔍 SEARCHING FOR SPECIFIC STATIONS")
print("=" * 70)

# Load coordinate mapping to see station names
with open('coordinate_mapping.json') as f:
    coord_mapping = json.load(f)

# Find Herald Square
print("\nSearching for Herald Square (34 St):")
for station_id, data in coord_mapping['mta'].items():
    if 'herald' in data['stop_name'].lower() or ('34' in data['stop_name'] and 'herald' in data['stop_name'].lower()):
        lines = mta_stations.get(station_id, [])
        print(f"  {station_id}: {data['stop_name']} -> {lines}")

# Find Union Square (14 St)
print("\nSearching for Union Square (14 St):")
for station_id, data in coord_mapping['mta'].items():
    if 'union' in data['stop_name'].lower():
        lines = mta_stations.get(station_id, [])
        print(f"  {station_id}: {data['stop_name']} -> {lines}")

# Find 23 St stations
print("\nSearching for 23 St stations:")
for station_id, data in coord_mapping['mta'].items():
    if data['stop_name'].startswith('23 St'):
        lines = mta_stations.get(station_id, [])
        print(f"  {station_id}: {data['stop_name']} -> {lines}")

# Find Christopher St stations
print("\nSearching for Christopher St / Sheridan Sq:")
for station_id, data in coord_mapping['mta'].items():
    if 'christopher' in data['stop_name'].lower() or 'sheridan' in data['stop_name'].lower():
        lines = mta_stations.get(station_id, [])
        print(f"  {station_id}: {data['stop_name']} -> {lines}")

# Find Fulton St
print("\nSearching for Fulton St:")
for station_id, data in coord_mapping['mta'].items():
    if 'fulton' in data['stop_name'].lower():
        lines = mta_stations.get(station_id, [])
        print(f"  {station_id}: {data['stop_name']} -> {lines}")

# Find Cortlandt St / WTC Cortlandt
print("\nSearching for Cortlandt / WTC:")
for station_id, data in coord_mapping['mta'].items():
    if 'cortlandt' in data['stop_name'].lower() or (data['stop_name'].startswith('WTC') and 'world' not in data['stop_name'].lower()):
        lines = mta_stations.get(station_id, [])
        print(f"  {station_id}: {data['stop_name']} -> {lines}")

# Find Chambers St
print("\nSearching for Chambers St:")
for station_id, data in coord_mapping['mta'].items():
    if 'chambers' in data['stop_name'].lower():
        lines = mta_stations.get(station_id, [])
        print(f"  {station_id}: {data['stop_name']} -> {lines}")
