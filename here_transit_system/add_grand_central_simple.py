"""
Add missing stations 723 and 901 for Grand Central complex
Based on NYC subway system knowledge
"""

import json

print("Adding missing Grand Central stations 723 and 901")
print("=" * 70)

with open('station_lines.json', encoding='utf-8') as f:
    sl = json.load(f)

mta = sl.get('mta_all_stations', {})

# Grand Central-42 St has multiple platform IDs:
# 631: Main Grand Central (4/5/6)
# 723: Likely the 7 train platform at Grand Central
# 901: Likely the shuttle (S) platform

print("\nCurrent Grand Central entries:")
if '631' in mta:
    print(f"  631: {mta['631']}")
if '723' in mta:
    print(f"  723: {mta['723']}")
else:
    print("  723: NOT FOUND")
if '901' in mta:
    print(f"  901: {mta['901']}")
else:
    print("  901: NOT FOUND")

# According to MTA system:
# - Station 723 serves the 7 train
# - Station 901 serves the Grand Central Shuttle (S)

added_count = 0

if '723' not in mta:
    mta['723'] = ['7', '7X']
    print("\nAdded 723 (7 train platform): ['7', '7X']")
    added_count += 1

if '901' not in mta:
    mta['901'] = ['S']
    print("Added 901 (shuttle platform): ['S']")
    added_count += 1

if added_count > 0:
    sl['mta_all_stations'] = mta
    
    with open('station_lines.json', 'w', encoding='utf-8') as f:
        json.dump(sl, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved! Added {added_count} stations")
    print(f"Total MTA stations: {len(mta)}")
else:
    print("\nNo stations added - they already exist")

print("\n" + "=" * 70)
print("Grand Central-42 St complex now includes:")
print("  631: 4, 5, 6, 6X (Lexington line)")
print("  723: 7, 7X (Flushing line)")
print("  901: S (Grand Central Shuttle)")
