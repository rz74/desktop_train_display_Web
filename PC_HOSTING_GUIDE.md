# HERE Transit Display - PC Hosting Guide

Complete setup guide for hosting the HERE Transit Display system on a Windows PC with automated maintenance and security features.

---

## 🚀 Quick Start

### 1. Automated Setup

Run the automated setup script to configure your environment:

```bash
python setup_env.py
```

This script will:
- ✅ Check Python version (3.8+ required)
- ✅ Create virtual environment (`venv/`)
- ✅ Install all dependencies from `requirements.txt`
- ✅ Install Playwright Chromium browser
- ✅ Create `.env` configuration file
- ✅ Create `archive/` directory for deprecated files

### 2. Configure Environment

Edit `here_transit_system/.env` with your API keys:

```bash
# HERE Maps API Key
HERE_API_KEY=your_here_api_key_here

# OpenWeather API Key
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Session Secret (generate with command below)
SESSION_SECRET_KEY=your_64_character_secret_key

# Root path for deployment
ROOT_PATH=/einktrain
```

**Generate Session Secret:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start the Server

Use the automated launcher:

```bash
python run_server.py
```

The server will:
- ✅ Verify environment setup
- ✅ Activate virtual environment
- ✅ Start on `http://0.0.0.0:8000`
- ✅ Enable auto-reload for development

**Access the application:**
- Local: `http://localhost:8000`
- Network: `http://YOUR_PC_IP:8000`
- Display page: `http://localhost:8000/user1`
- Config page: `http://localhost:8000/user1/config`

---

## 📁 Project Structure

```
desktop_train_display/
├── archive/                    # Auto-archived deprecated files
├── here_transit_system/
│   ├── main.py                # Main FastAPI application
│   ├── station_lines.json     # Station metadata (517 entries)
│   ├── user_configs.json      # User display configurations
│   ├── .env                   # Environment configuration
│   ├── static/                # Frontend assets
│   └── templates/             # Jinja2 templates
├── venv/                      # Virtual environment
├── setup_env.py              # Automated environment setup
├── run_server.py             # Server launcher
└── requirements.txt          # Python dependencies
```

---

## 🔒 Security Features

### Session-Based Authentication

**Protected Routes:**
- `/user1/config` - Requires valid session
- POST config saves - Requires authentication

**Authentication Flow:**
1. User accesses `/user1/config`
2. If not logged in → Redirect to `/login?redirect_to=/user1/config`
3. User enters Display ID and Password
4. System verifies against `user_configs.json`
5. Creates session with `display_id`
6. Redirects back to config page

**Logout:**
- Click logout button in config page header
- Clears session and redirects to login

### Multi-Tenant Isolation

Each user can only access their own config:
- `user1` cannot access `/user2/config`
- Session validation enforces display_id matching

### Internal Rendering Bypass

Screenshot endpoint uses localhost for speed:
- Route: `/render/{display_id}`
- Uses: `http://localhost:8000/{display_id}`
- Bypasses: External auth and Cloudflare tunnel
- Purpose: Fast e-ink display rendering

---

## 🛠️ Automated Maintenance

### File Archiving (Automatic)

On server startup, deprecated files are automatically moved to `archive/`:

**Archived Patterns:**
- `main_v*.py` - Old version files
- `*_backup.py` - Backup files
- `*_old.py` - Legacy files
- `*.pyc` - Compiled Python files
- `__pycache__/` - Python cache directories
- `test_*.py.bak` - Test backups
- `.pytest_cache/` - Pytest cache
- `*.log.old` - Old log files
- `debug_*.txt` - Debug output files

**Archive Naming:**
Files are timestamped: `filename_20260127_143025.ext`

### Manual Cleanup

To manually archive additional files, move them to `archive/`:

```bash
# Windows
move old_file.py archive\
move backup_folder archive\

# Linux/Mac
mv old_file.py archive/
mv backup_folder archive/
```

---

## 📊 Data Integrity

### Station Data Verification

**E01 Fix Applied:**
- **Station:** World Trade Center Cortlandt (GTFS ID: E01)
- **Corrected:** Changed from E train to 1 train
- **Location:** `station_lines.json` line 1782

**Current Status:**
- ✅ 517 total entries in `station_lines.json`
- ✅ 13 PATH stations
- ✅ 8 major hub complexes
- ✅ 496 MTA stations
- ✅ 100% coverage with manual overrides

### Verification Script

Check data integrity:

```bash
cd here_transit_system
python -c "
import json
with open('station_lines.json', 'r') as f:
    data = json.load(f)
    print(f'PATH stations: {len(data[\"path_stations\"])}')
    print(f'Complexes: {len(data[\"complexes\"])}')
    print(f'MTA stations: {len(data[\"mta_all_stations\"])}')
    print(f'E01 trains: {data[\"mta_all_stations\"][\"E01\"]}')
"
```

Expected output:
```
PATH stations: 13
Complexes: 8
MTA stations: 496
E01 trains: ['1']
```

---

## 🌐 Deployment Options

### Option 1: Local Network

Server is accessible on your local network:

```bash
python run_server.py
```

Access from other devices:
- `http://YOUR_PC_IP:8000/user1`

### Option 2: Cloudflare Tunnel

Expose to the internet securely:

```bash
# Install Cloudflare Tunnel
# Windows: Download from cloudflare.com
# Linux: curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared

# Run tunnel
cloudflared tunnel --url http://localhost:8000
```

### Option 3: Nginx Reverse Proxy

For subfolder routing (`/einktrain`):

