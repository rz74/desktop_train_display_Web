# Station Coverage Report

## Summary
Successfully discovered and verified **32 transit stations** across NYC and Jersey City using the HERE Transit API v8.

### Coverage Statistics
- **Total Stations**: 32
- **PATH Stations**: 12/12 (100%)
- **MTA Stations**: 20/22 (91%)

## PATH Stations (12/12) ✓

### Newark Line
- ✓ Newark Penn Station (`newark` → `21285_1196`)
- ✓ Harrison (`harrison` → `15242_78`)
- ✓ Journal Square (`jsq` → `15242_61`)

### JSQ ↔ 33rd Street Line
- ✓ Journal Square (`jsq` → `15242_61`)
- ✓ Grove Street (`grove` → `15242_6`)
- ✓ Exchange Place (`exchange` → `15242_88`)
- ✓ World Trade Center (`wtc_path` → `10327_856`)
- ✓ Christopher Street (`christopher` → `15242_4`)
- ✓ 9th Street (`9th_street` → `15242_3`)
- ✓ 14th Street (`14th_street` → `15242_0`)
- ✓ 23rd Street (`23rd_street` → `15242_1`)
- ✓ 33rd Street (`33rd_street` → `15242_2`)

### Hoboken Line
- ✓ Hoboken (`hoboken` → `15242_56`)

## MTA Stations (20/22)

### Lower Manhattan
- ✓ Fulton St (`fulton` → `10327_1251`)
- ✓ WTC Cortlandt (`cortlandt` → `10327_1347`)
- ✓ City Hall (`city_hall` → `10327_1344`)
- ✓ Franklin St/Canal area (`canal` → `10327_100`)
- ✗ Chambers St (not found in HERE API)

### Midtown
- ✓ Penn Station (`penn_station` → `10324_2`)
- ✓ Herald Square (`herald_square` → `10327_1323`)
- ✓ Port Authority (`port_authority` → `10327_592`)
- ✓ Grand Central (`grand_central` → `21285_1337`)
- ✓ Lexington Ave/53rd St (`lexington_53` → `10327_883`)
- ✓ Lexington Ave/59th St (`lexington_59` → `10327_1308`)
- ✗ Times Square (not found in HERE API)

### Union Square Area
- ✓ Union Square (`union_square` → `10327_1137`)
- ✓ Astor Place (`astor_place` → `10327_448`)

### Upper Manhattan
- ✓ Columbus Circle (`columbus_circle` → `10327_67`)
- ✓ 72nd Street (`72nd_street` → `10327_61`)
- ✓ 86th Street (`86th_street` → `10327_418`)
- ✓ 96th Street (`96th_street` → `10327_52`)

### Brooklyn
- ✓ Atlantic Terminal-Barclays (`atlantic_terminal` → `10327_799`)
- ✓ Jay St-MetroTech (`jay_street` → `10327_622`)

### Queens
- ✓ Queensboro Plaza (`queensboro` → `10327_1305`)
- ✓ Jackson Heights-Roosevelt Ave (`jackson_heights` → `10327_982`)

## Missing Stations (2)
1. **Chambers St** - Not found in HERE API transit data
2. **Times Square** - Not found in HERE API transit data

These stations may not be available in the HERE Transit API's dataset, or may require different search parameters.

## Verification Results

All 32 discovered stations have been **tested and verified** to return live transit data:

- **PATH trains**: Real-time departure data working
- **MTA Subway**: Multiple lines showing live arrivals
- **Regional Rail**: Penn Station and Grand Central showing Amtrak/LIRR

### Sample Verification Output

#### Journal Square (PATH)
```
✓ Live arrivals:
  PATH → 33rd Street (6 min)
  PATH → Newark (13 min)
  PATH → World Trade Center (15 min)
```

#### Union Square (MTA)
```
✓ Live arrivals:
  L → 8 Av (0 min)
  L → Canarsie-Rockaway Pkwy (4 min)
```

#### Atlantic Terminal (MTA Brooklyn)
```
✓ Live arrivals:
  B → Brighton Beach (1 min)
  Q → 96 St (1 min)
  Q → Coney Island (2 min)
```

## Files Generated

1. `stations.json` - Flat map of all station IDs (used by API)
2. `stations_organized.json` - Hierarchical organization (for reference)
3. `all_stations_discovered.json` - Full discovery results with metadata
4. `stations_complete.json` - Complete verified stations
5. `missing_stations_found.json` - Results of missing station search

## Frontend Integration

The web interface now includes all 32 stations organized into **7 dropdown sections**:

1. PATH - Newark Line (3 stations)
2. PATH - JSQ ↔ 33rd (9 stations)
3. PATH - Hoboken Line (1 station)
4. MTA - Lower Manhattan (4 stations)
5. MTA - Midtown (6 stations)
6. MTA - Union Square Area (2 stations)
7. MTA - Upper Manhattan (4 stations)
8. MTA - Brooklyn (2 stations)
9. MTA - Queens (2 stations)

## Discovery Process

### Phase 1: Initial Discovery
- Searched for 34 target stations using known coordinates
- Found 25 stations on first pass

### Phase 2: Missing Station Search
- Expanded search radius to 800m
- Used alternative search terms
- Found 7 additional stations

### Phase 3: Verification
- Tested all 32 stations for live data
- Confirmed real-time arrivals working
- Updated frontend with organized station list

## Technical Details

### API Endpoint
- **Service**: HERE Transit API v8
- **Endpoint**: `https://transit.hereapi.com/v8/stations`
- **Method**: Proximity search by coordinates
- **Radius**: 500-800m per station

### Station ID Format
- PATH stations: `15242_*` prefix
- MTA stations: `10327_*` or `10324_*` prefix
- Regional rail: `21285_*` prefix

### Transport Modes Detected
- `regionalTrain`: PATH, Amtrak, LIRR
- `subway`: MTA subway lines
- `bus`: Bus stops (filtered out)

## Success Rate
- **Overall**: 94% (32/34 stations found)
- **PATH**: 100% (12/12 stations found)
- **MTA**: 91% (20/22 stations found)

## Next Steps (Optional)
1. Search for alternative station IDs for Chambers St and Times Square
2. Add more outer borough stations (Bronx, Staten Island)
3. Add NJ Transit stations beyond PATH
4. Implement station search by name in frontend

---

**Generated**: January 22, 2026  
**System**: HERE Transit API v8  
**Status**: ✅ Production Ready
