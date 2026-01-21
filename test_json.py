import json
import os

# Test JSON loading
json_path = os.path.join(os.path.dirname(__file__), 'all_mta_stations.json')
print(f"Looking for JSON at: {json_path}")
print(f"File exists: {os.path.exists(json_path)}")

if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    print(f"✓ Loaded {len(data)} stations")
    
    # Test a few searches
    test_queries = ["queens", "astoria", "coney", "flushing", "bronx"]
    
    for query in test_queries:
        matches = [s for s in data.keys() if query.lower() in s.lower()]
        print(f"\n'{query}' → {len(matches)} matches")
        for m in matches[:3]:
            print(f"  • {m}: {data[m]}")
else:
    print("ERROR: JSON file not found!")
