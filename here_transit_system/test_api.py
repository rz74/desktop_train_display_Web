"""
Test the HERE Transit API integration
"""
import httpx
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing /health endpoint...")
    response = httpx.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_stations():
    print("Testing /api/stations endpoint...")
    response = httpx.get(f"{BASE_URL}/api/stations")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_arrivals(station_key):
    print(f"Testing /api/arrivals/{station_key} endpoint...")
    response = httpx.get(f"{BASE_URL}/api/arrivals/{station_key}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Station: {data['station']}")
        print(f"Station ID: {data['station_id']}")
        print(f"Count: {data['count']}")
        print(f"Updated: {data['updated']}")
        print("\nArrivals:")
        for arrival in data['arrivals'][:5]:  # Show first 5
            print(f"  {arrival['line']:6s} → {arrival['destination']:30s} {arrival['minutes']:>3d} min")
    else:
        print(json.dumps(response.json(), indent=2))
    print()

if __name__ == "__main__":
    print("="*60)
    print("HERE Transit API Test")
    print("="*60)
    print()
    
    test_health()
    test_stations()
    test_arrivals("jsq")
    test_arrivals("wtc")
