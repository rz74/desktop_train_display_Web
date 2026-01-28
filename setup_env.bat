@echo off
echo ============================================================
echo Desktop Train Display - Environment Setup
echo ============================================================
echo.

REM Navigate to project root
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Python detected: 
python --version
echo.

REM Check if venv already exists
if exist "venv\" (
    echo [2/5] Virtual environment already exists at: venv\
    echo       Skipping creation...
) else (
    echo [2/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure you have Python venv module installed
        pause
        exit /b 1
    )
    echo       ^> Virtual environment created successfully
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo       ^> Virtual environment activated
echo.

REM Check if pip is available
echo [4/5] Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo       pip not found, installing pip...
    python -m ensurepip --default-pip
    if errorlevel 1 (
        echo ERROR: Failed to install pip
        pause
        exit /b 1
    )
)
echo       ^> pip version:
python -m pip --version
echo.

REM Upgrade pip to latest version
echo       Upgrading pip to latest version...
python -m pip install --upgrade pip >nul 2>&1
echo.

REM Install required packages
echo [5/5] Installing required packages from requirements.txt...
if not exist "here_transit_system\requirements.txt" (
    echo ERROR: requirements.txt not found in here_transit_system\
    pause
    exit /b 1
)

python -m pip install -r here_transit_system\requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install packages
    echo.
    echo If you see "Microsoft Visual C++ 14.0 or greater is required" error:
    echo   Option 1: Install Microsoft C++ Build Tools from:
    echo             https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo   Option 2: Install pre-built packages individually:
    echo             python -m pip install fastapi uvicorn[standard] httpx python-dotenv jinja2 pillow
    echo.
    pause
    exit /b 1
)
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Virtual environment is ready at: %CD%\venv
echo.
echo Next steps:
echo   1. Navigate to here_transit_system folder
echo   2. Create .env file with your API keys (see .env.example)
echo   3. Run start_server.bat to start the application
echo.
echo NOTE: Playwright browser rendering is disabled by default.
echo       The system uses Pillow-based image rendering instead.
echo       To enable Playwright, set ENABLE_PLAYWRIGHT_RENDERING = True in main.py
echo       and run: python -m playwright install chromium
echo.
pause
