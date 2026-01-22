"""
Test live train data across all MTA lines.
This script runs in the background and doesn't interfere with the server.
"""

import json
import urllib.request
import urllib.error
import time

def test_url(url):
    """Test a URL without using requests library."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read().decode('utf-8')
            return True, json.loads(data)
    except Exception as e:
        return False, str(e)

def main():
    print("="*80)
    print("TRAIN DATA VERIFICATION")
    print("="*80)
    
    # Wait for server
    print("\nWaiting for server...")
    time.sleep(2)
    
    # Test stations across all lines
    test_cases = [
        ("times sq-42 st", "1", "Times Sq on 1 train"),
        ("times sq-42 st", "N", "Times Sq on N train"),
        ("grand central-42 st", "4", "Grand Central on 4 train"),
        ("grand central-42 st", "7", "Grand Central on 7 train"),
        ("coney island-stillwell av", "D", "Coney Island on D train"),
        ("coney island-stillwell av", "F", "Coney Island on F train"),
        ("flushing-main st", "7", "Flushing on 7 train"),
        ("jamaica-179 st", "F", "Jamaica on F train"),
        ("astoria-ditmars blvd", "N", "Astoria on N train"),
        ("161 st-yankee stadium", "4", "Yankee Stadium on 4 train"),
        ("world trade center", "E", "WTC on E train"),
        ("34 st-penn", "A", "Penn Station on A train"),
        ("14 st-union sq", "L", "Union Sq on L train"),
        ("court sq-23 st", "G", "Court Sq on G train"),
        ("atlantic av-barclays ctr", "2", "Atlantic on 2 train"),
        ("fulton st", "A", "Fulton St on A train"),
        ("canal st", "N", "Canal St on N train"),
    ]
    
    print(f"\nTesting {len(test_cases)} station/line combinations...")
    print("="*80)
    
    results = {"success": 0, "no_data": 0, "error": 0}
    
    for station, line, description in test_cases:
        # URL encode the station name
        station_encoded = station.replace(' ', '%20')
        url = f"http://127.0.0.1:8000/arrivals?station={station_encoded}&line={line}&max_minutes=60"
        
        success, data = test_url(url)
        
        if success:
            if isinstance(data, list) and len(data) > 0:
                results["success"] += 1
                print(f"✓ {description:35} - {len(data)} trains")
            elif isinstance(data, list):
                results["no_data"] += 1
                print(f"⚠ {description:35} - No trains (may be normal)")
            else:
                results["error"] += 1
                print(f"✗ {description:35} - Unexpected response")
        else:
            results["error"] += 1
            print(f"✗ {description:35} - Error: {data}")
        
        time.sleep(0.3)
    
    # Final results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    total = len(test_cases)
    print(f"\n✓ Has train data: {results['success']}/{total} ({results['success']/total*100:.1f}%)")
    print(f"⚠ No trains (empty): {results['no_data']}/{total} ({results['no_data']/total*100:.1f}%)")
    print(f"✗ Errors: {results['error']}/{total} ({results['error']/total*100:.1f}%)")
    
    # Verdict
    if results['success'] + results['no_data'] >= total * 0.95:
        print("\n✓ TRAIN DATA VERIFICATION PASSED")
        print("  (Empty results are normal - depends on time of day)")
    else:
        print("\n✗ TRAIN DATA VERIFICATION FAILED")
        print(f"  Too many errors: {results['error']}")
    
    print("="*80)

if __name__ == "__main__":
    main()
