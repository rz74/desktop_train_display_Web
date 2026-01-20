"""Explore all MTA stations available in underground library"""
from underground import metadata
import json

print(f"Total stops in metadata: {len(metadata.stops)}")
print("\nSample stops:")

# Show first 20 stops
for i, (stop_id, stop_info) in enumerate(list(metadata.stops.items())[:20]):
    print(f"{stop_id}: {stop_info}")
    
# Find stations with "Herald" in name
print("\n\nSearching for 'Herald Square':")
for stop_id, stop_info in metadata.stops.items():
    if 'Herald' in stop_info.get('stop_name', ''):
        print(f"{stop_id}: {stop_info}")

# Find stations with "Grand Central"
print("\n\nSearching for 'Grand Central':")
for stop_id, stop_info in metadata.stops.items():
    if 'Grand Central' in stop_info.get('stop_name', ''):
        print(f"{stop_id}: {stop_info}")
