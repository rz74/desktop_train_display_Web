"""
Debug the HERE API response for departures
"""
import httpx
import json
from pathlib import Path

# Load API key
env_file = Path(__file__).parent / ".env.example"
with open(env_file, 'r') as f:
    for line in f:
        if line.startswith('HERE_API_KEY='):
            HERE_API_KEY = line.split('=', 1)[1].strip()
            break

# Load stations
with open('stations.json', 'r') as f:
    stations = json.load(f)

station_id = stations['jsq']
url = "https://transit.hereapi.com/v8/departures"

params = {
    'ids': station_id,
    'apiKey': HERE_API_KEY,
    'return': 'transport,time'
}

print(f"Fetching departures for station: {station_id}")
print(f"URL: {url}")
print(f"Params: {params}\n")

with httpx.Client(timeout=30.0) as client:
    response = client.get(url, params=params)
    print(f"Status: {response.status_code}\n")
    
    data = response.json()
    print("Full Response:")
    print("="*60)
    print(json.dumps(data, indent=2))
