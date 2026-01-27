"""
Optionally rename 'mta_major_stations' to 'mta_all_stations' as requested.
"""

import json

# Load station_lines.json
with open('station_lines.json') as f:
    data = json.load(f)

print("📝 RENAMING SECTION")
print("=" * 70)

if "mta_major_stations" in data:
    print("Current key: 'mta_major_stations'")
    print(f"Entries: {len(data['mta_major_stations'])}")
    print("\nRenaming to: 'mta_all_stations'")
    
    # Rename by creating new dict with proper order
    new_data = {}
    new_data["path_stations"] = data["path_stations"]
    new_data["complexes"] = data["complexes"]
    new_data["mta_all_stations"] = data["mta_major_stations"]
    
    # Save
    with open('station_lines.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Renamed successfully!")
    print("\nFinal structure:")
    print(f"  • path_stations: {len(new_data['path_stations'])}")
    print(f"  • complexes: {len(new_data['complexes'])}")
    print(f"  • mta_all_stations: {len(new_data['mta_all_stations'])}")
elif "mta_all_stations" in data:
    print("✓ Already renamed to 'mta_all_stations'")
    print(f"Entries: {len(data['mta_all_stations'])}")
else:
    print("⚠️  Neither 'mta_major_stations' nor 'mta_all_stations' found!")
