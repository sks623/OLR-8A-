"""
OLR 8A - Telemetry Module
Automatic usage tracking to Google Sheets

Collects: Computer name, Windows version, username, IP, install date, usage stats
NO user credentials are collected.
"""

import os
import platform
import uuid
from datetime import datetime
import urllib.request
import threading

# Google Sheets imports
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("Warning: gspread not installed. Run: pip install gspread google-auth")

# Configuration
SHEET_NAME = "OLR8A_Telemetry"
APP_VERSION = "1.0.0"


def get_config_dir():
    """Get app config directory in AppData"""
    config_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'OLR8A')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_machine_id():
    """Get or create unique machine ID"""
    id_file = os.path.join(get_config_dir(), 'machine_id')
    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            return f.read().strip()
    else:
        machine_id = str(uuid.uuid4())[:8]
        with open(id_file, 'w') as f:
            f.write(machine_id)
        return machine_id


def is_first_run():
    """Check if this is first run"""
    return not os.path.exists(os.path.join(get_config_dir(), 'installed.flag'))


def mark_installed():
    """Mark as installed"""
    flag_file = os.path.join(get_config_dir(), 'installed.flag')
    with open(flag_file, 'w') as f:
        f.write(datetime.now().isoformat())


def get_public_ip():
    """Get public IP address"""
    try:
        services = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ipinfo.io/ip'
        ]
        for service in services:
            try:
                ip = urllib.request.urlopen(service, timeout=5).read().decode('utf8').strip()
                if ip and len(ip) < 50:
                    return ip
            except:
                continue
        return "Unknown"
    except:
        return "Unknown"


def collect_system_info():
    """Collect system information"""
    try:
        return {
            'computer_name': platform.node() or "Unknown",
            'windows_version': platform.platform() or "Unknown",
            'username': os.getlogin() if hasattr(os, 'getlogin') else os.getenv('USERNAME', 'Unknown'),
            'public_ip': get_public_ip(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'machine_id': get_machine_id(),
            'app_version': APP_VERSION
        }
    except Exception as e:
        return {
            'computer_name': "Error",
            'windows_version': "Error",
            'username': "Error",
            'public_ip': "Error",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'machine_id': "Error",
            'app_version': APP_VERSION
        }


def get_gsheet_client():
    """Get authenticated Google Sheets client"""
    if not GSPREAD_AVAILABLE:
        return None

    try:
        # Look for credentials file in multiple locations
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'gsheet_creds.json'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gsheet_creds.json'),
            os.path.join(get_config_dir(), 'gsheet_creds.json'),
            'gsheet_creds.json'
        ]

        creds_file = None
        for path in possible_paths:
            if os.path.exists(path):
                creds_file = path
                break

        if not creds_file:
            print("Telemetry: Credentials file not found")
            return None

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Telemetry error (auth): {e}")
        return None


def _send_event_async(event_type, forward_count=0, reject_count=0):
    """Internal function to send event (runs in thread)"""
    try:
        client = get_gsheet_client()
        if not client:
            return

        sheet = client.open(SHEET_NAME).sheet1
        info = collect_system_info()

        row_data = [
            info['computer_name'],
            info['windows_version'],
            info['username'],
            info['public_ip'],
            info['timestamp'],
            forward_count,
            reject_count,
            info['app_version'],
            event_type
        ]

        sheet.append_row(row_data)
        print(f"Telemetry: {event_type} event sent successfully")

    except Exception as e:
        print(f"Telemetry error: {e}")


def send_install_event():
    """Send installation event to Google Sheets (async)"""
    if not is_first_run():
        return  # Already registered

    # Mark as installed first to prevent duplicate sends
    mark_installed()

    # Send event in background thread
    thread = threading.Thread(
        target=_send_event_async,
        args=('INSTALL', 0, 0),
        daemon=True
    )
    thread.start()


def send_usage_event(forward_count, reject_count):
    """Send usage event after batch processing (async)"""
    thread = threading.Thread(
        target=_send_event_async,
        args=('USAGE', forward_count, reject_count),
        daemon=True
    )
    thread.start()


# Test function
if __name__ == "__main__":
    print("Testing telemetry module...")
    print(f"Config dir: {get_config_dir()}")
    print(f"Machine ID: {get_machine_id()}")
    print(f"First run: {is_first_run()}")
    print(f"System info: {collect_system_info()}")
    print(f"GSpread available: {GSPREAD_AVAILABLE}")

    # Test sending
    print("\nTesting Google Sheets connection...")
    client = get_gsheet_client()
    if client:
        print("Connected successfully!")
        # Uncomment to test:
        # send_install_event()
    else:
        print("Connection failed - check credentials")
