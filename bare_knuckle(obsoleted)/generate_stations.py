import json

# Feed group mappings based on MTA GTFS structure
FEED_GROUPS = {
    "1": "123", "2": "123", "3": "123",
    "4": "456", "5": "456", "6": "456",
    "A": "ace", "C": "ace", "E": "ace",
    "B": "bdfm", "D": "bdfm", "F": "bdfm", "M": "bdfm",
    "N": "nqrw", "Q": "nqrw", "R": "nqrw", "W": "nqrw",
    "L": "l",
    "G": "g",
    "J": "jz", "Z": "jz",
    "S": "s", "GS": "s", "FS": "s"
}

# Load existing data
with open("all_mta_stations.json", "r", encoding="utf-8") as f:
    all_mta = json.load(f)

with open("station_lines_map.json", "r", encoding="utf-8") as f:
    lines_map = json.load(f)

# PATH-only stations
path_stations = {
    "journal square": {
        "display_name": "Journal Square",
        "path": {"stop_id": 26731, "routes": ["860", "861", "862", "1024"]}
    },
    "grove street": {
        "display_name": "Grove Street",
        "path": {"stop_id": 26729, "routes": ["860", "861", "862", "1024"]}
    },
    "33 st": {
        "display_name": "33 St (PATH)",
        "path": {"stop_id": 26725, "routes": ["860", "861", "1024"]}
    },
    "hoboken": {
        "display_name": "Hoboken",
        "path": {"stop_id": 26727, "routes": ["860", "1024"]}
    },
    "newport": {
        "display_name": "Newport",
        "path": {"stop_id": 26728, "routes": ["860", "861", "862", "1024"]}
    },
    "exchange place": {
        "display_name": "Exchange Place",
        "path": {"stop_id": 26730, "routes": ["860", "861", "862", "1024"]}
    },
    "harrison": {
        "display_name": "Harrison",
        "path": {"stop_id": 26732, "routes": ["862"]}
    },
    "newark": {
        "display_name": "Newark",
        "path": {"stop_id": 26733, "routes": ["862"]}
    }
}

# Dual-agency hubs
dual_hubs = {
    "world trade center": {
        "display_name": "World Trade Center",
        "mta": [
            {"stop_id": "138", "feed_group": "123", "routes": ["1"]},
            {"stop_id": "E01", "feed_group": "ace", "routes": ["E"]},
            {"stop_id": "R25", "feed_group": "nqrw", "routes": ["N", "R", "W"]}
        ],
        "path": {"stop_id": 26734, "routes": ["862"]}
    },
    "christopher st-stonewall": {
        "display_name": "Christopher St-Stonewall",
        "mta": [{"stop_id": "133", "feed_group": "123", "routes": ["1"]}],
        "path": {"stop_id": 26726, "routes": ["860", "861", "1024"]}
    },
    "14 st": {
        "display_name": "14 St-Union Sq",
        "mta": [
            {"stop_id": "128", "feed_group": "123", "routes": ["1", "2", "3"]},
            {"stop_id": "A31", "feed_group": "ace", "routes": ["A", "C", "E"]},
            {"stop_id": "D14", "feed_group": "bdfm", "routes": ["B", "D", "F", "M"]}
        ],
        "path": {"stop_id": 26722, "routes": ["860", "861", "1024"]}
    },
    "23 st": {
        "display_name": "23 St",
        "mta": [
            {"stop_id": "130", "feed_group": "123", "routes": ["1"]},
            {"stop_id": "A30", "feed_group": "ace", "routes": ["C", "E"]},
            {"stop_id": "D18", "feed_group": "bdfm", "routes": ["B", "D", "F", "M"]},
            {"stop_id": "R19", "feed_group": "nqrw", "routes": ["R", "W"]},
            {"stop_id": "634", "feed_group": "456", "routes": ["6"]}
        ],
        "path": {"stop_id": 26723, "routes": ["860", "861", "1024"]}
    },
    "34 st-herald sq": {
        "display_name": "34 St-Herald Sq",
        "mta": [
            {"stop_id": "D17", "feed_group": "bdfm", "routes": ["B", "D", "F", "M"]},
            {"stop_id": "R17", "feed_group": "nqrw", "routes": ["N", "Q", "R", "W"]}
        ],
        "path": {"stop_id": 26724, "routes": ["860", "861", "1024"]}
    }
}

# Generate stations.json
stations = {}

# Add PATH-only stations
stations.update(path_stations)

# Add dual-agency hubs
stations.update(dual_hubs)

# Add all MTA stations
for station_id, stops in all_mta.items():
    # Skip if already in dual hubs
    if station_id in dual_hubs:
        continue
    
    # Get display name from lines_map
    display_name = lines_map.get(station_id, {}).get("display_name", station_id.title())
    
    # Group stops by stop_id and aggregate routes
    stop_map = {}
    for stop_id, feed, name in stops:
        if stop_id not in stop_map:
            stop_map[stop_id] = set()
        # Get the route from the feed (second element)
        route = feed
        stop_map[stop_id].add(route)
    
    # Create MTA stops list
    mta_stops = []
    for stop_id, routes in stop_map.items():
        # Determine feed group based on routes
        feed_group = None
        for route in routes:
            if route in FEED_GROUPS:
                feed_group = FEED_GROUPS[route]
                break
        
        if feed_group:
            mta_stops.append({
                "stop_id": stop_id,
                "feed_group": feed_group,
                "routes": sorted(list(routes))
            })
    
    if mta_stops:
        stations[station_id] = {
            "display_name": display_name,
            "mta": mta_stops
        }

# Write to file
with open("stations.json", "w", encoding="utf-8") as f:
    json.dump(stations, f, indent=2)

print(f"✓ Generated stations.json with {len(stations)} stations")
print(f"  - PATH-only: {len(path_stations)}")
print(f"  - Dual-agency: {len(dual_hubs)}")
print(f"  - MTA-only: {len(stations) - len(path_stations) - len(dual_hubs)}")
