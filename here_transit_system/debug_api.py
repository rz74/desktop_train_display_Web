"""
Debug script to see the raw API response
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

BASE_URL = "https://transit.hereapi.com/v8/stations"

# Test with Journal Square coordinates
params = {
    'apiKey': HERE_API_KEY,
    'in': '40.7334,-74.0631;r=500',
    'return': 'transport'
}

print("Making API request...")
print(f"URL: {BASE_URL}")
print(f"Params: {params}\n")

with httpx.Client(timeout=30.0) as client:
    response = client.get(BASE_URL, params=params)
    print(f"Status: {response.status_code}\n")
    
    data = response.json()
    print("Full JSON Response:")
    print("="*60)
    print(json.dumps(data, indent=2))
