"""
Quick start script for HERE Transit System.
Checks configuration and guides you through setup.
"""
import os
import json
from pathlib import Path

def check_api_key():
    """Check if HERE API key is configured."""
    api_key = os.getenv("HERE_API_KEY")
    if not api_key or api_key == "YOUR_HERE_API_KEY":
        return False, "Not configured"
    return True, api_key[:8] + "..." if len(api_key) > 8 else "***"

def check_stations():
    """Check if stations.json has real IDs."""
    stations_file = Path(__file__).parent / "stations.json"
    try:
        with open(stations_file, 'r') as f:
            stations = json.load(f)
        
        placeholder_count = sum(1 for v in stations.values() if v.startswith("HERE_STATION_ID_"))
        real_count = len(stations) - placeholder_count
        
        if placeholder_count > 0:
            return False, f"{real_count}/{len(stations)} configured"
        return True, f"All {len(stations)} stations configured"
    except Exception as e:
        return False, f"Error: {e}"

def check_dependencies():
    """Check if required packages are installed."""
    required = ['fastapi', 'uvicorn', 'httpx']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, "All installed"

def print_status(name, status, detail):
    """Print a status line."""
    icon = "✓" if status else "✗"
    color = "32" if status else "31"  # Green or Red
    print(f"  {icon} {name}: {detail}")

def main():
    print("="*60)
    print("HERE Transit System - Quick Start")
    print("="*60)
    print()
    
    # Check all components
    print("Checking configuration...")
    print()
    
    api_ok, api_detail = check_api_key()
    stations_ok, stations_detail = check_stations()
    deps_ok, deps_detail = check_dependencies()
    
    print_status("Dependencies", deps_ok, deps_detail)
    print_status("HERE API Key", api_ok, api_detail)
    print_status("Station IDs", stations_ok, stations_detail)
    
    print()
    print("="*60)
    
    # Determine overall status
    all_ok = api_ok and stations_ok and deps_ok
    
    if all_ok:
        print("✓ System ready to run!")
        print()
        print("Start the server with:")
        print("  python main.py")
        print()
        print("Then open: http://localhost:8000")
    else:
        print("⚠ Setup required")
        print()
        
        if not deps_ok:
            print("1. Install dependencies:")
            print("   pip install -r requirements.txt")
            print()
        
        if not api_ok:
            print("2. Set your HERE API key:")
            print("   Windows (PowerShell):")
            print('     $env:HERE_API_KEY="your_key_here"')
            print("   Windows (CMD):")
            print('     set HERE_API_KEY=your_key_here')
            print("   Linux/Mac:")
            print('     export HERE_API_KEY="your_key_here"')
            print()
        
        if not stations_ok:
            print("3. Discover station IDs:")
            print("   a. Edit discover_stations.py with your API key")
            print("   b. Run: python discover_stations.py")
            print("   c. Update stations.json with the discovered IDs")
            print()
        
        print("For detailed setup instructions, see README.md")
    
    print("="*60)

if __name__ == "__main__":
    main()
