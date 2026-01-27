# HERE Transit Display - Quick Start Guide

🚀 **Get your transit display running in 3 minutes!**

---

## Step 1: Setup Environment (First Time Only)

```bash
python setup_env.py
```

This creates your virtual environment and installs everything.

---

## Step 2: Configure API Keys

Edit `here_transit_system/.env`:

```bash
HERE_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here
SESSION_SECRET_KEY=run_this_command_below
ROOT_PATH=/einktrain
```

**Generate Session Secret:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 3: Verify System

```bash
python verify_system.py
```

All checks should pass ✓

---

## Step 4: Start Server

```bash
python run_server.py
```

Server starts on: **http://localhost:8000**

---

## Access Your Display

- **Main Page:** http://localhost:8000/user1
- **Config Page:** http://localhost:8000/user1/config
- **Login:** Redirects automatically if not authenticated

---

## Default Login

- **Display ID:** `user1`
- **Password:** Check `here_transit_system/user_configs.json`

---

## Troubleshooting

### Can't access config page?
- Clear browser cookies
- Try: http://localhost:8000/login

### Port 8000 in use?
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Setup failed?
Run setup again:
```bash
python setup_env.py
```

---

## 📖 Full Documentation

See `PC_HOSTING_GUIDE.md` for complete details on:
- Security features
- Multi-tenant setup
- Cloudflare deployment
- Customization options
- API endpoints

---

## 🎯 You're Ready!

Your transit display is now:
- ✅ Secured with session authentication
- ✅ Auto-archiving deprecated files
- ✅ Optimized for e-ink rendering
- ✅ Ready for Cloudflare hosting

**Enjoy your real-time transit display!** 🚇🚆🚉
