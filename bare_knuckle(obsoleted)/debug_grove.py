"""
Debug PATH station line detection
"""
import json

# Simulate the station_id that comes in
station_id = "grove_street"
station_id_lower = station_id.lower().replace("_", " ")

print(f"Searching for: '{station_id}'")
print(f"Normalized: '{station_id_lower}'")

# Load PATH stations
from mappings import PATH_STATIONS, PATH_STATION_ROUTES, PATH_ROUTES_ABBREV

print(f"\nPATH_STATIONS:")
for stop_id, name in PATH_STATIONS.items():
    name_normalized = name.lower().replace(" ", "_")
    match = station_id_lower == name.lower().replace(" ", "_")
    print(f"  {stop_id}: {name} -> '{name_normalized}' -> Match: {match}")

print(f"\nChecking Grove Street (26728):")
if "26728" in PATH_STATION_ROUTES:
    print(f"  Routes: {PATH_STATION_ROUTES['26728']}")
    for route_id in PATH_STATION_ROUTES['26728']:
        abbrev = PATH_ROUTES_ABBREV.get(route_id, route_id)
        print(f"    {route_id} -> {abbrev}")
else:
    print("  NOT FOUND in PATH_STATION_ROUTES")
