"""
Merge all discovered stations into final comprehensive stations.json
"""
import json
from pathlib import Path

# Load all discovered stations
all_stations_file = Path(__file__).parent / "all_stations_discovered.json"
with open(all_stations_file, 'r') as f:
    all_stations = json.load(f)

# Load missing stations found
missing_file = Path(__file__).parent / "missing_stations_found.json"
with open(missing_file, 'r') as f:
    missing_stations = json.load(f)

# Merge everything - create final stations map
final_stations = {}

# Add all originally discovered stations (exclude NOT_FOUND)
for key, info in all_stations.items():
    if not info['id'].startswith('NOT_FOUND'):
        final_stations[key] = info['id']

# Add the newly found missing stations (exclude NOT_FOUND)
for key, station_id in missing_stations.items():
    if not station_id.startswith('NOT_FOUND'):
        final_stations[key] = station_id

# Create organized structure for display
stations_organized = {
    "path": {
        "newark_line": {
            "newark": final_stations.get("newark"),
            "harrison": final_stations.get("harrison"),
            "jsq": final_stations.get("jsq")
        },
        "jsq_33rd_line": {
            "jsq": final_stations.get("jsq"),
            "grove": final_stations.get("grove"),
            "exchange": final_stations.get("exchange"),
            "wtc_path": final_stations.get("wtc_path"),
            "christopher": final_stations.get("christopher"),
            "9th_street": final_stations.get("9th_street"),
            "14th_street": final_stations.get("14th_street"),
            "23rd_street": final_stations.get("23rd_street"),
            "33rd_street": final_stations.get("33rd_street")
        },
        "hoboken_line": {
            "hoboken": final_stations.get("hoboken"),
            "christopher": final_stations.get("christopher"),
            "9th_street": final_stations.get("9th_street"),
            "14th_street": final_stations.get("14th_street"),
            "23rd_street": final_stations.get("23rd_street"),
            "33rd_street": final_stations.get("33rd_street")
        }
    },
    "mta": {
        "lower_manhattan": {
            "fulton": final_stations.get("fulton"),
            "cortlandt": final_stations.get("cortlandt"),
            "city_hall": final_stations.get("city_hall"),
            "canal": final_stations.get("canal")
        },
        "midtown": {
            "herald_square": final_stations.get("herald_square"),
            "penn_station": final_stations.get("penn_station"),
            "port_authority": final_stations.get("port_authority"),
            "grand_central": final_stations.get("grand_central"),
            "lexington_53": final_stations.get("lexington_53"),
            "lexington_59": final_stations.get("lexington_59")
        },
        "union_square_area": {
            "union_square": final_stations.get("union_square"),
            "astor_place": final_stations.get("astor_place")
        },
        "upper_manhattan": {
            "columbus_circle": final_stations.get("columbus_circle"),
            "72nd_street": final_stations.get("72nd_street"),
            "86th_street": final_stations.get("86th_street"),
            "96th_street": final_stations.get("96th_street")
        },
        "brooklyn": {
            "atlantic_terminal": final_stations.get("atlantic_terminal"),
            "jay_street": final_stations.get("jay_street")
        },
        "queens": {
            "queensboro": final_stations.get("queensboro"),
            "jackson_heights": final_stations.get("jackson_heights")
        }
    }
}

# Clean up None values
def remove_none(d):
    if isinstance(d, dict):
        return {k: remove_none(v) for k, v in d.items() if v is not None}
    return d

stations_organized = remove_none(stations_organized)

# Save files
# 1. Flat map for API
flat_map_file = Path(__file__).parent / "stations.json"
with open(flat_map_file, 'w') as f:
    json.dump(final_stations, f, indent=2, sort_keys=True)

# 2. Organized for frontend
organized_file = Path(__file__).parent / "stations_organized.json"
with open(organized_file, 'w') as f:
    json.dump(stations_organized, f, indent=2)

# Print summary
print("="*80)
print("FINAL STATIONS SUMMARY")
print("="*80)

path_count = sum(1 for k in final_stations.keys() if k in ['newark', 'harrison', 'jsq', 'grove', 'exchange', 'wtc_path', 'christopher', '9th_street', '14th_street', '23rd_street', '33rd_street', 'hoboken'])
mta_count = len(final_stations) - path_count

print(f"\nTotal Stations: {len(final_stations)}")
print(f"  PATH: {path_count}")
print(f"  MTA: {mta_count}")

print(f"\n✓ Saved flat map to: {flat_map_file}")
print(f"✓ Saved organized map to: {organized_file}")

print("\nAll station keys:")
for i, key in enumerate(sorted(final_stations.keys()), 1):
    print(f"  {i:2d}. {key}")
