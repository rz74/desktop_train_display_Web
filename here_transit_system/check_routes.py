import json

# Load both files
with open('station_lines.json') as f:
    sl = json.load(f)

with open('coordinate_mapping.json') as f:
    cm = json.load(f)

print("Sample from station_lines.json:")
for i, (k, v) in enumerate(list(sl['mta_major_stations'].items())[:5]):
    stop_name = cm['mta'].get(k, {}).get('stop_name', 'Unknown')
    print(f'{k} ({stop_name}): {v}')

print("\nSample from coordinate_mapping.json:")
for i, (k, v) in enumerate(list(cm['mta'].items())[:5]):
    has_routes = 'routes' in v
    print(f'{k} ({v["stop_name"]}): has routes field = {has_routes}')
    if has_routes:
        print(f'  routes: {v["routes"]}')
