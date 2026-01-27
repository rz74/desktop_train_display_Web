import json

with open('all_mta_stations.json', 'r') as f:
    data = json.load(f)

print("Looking for stop 138 (WTC Cortlandt):")
for station_key, stops in data.items():
    for stop_info in stops:
        stop_id, feed, display_name = stop_info
        if stop_id == "138":
            print(f"Station key: {station_key}")
            print(f"  {stop_id} - Feed {feed} - {display_name}")
