# HERE Transit System

A minimalist, library-free transit display system using the HERE Public Transit API v8. No GTFS-RT parsing, no Protobuf, no complex mappings - just clean HTTP requests.

## Features

- ✨ **Zero Dependencies on GTFS Libraries** - Pure HTTP API calls
- 🎯 **Automatic MTA + PATH Merge** - HERE API handles the integration
- 📱 **E-ink Optimized UI** - High contrast, bold fonts, 4.2" screen ready
- 🔄 **Auto-refresh** - Updates every 60 seconds
- 💾 **Persistent Selection** - Remembers your station choice

## Project Structure

```
here_transit_system/
├── discover_stations.py    # One-off script to find HERE Station IDs
├── stations.json           # Station key → HERE ID mapping
├── main.py                 # FastAPI backend proxy
├── requirements.txt        # Python dependencies
├── static/
│   └── index.html         # E-ink styled frontend
└── README.md              # This file
```

## Setup Instructions

### Step 1: Get a HERE API Key

1. Visit https://platform.here.com/
2. Sign up for a free account
3. Create a new project
4. Generate an API key with "Public Transit" permissions
5. Save your API key securely

### Step 2: Discover Station IDs

1. Open `discover_stations.py`
2. Replace `YOUR_HERE_API_KEY` with your actual API key
3. Run the script:

```bash
python discover_stations.py
```

4. The script will output HERE Station IDs for:
   - Journal Square
   - World Trade Center
   - Fulton St
   - WTC Cortlandt

5. Copy the discovered IDs

### Step 3: Configure Stations

Edit `stations.json` with the actual HERE Station IDs from Step 2:

```json
{
  "jsq": "actual_here_id_for_jsq",
  "wtc": "actual_here_id_for_wtc",
  "fulton": "actual_here_id_for_fulton",
  "cortlandt": "actual_here_id_for_cortlandt"
}
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run the Server

Set your HERE API key as an environment variable:

**Windows (PowerShell):**
```powershell
$env:HERE_API_KEY="your_api_key_here"
python main.py
```

**Windows (Command Prompt):**
```cmd
set HERE_API_KEY=your_api_key_here
python main.py
```

**Linux/Mac:**
```bash
export HERE_API_KEY="your_api_key_here"
python main.py
```

### Step 6: Access the Display

Open your browser and navigate to:
```
http://localhost:8000
```

## API Endpoints

### `GET /`
Redirects to the static frontend

### `GET /api/stations`
Returns list of available station keys
```json
{
  "stations": ["jsq", "wtc", "fulton", "cortlandt"]
}
```

### `GET /api/arrivals/{station_key}`
Returns next 10 arrivals for the specified station
```json
{
  "station": "jsq",
  "station_id": "HERE_ID",
  "updated": "2026-01-22T10:30:00",
  "arrivals": [
    {
      "line": "PATH",
      "destination": "33rd Street",
      "minutes": 2,
      "time": "2026-01-22T10:32:00Z"
    }
  ],
  "count": 10
}
```

### `GET /health`
Health check endpoint
```json
{
  "status": "ok",
  "api_key_configured": true,
  "stations_loaded": 4,
  "timestamp": "2026-01-22T10:30:00"
}
```

## Frontend Features

### E-ink Optimized Design
- **Pure Black & White**: #000 and #FFF only
- **Bold Borders**: 2px solid lines for crisp rendering
- **Large Fonts**: 24pt+ for readability
- **System Fonts**: Native font stack for best performance

### Auto-refresh
- Automatically fetches new data every 60 seconds
- Pauses when page is hidden (saves API calls)
- Resumes when page becomes visible

### Persistent Selection
- Saves selected station to `localStorage`
- Automatically loads last selection on page reload

## Troubleshooting

### "Station ID not configured" error
- Run `discover_stations.py` to get actual HERE Station IDs
- Update `stations.json` with the discovered IDs

### "HERE API key not configured" error
- Set the `HERE_API_KEY` environment variable before running
- Make sure your API key has "Public Transit" permissions

### "Station not found" error
- Check that the station key exists in `stations.json`
- Valid keys: `jsq`, `wtc`, `fulton`, `cortlandt`

### No arrivals showing
- Verify the station ID is correct in `stations.json`
- Check HERE API status at https://status.here.com/
- Try running the health check: http://localhost:8000/health

## Production Deployment

### Environment Variables
```bash
HERE_API_KEY=your_actual_api_key
```

### Run with Uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV HERE_API_KEY=""
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Architecture Notes

### Why HERE Transit API?
- **Single Endpoint**: One API call gets all transit data
- **Automatic Merging**: MTA + PATH combined automatically
- **No GTFS Complexity**: No feed parsing, no static schedules
- **Reliable**: Commercial-grade infrastructure
- **Simple**: Clean REST API, JSON responses

### Design Philosophy
- **Stateless**: No databases, no caching layers
- **Minimal**: Only essential dependencies
- **Robust**: Comprehensive error handling
- **Fast**: Direct HTTP calls, no overhead

## License

MIT

## Support

For issues with:
- **HERE API**: https://developer.here.com/help
- **This codebase**: Open an issue in the repository
