#!/usr/bin/env python3
"""
System Verification Script for HERE Transit Display
Checks all components are properly configured before deployment.
"""

import json
from pathlib import Path


def print_header(message):
    print("\n" + "=" * 60)
    print(message)
    print("=" * 60)


def print_check(message, status):
    symbol = "✓" if status else "✗"
    print(f"{symbol} {message}")
    return status


def verify_station_data():
    """Verify station_lines.json integrity."""
    print_header("Station Data Verification")
    
    station_file = Path("here_transit_system/station_lines.json")
    
    if not station_file.exists():
        print_check("station_lines.json exists", False)
        return False
    
    try:
        with open(station_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check structure
        has_path = print_check(
            f"PATH stations: {len(data.get('path_stations', {}))} entries",
            'path_stations' in data
        )
        
        has_complexes = print_check(
            f"Complexes: {len(data.get('complexes', {}))} entries",
            'complexes' in data
        )
        
        has_mta = print_check(
            f"MTA stations: {len(data.get('mta_all_stations', {}))} entries",
            'mta_all_stations' in data
        )
        
        # Check E01 data integrity
        e01_correct = False
        if 'mta_all_stations' in data and 'E01' in data['mta_all_stations']:
            e01_lines = data['mta_all_stations']['E01']
            e01_correct = e01_lines == ["1"]
            print_check(
                f"E01 (WTC Cortlandt) correct: {e01_lines}",
                e01_correct
            )
        else:
            print_check("E01 station exists", False)
        
        return has_path and has_complexes and has_mta and e01_correct
        
    except Exception as e:
        print_check(f"Error reading station_lines.json: {e}", False)
        return False


def verify_security():
    """Verify security implementation."""
    print_header("Security Verification")
    
    main_file = Path("here_transit_system/main.py")
    
    if not main_file.exists():
        print_check("main.py exists", False)
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check SessionMiddleware
    has_middleware = print_check(
        "SessionMiddleware imported",
        "from starlette.middleware.sessions import SessionMiddleware" in content
    )
    
    has_middleware_setup = print_check(
        "SessionMiddleware configured",
        "app.add_middleware(SessionMiddleware" in content
    )
    
    # Check authentication routes
    has_login = print_check(
        "Login route exists",
        '@app.get("/login")' in content or '@app.post("/login")' in content
    )
    
    has_logout = print_check(
        "Logout route exists",
        '@app.get("/logout")' in content
    )
    
    # Check session validation
    has_session_check = print_check(
        "Session validation in config routes",
        "session_display_id = request.session.get('display_id')" in content
    )
    
    # Check render bypass
    has_localhost = print_check(
        "Render endpoint uses localhost",
        'url = f"http://localhost:8000/{display_id}"' in content
    )
    
    return all([
        has_middleware,
        has_middleware_setup,
        has_login,
        has_logout,
        has_session_check,
        has_localhost
    ])


def verify_automation():
    """Verify automation scripts."""
    print_header("Automation Verification")
    
    setup_script = Path("setup_env.py")
    launcher_script = Path("run_server.py")
    
    has_setup = print_check(
        "setup_env.py exists",
        setup_script.exists()
    )
    
    has_launcher = print_check(
        "run_server.py exists",
        launcher_script.exists()
    )
    
    # Check archive function in main.py
    main_file = Path("here_transit_system/main.py")
    has_archive = False
    if main_file.exists():
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        has_archive = print_check(
            "File archiving function exists",
            "def archive_deprecated_files():" in content
        )
    
    return has_setup and has_launcher and has_archive


def verify_environment():
    """Verify environment configuration."""
    print_header("Environment Configuration")
    
    env_file = Path("here_transit_system/.env")
    
    if not env_file.exists():
        print_check(".env file exists", False)
        print("  → Run: python setup_env.py")
        return False
    
    print_check(".env file exists", True)
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Check required keys
    required_keys = {
        "HERE_API_KEY": "HERE Maps API key",
        "OPENWEATHER_API_KEY": "OpenWeather API key",
        "SESSION_SECRET_KEY": "Session secret key",
        "ROOT_PATH": "Root path configuration"
    }
    
    all_configured = True
    for key, description in required_keys.items():
        if key in env_content:
            value = env_content.split(f"{key}=")[1].split("\n")[0].strip()
            if value and "your_" not in value.lower() and len(value) > 5:
                print_check(f"{description} configured", True)
            else:
                print_check(f"{description} configured", False)
                all_configured = False
        else:
            print_check(f"{description} exists", False)
            all_configured = False
    
    return all_configured


def verify_templates():
    """Verify template files."""
    print_header("Template Verification")
    
    templates_dir = Path("here_transit_system/templates")
    
    if not templates_dir.exists():
        print_check("templates/ directory exists", False)
        return False
    
    required_templates = [
        "login.html",
        "config.html"
    ]
    
    all_exist = True
    for template in required_templates:
        exists = (templates_dir / template).exists()
        print_check(f"{template} exists", exists)
        all_exist = all_exist and exists
    
    # Check if login.html has redirect_to handling
    login_file = templates_dir / "login.html"
    if login_file.exists():
        with open(login_file, 'r') as f:
            login_content = f.read()
        has_redirect = print_check(
            "Login template has redirect_to handling",
            'redirect_to' in login_content
        )
        all_exist = all_exist and has_redirect
    
    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("HERE Transit Display - System Verification")
    print("=" * 60)
    
    results = {
        "Station Data": verify_station_data(),
        "Security": verify_security(),
        "Automation": verify_automation(),
        "Environment": verify_environment(),
        "Templates": verify_templates()
    }
    
    print_header("Verification Summary")
    
    all_passed = True
    for category, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{category:20s} {status}")
        all_passed = all_passed and passed
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - System Ready for Deployment")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Start server: python run_server.py")
        print("  2. Test login: http://localhost:8000/user1/config")
        print("  3. Configure Cloudflare Tunnel for public access")
    else:
        print("✗ SOME CHECKS FAILED - Please Review Above")
        print("=" * 60)
        print("\nRecommended actions:")
        print("  1. Run setup: python setup_env.py")
        print("  2. Configure .env file with API keys")
        print("  3. Run this script again to verify")
    
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
