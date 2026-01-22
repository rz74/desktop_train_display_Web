import json
import requests
import time

# Wait for server to start
time.sleep(2)

# Test searches
test_queries = [
    "queens",
    "coney island", 
    "flushing",
    "astoria",
    "brooklyn",
    "bronx",
    "yankee",
]

print("Testing comprehensive station coverage:")
print("=" * 60)

for query in test_queries:
    try:
        response = requests.get(f"http://127.0.0.1:8000/search?query={query}")
        results = response.json()
        print(f"\n'{query}' → {len(results)} results")
        for station in results[:5]:
            print(f"  • {station}")
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more")
    except Exception as e:
        print(f"\n'{query}' → ERROR: {e}")

# Count total stations
print("\n" + "=" * 60)
print("STATION STATISTICS:")
print("=" * 60)

with open('all_mta_stations.json', 'r') as f:
    data = json.load(f)
    
mta_count = len(data)
path_count = 13  # Fixed PATH count

print(f"MTA Stations: {mta_count}")
print(f"PATH Stations: {path_count}")
print(f"Total Coverage: {mta_count + path_count} stations")
print(f"\nMTA System Total: ~472 stations")
print(f"Coverage Percentage: {(mta_count / 472) * 100:.1f}%")
