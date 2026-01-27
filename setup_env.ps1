# Desktop Train Display - Environment Setup (PowerShell)
# ==============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Desktop Train Display - Environment Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project root
Set-Location $PSScriptRoot

# Check if Python is installed
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10 or higher from https://www.python.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check if venv already exists
if (Test-Path "venv") {
    Write-Host "[2/5] Virtual environment already exists at: venv\" -ForegroundColor Yellow
    Write-Host "      Skipping creation..." -ForegroundColor Gray
} else {
    Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Write-Host "Make sure you have Python venv module installed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "      > Virtual environment created successfully" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "      > Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Check if pip is available
Write-Host "[4/5] Checking pip installation..." -ForegroundColor Yellow
$pipCheck = python -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "      pip not found, installing pip..." -ForegroundColor Gray
    python -m ensurepip --default-pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install pip" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
$pipVersion = python -m pip --version
Write-Host "      > pip version: $pipVersion" -ForegroundColor Green
Write-Host ""

# Upgrade pip to latest version
Write-Host "      Upgrading pip to latest version..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet
Write-Host ""

# Install required packages
Write-Host "[5/5] Installing required packages from requirements.txt..." -ForegroundColor Yellow
if (-not (Test-Path "here_transit_system\requirements.txt")) {
    Write-Host "ERROR: requirements.txt not found in here_transit_system\" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

python -m pip install -r here_transit_system\requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install packages" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Virtual environment is ready at: $PWD\venv" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Navigate to here_transit_system folder" -ForegroundColor White
Write-Host "  2. Create .env file with your API keys (see .env.example)" -ForegroundColor White
Write-Host "  3. Run start_server.bat to start the application" -ForegroundColor White
Write-Host ""
Write-Host "To activate the virtual environment manually:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
