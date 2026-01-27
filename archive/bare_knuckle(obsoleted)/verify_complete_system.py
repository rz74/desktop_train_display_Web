"""
Comprehensive verification of station coverage and live train data availability.
Tests multiple stations across all lines to ensure 100% functionality.
"""

import json
import requests
import time
from collections import defaultdict

def load_stations():
    """Load stations from JSON."""
    with open('all_mta_stations.json', 'r') as f:
        return json.load(f)

def test_station_search(station_name):
    """Test if station search returns results."""
    try:
        response = requests.get(
            f"http://127.0.0.1:8000/search?query={station_name}",
            timeout=5
        )
        if response.status_code == 200:
            results = response.json()
            return len(results) > 0, results
        return False, []
    except Exception as e:
        return False, str(e)

def test_station_arrivals(station_name):
    """Test if station has live arrival data."""
    try:
        # First search for the station
        search_response = requests.get(
            f"http://127.0.0.1:8000/search?query={station_name}",
            timeout=5
        )
        if search_response.status_code != 200 or not search_response.json():
            return False, "Station not found in search"
        
        # Get the first result
        station = search_response.json()[0]
        
        # Get available lines
        lines_response = requests.get(
            f"http://127.0.0.1:8000/lines?station={station}",
            timeout=5
        )
        if lines_response.status_code != 200:
            return False, "Lines endpoint failed"
        
        lines_data = lines_response.json()
        if not lines_data.get('mta_lines') and not lines_data.get('path_lines'):
            return False, "No lines available"
        
        # Test arrivals for MTA
        if lines_data.get('mta_lines'):
            line = lines_data['mta_lines'][0]
            arrivals_response = requests.get(
                f"http://127.0.0.1:8000/arrivals?station={station}&line={line}",
                timeout=10
            )
            if arrivals_response.status_code == 200:
                arrivals = arrivals_response.json()
                return True, f"{len(arrivals)} trains found"
        
        # Test arrivals for PATH
        if lines_data.get('path_lines'):
            line = lines_data['path_lines'][0]
            arrivals_response = requests.get(
                f"http://127.0.0.1:8000/arrivals?station={station}&line={line}",
                timeout=10
            )
            if arrivals_response.status_code == 200:
                arrivals = arrivals_response.json()
                return True, f"{len(arrivals)} trains found"
        
        return False, "No arrivals available"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print("="*80)
    print("COMPREHENSIVE STATION & TRAIN DATA VERIFICATION")
    print("="*80)
    
    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    time.sleep(2)
    
    # Load stations
    stations = load_stations()
    print(f"\n✓ Loaded {len(stations)} station entries from JSON")
    
    # Count unique stations (excluding aliases)
    unique_count = len(set(tuple(v) for vals in stations.values() for v in vals))
    print(f"✓ Unique stop IDs: {unique_count}")
    
    # Test critical stations across all boroughs and lines
    test_stations = {
        "Manhattan - IRT (1/2/3)": ["times sq", "grand central", "penn station", "columbus circle"],
        "Manhattan - IRT (4/5/6)": ["grand central", "59 st", "union square", "brooklyn bridge"],
        "Manhattan - IRT (7)": ["times sq", "grand central", "hunters point"],
        "Manhattan - BMT (N/Q/R/W)": ["times sq", "herald sq", "canal", "city hall"],
        "Manhattan - IND (A/C/E)": ["penn station", "world trade center", "59 st", "125 st"],
        "Manhattan - IND (B/D/F/M)": ["rockefeller", "bryant park", "grand st"],
        "Brooklyn": ["coney island", "atlantic", "borough hall", "prospect park"],
        "Queens": ["flushing", "jamaica", "astoria", "forest hills"],
        "Bronx": ["yankee", "pelham", "woodlawn", "fordham"],
        "Staten Island": ["st george", "tompkinsville"],
        "PATH": ["world trade center", "14th", "23rd", "33rd"],
        "L Train": ["14 st", "bedford", "lorimer", "jefferson"],
        "G Train": ["court sq", "greenpoint", "hoyt"],
    }
    
    results = {
        "search_pass": 0,
        "search_fail": 0,
        "arrivals_pass": 0,
        "arrivals_fail": 0,
        "failed_stations": []
    }
    
    print("\n" + "="*80)
    print("TESTING STATIONS BY LINE")
    print("="*80)
    
    for category, station_list in test_stations.items():
        print(f"\n{category}:")
        for station in station_list:
            # Test search
            search_ok, search_result = test_station_search(station)
            
            if search_ok:
                results["search_pass"] += 1
                print(f"  ✓ {station:20} - Search OK", end="")
                
                # Test arrivals
                arrivals_ok, arrivals_result = test_station_arrivals(station)
                if arrivals_ok:
                    results["arrivals_pass"] += 1
                    print(f" | Trains: {arrivals_result}")
                else:
                    results["arrivals_fail"] += 1
                    results["failed_stations"].append((station, arrivals_result))
                    print(f" | ✗ No trains: {arrivals_result}")
            else:
                results["search_fail"] += 1
                results["failed_stations"].append((station, f"Search failed: {search_result}"))
                print(f"  ✗ {station:20} - Search FAILED: {search_result}")
            
            time.sleep(0.5)  # Rate limiting
    
    # Final statistics
    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)
    
    total_tested = results["search_pass"] + results["search_fail"]
    
    print(f"\nStation Search:")
    print(f"  ✓ Passed: {results['search_pass']}/{total_tested}")
    print(f"  ✗ Failed: {results['search_fail']}/{total_tested}")
    
    print(f"\nLive Train Data:")
    print(f"  ✓ Has trains: {results['arrivals_pass']}/{results['search_pass']}")
    print(f"  ✗ No trains: {results['arrivals_fail']}/{results['search_pass']}")
    
    print(f"\nStation Database:")
    print(f"  Total entries in JSON: {len(stations)}")
    print(f"  Unique stop IDs: {unique_count}")
    print(f"  MTA system total: ~472 stations")
    print(f"  Coverage: {(unique_count/472)*100:.1f}%")
    
    # Show failed stations
    if results["failed_stations"]:
        print(f"\n⚠ STATIONS WITH ISSUES ({len(results['failed_stations'])}):")
        for station, reason in results["failed_stations"]:
            print(f"  • {station}: {reason}")
    else:
        print("\n✓ ALL TESTED STATIONS PASSED!")
    
    # Overall verdict
    print("\n" + "="*80)
    search_rate = (results["search_pass"] / total_tested * 100) if total_tested > 0 else 0
    arrivals_rate = (results["arrivals_pass"] / results["search_pass"] * 100) if results["search_pass"] > 0 else 0
    
    if search_rate >= 95 and arrivals_rate >= 80:
        print("✓ VERIFICATION PASSED - System is operational")
    elif search_rate >= 95:
        print("⚠ PARTIAL PASS - All stations searchable, some missing train data")
    else:
        print("✗ VERIFICATION FAILED - Station search issues detected")
    
    print(f"  Search success rate: {search_rate:.1f}%")
    print(f"  Live data success rate: {arrivals_rate:.1f}%")
    print("="*80)

if __name__ == "__main__":
    main()
