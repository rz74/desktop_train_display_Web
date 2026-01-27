@echo off
echo ============================================================
echo HERE Transit Display - Starting Server
echo ============================================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "..\venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_env.bat from the project root directory first
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call ..\venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please run setup_env.bat from the project root directory
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create .env with required API keys:
    echo   - HERE_API_KEY
    echo   - OPENWEATHER_API_KEY (optional)
    echo   - ADMIN_PASSCODE
    echo   - USER1_PW, USER2_PW, etc. (one for each user)
    echo   - SESSION_SECRET_KEY (optional - will auto-generate)
    echo See .env.example for reference
    pause
    exit /b 1
)

REM Start the server
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop
echo.
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Server stopped with error code %errorlevel%
    pause
)
