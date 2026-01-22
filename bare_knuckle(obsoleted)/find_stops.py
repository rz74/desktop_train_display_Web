import json

with open('all_mta_stations.json', 'r') as f:
    data = json.load(f)

print("Looking for WTC/Cortlandt stops:")
for station_key, stops in data.items():
    if 'world trade' in station_key.lower() or 'wtc' in station_key.lower() or 'cortlandt' in station_key.lower():
        print(f"\nStation key: {station_key}")
        for stop_info in stops:
            stop_id, feed, display_name = stop_info
            print(f"  {stop_id} - Feed {feed} - {display_name}")
