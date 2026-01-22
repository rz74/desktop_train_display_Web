# NYC Transit Display System
### Real-time MTA Subway & PATH Train Arrivals

A production-ready transit display system designed for 4.2" e-ink screens, powered by HERE Transit API v8. Shows live arrival times for all 509 MTA subway stations and 13 PATH stations across NYC and Jersey City.

---

## 📖 Table of Contents

1. [For Regular Users (Non-Technical)](#-for-regular-users-non-technical)
2. [For Developers (Technical Documentation)](#-for-developers-technical-documentation)
3. [API Reference](#-api-reference)
4. [Troubleshooting](#-troubleshooting)

---

## For Regular Users (Non-Technical)

### What This System Does

This is a website that shows you when the next subway or PATH train is arriving at your favorite station. It's like the arrival boards you see in the subway station, but on your computer or phone.

**Example:** If you're at World Trade Center and want to know when the next trains are coming, you can see things like:
- Line **1** to Van Cortlandt Park in **3 minutes**
- Line **E** to Jamaica Center in **5 minutes**  
- **PATH** to 33rd Street in **7 minutes**

### How to Use It

#### Step 1: Open the Website
1. Make sure the server is running (someone technical needs to start it first)
2. Open your web browser (Chrome, Firefox, Safari, etc.)
3. Type in the address bar: `http://localhost:8000`
4. Press Enter

#### Step 2: Pick Your Station
You'll see a search box at the top. You can either:
- **Type to search**: Start typing your station name (like "Times" for Times Square)
- **Scroll and click**: Scroll through the list and click on your station

**Tip:** Stations are organized into three groups:
- **MAJOR HUBS** - Big transfer stations like World Trade Center, 33rd Street
- **PATH TRAIN** - PATH stations in NYC and Jersey City
- **MTA SUBWAY** - All regular subway stations

#### Step 3: Choose Your Time Window
Below the station picker, you'll see:
```
Show trains arriving in: [2] to [20] minutes
```

- **First number (2)**: Don't show trains that are too close (you might miss them!)
- **Second number (20)**: Don't show trains that are too far away (you don't care yet!)

**Change these numbers to fit your needs:**
- Going to station in 5 minutes? Set it to **5 to 30**
- Already at the platform? Set it to **0 to 15**
- Planning ahead? Set it to **10 to 40**

#### Step 4: Read the Arrivals
You'll see a table with columns:
- **LINE**: Which train (1, 2, A, C, PATH, etc.)
- **DESTINATION**: Where the train is going
- **ARRIVES IN**: How many minutes until it arrives

The list updates automatically every 30 seconds, so you always see fresh information!

#### Step 5: The Website Remembers You
Next time you open the website, it will remember:
- Which station you last picked
- Your time window settings

So you don't have to set it up again!

### Common Questions

**Q: Why don't I see any trains?**  
A: Either there are no trains in your time window, or you might want to adjust your minutes (try 0 to 60 to see everything).

**Q: Can I use this on my phone?**  
A: Yes! Just open your phone's web browser and go to the same address.

**Q: Will this work on the subway (no internet)?**  
A: No, you need an internet connection. Use it before you leave home or on WiFi.

**Q: Is this real-time or a schedule?**  
A: Real-time! If a train is delayed, you'll see the actual delayed time, not the scheduled time.

**Q: What are "Major Hubs"?**  
A: These are big stations where multiple lines meet. We combine them so you see ALL trains at once (for example, WTC shows 1/2/3/4/5/A/C/E/R/W + PATH all together).

---

## 🔧 For Developers (Technical Documentation)

### System Overview

**Purpose**: Production-ready real-time transit arrival display optimized for e-ink screens, covering 100% of NYC subway and PATH systems.

**Technology Stack:**
- Backend: FastAPI (Python 3.10+)
- Frontend: Vanilla HTML/CSS/JavaScript (no frameworks)
- API: HERE Transit API v8
- Deployment: Uvicorn ASGI server

**Coverage:**
- 472 MTA subway stations (all lines)
- 13 PATH stations  
- 24 service lines total
- 5 major transfer hub complexes

### Architecture

### Architecture

**Data Flow:**
```
User Browser → FastAPI Backend → HERE Transit API v8 → Real-time GTFS Data
     ↑                                                            ↓
     └────────────────── JSON Response ←──────────────────────────┘
```

**Key Design Decisions:**
1. **No GTFS-RT Parsing**: HERE API handles all GTFS complexity
2. **Stateless**: Zero database, zero caching (except browser localStorage)
3. **Direct Proxy**: Backend forwards requests to HERE API with minimal processing
4. **Station Complexes**: Major hubs query multiple platforms and merge results
5. **Time-based Filtering**: Client controls arrival window (default 2-20 minutes)

### Project Structure

```
here_transit_system/
├── main.py                      # FastAPI backend server
├── gtfs_to_here_map.json        # 509 GTFS Station ID → HERE ID mappings
├── coordinate_mapping.json      # Discovery metadata (reference only)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── start_server.bat             # Windows server launcher
├── static/
│   └── index.html              # E-ink optimized frontend
├── archive/                     # Historical discovery artifacts
│   ├── coordinate_mapping.py
│   ├── check_results.py
│   └── [other discovery scripts]
└── README.md                    # This file
```

### Complete Setup Guide

#### Prerequisites
- Python 3.10 or higher
- HERE API key with Public Transit permissions
- pip (Python package manager)
- Git (for cloning repository)

#### Step 1: Clone Repository
```bash
git clone https://github.com/rz74/desktop_train_display_Web.git
cd desktop_train_display_Web/here_transit_system
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `httpx` - Async HTTP client
- `python-dotenv` - Environment variable management

#### Step 4: Configure Environment

Create `.env` file in `here_transit_system/` directory:
```bash
HERE_API_KEY=your_actual_api_key_here
```

**Get a HERE API Key:**
1. Visit https://platform.here.com/
2. Sign up for free account (generous free tier)
3. Create new project
4. Generate API key with "Public Transit" scope
5. Copy key to `.env` file

#### Step 5: Run the Server

**Option A: Direct Python**
```bash
# Make sure you're in here_transit_system/ directory
# and virtual environment is activated
python main.py
```

**Option B: Uvicorn (Production)**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Option C: Windows Batch File**
```cmd
start_server.bat
```

**Server Output:**
```
✓ Loaded 509 station mappings
✓ Manual overrides: ['723', '901', 'Newark Penn Station']

============================================================
HERE Transit Display - Starting Server
============================================================
Total stations: 509
Coverage: 100% (including manual overrides)
Server: http://localhost:8000
============================================================
```

#### Step 6: Access the Application
Open browser to: `http://localhost:8000`

### Core Components Explained

#### 1. Station Mapping System

**File**: `gtfs_to_here_map.json`

Maps GTFS Station IDs to HERE Transit Station IDs. Built using coordinate-based proximity search.

**Format:**
```json
{
  "GTFS_ID": "HERE_STATION_ID",
  "D19": "10327_1152",
  "Journal Square": "14293_1",
  "World Trade Center": "10327_100"
}
```

**Discovery Method:**
- Query MTA GTFS for all station coordinates
- For each coordinate, query HERE `/stations` endpoint with 100m radius
- Match stations by name similarity and mode (subway/lightRail)
- Manual overrides for 3 edge cases

**Coverage Achieved:**
- Automatic: 506/509 (99.4%)
- Manual overrides: 3 (Grand Central x2, Newark Penn)
- Total: 509/509 (100%)

#### 2. Station Complexes

**Location**: `main.py` → `STATION_COMPLEXES` dictionary

Merges multiple physical platforms into single logical station for major transfer hubs.

**Example - World Trade Center Complex:**
```python
"WTC": {
    "name": "World Trade Center Complex",
    "gtfs_ids": [
        "World Trade Center",  # PATH
        "142",                 # Cortlandt St (R/W)
        "418",                 # Fulton St (2/3/4/5/A/C/J/Z)
        "E01",                 # WTC Cortlandt (1)
        "A38",                 # Chambers St (A/C)
    ]
}
```

**Current Complexes:**
- WTC (5 platforms, 10+ lines)
- 33rd Street (2 platforms, PATH + 8 lines)
- 14th Street (2 platforms, PATH + 8 lines)
- 23rd Street (2 platforms, PATH + 2 lines)
- Christopher Street (2 platforms, PATH + 1 line)

**How It Works:**
1. User selects complex from dropdown
2. Backend queries ALL constituent GTFS IDs in parallel
3. Merge all arrivals into single list
4. Sort by arrival time
5. Filter by user's time window
6. Return combined results

#### 3. Backend API (main.py)

**FastAPI Application** - Async HTTP server proxying HERE API requests.

**Key Endpoints:**

`GET /api/stations`
- Returns all 509 stations + 5 complexes
- Grouped by type: COMPLEX, PATH, MTA SUBWAY
- Used to populate frontend dropdown

`GET /api/arrivals/{gtfs_id}?min_minutes=2&max_minutes=20`
- Takes GTFS ID (or complex ID)
- Queries HERE API for departure board
- Transforms HERE response to clean format
- Filters by time window
- Returns sorted arrivals

**Error Handling:**
- 404 for unknown station IDs
- 500 for HERE API failures (with details)
- Timeout handling (30s per request)
- Continues on partial failures for complexes

**Data Transformation:**
```python
# HERE API Response (complex)
{
  "boards": [{
    "place": {"name": "Fulton St"},
    "departures": [{
      "transport": {"name": "2", "headsign": "Wakefield"},
      "time": 3  # minutes
    }]
  }]
}

# Our API Response (clean)
{
  "line": "2",
  "dest": "Wakefield",
  "min": 3
}
```

#### 4. Frontend (static/index.html)

**Pure Vanilla JavaScript** - No frameworks, no build step.

**E-ink Optimization:**
- Colors: Pure #000 and #FFF only
- Fonts: 24pt+ for readability
- Borders: 3px solid for crisp rendering
- Contrast: Maximum black/white contrast

**Features:**

1. **Station Search**
   - Real-time filtering as you type
   - Case-insensitive search
   - Searches both station name and lines served

2. **Time Window Control**
   - Two number inputs: min and max minutes
   - Defaults: 2 min (skip imminent) to 20 min (ignore distant)
   - Updates arrivals immediately on change

3. **Auto-refresh**
   - Polls every 30 seconds
   - Pauses when tab is hidden (Page Visibility API)
   - Resumes on tab focus

4. **Persistent State**
   - Saves selected station to localStorage
   - Saves time window preferences
   - Restores on page load

**UI Layout:**
```
┌─────────────────────────────────────┐
│  🚇 ARRIVALS                       │
├─────────────────────────────────────┤
│  Search: [Times Sq______]          │
│                                     │
│  [Dropdown with 514 stations]      │
│                                     │
│  Show trains: [2] to [20] min      │
├─────────────────────────────────────┤
│  LINE │ DESTINATION      │ MIN     │
├───────┼──────────────────┼─────────┤
│   1   │ Van Cortlandt    │  3      │
│   2   │ Wakefield        │  5      │
│   E   │ Jamaica Center   │  7      │
└─────────────────────────────────────┘
```

### Production Deployment

#### Environment Configuration

**Required:**
```bash
HERE_API_KEY=your_key_here
```

**Optional:**
```bash
PORT=8000                    # Default: 8000
HOST=0.0.0.0                # Default: 0.0.0.0
LOG_LEVEL=info              # Default: info
```

#### Run with Uvicorn

**Development:**
```bash
uvicorn main:app --reload
```

**Production:**
```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --log-level info
```

**Why 1 worker?**
- Stateless application
- HERE API does rate limiting per key
- Multiple workers = multiple processes = API key contention
- Async FastAPI handles concurrency efficiently with single worker

#### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .
COPY gtfs_to_here_map.json .
COPY coordinate_mapping.json .
COPY static/ ./static/

# Environment
ENV HERE_API_KEY=""
ENV PORT=8000

# Run
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Run:**
```bash
docker build -t transit-display .
docker run -p 8000:8000 -e HERE_API_KEY=your_key transit-display
```

#### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name transit.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Extending the System

#### Adding More Stations

The current system includes all 509 stations. To add new stations:

1. Get station coordinates from GTFS
2. Query HERE API:
   ```bash
   curl "https://transit.hereapi.com/v8/stations?in=40.748,-73.987;r=100&apiKey=YOUR_KEY"
   ```
3. Find matching station ID
4. Add to `gtfs_to_here_map.json`:
   ```json
   "NEW_GTFS_ID": "new_here_id"
   ```
5. Restart server

#### Adding More Complexes

Edit `STATION_COMPLEXES` in `main.py`:

```python
"Times Square": {
    "name": "Times Square-42 St Complex",
    "gtfs_ids": [
        "725",  # Times Sq-42 St (1/2/3)
        "902",  # Times Sq-42 St (N/Q/R/W)
        "127",  # Times Sq-42 St (7)
        "A27",  # Times Sq-42 St (A/C/E)
        "D01",  # Times Sq-42 St (S shuttle)
    ]
}
```

#### Customizing Time Windows

**Backend** (`main.py`):
```python
@app.get("/api/arrivals/{gtfs_id}")
async def get_arrivals(
    gtfs_id: str, 
    min_minutes: int = 0,    # Change defaults here
    max_minutes: int = 30
)
```

**Frontend** (`static/index.html`):
```html
<input type="number" id="minMinutes" value="0" ...>
<input type="number" id="maxMinutes" value="30" ...>
```

#### Adding New Features

**Backend Example - Add "Express" flag:**
```python
# In transform_arrivals function
arrival = {
    "line": transport.get("name"),
    "dest": transport.get("headsign"),
    "min": dep.get("time"),
    "express": "<" in transport.get("headsign", "")  # NEW
}
```

**Frontend Example - Display express trains:**
```javascript
const row = `
  <tr>
    <td class="line-cell">${arr.line}${arr.express ? ' 🚀' : ''}</td>
    ...
  </tr>
`;
```

### Testing

#### Manual Testing

#### Manual Testing

**Test Single Station:**
```bash
# Start server
python main.py

# In browser or curl
curl "http://localhost:8000/api/arrivals/D19?min_minutes=0&max_minutes=30"
```

**Expected Response:**
```json
{
  "station_id": "D19",
  "here_id": "10327_1152",
  "arrivals": [
    {"line": "B", "dest": "Brighton Beach", "min": 2},
    {"line": "D", "dest": "Coney Island", "min": 5},
    ...
  ]
}
```

**Test Station Complex:**
```bash
curl "http://localhost:8000/api/arrivals/WTC?min_minutes=2&max_minutes=20"
```

**Expected Response:**
```json
{
  "station_id": "WTC",
  "station_name": "World Trade Center Complex",
  "here_ids": ["10327_100", "10327_322", ...],
  "arrivals": [
    {"line": "PATH", "dest": "33rd Street", "min": 3},
    {"line": "1", "dest": "Van Cortlandt", "min": 4},
    {"line": "E", "dest": "Jamaica Center", "min": 6},
    ...
  ]
}
```

**Test Station List:**
```bash
curl "http://localhost:8000/api/stations"
```

#### Load Testing

```bash
# Install Apache Bench
# Ubuntu/Debian: apt-get install apache2-utils
# Mac: brew install ab

# Test 100 requests with 10 concurrent
ab -n 100 -c 10 http://localhost:8000/api/arrivals/D19
```

**Expected Performance:**
- 95%ile response time: < 1s (depends on HERE API)
- Server handles 10+ concurrent requests easily
- Memory usage: ~50-100MB

### Performance Characteristics

**Response Times:**
- Static frontend: < 10ms
- `/api/stations`: < 5ms (reads from memory)
- `/api/arrivals/{single}`: 200-800ms (HERE API latency)
- `/api/arrivals/{complex}`: 500-2000ms (multiple HERE calls in parallel)

**API Limits:**
- HERE Free Tier: 250,000 requests/month
- Estimated usage: ~86,400 requests/month (1 user refreshing every 30s)
- Supports ~2-3 concurrent users within free tier

**Caching Strategy:**
- None on backend (stateless design)
- Browser caches static assets (1 day)
- API responses not cached (real-time data)

### System Requirements

**Server:**
- CPU: 1 core sufficient
- RAM: 256MB minimum
- Storage: < 5MB
- Network: Stable internet connection for HERE API

**Client:**
- Any modern web browser (Chrome 90+, Firefox 88+, Safari 14+)
- JavaScript enabled
- 4.2" e-ink display: 400x300 or 800x600 resolution recommended

---

## 📡 API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### GET `/`
Serves static frontend HTML.

**Response:** HTML page

---

#### GET `/api/stations`
Returns all available stations grouped by type.

**Query Parameters:** None

**Response:**
```json
{
  "stations": [
    {
      "id": "WTC",
      "name": "World Trade Center Complex",
      "agency": "COMPLEX"
    },
    {
      "id": "Journal Square",
      "name": "Journal Square",
      "agency": "PATH"
    },
    {
      "id": "D19",
      "name": "47-50 Sts-Rockefeller Ctr",
      "agency": "MTA"
    },
    ...
  ]
}
```

**Station Object:**
- `id`: GTFS Station ID (used in arrivals endpoint)
- `name`: Human-readable station name
- `agency`: `"COMPLEX"` | `"PATH"` | `"MTA"`

---

#### GET `/api/arrivals/{gtfs_id}`
Returns real-time arrivals for specified station or complex.

**Path Parameters:**
- `gtfs_id` (required): GTFS Station ID or Complex ID

**Query Parameters:**
- `min_minutes` (optional, default=2): Minimum minutes until arrival
- `max_minutes` (optional, default=20): Maximum minutes until arrival

**Example Requests:**
```bash
# Get arrivals for single station
GET /api/arrivals/D19?min_minutes=0&max_minutes=30

# Get arrivals for complex
GET /api/arrivals/WTC?min_minutes=5&max_minutes=25
```

**Response (Single Station):**
```json
{
  "station_id": "D19",
  "here_id": "10327_1152",
  "arrivals": [
    {
      "line": "B",
      "dest": "Brighton Beach",
      "min": 3
    },
    {
      "line": "D",
      "dest": "Coney Island",
      "min": 7
    }
  ]
}
```

**Response (Complex):**
```json
{
  "station_id": "WTC",
  "station_name": "World Trade Center Complex",
  "here_ids": ["10327_100", "10327_322", "10327_1", "10327_2", "10327_38"],
  "arrivals": [
    {
      "line": "PATH",
      "dest": "33rd Street",
      "min": 3,
      "station_name": "World Trade Center"
    },
    {
      "line": "1",
      "dest": "Van Cortlandt Park",
      "min": 4,
      "station_name": "WTC Cortlandt"
    }
  ]
}
```

**Arrival Object:**
- `line`: Route name (e.g., "1", "A", "PATH")
- `dest`: Final destination of train
- `min`: Minutes until arrival (integer)
- `station_name`: (Complex only) Which platform within complex

**Error Responses:**
```json
// 404 - Station not found
{
  "detail": "Station 'INVALID' not found in mapping"
}

// 500 - HERE API error
{
  "detail": "Failed to fetch departures: Connection timeout"
}
```

---

## 🔧 Troubleshooting

### Server Won't Start

**Error: `ModuleNotFoundError: No module named 'fastapi'`**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error: `HERE_API_KEY not configured`**
```bash
# Solution: Create .env file
echo "HERE_API_KEY=your_key_here" > .env
```

**Error: `Address already in use`**
```bash
# Solution: Kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

### No Arrivals Showing

**Problem: Station returns empty array**

**Possible Causes:**
1. No trains in your time window
   - **Solution**: Widen time window (0 to 60 minutes)

2. Station ID not in mapping
   - **Check**: Search for station in dropdown
   - **Solution**: If missing, check `gtfs_to_here_map.json`

3. HERE API error (rare)
   - **Check**: Server logs for error messages
   - **Solution**: Verify API key has Public Transit permissions

**Debug Steps:**
```bash
# 1. Check station exists
curl http://localhost:8000/api/stations | grep "your_station"

# 2. Try wide time window
curl "http://localhost:8000/api/arrivals/D19?min_minutes=0&max_minutes=60"

# 3. Check server logs
# Look for "Warning:" or "Error:" messages in terminal
```

---

### Frontend Not Loading

**Problem: Blank page or "Cannot connect"**

1. **Verify server is running**
   ```bash
   curl http://localhost:8000
   # Should return HTML
   ```

2. **Check browser console (F12)**
   - Look for JavaScript errors
   - Check Network tab for failed requests

3. **Clear browser cache**
   - Chrome: Ctrl+Shift+Del
   - Firefox: Ctrl+Shift+Del
   - Safari: Cmd+Option+E

---

### Performance Issues

**Problem: Slow response times (>5 seconds)**

**Causes & Solutions:**

1. **HERE API slow**
   - Normal during peak hours
   - Check https://status.here.com/
   - Consider caching (adds complexity)

2. **Complex queries slow**
   - Expected: WTC complex queries 5 stations
   - Each takes 500-800ms, total ~2-3s
   - This is normal behavior

3. **Network issues**
   - Check internet connection
   - Ping api.transit.here.com
   - Consider local/cloud deployment closer to HERE servers

---

### E-ink Display Issues

**Problem: Text hard to read**

**Solutions:**
- Increase font size in CSS (24pt → 32pt)
- Reduce table rows (show fewer arrivals)
- Adjust screen contrast settings

**Problem: Screen not refreshing**

**Solutions:**
- Check if browser auto-refresh is working (console logs)
- Some e-ink displays need manual refresh
- Consider adding refresh button

---

## 📚 Additional Resources

### HERE Transit API Documentation
- API Reference: https://developer.here.com/documentation/public-transit/dev_guide/index.html
- Get API Key: https://platform.here.com/
- Status Page: https://status.here.com/

### GTFS Resources
- MTA GTFS: https://new.mta.info/developers
- PATH GTFS: (integrated via HERE API)
- GTFS Specification: https://gtfs.org/

### Related Projects
- MTA Real-time Feeds: https://api.mta.info/
- TransitClock: https://transitclock.org/
- OneBusAway: https://onebusaway.org/

---

## 🤝 Contributing

### Reporting Issues
1. Check existing issues
2. Include server logs
3. Specify station ID and time window
4. Include browser console output

### Code Style
- Python: PEP 8
- JavaScript: StandardJS
- Use async/await for async operations
- Comment complex logic

### Pull Requests
1. Fork repository
2. Create feature branch
3. Test changes locally
4. Update README if needed
5. Submit PR with description

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **HERE Technologies**: Transit API
- **MTA**: GTFS data
- **PATH**: GTFS data
- **FastAPI**: Web framework
- **All contributors**: Thank you!

---

## 📞 Support

**For technical issues:**
- Open issue on GitHub
- Include: OS, Python version, error logs

**For HERE API issues:**
- Contact: https://developer.here.com/help
- Check: https://status.here.com/

**For station data issues:**
- MTA: https://new.mta.info/contact-us
- PATH: https://www.panynj.gov/path/en/contact-us.html

---

**Last Updated:** January 22, 2026  
**Version:** 1.0.0  
**Maintainer:** Transit Display Team
