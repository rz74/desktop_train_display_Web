import json

with open('here_stations.json', 'r') as f:
    data = json.load(f)

print("="*60)
print("DISCOVERY RESULTS SUMMARY")
print("="*60)
print(f"\nMTA Stations: {len(data['mta'])} found")
print(f"PATH Stations: {len(data['path'])} found")
print(f"Total: {len(data['mta']) + len(data['path'])} stations mapped to HERE IDs")
print(f"\nOriginal: {data['metadata']['total_stations']} stations searched")
print(f"Match Rate: {data['metadata']['found_stations']*100//data['metadata']['total_stations']}%")

print("\n" + "="*60)
print("PATH STATIONS FOUND:")
print("="*60)
for name, info in data['path'].items():
    print(f"  {name:30s} -> {info['here_name']}")

print("\n" + "="*60)
print("SAMPLE MTA STATIONS (first 10):")
print("="*60)
for i, (name, info) in enumerate(list(data['mta'].items())[:10]):
    print(f"  {name:30s} -> {info['here_name']}")
