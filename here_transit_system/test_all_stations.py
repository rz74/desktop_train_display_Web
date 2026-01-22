"""
Test multiple stations from the comprehensive list
"""
import httpx
import json

BASE_URL = "http://localhost:8000"

# Test a variety of stations
TEST_STATIONS = [
    'jsq',  # PATH
    'wtc_path',  # PATH WTC
    'fulton',  # MTA Lower Manhattan
    'penn_station',  # MTA Midtown
    'union_square',  # MTA Union Square
    'atlantic_terminal',  # MTA Brooklyn
    'hoboken',  # PATH Hoboken
    'grand_central',  # MTA Grand Central
]

def test_station(station_key):
    print(f"\n{'='*70}")
    print(f"Testing: {station_key}")
    print('='*70)
    
    try:
        response = httpx.get(f"{BASE_URL}/api/arrivals/{station_key}", timeout=15.0)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Station: {data['station']}")
            print(f"  ID: {data['station_id']}")
            print(f"  Arrivals: {data['count']}")
            
            if data['arrivals']:
                print("\n  Next arrivals:")
                for arrival in data['arrivals'][:5]:
                    print(f"    {arrival['line']:8s} → {arrival['destination']:35s} {arrival['minutes']:3d} min")
            else:
                print("  No upcoming arrivals")
        else:
            print(f"✗ Error {response.status_code}: {response.json().get('detail', 'Unknown error')}")
    
    except Exception as e:
        print(f"✗ Exception: {e}")

def main():
    print("="*70)
    print("COMPREHENSIVE STATION TEST")
    print("="*70)
    
    for station in TEST_STATIONS:
        test_station(station)
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)

if __name__ == "__main__":
    main()
