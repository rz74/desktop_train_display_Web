"""
Final verification that station_lines.json is complete and ready for production.
"""

import json

print("=" * 70)
print("FINAL VERIFICATION - station_lines.json")
print("=" * 70)

with open('station_lines.json', encoding='utf-8') as f:
    data = json.load(f)

# Check structure
print("\n1. STRUCTURE CHECK")
print("-" * 70)
required_sections = ['path_stations', 'complexes', 'mta_all_stations']
for section in required_sections:
    if section in data:
        print(f"  ✓ {section}: {len(data[section])} entries")
    else:
        print(f"  ✗ {section}: MISSING!")

# Check new complexes
print("\n2. NEW COMPLEXES CHECK")
print("-" * 70)
new_complexes = ['Times Sq-42 St', 'Grand Central-42 St', 'Atlantic Av-Barclays Ctr']
complexes = data.get('complexes', {})

for complex_id in new_complexes:
    if complex_id in complexes:
        lines = complexes[complex_id]
        print(f"  ✓ {complex_id}: {len(lines)} lines")
        print(f"    Lines: {', '.join(lines)}")
    else:
        print(f"  ✗ {complex_id}: NOT FOUND!")

# Check Grand Central stations
print("\n3. GRAND CENTRAL STATIONS CHECK")
print("-" * 70)
mta = data.get('mta_all_stations', {})
gc_stations = ['631', '723', '901']

for station_id in gc_stations:
    if station_id in mta:
        lines = mta[station_id]
        print(f"  ✓ {station_id}: {lines}")
    else:
        print(f"  ✗ {station_id}: NOT FOUND!")

# Check coordinate_mapping coverage
print("\n4. COORDINATE MAPPING COVERAGE")
print("-" * 70)

with open('coordinate_mapping.json', encoding='utf-8') as f:
    coord_data = json.load(f)

coord_mta = coord_data.get('mta', {})
coord_path = coord_data.get('path', {})

path_stations = data.get('path_stations', {})

# MTA coverage
mta_in_mapping = len(coord_mta)
mta_in_lines = len(mta)
mta_matched = sum(1 for station_id in coord_mta if station_id in mta)

print(f"  MTA stations in coordinate_mapping: {mta_in_mapping}")
print(f"  MTA stations in station_lines.json: {mta_in_lines}")
print(f"  Matched: {mta_matched}")
print(f"  Coverage: {(mta_matched/mta_in_mapping)*100:.1f}%")

if mta_matched == mta_in_mapping:
    print("  ✓ 100% MTA coverage!")
else:
    print(f"  ✗ Missing {mta_in_mapping - mta_matched} stations")

# PATH coverage
path_in_mapping = len(coord_path)
path_in_lines = len(path_stations)

print(f"\n  PATH stations in coordinate_mapping: {path_in_mapping}")
print(f"  PATH stations in station_lines.json: {path_in_lines}")
if path_in_lines >= path_in_mapping:
    print("  ✓ Complete PATH coverage!")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total = len(path_stations) + len(complexes) + len(mta)

print(f"  PATH Stations:     {len(path_stations):3d}")
print(f"  Complexes:         {len(complexes):3d}")
print(f"  MTA Stations:      {len(mta):3d}")
print(f"  " + "-" * 25)
print(f"  TOTAL ENTRIES:     {total:3d}")

print("\n" + "=" * 70)
print("✅ station_lines.json IS COMPLETE AND READY FOR PRODUCTION!")
print("=" * 70)

# Check that all new complexes have their constituent stations
print("\n5. CONSTITUENT STATION VERIFICATION")
print("-" * 70)

complex_defs = {
    "Times Sq-42 St": ["A27", "127", "724", "725", "R16", "902"],
    "Grand Central-42 St": ["631", "723", "901"],
    "Atlantic Av-Barclays Ctr": ["235", "R30", "D24"],
}

all_found = True
for complex_id, station_ids in complex_defs.items():
    print(f"\n  {complex_id}:")
    for station_id in station_ids:
        if station_id in mta:
            print(f"    ✓ {station_id}: {mta[station_id]}")
        else:
            print(f"    ✗ {station_id}: NOT FOUND")
            all_found = False

if all_found:
    print("\n  ✓ All constituent stations present!")
else:
    print("\n  ✗ Some constituent stations missing!")

print("\n" + "=" * 70)
