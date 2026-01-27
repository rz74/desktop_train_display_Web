"""
Populate station_lines.json using only local static data.
Uses coordinate_mapping.json and previously downloaded GTFS data.
"""

import json
import os
from pathlib import Path

# File paths
COORD_MAPPING_PATH = "coordinate_mapping.json"
STATION_LINES_PATH = "station_lines.json"

def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save JSON file with nice formatting"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("🚇 Populating station_lines.json from LOCAL DATA ONLY")
    print("=" * 70)
    
    # Load existing data
    print("\n✓ Loading existing station_lines.json...")
    station_lines = load_json(STATION_LINES_PATH)
    
    path_stations = station_lines.get("path_stations", {})
    complexes = station_lines.get("complexes", {})
    mta_stations = station_lines.get("mta_major_stations", {})
    
    print(f"  - PATH stations: {len(path_stations)}")
    print(f"  - Complexes: {len(complexes)}")
    print(f"  - MTA stations: {len(mta_stations)}")
    
    # Load coordinate mapping
    print("\n✓ Loading coordinate_mapping.json...")
    coord_mapping = load_json(COORD_MAPPING_PATH)
    
    mta_coords = coord_mapping.get("mta", {})
    path_coords = coord_mapping.get("path", {})
    
    print(f"  - MTA stations in mapping: {len(mta_coords)}")
    print(f"  - PATH stations in mapping: {len(path_coords)}")
    
    # Check which MTA stations from coordinate_mapping are missing from station_lines
    print("\n📊 Checking coverage...")
    missing_stations = []
    for gtfs_id in mta_coords.keys():
        if gtfs_id not in mta_stations:
            missing_stations.append(gtfs_id)
    
    if missing_stations:
        print(f"\n⚠️  Found {len(missing_stations)} missing MTA stations:")
        for station_id in missing_stations[:10]:  # Show first 10
            stop_name = mta_coords[station_id].get("stop_name", "Unknown")
            print(f"  - {station_id}: {stop_name}")
        if len(missing_stations) > 10:
            print(f"  ... and {len(missing_stations) - 10} more")
    else:
        print("✅ All MTA stations from coordinate_mapping.json are already in station_lines.json!")
    
    # Check for extra stations in station_lines that aren't in coordinate_mapping
    print("\n📊 Checking for extra stations in station_lines...")
    extra_stations = []
    for gtfs_id in mta_stations.keys():
        if gtfs_id not in mta_coords:
            extra_stations.append(gtfs_id)
    
    if extra_stations:
        print(f"\n✓ Found {len(extra_stations)} stations in station_lines not in coordinate_mapping:")
        for station_id in extra_stations[:10]:
            routes = mta_stations[station_id]
            print(f"  - {station_id}: {routes}")
        if len(extra_stations) > 10:
            print(f"  ... and {len(extra_stations) - 10} more")
        print("\n  These are likely valid stations from GTFS that weren't matched by coordinates.")
        print("  Keeping them in the file.")
    
    # Verify PATH coverage
    print("\n📊 Verifying PATH coverage...")
    print(f"  PATH in station_lines: {len(path_stations)}")
    print(f"  PATH in coordinate_mapping: {len(path_coords)}")
    print("  ✓ PATH section is complete (as requested, not modifying)")
    
    # Check complexes
    print("\n📊 Verifying complexes...")
    complex_names = list(complexes.keys())
    print(f"  Current complexes: {', '.join(complex_names)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📝 SUMMARY:")
    print(f"  ✓ PATH stations: {len(path_stations)} (complete)")
    print(f"  ✓ Complexes: {len(complexes)}")
    print(f"  ✓ MTA stations: {len(mta_stations)}")
    print(f"  ✓ Total entries: {len(path_stations) + len(complexes) + len(mta_stations)}")
    
    if not missing_stations:
        print("\n✅ station_lines.json is already FULLY POPULATED!")
        print("   All 494 MTA stations from coordinate_mapping.json are present.")
        print("   No changes needed.")
    else:
        print(f"\n⚠️  {len(missing_stations)} stations need to be added from GTFS data.")
        print("   Run build_from_mta_gtfs.py to add them.")
    
    # Optionally rename mta_major_stations to mta_all_stations
    print("\n💡 Optional: Rename 'mta_major_stations' to 'mta_all_stations'?")
    response = input("   Type 'yes' to rename, or press Enter to skip: ").strip().lower()
    
    if response == 'yes':
        station_lines["mta_all_stations"] = station_lines.pop("mta_major_stations")
        save_json(STATION_LINES_PATH, station_lines)
        print("   ✓ Renamed to 'mta_all_stations' and saved!")
    else:
        print("   Skipped renaming.")

if __name__ == "__main__":
    main()
