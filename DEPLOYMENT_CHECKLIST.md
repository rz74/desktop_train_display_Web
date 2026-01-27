# Server Deployment Checklist

## Current Status
✅ Session authentication removed from main.py
✅ start_server.bat updated (SESSION_SECRET_KEY removed)
✅ main.py compiles without syntax errors
✅ requirements.txt includes python-multipart>=0.0.5

## Server PC Deployment Steps

### Location
**Server PC Path:** `C:\Users\RZ\Desktop\eink\desktop_train_display_Web\here_transit_system`

### Step 1: Install Missing Dependency
```bash
cd C:\Users\RZ\Desktop\eink\desktop_train_display_Web\here_transit_system
..\venv\Scripts\activate
pip install python-multipart
```

**Expected Output:**
```
Successfully installed python-multipart-0.0.x
```

### Step 2: Verify .env File
Check that `.env` exists with these variables:
```
HERE_API_KEY=your_key_here
ADMIN_PASSCODE=your_password
USER1_PW=user1_password
USER2_PW=user2_password
OPENWEATHER_API_KEY=your_key_here (optional)
ROOT_PATH=/einktrain (optional)
```

**NO LONGER NEEDED:**
- ❌ SESSION_SECRET_KEY (removed)

### Step 3: Start Server
```bash
start_server.bat
```

**Expected Output:**
```
============================================================
HERE Transit Display - Starting Server
============================================================

Starting server on http://localhost:8000
Press Ctrl+C to stop

INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Should NOT see:**
- ❌ `RuntimeError: Form data requires "python-multipart" to be installed`
- ❌ SESSION_SECRET_KEY errors
- ❌ Session-related warnings

### Step 4: Test Endpoints

1. **Display Page:**
   ```
   http://localhost:8000/user1
   ```
   Should show train arrival display

2. **Config Page:**
   ```
   http://localhost:8000/user1/config
   ```
   Should show configuration form (no login required)

3. **Admin Page:**
   ```
   http://localhost:8000/admin
   ```
   Should show admin panel (requires ADMIN_PASSCODE)

### Step 5: Verify on Network

From another device on the same network:
```
http://<SERVER_PC_IP>:8000/user1
```

Replace `<SERVER_PC_IP>` with the server's IP address (e.g., 192.168.1.100)

## Troubleshooting

### Problem: python-multipart error
**Solution:** Run `pip install python-multipart` in activated venv

### Problem: Server won't start
**Check:**
1. Is venv activated?
2. Does .env file exist?
3. Are required environment variables set?
4. Is port 8000 already in use?

### Problem: Can't access from other devices
**Check:**
1. Windows Firewall settings (allow port 8000)
2. Server PC IP address (use `ipconfig` to find it)
3. Both devices on same network

### Problem: Config page won't save
**Check:**
1. python-multipart installed?
2. user_configs.json writable?
3. Check browser console for errors

## Quick Verification Commands

```bash
# Check Python version
python --version

# Check installed packages
pip list | findstr "multipart\|fastapi\|uvicorn"

# Check if port 8000 is in use
netstat -ano | findstr ":8000"

# Get server IP address
ipconfig | findstr "IPv4"
```

## Success Criteria

✅ Server starts without errors
✅ Display pages load with train data
✅ Config pages accessible without login
✅ Can update configuration and save
✅ Accessible from other devices on network
✅ No SESSION_SECRET_KEY warnings

## Date
2025-01-XX

## Next Steps After Deployment

Once server is running:
1. Configure each display (user1, user2, etc.)
2. Test e-ink display refresh
3. Set up auto-start (optional):
   - Add start_server.bat to Windows Startup folder
   - Or create Windows Task Scheduler task

## Notes

- Session authentication removed for simplicity
- Direct access to all pages (acceptable for private network)
- Passwords still validated on initial configuration
- python-multipart required for form handling
- Playwright optional (for screenshots)
