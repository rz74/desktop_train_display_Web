@echo off
echo ============================================================
echo HERE Transit Display - Starting Server
echo ============================================================
echo.

REM Navigate to project root (parent of here_transit_system)
cd /d "%~dp0\.."

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please run setup_env.bat first
    pause
    exit /b 1
)

REM Navigate to here_transit_system and start server
cd here_transit_system
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Server stopped with error code %errorlevel%
    pause
)
