import json

# Load stations data
with open('all_mta_stations.json', 'r') as f:
    data = json.load(f)

print("Looking for A40-A49 stops:")
for station_key, stops in data.items():
    for stop_info in stops:
        stop_id, feed, display_name = stop_info
        if stop_id in ['A40', 'A41', 'A42', 'A43', 'A44', 'A45', 'A46', 'A47', 'A48', 'A49']:
            print(f"{stop_id}: {display_name} (key: {station_key})")
