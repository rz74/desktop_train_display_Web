#!/usr/bin/env python3
"""
Server Launcher for HERE Transit Display
Activates virtual environment and starts Uvicorn server with correct configuration.
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 60)
    print(message)
    print("=" * 60 + "\n")


def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")


def get_venv_python(venv_path):
    """Get the path to the virtual environment's Python executable."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def check_environment(project_root):
    """Check if environment is properly set up."""
    venv_path = project_root / "venv"
    python_path = get_venv_python(venv_path)
    env_file = project_root / "here_transit_system" / ".env"
    
    issues = []
    
    # Check virtual environment
    if not venv_path.exists():
        issues.append("Virtual environment not found. Run: python setup_env.py")
    elif not python_path.exists():
        issues.append(f"Python executable not found in venv: {python_path}")
    
    # Check .env file
    if not env_file.exists():
        issues.append(".env file not found. Run: python setup_env.py")
    else:
        # Check if keys are configured
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if "your_here_api_key_here" in env_content or "your_openweather_api_key_here" in env_content:
            issues.append(".env file contains placeholder values. Please configure your API keys.")
        
        if not any(line.startswith("SESSION_SECRET_KEY=") and len(line.split("=")[1].strip()) > 0 
                   for line in env_content.split("\n")):
            issues.append("SESSION_SECRET_KEY not set in .env file.")
    
    return issues


def main():
    """Main server launcher function."""
    print_header("HERE Transit Display - Server Launcher")
    
    # Get project root
    project_root = Path(__file__).parent.absolute()
    venv_path = project_root / "venv"
    python_path = get_venv_python(venv_path)
    here_transit_dir = project_root / "here_transit_system"
    
    # Check environment
    issues = check_environment(project_root)
    
    if issues:
        print_error("Environment check failed:\n")
        for issue in issues:
            print(f"  ✗ {issue}")
        print("\nPlease run the setup script first:")
        print("  python setup_env.py\n")
        sys.exit(1)
    
    print("✓ Environment check passed")
    print(f"✓ Virtual environment: {venv_path}")
    print(f"✓ Python executable: {python_path}")
    print(f"✓ Working directory: {here_transit_dir}")
    
    # Start server
    print_header("Starting Uvicorn Server")
    print("Server will run on: http://0.0.0.0:8000")
    print("Access via: http://localhost:8000")
    print("Root path: /einktrain")
    print("\nPress CTRL+C to stop the server\n")
    print("-" * 60 + "\n")
    
    try:
        # Change to here_transit_system directory
        os.chdir(here_transit_dir)
        
        # Start Uvicorn server
        subprocess.run(
            [
                str(python_path),
                "-m",
                "uvicorn",
                "main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ],
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Server stopped by user")
        print("=" * 60 + "\n")
    except subprocess.CalledProcessError as e:
        print_error(f"Server failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
