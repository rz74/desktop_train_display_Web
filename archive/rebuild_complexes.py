"""
Rebuild complexes in station_lines.json with proper aggregation.
Uses all relevant station IDs for each complex.
"""

import json

# Load files
with open('station_lines.json') as f:
    station_lines = json.load(f)

with open('coordinate_mapping.json') as f:
    coord_mapping = json.load(f)

path_stations = station_lines.get("path_stations", {})
mta_stations = station_lines.get("mta_major_stations", {})

# Properly defined complexes with ALL constituent stations
COMPLEXES_PROPER = {
    "WTC": {
        "name": "World Trade Center Complex",
        "stations": {
            # PATH
            "World Trade Center": ["NWK-WTC"],
            # All Fulton St platforms
            "418": ["4", "5"],  # Fulton St (Lexington)
            "229": ["2", "3"],  # Fulton St (Broadway)
            "A38": ["A", "C"],  # Fulton St (8th Ave)
            "M22": ["J", "Z"],  # Fulton St (Nassau)
            # Cortlandt/WTC stations
            "138": ["1"],  # WTC Cortlandt (Broadway-7th Ave)
            "R25": ["N", "R", "W"],  # Cortlandt St (Broadway)
            # Nearby Chambers St (connects via Park Place)
            "137": ["1", "2", "3"],  # Chambers St (Broadway-7th Ave)
            "A36": ["A", "C"],  # Chambers St (8th Ave)
            "M21": ["J", "Z"],  # Chambers St (Nassau)
        }
    },
    "33rd St": {
        "name": "33rd Street Complex (Herald Sq / PATH)",
        "stations": {
            # PATH
            "33rd St": ["JSQ-33", "HOB-33"],
            # Herald Sq platforms (34 St)
            "R17": ["N", "Q", "R", "W"],  # 34 St-Herald Sq (Broadway)
            "D17": ["B", "D", "F", "FX", "M"],  # 34 St-Herald Sq (6th Ave)
        }
    },
    "14th St": {
        "name": "14th Street Complex (Union Sq / PATH)",
        "stations": {
            # PATH
            "14th St": ["JSQ-33", "HOB-33"],
            "9th St": ["JSQ-33", "HOB-33"],
            # Union Sq platforms
            "635": ["4", "5", "6", "6X"],  # 14 St-Union Sq (Lexington)
            "L03": ["L"],  # 14 St-Union Sq (14th St-Canarsie)
            "R20": ["N", "Q", "R", "W"],  # 14 St-Union Sq (Broadway)
        }
    },
    "23rd St": {
        "name": "23rd Street Complex (PATH/Multiple Lines)",
        "stations": {
            # PATH
            "23rd St": ["JSQ-33", "HOB-33"],
            # 23 St stations on different lines
            "R19": ["N", "Q", "R", "W"],  # 23 St (Broadway)
            "D18": ["F", "FX", "M"],  # 23 St (6th Ave)
            "634": ["4", "6", "6X"],  # 23 St-Baruch College (Lexington)
            "A30": ["A", "C", "E"],  # 23 St (8th Ave)
            "130": ["1", "2"],  # 23 St (Broadway-7th Ave)
        }
    },
    "Christopher St": {
        "name": "Christopher Street Complex",
        "stations": {
            # PATH
            "Christopher Street": ["JSQ-33", "HOB-33"],
            # Christopher St MTA
            "133": ["1", "2"],  # Christopher St-Stonewall (Broadway-7th Ave)
        }
    },
}

print("🔧 REBUILDING COMPLEXES")
print("=" * 70)

new_complexes = {}

for complex_id, complex_def in COMPLEXES_PROPER.items():
    print(f"\n📍 {complex_def['name']}")
    
    all_lines = set()
    
    for station_id, expected_lines in complex_def['stations'].items():
        # Get actual lines from station_lines.json
        if station_id in path_stations:
            actual_lines = path_stations[station_id]
            source = "PATH"
        elif station_id in mta_stations:
            actual_lines = mta_stations[station_id]
            source = "MTA"
        else:
            print(f"   ⚠️  {station_id} NOT FOUND")
            continue
        
        print(f"   {station_id} ({source}): {actual_lines}")
        all_lines.update(actual_lines)
    
    # Sort the lines nicely (numbers first, then letters, then special)
    def sort_key(line):
        if line.isdigit():
            return (0, int(line))
        elif len(line) == 1:
            return (1, line)
        elif line in ["SIR", "FX", "6X", "7X"]:
            return (2, line)
        else:
            return (3, line)
    
    sorted_lines = sorted(all_lines, key=sort_key)
    new_complexes[complex_id] = sorted_lines
    
    print(f"   ➜ Aggregated: {sorted_lines}")

# Update station_lines.json
station_lines['complexes'] = new_complexes

# Save
with open('station_lines.json', 'w', encoding='utf-8') as f:
    json.dump(station_lines, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print("✅ UPDATED station_lines.json")
print(f"\nNew complexes:")
for complex_id, lines in new_complexes.items():
    print(f"  {complex_id}: {lines}")