**Nginx Configuration:**
```nginx
location /einktrain {
    proxy_pass http://localhost:8000;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Prefix /einktrain;
}
```

**Application Configuration:**
The `ROOT_PATH=/einktrain` in `.env` handles this automatically.

---

## 🔧 Troubleshooting

### Setup Issues

**Problem:** Virtual environment creation fails
```bash
# Solution: Install venv package
# Windows
py -m pip install virtualenv

# Linux/Mac
sudo apt-get install python3-venv
```

**Problem:** Playwright installation fails
```bash
# Solution: Manual installation
.\venv\Scripts\python.exe -m playwright install chromium
```

### Runtime Issues

**Problem:** Port 8000 already in use
```bash
# Solution: Kill existing process
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Problem:** Weather not updating
```bash
# Check .env has valid OPENWEATHER_API_KEY
# Verify API key at: https://openweathermap.org/api
```

**Problem:** Transit data not loading
```bash
# Check .env has valid HERE_API_KEY
# Verify API key at: https://developer.here.com/
```

### Session/Login Issues

**Problem:** Cannot access config page
```bash
# Clear browser cookies for localhost:8000
# Try accessing /login directly
# Verify SESSION_SECRET_KEY in .env
```

**Problem:** Login fails with valid credentials
```bash
# Check user_configs.json exists
# Verify display_id and password match
# Check server logs for error messages
```

---

## 📝 User Configuration

### Adding New Users

Edit `here_transit_system/user_configs.json`:

```json
{
  "user1": {
    "gtfs_id": "D19",
    "min_minutes": 2,
    "max_minutes": 20,
    "display_res": "800x480",
    "custom_note": "Christopher St - Stonewall",
    "selected_lines": ["1", "PATH"],
    "password": "secure_password_here",
    "weather_data": {
      "temp_c": "--",
      "temp_f": "--",
      "condition": "N/A",
      "icon": "cloud",
      "high_c": "--",
      "low_c": "--"
    }
  },
  "user2": {
    "gtfs_id": "WTC",
    "min_minutes": 2,
    "max_minutes": 20,
    "display_res": "800x480",
    "custom_note": "World Trade Center",
    "selected_lines": ["E", "PATH"],
    "password": "another_secure_password",
    "weather_data": {
      "temp_c": "--",
      "temp_f": "--",
      "condition": "N/A",
      "icon": "cloud",
      "high_c": "--",
      "low_c": "--"
    }
  }
}
```

### Configuration Fields

- **gtfs_id**: Station GTFS ID (see `station_lines.json`)
- **min_minutes**: Minimum arrival time filter (default: 2)
- **max_minutes**: Maximum arrival time filter (default: 20)
- **display_res**: Display resolution (800x480, 640x384, etc.)
- **custom_note**: Custom text shown on display (max 200 chars)
- **selected_lines**: Array of transit lines to display
- **password**: User's login password
- **weather_data**: Auto-updated hourly by server

---

## 🎨 Customization

### Display Resolution

Supported resolutions in config page:
- `800x480` - Standard e-ink (default)
- `640x384` - Waveshare 7.5"
- `600x448` - Waveshare 5.83"
- `400x300` - Waveshare 4.2"

### Custom Notes

Add personalized text to display:
- Maximum 200 characters
- Shown below station name
- Editable in config page

### Line Filtering

Show only specific transit lines:
- Select lines in config page
- Dynamically updates display
- Supports MTA and PATH lines

---

## 🔄 Updates and Maintenance

### Updating Dependencies

```bash
# Activate virtual environment
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Update packages
pip install --upgrade -r requirements.txt
```

### Backing Up Configuration

```bash
# Backup user configs
copy here_transit_system\user_configs.json user_configs.backup.json

# Backup environment
copy here_transit_system\.env .env.backup
```

### Rerunning Setup

If you encounter issues, rerun setup:

```bash
# This is safe - won't overwrite existing configs
python setup_env.py
```

---

## 📖 API Endpoints

### Public Endpoints

- `GET /` - Frontend interface
- `GET /{display_id}` - Display page (no auth required)
- `GET /api/stations` - List all stations
- `GET /api/arrivals/{station}` - Get arrival times

### Protected Endpoints (Requires Session)

- `GET /{display_id}/config` - Configuration page
- `POST /{display_id}/config` - Save configuration

### Authentication Endpoints

- `GET /login` - Login page
- `POST /login` - Process login
- `GET /logout` - Logout and clear session

### Internal Endpoints

- `GET /render/{display_id}` - Screenshot generation (uses localhost)

---

## 🏆 Production Checklist

Before deploying to production:

- [ ] Run `python setup_env.py` and verify all checks pass
- [ ] Configure `.env` with real API keys
- [ ] Generate strong SESSION_SECRET_KEY
- [ ] Review `user_configs.json` passwords
- [ ] Test login/logout flow
- [ ] Verify screenshot rendering works
- [ ] Check weather updates are working
- [ ] Test transit data loading
- [ ] Configure firewall rules if needed
- [ ] Set up Cloudflare Tunnel or reverse proxy
- [ ] Test from external network
- [ ] Set up monitoring/logging

---

## 📞 Support

For issues or questions:

1. Check this README for solutions
2. Review server logs in terminal
3. Verify `.env` configuration
4. Check `user_configs.json` format
5. Ensure all dependencies installed

---

## 📄 License & Credits

**HERE Transit Display**
- Transit data: HERE Maps API
- Weather data: OpenWeather API
- Static data: MTA GTFS feeds
- Framework: FastAPI + Playwright

---

**Last Updated:** January 27, 2026  
**Version:** 2.0 (Automated Maintenance & Security)
