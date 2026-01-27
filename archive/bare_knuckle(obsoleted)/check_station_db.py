"""
Simple manual test - check station count and verify key stations exist.
"""

import json
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load stations
with open('all_mta_stations.json', 'r') as f:
    stations = json.load(f)

print("="*80)
print("STATION DATABASE ANALYSIS")
print("="*80)

print(f"\nTotal entries in JSON: {len(stations)}")

# Count unique stop IDs
unique_stops = set()
for station_entries in stations.values():
    for entry in station_entries:
        unique_stops.add(entry[0])  # stop_id

print(f"Unique stop IDs: {len(unique_stops)}")
print(f"MTA system total: ~472 stations")
print(f"Coverage: {(len(unique_stops)/472)*100:.1f}%")

# Test key stations by searching keys
test_queries = {
    "Times Square": ["times sq", "times square", "42 st"],
    "Grand Central": ["grand central", "42 st"],
    "Coney Island": ["coney", "coney island", "stillwell"],
    "Flushing": ["flushing", "main st"],
    "Jamaica": ["jamaica", "179"],
    "Astoria": ["astoria", "ditmars"],
    "Yankee Stadium": ["yankee", "161 st"],
    "JFK Airport": ["howard beach", "jfk"],
    "WTC": ["world trade", "wtc"],
    "Penn Station": ["penn", "34 st"],
}

print("\n" + "="*80)
print("KEY STATION AVAILABILITY CHECK")
print("="*80)

all_found = True
for station_name, search_terms in test_queries.items():
    found = False
    found_key = None
    for term in search_terms:
        term_lower = term.lower()
        matches = [k for k in stations.keys() if term_lower in k.lower()]
        if matches:
            found = True
            found_key = matches[0]
            break
    
    if found:
        print(f"✓ {station_name:20} - Found as '{found_key}'")
        # Show the entries
        for entry in stations[found_key]:
            print(f"    └─ Stop ID: {entry[0]}, Feed: {entry[1]}, Name: {entry[2]}")
    else:
        print(f"✗ {station_name:20} - NOT FOUND (searched: {search_terms})")
        all_found = False

# Check PATH stations
print("\n" + "="*80)
print("PATH STATION AVAILABILITY (should be in DUAL_SYSTEM_STATIONS)")
print("="*80)

path_searches = ["world trade center", "14", "23", "33"]
for search in path_searches:
    matches = [k for k in stations.keys() if search in k.lower()]
    if matches:
        print(f"✓ PATH stations with '{search}': {matches}")
    else:
        print(f"✗ No matches for '{search}'")

# Sample stations from each borough
print("\n" + "="*80)
print("SAMPLE STATIONS BY BOROUGH")
print("="*80)

borough_samples = {
    "Manhattan": ["times sq", "grand central", "wall st", "inwood"],
    "Brooklyn": ["coney", "atlantic", "borough hall", "bedford"],
    "Queens": ["flushing", "jamaica", "astoria", "forest hills"],
    "Bronx": ["yankee", "pelham", "woodlawn", "fordham"],
}

for borough, searches in borough_samples.items():
    print(f"\n{borough}:")
    for search in searches:
        matches = [k for k in stations.keys() if search in k.lower()]
        if matches:
            print(f"  ✓ '{search}' → {len(matches)} match(es): {matches[0]}")
        else:
            print(f"  ✗ '{search}' → NO MATCH")

# Final verdict
print("\n" + "="*80)
print("VERDICT")
print("="*80)

if len(unique_stops) >= 378:
    print(f"✓ COMPREHENSIVE COVERAGE: {len(unique_stops)} unique stops")
    print(f"✓ {len(stations)} searchable entries (including aliases)")
    
    if all_found:
        print("✓ ALL KEY STATIONS VERIFIED")
    else:
        print("⚠ SOME KEY STATIONS MISSING FROM SEARCH TERMS")
        
    if len(unique_stops) >= 472:
        print("✓ 100% COVERAGE ACHIEVED!")
    else:
        print(f"⚠ Coverage: {(len(unique_stops)/472)*100:.1f}% ({472-len(unique_stops)} stations remaining)")
else:
    print(f"✗ INSUFFICIENT COVERAGE: Only {len(unique_stops)} stops")

print("="*80)
