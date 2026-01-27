#!/usr/bin/env python3
"""
Environment Setup Script for HERE Transit Display
Automates virtual environment creation, dependency installation, and configuration.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 60)
    print(message)
    print("=" * 60 + "\n")


def print_step(message):
    """Print a step message."""
    print(f"► {message}")


def print_success(message):
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")


def check_python_version():
    """Verify Python version is 3.8 or higher."""
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True


def create_virtual_environment(venv_path):
    """Create a virtual environment if it doesn't exist."""
    print_step("Checking virtual environment...")
    
    if venv_path.exists():
        print_success(f"Virtual environment already exists at: {venv_path}")
        return True
    
    try:
        print_step(f"Creating virtual environment at: {venv_path}")
        venv.create(venv_path, with_pip=True)
        print_success("Virtual environment created successfully")
        return True
    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def get_venv_python(venv_path):
    """Get the path to the virtual environment's Python executable."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip(venv_path):
    """Get the path to the virtual environment's pip executable."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def install_dependencies(venv_path, requirements_file):
    """Install dependencies from requirements.txt."""
    print_step("Installing dependencies from requirements.txt...")
    
    if not requirements_file.exists():
        print_error(f"requirements.txt not found at: {requirements_file}")
        return False
    
    pip_path = get_venv_pip(venv_path)
    
    try:
        # Upgrade pip first
        print_step("Upgrading pip...")
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print_success("pip upgraded")
        
        # Install requirements
        print_step("Installing packages...")
        result = subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)],
            check=True,
            capture_output=False
        )
        print_success("All dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def install_playwright_browser(venv_path):
    """Install Playwright Chromium browser."""
    print_step("Installing Playwright Chromium browser...")
    
    python_path = get_venv_python(venv_path)
    
    try:
        subprocess.run(
            [str(python_path), "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=False
        )
        print_success("Playwright Chromium installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install Playwright browser: {e}")
        print("You may need to run this manually later:")
        print(f"  {python_path} -m playwright install chromium")
        return False


def check_env_file(project_root):
    """Check if .env file exists and prompt user if missing."""
    env_file = project_root / "here_transit_system" / ".env"
    env_example = project_root / "here_transit_system" / ".env.example"
    
    print_step("Checking environment configuration...")
    
    if env_file.exists():
        print_success(f".env file exists at: {env_file}")
        
        # Check if required keys are present
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        required_keys = [
            "HERE_API_KEY",
            "OPENWEATHER_API_KEY",
            "SESSION_SECRET_KEY",
            "ROOT_PATH"
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in env_content or f"{key}=" in env_content and not env_content.split(f"{key}=")[1].split("\n")[0].strip():
                missing_keys.append(key)
        
        if missing_keys:
            print(f"\n⚠ Warning: The following keys are missing or empty in .env:")
            for key in missing_keys:
                print(f"  - {key}")
            print(f"\nPlease edit {env_file} and fill in the required values.")
            return False
        else:
            print_success("All required environment variables are configured")
            return True
    else:
        print_error(f".env file not found at: {env_file}")
        
        # Create from example if available
        if env_example.exists():
            print_step("Creating .env from .env.example...")
            with open(env_example, 'r') as src:
                content = src.read()
            with open(env_file, 'w') as dst:
                dst.write(content)
            print_success(".env file created from template")
        else:
            # Create basic .env template
            print_step("Creating basic .env template...")
            template = """# HERE Transit Display - Environment Configuration

# HERE Maps API Key (required for transit data)
# Get yours at: https://developer.here.com/
HERE_API_KEY=your_here_api_key_here

# OpenWeather API Key (required for weather data)
# Get yours at: https://openweathermap.org/api
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Session Secret Key (required for authentication)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SESSION_SECRET_KEY=

# Root Path for deployment (default: /einktrain)
ROOT_PATH=/einktrain
"""
            with open(env_file, 'w') as f:
                f.write(template)
            print_success(".env template created")
        
        print(f"\n⚠ IMPORTANT: Please edit {env_file} and fill in:")
        print("  1. HERE_API_KEY - Get from https://developer.here.com/")
        print("  2. OPENWEATHER_API_KEY - Get from https://openweathermap.org/api")
        print("  3. SESSION_SECRET_KEY - Generate with:")
        print('     python -c "import secrets; print(secrets.token_hex(32))"')
        print("  4. ROOT_PATH - Set to /einktrain (or your preferred path)")
        return False


def create_archive_directory(project_root):
    """Create archive directory for deprecated files."""
    print_step("Creating archive directory...")
    archive_dir = project_root / "archive"
    archive_dir.mkdir(exist_ok=True)
    print_success(f"Archive directory ready at: {archive_dir}")
    return True


def main():
    """Main setup function."""
    print_header("HERE Transit Display - Environment Setup")
    
    # Get project root
    project_root = Path(__file__).parent.absolute()
    print(f"Project root: {project_root}\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    venv_path = project_root / "venv"
    if not create_virtual_environment(venv_path):
        sys.exit(1)
    
    # Install dependencies
    requirements_file = project_root / "requirements.txt"
    if not install_dependencies(venv_path, requirements_file):
        print("\n⚠ Warning: Some dependencies may not have installed correctly.")
        print("You may need to install them manually.")
    
    # Install Playwright browser
    if not install_playwright_browser(venv_path):
        print("\n⚠ Warning: Playwright browser installation failed.")
        print("Screenshot functionality may not work until you run:")
        print(f"  {get_venv_python(venv_path)} -m playwright install chromium")
    
    # Check .env configuration
    env_ready = check_env_file(project_root)
    
    # Create archive directory
    create_archive_directory(project_root)
    
    # Final summary
    print_header("Setup Complete!")
    
    if env_ready:
        print_success("Environment is fully configured and ready to use!")
        print("\nTo start the server, run:")
        if sys.platform == "win32":
            print(f"  python run_server.py")
        else:
            print(f"  python3 run_server.py")
    else:
        print("⚠ Setup is almost complete!")
        print("\nNext steps:")
        print("  1. Edit the .env file with your API keys")
        print("  2. Run this setup script again to verify")
        print("  3. Start the server with: python run_server.py")
    
    print("\nFor more information, see the documentation.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
