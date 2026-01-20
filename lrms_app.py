"""
LRMS - Land Records Management System Login & Data Extraction Application
===========================================================================
Version 3.0 - With Tabbed UI, Incremental CSV Save, Resume Support

DESIGNED BY SUSHANT
"""

import customtkinter as ctk
from tkinter import messagebox, StringVar, filedialog
import json
import os
import sys
import csv
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import shutil
import math

# Telemetry for usage tracking
try:
    from telemetry import send_install_event, send_usage_event
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    print("Telemetry disabled - module not found")


# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Premium Color Palette
COLORS = {
    "bg_dark": "#0a0a0f",
    "bg_card": "#12141a",
    "bg_card_hover": "#1a1d24",
    "accent_cyan": "#00d4ff",
    "accent_cyan_dark": "#0099cc",
    "accent_blue": "#2980b9", # Added blue
    "accent_green": "#00ff88",
    "accent_green_dark": "#00cc6a",
    "accent_orange": "#ff9500",
    "accent_orange_dark": "#cc7700",
    "text_primary": "#ffffff",
    "text_secondary": "#8892a0",
    "border_subtle": "#2a2d35",
}

# Dynamic wait timeout (seconds)
WAIT_TIMEOUT = 30

# PDF size limit (295KB in bytes)
PDF_MAX_SIZE_KB = 295
PDF_MAX_SIZE_BYTES = PDF_MAX_SIZE_KB * 1024

# =============================================================================
# FILE SYSTEM & PATH MANAGEMENT (SAFE STORAGE)
# =============================================================================
class AppPaths:
    """Manages safe storage locations in User Documents to avoid Permission Errors."""
    
    # Base Directory: ~\Documents\LRMS_Data
    BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "LRMS_Data")
    
    # Subdirectories
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
    
    # File Paths
    CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
    VILLAGE_CACHE_FILE = os.path.join(CACHE_DIR, "village_plots_cache.json")
    BENCHMARK_CACHE_FILE = os.path.join(CACHE_DIR, "valuation_benchmark_cache.json")
    MAPPINGS_FILE = os.path.join(CONFIG_DIR, "village_mappings.json")
    
    @classmethod
    def initialize(cls):
        """Ensure all directories exist and migrate old data if needed."""
        try:
            # Create directories
            for path in [cls.BASE_DIR, cls.CACHE_DIR, cls.CONFIG_DIR, cls.TEMP_DIR, cls.EXPORTS_DIR]:
                os.makedirs(path, exist_ok=True)
                
            # MIGRATION: Check for files in OLD location (App Dir) and move them
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 1. Credentials
            old_creds = os.path.join(app_dir, "credentials.json")
            if os.path.exists(old_creds) and not os.path.exists(cls.CREDENTIALS_FILE):
                try:
                    shutil.copy2(old_creds, cls.CREDENTIALS_FILE)
                    print(f"📦 Migrated credentials to {cls.CREDENTIALS_FILE}")
                except Exception as e:
                    print(f"⚠️ Failed to migrate credentials: {e}")

            # 2. Caches
            old_village = os.path.join(app_dir, "village_plots_cache.json")
            if os.path.exists(old_village) and not os.path.exists(cls.VILLAGE_CACHE_FILE):
                try: shutil.copy2(old_village, cls.VILLAGE_CACHE_FILE)
                except: pass

            old_bench = os.path.join(app_dir, "valuation_benchmark_cache.json")
            if os.path.exists(old_bench) and not os.path.exists(cls.BENCHMARK_CACHE_FILE):
                try: shutil.copy2(old_bench, cls.BENCHMARK_CACHE_FILE)
                except: pass

            old_mappings = os.path.join(app_dir, "village_mappings.json")
            if os.path.exists(old_mappings) and not os.path.exists(cls.MAPPINGS_FILE):
                try: shutil.copy2(old_mappings, cls.MAPPINGS_FILE)
                except: pass

        except Exception as e:
            print(f"❌ Critical Storage Error: {e}")
            messagebox.showerror("Storage Error", f"Failed to initialize storage in Documents folder.\n\n{e}")

# Initialize Paths Immediately
AppPaths.initialize()

# Compressed PDFs folder (Temp)
COMPRESSED_PDF_FOLDER = AppPaths.TEMP_DIR

# Village Cache File
VILLAGE_CACHE_FILE = AppPaths.VILLAGE_CACHE_FILE

# Benchmark Cache File
BENCHMARK_CACHE_FILE = AppPaths.BENCHMARK_CACHE_FILE

# Compression method available
GHOSTSCRIPT_AVAILABLE = None
PIKEPDF_AVAILABLE = None

# ChromeDriver path (set by background thread on startup)
CHROMEDRIVER_PATH = None

def prepare_chromedriver_background():
    """Prepare ChromeDriver in background thread (optimization)"""
    global CHROMEDRIVER_PATH
    try:
        CHROMEDRIVER_PATH = ChromeDriverManager().install()
        print("ChromeDriver ready")
    except Exception as e:
        print(f"ChromeDriver check failed: {e}")
        CHROMEDRIVER_PATH = None


def install_ghostscript():
    """Auto-install Ghostscript using winget (Windows Package Manager)."""
    print("📦 Installing Ghostscript...")
    
    try:
        # Try winget first (Windows 10/11)
        # Try winget first (Windows 10/11)
        # Fix: Add CREATE_NO_WINDOW to prevent EXE freeze
        result = subprocess.run(
            ["winget", "install", "-e", "--id", "ArtifexSoftware.GhostScript", "--silent", "--accept-package-agreements", "--accept-source-agreements"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout for installation
            creationflags=0x08000000, # CREATE_NO_WINDOW
            stdin=subprocess.DEVNULL
        )
        
        if result.returncode == 0:
            print("✅ Ghostscript installed successfully via winget!")
            return True
        else:
            print(f"⚠️ winget installation returned: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("⚠️ winget not found. Trying alternative method...")
        
        # Try chocolatey as fallback
        try:
            result = subprocess.run(
                ["choco", "install", "ghostscript", "-y"],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=0x08000000,
                stdin=subprocess.DEVNULL
            )
            if result.returncode == 0:
                print("✅ Ghostscript installed successfully via chocolatey!")
                return True
        except:
            pass
        
        return False
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False


def check_ghostscript(auto_install=True):
    """Check if Ghostscript is installed, optionally auto-install."""
    global GHOSTSCRIPT_AVAILABLE
    
    # Check if already verified
    if GHOSTSCRIPT_AVAILABLE is not None and GHOSTSCRIPT_AVAILABLE:
        return GHOSTSCRIPT_AVAILABLE
    
    # Check common Ghostscript commands
    for gs_cmd in ["gswin64c", "gswin32c", "gs"]:
        try:
            result = subprocess.run(
                [gs_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=0x08000000,
                stdin=subprocess.DEVNULL
            )
            if result.returncode == 0:
                GHOSTSCRIPT_AVAILABLE = gs_cmd
                print(f"✅ Ghostscript found: {gs_cmd}")
                return gs_cmd
        except:
            continue
    
    # Not found - try to install
    if auto_install:
        print("⚠️ Ghostscript not found. Attempting auto-install...")
        if install_ghostscript():
            # Reset and check again after installation
            GHOSTSCRIPT_AVAILABLE = None
            
            # Need to refresh PATH - Ghostscript adds itself to PATH
            # Try common installation paths
            gs_paths = [
                r"C:\Program Files\gs\gs10.03.1\bin",
                r"C:\Program Files\gs\gs10.02.1\bin",
                r"C:\Program Files\gs\gs10.01.1\bin",
                r"C:\Program Files\gs\gs10.00.0\bin",
                r"C:\Program Files (x86)\gs\gs10.03.1\bin",
            ]
            
            for gs_path in gs_paths:
                gs_exe = os.path.join(gs_path, "gswin64c.exe")
                if os.path.exists(gs_exe):
                    GHOSTSCRIPT_AVAILABLE = gs_exe
                    print(f"✅ Ghostscript ready: {gs_exe}")
                    return gs_exe
                    
                gs_exe = os.path.join(gs_path, "gswin32c.exe")
                if os.path.exists(gs_exe):
                    GHOSTSCRIPT_AVAILABLE = gs_exe
                    print(f"✅ Ghostscript ready: {gs_exe}")
                    return gs_exe
            
            # Check PATH again
            for gs_cmd in ["gswin64c", "gswin32c", "gs"]:
                try:
                    result = subprocess.run(
                        [gs_cmd, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=0x08000000,
                        stdin=subprocess.DEVNULL
                    )
                    if result.returncode == 0:
                        GHOSTSCRIPT_AVAILABLE = gs_cmd
                        return gs_cmd
                except:
                    continue
    
    GHOSTSCRIPT_AVAILABLE = False
    return False


def check_and_install_pikepdf():
    """Check if pikepdf is available, install if not."""
    global PIKEPDF_AVAILABLE
    
    if PIKEPDF_AVAILABLE is not None:
        return PIKEPDF_AVAILABLE
    
    try:
        import pikepdf
        PIKEPDF_AVAILABLE = True
        return True
    except ImportError:
        # Try to install pikepdf
        print("📦 Installing pikepdf for PDF compression...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pikepdf", "-q"],
                capture_output=True,
                timeout=120,
                creationflags=0x08000000,
                stdin=subprocess.DEVNULL
            )
            import pikepdf
            PIKEPDF_AVAILABLE = True
            print("✅ pikepdf installed successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to install pikepdf: {e}")
            PIKEPDF_AVAILABLE = False
            return False


def compress_pdf_ghostscript(input_path, output_path, gs_cmd):
    """Compress PDF using Ghostscript with dynamic settings."""
    input_size = os.path.getsize(input_path)

    # Try compression levels: ebook first, then screen if needed
    for setting in ["/ebook", "/screen"]:
        try:
            gs_command = [
                gs_cmd,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS={setting}",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={output_path}",
                input_path
            ]

            result = subprocess.run(gs_command, capture_output=True, text=True, timeout=60, creationflags=0x08000000, stdin=subprocess.DEVNULL)

            if result.returncode == 0 and os.path.exists(output_path):
                output_size = os.path.getsize(output_path)

                # Check if compression actually reduced size
                if output_size < input_size:
                    print(f"Ghostscript: {setting} reduced {input_size} → {output_size} bytes")
                    return True  # Success!
                else:
                    # Compression made it bigger, try next setting
                    print(f"Ghostscript: {setting} increased size ({input_size} → {output_size}), trying next...")
                    os.remove(output_path)
                    continue
        except Exception as e:
            print(f"Ghostscript compression error ({setting}): {e}")
            continue

    return False  # All settings failed


def compress_pdf_pikepdf(input_path, output_path):
    """Compress PDF using pikepdf (Python library)."""
    try:
        import pikepdf
        
        with pikepdf.open(input_path) as pdf:
            pdf.save(output_path, 
                     compress_streams=True,
                     object_stream_mode=pikepdf.ObjectStreamMode.generate,
                     recompress_flate=True)
        
        return os.path.exists(output_path)
    except Exception as e:
        print(f"pikepdf compression error: {e}")
        return False


def compress_pdf(input_path, output_path):
    """Compress PDF using available method (Ghostscript or pikepdf)."""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Try Ghostscript first (better compression)
        gs_cmd = check_ghostscript()
        if gs_cmd:
            if compress_pdf_ghostscript(input_path, output_path, gs_cmd):
                return True
        
        # Fallback to pikepdf
        if check_and_install_pikepdf():
            if compress_pdf_pikepdf(input_path, output_path):
                return True
        
        return False
        
    except Exception as e:
        print(f"Compression error: {e}")
        return False


def get_compression_method():
    """Get the available compression method name."""
    gs = check_ghostscript()
    if gs:
        return f"Ghostscript ({gs})"
    if check_and_install_pikepdf():
        return "pikepdf (Python)"
    return None


def get_file_size_kb(filepath):
    """Get file size in KB."""
    return os.path.getsize(filepath) / 1024


class CredentialManager:
    """Manages saving and loading credentials securely."""
    
    def __init__(self, filename="credentials.json"):
        # Use Safe Config Path
        self.filepath = AppPaths.CREDENTIALS_FILE
        self.credentials = self.load()
    
    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except:
                return {"saccess": [], "lrms": []}
        return {"saccess": [], "lrms": []}
    
    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.credentials, f, indent=2)
    
    def add_saccess(self, username, password):
        for cred in self.credentials["saccess"]:
            if cred["username"] == username:
                cred["password"] = password
                self.save()
                return
        self.credentials["saccess"].append({"username": username, "password": password})
        self.save()
    
    def add_lrms(self, username, password):
        for cred in self.credentials["lrms"]:
            if cred["username"] == username:
                cred["password"] = password
                self.save()
                return
        self.credentials["lrms"].append({"username": username, "password": password})
        self.save()
    
    def get_saccess_users(self):
        return [cred["username"] for cred in self.credentials["saccess"]]
    
    def get_lrms_users(self):
        return [cred["username"] for cred in self.credentials["lrms"]]
    
    def get_saccess_password(self, username):
        for cred in self.credentials["saccess"]:
            if cred["username"] == username:
                return cred["password"]
        return ""
    
    def get_lrms_password(self, username):
        for cred in self.credentials["lrms"]:
            if cred["username"] == username:
                return cred["password"]
        return ""
    
    def delete_saccess(self, username):
        self.credentials["saccess"] = [c for c in self.credentials["saccess"] if c["username"] != username]
        self.save()
    
    def delete_lrms(self, username):
        self.credentials["lrms"] = [c for c in self.credentials["lrms"] if c["username"] != username]
        self.save()


class ExcelManager:
    """Manages incremental Excel writing with openpyxl."""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.headers = None
        self.row_count = 1  # Start after header row
        
        # Check if file exists and load it
        if os.path.exists(filepath):
            try:
                from openpyxl import load_workbook
                self.workbook = load_workbook(filepath)
                self.sheet = self.workbook.active
                self.row_count = self.sheet.max_row + 1
                self.headers = [cell.value for cell in self.sheet[1]]
            except:
                self._create_new_workbook()
        else:
            self._create_new_workbook()
    
    def _create_new_workbook(self):
        """Create a new workbook."""
        from openpyxl import Workbook
        self.workbook = Workbook()
        self.sheet = self.workbook.active
        self.sheet.title = "OLR 8A Cases"
        self.row_count = 1
        self.headers = None
    
    def write_row(self, data_dict):
        """Write a single row to Excel immediately."""
        try:
            # Skip internal keys like _plot_rows
            filtered_data = {k: v for k, v in data_dict.items() if not k.startswith('_') and not isinstance(v, list)}
            
            # Write headers if first row
            if self.headers is None:
                self.headers = list(filtered_data.keys())
                for col, header in enumerate(self.headers, 1):
                    self.sheet.cell(row=1, column=col, value=header)
                self.row_count = 2
            
            # Write data row
            for col, header in enumerate(self.headers, 1):
                value = filtered_data.get(header, "")
                self.sheet.cell(row=self.row_count, column=col, value=value)
            
            self.row_count += 1
            
            # REMOVED AUTO-SAVE FOR SPEED (Batch saving used instead)
            # self.workbook.save(self.filepath)
            
            return True
        except Exception as e:
            print(f"Excel write error: {e}")
            return False
    
    def save(self):
        """Explicitly save the workbook to disk."""
        try:
            self.workbook.save(self.filepath)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def close(self):
        """Close the workbook."""
        try:
            self.workbook.save(self.filepath)
        except:
            pass


class LoginAutomation:
    """Handles the browser automation for login and data extraction."""
    
    def __init__(self, status_callback=None, progress_callback=None):
        self.driver = None
        self.wait = None
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.running = False
        self.stop_extraction = False  # Flag to stop extraction midway
        self.lrms_username = ""
        self.lrms_password = ""
        self.excel_manager = None
        self.cases_extracted = 0
    
    def update_status(self, message):
        if self.status_callback:
            self.status_callback(message)
        print(message)
    
    def update_progress(self, current, total, filename=""):
        if self.progress_callback:
            self.progress_callback(current, total, filename)
    
    def wait_for_element(self, by, value, clickable=False):
        """Dynamic wait for element - NO HARDCODED SLEEPS."""
        try:
            if clickable:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
            else:
                element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element
        except Exception as e:
            return None
    
    def wait_for_page_load(self):
        """Wait for page to be fully loaded."""
        try:
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            return True
        except:
            return False

    def initialize_browser(self):
        self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.update_status("🚀 STARTING LOGIN PROCESS")
        self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.update_status("⏳ Initializing Chrome browser...")

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Use pre-prepared ChromeDriver path if available, otherwise get it now
        if CHROMEDRIVER_PATH:
            service = Service(CHROMEDRIVER_PATH)
        else:
            service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, WAIT_TIMEOUT)
        self.running = True
        
        # 1. CAPTURE VPN WINDOW HANDLE (The "Sacred" Window)
        self.vpn_window_handle = self.driver.current_window_handle
        self.lrms_window_handle = None
        
        self.update_status("✅ Browser initialized successfully!")
        self.update_status(f"🔒 VPN Window Handle captured: {self.vpn_window_handle}")
    
    def login_saccess(self, username, password):
        try:
            self.update_status("")
            self.update_status("📡 STEP 1: SACCESS LOGIN")
            self.update_status("─────────────────────────")
            self.update_status("🌐 Navigating to saccess.nic.in...")
            self.driver.get("https://saccess.nic.in")
            self.wait_for_page_load()
            self.update_status("✅ SACCESS page loaded")
            
            self.update_status("🔄 Accessing login frame...")
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "base")))
            self.update_status("✅ Login frame accessed")
            
            self.update_status("📝 Entering username: " + username)
            username_field = self.wait_for_element(By.ID, "uname")
            if username_field:
                username_field.clear()
                username_field.send_keys(username)
            
            self.update_status("🔑 Entering password...")
            password_field = self.wait_for_element(By.ID, "password")
            if password_field:
                password_field.clear()
                password_field.send_keys(password)
            
            self.update_status("")
            self.update_status("✅ SACCESS CREDENTIALS ENTERED!")
            self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.update_status("👆 NOW DO THE FOLLOWING IN BROWSER:")
            self.update_status("   1. Click 'Sign-in' button")
            self.update_status("   2. Click 'Send OTP'")
            self.update_status("   3. Enter OTP received on mobile")
            self.update_status("   4. Click 'Sign-in' to complete login")
            self.update_status("   5. Click 'LRMS_Odisha' application")
            self.update_status("   6. Click 'Login' on LRMS page")
            self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.update_status("")
            self.update_status("⏳ Monitoring for LRMS login page...")
            
            return True
            
        except Exception as e:
            self.update_status(f"❌ SACCESS Error: {str(e)}")
            return False
    
    def monitor_for_lrms(self, lrms_username, lrms_password):
        self.lrms_username = lrms_username
        self.lrms_password = lrms_password
        lrms_detected = False
        lrms_handle = None
        
        while self.running:
            try:
                # OPTIMIZATION: Check current window first if we found it
                current_is_valid = False
                if lrms_handle:
                    try:
                        if self.driver.current_window_handle == lrms_handle:
                            if "lrmsodisha.saccess.nic.in" in self.driver.current_url:
                                current_is_valid = True
                    except:
                        lrms_handle = None # Window closed/invalid
                
                # Only scan handles if current one isn't valid
                if not current_is_valid:
                    valid_found = False
                    for handle in self.driver.window_handles:
                        # Skip the VPN window
                        if hasattr(self, 'vpn_window_handle') and handle == self.vpn_window_handle:
                            continue
                            
                        try:
                            self.driver.switch_to.window(handle)
                            if "lrmsodisha.saccess.nic.in" in self.driver.current_url and "Default.aspx" in self.driver.current_url:
                                lrms_handle = handle
                                self.lrms_window_handle = handle  # STORE IT
                                valid_found = True
                                break
                        except:
                            continue
                    
                    if not valid_found:
                        # No valid window found, wait and retry
                        time.sleep(1)
                        continue

                # =================================================
                # FAST DETECTION LOGIC (No window switching below)
                # =================================================
                
                # Check if this is first detection
                if not lrms_detected:
                    self.update_status("")
                    self.update_status("🎯 LRMS LOGIN PAGE DETECTED!")
                    self.update_status("─────────────────────────")
                    lrms_detected = True
                
                # Try to fill Password (INSTANT CHECK)
                try:
                    # Use implicit wait 0 for instant failure if not found
                    self.driver.implicitly_wait(0) 
                    pwd_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                    if pwd_field:
                        # Only type if empty or different
                        current_pass = pwd_field.get_attribute("value")
                        if current_pass != self.lrms_password:
                            pwd_field.clear()
                            pwd_field.send_keys(self.lrms_password)
                            self.update_status("🔑 Password Auto-filled!")
                except:
                    pass
                finally:
                    self.driver.implicitly_wait(WAIT_TIMEOUT) # Restore wait

                # Try to fill Username (INSTANT CHECK)
                if self.lrms_username:
                    try:
                        self.driver.implicitly_wait(0)
                        # Try multiple XPaths for username
                        user_field = None
                        for xpath in ["//*[@id='txtLogin']", "//input[@name='txtLogin']", "//input[contains(@id, 'txtLogin')]"]:
                            try:
                                user_field = self.driver.find_element(By.XPATH, xpath)
                                break
                            except:
                                continue
                        
                        if user_field:
                            current_user = user_field.get_attribute("value")
                            # Only type if empty (don't overwrite if user is typing)
                            if not current_user:
                                user_field.clear()
                                user_field.send_keys(self.lrms_username)
                                self.update_status("👤 Username Auto-filled!")
                            elif current_user == self.lrms_username:
                                # Start checking if we can stop monitoring
                                pass
                    except:
                        pass
                    finally:
                        self.driver.implicitly_wait(WAIT_TIMEOUT)

                # Stop condition: if both fields match our credentials, we can stop or pause
                # But to stay responsive if page reloads, we just loop with delay.
                # Use a slightly longer delay if values are already filled to save CPU.
                time.sleep(1.0)
                
            except Exception as e:
                pass
        
        return False
    
    # ==================== OLR 8(A) EXTRACTION METHODS ====================
    
    def clean_mouza(self, raw_mouza):
        """Clean Mouza value - remove 'Mouza-' prefix and P.S data."""
        if not raw_mouza:
            return ""
        
        mouza = raw_mouza
        
        # Remove "Mouza-" prefix
        if "Mouza-" in mouza:
            mouza = mouza.replace("Mouza-", "")
        
        # Remove P.S data (everything from "P.S" onwards)
        if "P.S" in mouza:
            mouza = mouza.split("P.S")[0]
        
        # Trim whitespace
        mouza = mouza.strip()
        
        return mouza
    
    def click_olr_8a(self):
        """Click on Online OLR 8(A) Case using JavaScript."""
        try:
            self.update_status("📂 Navigating to OLR 8(A)...")
            self.driver.execute_script("__doPostBack('ctl00$Menu1','103')")
            time.sleep(1)  # Brief pause for postback
            self.wait_for_page_load()
            self.update_status("✅ OLR 8(A) page loaded")
            return True
        except Exception as e:
            self.update_status(f"❌ Failed to click OLR 8(A): {str(e)}")
            return False
    
    def click_view_all(self):
        """Click the View All button with dynamic wait."""
        try:
            self.update_status("📋 Clicking View All...")
            view_all_btn = self.wait_for_element(
                By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_btnviewall']", clickable=True
            )
            if view_all_btn:
                view_all_btn.click()
                time.sleep(1)  # Brief pause for postback
                self.wait_for_page_load()
                self.update_status("✅ View All clicked")
                return True
            else:
                self.update_status("❌ View All button not found")
            return False
        except Exception as e:
            self.update_status(f"❌ Failed to click View All: {str(e)}")
            return False
    
    def count_cases_on_page(self):
        """Count the number of cases on current page using robust search."""
        try:
            # Find ALL buttons that look like "Show" buttons in the grid
            # This is robust against ID changes (e.g. ctl02 vs row01)
            # We look for inputs ending in 'btn_Show' inside the grid
            buttons = self.driver.find_elements(By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_gvForward']//input[contains(@id, 'btn_Show')]")
            return len(buttons)
        except:
            return 0
    
    def click_case_view(self, row_num):
        """Click View button for specific case row using direct 1-based XPath indexing (Fast & Robust)."""
        try:
            # Direct XPath to the Nth button - O(1) access, no list scanning
            # This completely avoids StaleElementReferenceException from stale lists
            xpath = f"(//*[@id='ctl00_ContentPlaceHolder1_gvForward']//input[contains(@id, 'btn_Show')])[{row_num}]"
            
            # Retry loop just in case of page refresh/dom update
            for attempt in range(3):
                try:
                    # Wait for THIS specific button to be clickable
                    # Reduced wait time to 5s as we expect it to be there if we counted it
                    btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    
                    # Scroll to it
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.1) # Brief stabilization
                    
                    btn.click()
                    
                    # Wait for page transition
                    time.sleep(0.5) 
                    self.wait_for_page_load()
                    return True
                    
                except StaleElementReferenceException:
                    time.sleep(0.5)
                    continue
                except Exception:
                    time.sleep(0.5)
                    continue
            
            self.update_status(f"❌ Failed to click case {row_num} after retries")
            return False
                
        except Exception as e:
            self.update_status(f"❌ Failed to click case {row_num}: {str(e)}")
            return False
    
    def extract_case_data(self):
        """Extract all data from the case details page."""
        data = {}
        
        try:
            # Wait for specific element (faster than full page load)
            try:
                # Wait max 5s for Applicant Name label (indicates content loaded)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_lblapplicantname']"))
                )
            except:
                # Fallback to older wait if element not found quickly
                self.wait_for_page_load()
            
            # Extract Applicant Name
            try:
                # ... (rest of extraction logic remains same)
                elem = self.driver.find_element(By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_lblapplicantname']")
                data['Applicant Name'] = elem.text.strip() if elem else ""
            except:
                data['Applicant Name'] = ""
            
            # ... (continue with other fields)

            
            # Extract Contact No
            try:
                elem = self.driver.find_element(By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_lblcontactno']")
                data['Contact No'] = elem.text.strip() if elem else ""
            except:
                data['Contact No'] = ""
            
            # Extract OLR Case No
            try:
                elem = self.driver.find_element(By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_lblcaseNo1']")
                data['OLR Case No'] = elem.text.strip() if elem else ""
            except:
                data['OLR Case No'] = ""
            
            # Extract Mouza (with cleaning)
            try:
                elem = self.driver.find_element(By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_pnlstage1']/div[2]/table[1]/tbody/tr[5]/td")
                raw_mouza = elem.text.strip() if elem else ""
                data['Mouza'] = self.clean_mouza(raw_mouza)
            except:
                data['Mouza'] = ""
            
            # Extract Plot Details Table - ALL ROWS
            try:
                table = self.driver.find_element(By.XPATH, "//*[@id='ctl00_ContentPlaceHolder1_gvplotDetails']")
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                if len(rows) >= 2:
                    # Get headers from first row
                    headers = rows[0].find_elements(By.TAG_NAME, "th")
                    header_texts = [h.text.strip() for h in headers]
                    
                    # Store all plot rows
                    plot_rows = []
                    
                    # Get data from ALL data rows (not just first!)
                    for row in rows[1:]:  # Skip header row
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if cells:
                            cell_texts = [c.text.strip() for c in cells]
                            plot_data = {}
                            for i, header in enumerate(header_texts):
                                if i < len(cell_texts) and header:
                                    plot_data[header] = cell_texts[i]
                            if plot_data:
                                plot_rows.append(plot_data)
                    
                    # Store plot rows list in data
                    data['_plot_rows'] = plot_rows
                    
                    # Also set first row data for backward compatibility
                    if plot_rows:
                        for key, val in plot_rows[0].items():
                            data[key] = val
            except:
                pass
            
            return data
            
        except Exception as e:
            self.update_status(f"⚠️ Error extracting data: {str(e)}")
            return data
    
    def count_total_pages(self):
        """Count total number of pages available using dynamic detection."""
        pages = 1
        try:
            # Wait a moment for pagination to render
            time.sleep(0.5)
            
            # Try multiple XPaths for pagination
            pagination_xpaths = [
                "//*[@id='ctl00_ContentPlaceHolder1_gvForward']//table//a",
                "//*[@id='ctl00_ContentPlaceHolder1_gvForward']//tr[last()]//a",
                "//table[@id='ctl00_ContentPlaceHolder1_gvForward']//a[contains(@href, 'Page')]",
                "//td//a[contains(@href, 'Page$')]",
            ]
            
            for xpath in pagination_xpaths:
                try:
                    page_links = self.driver.find_elements(By.XPATH, xpath)
                    if page_links:
                        for link in page_links:
                            try:
                                text = link.text.strip()
                                if text.isdigit():
                                    page_num = int(text)
                                    if page_num > pages:
                                        pages = page_num
                            except:
                                continue
                        if pages > 1:
                            break  # Found pagination, stop trying
                except:
                    continue
        except:
            pass
        
        return pages
    
    def go_to_page(self, page_num):
        """Navigate to a specific page with dynamic detection."""
        try:
            if page_num == 1:
                return True
            
            # Find the page link dynamically
            pagination_xpath = f"//*[@id='ctl00_ContentPlaceHolder1_gvForward']//table//a[text()='{page_num}']"
            page_link = self.wait_for_element(By.XPATH, pagination_xpath, clickable=True)
            
            if page_link:
                page_link.click()
                time.sleep(1)  # Brief pause for postback
                self.wait_for_page_load()
                self.update_status(f"   ✅ Navigated to Page {page_num}")
                return True
            else:
                self.update_status(f"⚠️ Page {page_num} link not found")
            return False
        except Exception as e:
            self.update_status(f"⚠️ Failed to go to page {page_num}: {str(e)}")
            return False
    
    def extract_olr_8a_cases(self, excel_filepath, start_page=1, is_resume=False):
        """Main extraction function for OLR 8(A) cases with incremental Excel save."""
        self.cases_extracted = 0
        self.stop_extraction = False  # Reset stop flag
        start_time = time.time()
        error_count = 0
        
        try:
            current_ts = datetime.now().strftime("%H:%M:%S")
            self.update_status("")
            self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.update_status("🚀 STARTING OLR 8(A) DATA EXTRACTION")
            self.update_status(f"⏰ Started at: {current_ts}")
            self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            if is_resume:
                self.update_status(f"📂 Resuming to: {os.path.basename(excel_filepath)}")
            else:
                self.update_status(f"📂 New file: {os.path.basename(excel_filepath)}")
            
            self.update_status(f"📄 Starting from Page: {start_page}")
            
            # Initialize Excel manager
            self.excel_manager = ExcelManager(excel_filepath)
            
            # Switch to LRMS window
            self.update_status("🔍 Looking for LRMS window...")
            lrms_found = False
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                current_url = self.driver.current_url
                self.update_status(f"   Checking: {current_url[:50]}...")
                if "lrmsodisha.saccess.nic.in" in current_url:
                    self.update_status(f"✅ Found LRMS window!")
                    lrms_found = True
                    break
            
            if not lrms_found:
                self.update_status("❌ LRMS window not found! Please make sure you are logged into LRMS.")
                return False
            
            # Click OLR 8(A)
            if not self.click_olr_8a():
                return False
            
            # Click View All
            if not self.click_view_all():
                return False
            
            # Count total pages
            total_pages = self.count_total_pages()
            self.update_status(f"📑 Total pages available: {total_pages}")
            
            if start_page > total_pages:
                self.update_status(f"❌ Start page {start_page} exceeds total pages {total_pages}")
                return False
            
            # Navigate to start page if needed
            if start_page > 1:
                self.update_status(f"📑 Navigating to Page {start_page}...")
                if not self.go_to_page(start_page):
                    return False
            
            # Estimate total cases
            first_page_count = self.count_cases_on_page()
            remaining_pages = total_pages - start_page + 1
            estimated_total = first_page_count + (remaining_pages - 1) * 20
            self.update_status(f"📊 Estimated remaining cases: ~{estimated_total}")
            
            # Process pages starting from start_page
            for current_page in range(start_page, total_pages + 1):
                # Check if stop requested
                if self.stop_extraction:
                    self.update_status("")
                    self.update_status("🛑 EXTRACTION STOPPED BY USER")
                    break
                
                self.update_status("")
                self.update_status(f"📑 PROCESSING PAGE {current_page}/{total_pages}")
                self.update_status("─────────────────────────────────")
                
                # If not on the first iteration, navigate to page
                if current_page > start_page:
                    if not self.click_olr_8a():
                        continue
                    if not self.click_view_all():
                        continue
                    if not self.go_to_page(current_page):
                        continue
                
                # Count cases on this page
                cases_on_page = self.count_cases_on_page()
                self.update_status(f"   Found {cases_on_page} cases on this page")
                
                # Process each case on this page
                for case_idx in range(1, cases_on_page + 1):
                    # Check if stop requested
                    if self.stop_extraction:
                        break
                    
                    self.cases_extracted += 1
                    current_ts = datetime.now().strftime("%H:%M:%S")
                    self.update_status("")
                    self.update_status(f"[{current_ts}] 📄 Case {self.cases_extracted} (Page {current_page}, Row {case_idx})")
                    
                    # Click View for this case
                    if not self.click_case_view(case_idx):
                        self.update_status("   ⚠️ Skipping - could not open case")
                        error_count += 1
                        continue
                    
                    # Extract data
                    case_data = self.extract_case_data()
                    
                    if case_data:
                        # Handle multiple plots per case
                        plots = case_data.get('_plot_rows', [])
                        
                        if plots and len(plots) > 0:
                            saved_count = 0
                            for i, plot in enumerate(plots):
                                # Create a combined row for this plot
                                row_data = case_data.copy()
                                # Remove the list itself from this row copy
                                if '_plot_rows' in row_data:
                                    del row_data['_plot_rows']
                                
                                # Merge plot specific data
                                row_data.update(plot)
                                
                                # Write this specific plot row
                                if self.excel_manager.write_row(row_data):
                                    saved_count += 1
                            
                            if saved_count > 0:
                                self.update_status(f"   ✅ {case_data.get('Applicant Name', 'N/A')[:30]}")
                            else:
                                self.update_status("   ⚠️ Failed to save to Excel")
                                error_count += 1
                        else:
                            # Fallback if no plots list found
                            if self.excel_manager.write_row(case_data):
                                self.update_status(f"   ✅ {case_data.get('Applicant Name', 'N/A')[:30]}")
                            else:
                                self.update_status("   ⚠️ Failed to save to Excel")
                                error_count += 1
                    
                    # BATCH SAVE OPTIMIZATION
                    # Save into file only every 10 cases
                    if self.cases_extracted % 10 == 0:
                        self.update_status(f"   💾 Batch saving... ({datetime.now().strftime('%H:%M:%S')})")
                        self.excel_manager.save()
                    
                    # Update progress
                    self.update_progress(self.cases_extracted, estimated_total, os.path.basename(excel_filepath))
                    
                    # Go back to list for next case
                    if not self.click_olr_8a():
                        error_count += 1
                        continue
                    if not self.click_view_all():
                        continue
                    
                    # Navigate back to current page
                    if current_page > 1:
                        self.go_to_page(current_page)
                
                # Check if stopped inside inner loop
                if self.stop_extraction:
                    break
            
            # Final save at the end of extraction loop
            if self.excel_manager:
                self.excel_manager.save()
                self.excel_manager.close()
            
            end_time = time.time()
            elapsed_seconds = int(end_time - start_time)
            elapsed_str = str(datetime.fromtimestamp(end_time) - datetime.fromtimestamp(start_time)).split('.')[0] # HH:MM:SS

            self.update_status("")
            self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            if self.stop_extraction:
                self.update_status("🛑 EXTRACTION STOPPED BY USER")
            else:
                self.update_status("✅ EXTRACTION COMPLETED SUCCESSFULLY")
            
            self.update_status("📊 FINAL SUMMARY:")
            self.update_status(f"   • Total Cases  : {self.cases_extracted}")
            self.update_status(f"   • Errors       : {error_count}")
            self.update_status(f"   • Time Taken   : {elapsed_str}")
            self.update_status(f"   • Saved to     : {excel_filepath}")
            self.update_status("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # Auto-open file
            try:
                os.startfile(excel_filepath)
                self.update_status("🚀 Auto-opened Excel file")
            except Exception as e:
                self.update_status(f"⚠️ Could not auto-open file: {e}")
            
            return True
            
        except Exception as e:
            self.update_status(f"❌ Extraction error: {str(e)}")
            self.update_status(f"💾 {self.cases_extracted} cases were saved before error.")
            return False
            if self.excel_manager:
                self.excel_manager.close()
            return False
    
    def stop_monitoring(self):
        self.running = False
    
    def close(self):
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


class NeonButton(ctk.CTkFrame):
    """Custom neon glow button with hover effects."""
    
    def __init__(self, master, text, command=None, glow_color="#00d4ff", width=220, **kwargs):
        super().__init__(master, fg_color="transparent")
        
        self.glow_color = glow_color
        self.command = command
        self.is_disabled = False
        
        self.button = ctk.CTkButton(
            self,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="transparent",
            hover_color=self._adjust_brightness(glow_color, 0.3),
            border_width=2,
            border_color=glow_color,
            text_color=glow_color,
            corner_radius=25,
            height=45,
            width=width,
            command=self._on_click
        )
        self.button.pack(padx=3, pady=3)
        
        self.button.bind("<Enter>", self._on_enter)
        self.button.bind("<Leave>", self._on_leave)
    
    def _adjust_brightness(self, color, factor):
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(min(255, int(c * (1 + factor))) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)
    
    def _on_enter(self, event):
        if not self.is_disabled:
            self.button.configure(
                fg_color=self._adjust_brightness(self.glow_color, -0.5),
                text_color="#ffffff"
            )
    
    def _on_leave(self, event):
        if not self.is_disabled:
            self.button.configure(
                fg_color="transparent",
                text_color=self.glow_color
            )
    
    def _on_click(self):
        if self.command and not self.is_disabled:
            self.command()
    
    def configure(self, **kwargs):
        if "state" in kwargs:
            if kwargs["state"] == "disabled":
                self.is_disabled = True
                self.button.configure(state="disabled", border_color="#555555", text_color="#555555")
            else:
                self.is_disabled = False
                self.button.configure(state="normal", border_color=self.glow_color, text_color=self.glow_color)


class LRMSApp(ctk.CTk):
    """Main application window with tabbed premium design."""
    
    def __init__(self):
        super().__init__()
        
        self.title("LRMS - Land Records Management System")
        self.geometry("950x800")
        self.minsize(900, 750)
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.cred_manager = CredentialManager()
        self.automation = None
        self.selected_excel_path = ""

        # Setup tab data
        self.all_cases = []      # All cases from Excel
        self.forward_cases = []  # List of cases to forward (FLAT list for Valuation)
        self.reject_cases = []   # List of cases to reject (FLAT list)
        self.forward_cases_grouped = [] # UNIQUE cases for UI & PDF Mapping
        self.reject_cases_grouped = []  # UNIQUE reject cases for UI
        
        self.pdf_mapping = {}    # Case No -> PDF path mapping
        self.pdf_dropdowns_fwd = {}   # Widgets for Fwd
        self.pdf_dropdowns_rej = {}   # Widgets for Rej
        self.fwd_case_edits = {}  # Store per-case overrides (Q4, Q5, Purpose)

        self.create_ui()
        self.load_saved_credentials()

        # Send telemetry install event (first run only)
        if TELEMETRY_AVAILABLE:
            try:
                send_install_event()
            except Exception as e:
                print(f"Telemetry error: {e}")

        # Prepare ChromeDriver in background (optimization)
        threading.Thread(target=prepare_chromedriver_background, daemon=True).start()

    def create_ui(self):
        """Create the tabbed premium user interface."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # ==================== HEADER ====================
        self.header_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0, height=80)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_propagate(False)
        
        # Logo
        self.logo_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, sticky="w", padx=10)
        
        self.logo_icon = ctk.CTkLabel(self.logo_frame, text="🏛️", font=ctk.CTkFont(size=32))
        self.logo_icon.pack(side="left", padx=(0, 8))
        
        self.title_frame = ctk.CTkFrame(self.logo_frame, fg_color="transparent")
        self.title_frame.pack(side="left")
        
        self.title_label = ctk.CTkLabel(
            self.title_frame, text="LRMS",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_frame, text="Land Records Management System",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_secondary"]
        )
        self.subtitle_label.pack(anchor="w")
        
        # Designer Credit
        self.designed_by = ctk.CTkLabel(
            self.header_frame,
            text="D E S I G N E D   B Y   S U S H A N T",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["accent_cyan"]
        )
        self.designed_by.grid(row=0, column=1, pady=15)
        
        # ==================== TABVIEW ====================
        self.tabview = ctk.CTkTabview(
            self, fg_color=COLORS["bg_card"],
            segmented_button_fg_color=COLORS["bg_dark"],
            segmented_button_selected_color=COLORS["accent_cyan"],
            segmented_button_unselected_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"]
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        # Create tabs (Status Log will be added last, after Forwarding)
        self.tab_login = self.tabview.add("🔐 Login")
        self.tab_extract = self.tabview.add("📥 Extraction")
        self.tab_setup = self.tabview.add("⚙️ Setup")
        self.tab_valuation = self.tabview.add("🔍 Valuation")

        # Configure tab grids
        self.tab_login.grid_columnconfigure((0, 1), weight=1)
        self.tab_extract.grid_columnconfigure(0, weight=1)
        self.tab_setup.grid_columnconfigure(0, weight=1)
        self.tab_valuation.grid_columnconfigure(0, weight=1)
        
        # ==================== LOGIN TAB ====================
        self.create_login_tab()
        
        # ==================== EXTRACTION TAB ====================
        self.create_extraction_tab()
        
        # ==================== SETUP TAB ====================
        self.create_setup_tab()
        
        # ==================== VALUATION TAB ====================
        self.create_valuation_tab()

        # ==================== FORWARDING TAB ====================
        self.tab_forwarding = self.tabview.add("📤 Forwarding")
        self.tab_forwarding.grid_columnconfigure(0, weight=1)
        self.create_forwarding_tab()

        # ==================== STATUS LOG TAB (RIGHTMOST) ====================
        self.tab_log = self.tabview.add("📋 Status Log")
        self.tab_log.grid_columnconfigure(0, weight=1)
        self.tab_log.grid_rowconfigure(0, weight=1)
        self.create_log_tab()
        
        # ==================== FOOTER ====================
        self.footer_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0, height=30)
        self.footer_frame.grid(row=2, column=0, sticky="ew")
        
        self.footer_label = ctk.CTkLabel(
            self.footer_frame,
            text="LRMS Automation Tool v3.0  |  © 2024 Sushant",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_secondary"]
        )
        self.footer_label.pack(pady=6)
    
    def create_login_tab(self):
        """Create the Login tab content."""
        # Container frame
        login_container = ctk.CTkFrame(self.tab_login, fg_color="transparent")
        login_container.grid(row=0, column=0, columnspan=2, pady=20)
        
        # SACCESS Card
        self.saccess_frame = ctk.CTkFrame(login_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        self.saccess_frame.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(self.saccess_frame, text="🔐 SACCESS Login", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        ctk.CTkLabel(self.saccess_frame, text="Username/Email:", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(padx=20, anchor="w")
        self.saccess_user_var = StringVar()
        self.saccess_user_combo = ctk.CTkComboBox(self.saccess_frame, variable=self.saccess_user_var, values=[], width=250, height=35, fg_color=COLORS["bg_card"], command=self.on_saccess_user_select)
        self.saccess_user_combo.pack(padx=20, pady=(3, 10))
        
        ctk.CTkLabel(self.saccess_frame, text="Password:", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(padx=20, anchor="w")
        self.saccess_pass_entry = ctk.CTkEntry(self.saccess_frame, show="•", width=250, height=35, fg_color=COLORS["bg_card"], placeholder_text="Enter password")
        self.saccess_pass_entry.pack(padx=20, pady=(3, 10))
        
        self.saccess_save_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.saccess_frame, text="Save credentials", variable=self.saccess_save_var, fg_color=COLORS["accent_cyan"]).pack(pady=5)
        
        ctk.CTkButton(self.saccess_frame, text="🗑️ Delete", width=100, height=28, fg_color="transparent", border_width=1, border_color=COLORS["border_subtle"], command=self.delete_saccess_cred).pack(pady=(3, 15))
        
        # LRMS Card
        self.lrms_frame = ctk.CTkFrame(login_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        self.lrms_frame.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(self.lrms_frame, text="🏠 LRMS Login", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        ctk.CTkLabel(self.lrms_frame, text="Username:", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(padx=20, anchor="w")
        self.lrms_user_var = StringVar()
        self.lrms_user_combo = ctk.CTkComboBox(self.lrms_frame, variable=self.lrms_user_var, values=[], width=250, height=35, fg_color=COLORS["bg_card"], command=self.on_lrms_user_select)
        self.lrms_user_combo.pack(padx=20, pady=(3, 10))
        
        ctk.CTkLabel(self.lrms_frame, text="Password:", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(padx=20, anchor="w")
        self.lrms_pass_entry = ctk.CTkEntry(self.lrms_frame, show="•", width=250, height=35, fg_color=COLORS["bg_card"], placeholder_text="Enter password")
        self.lrms_pass_entry.pack(padx=20, pady=(3, 10))
        
        self.lrms_save_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.lrms_frame, text="Save credentials", variable=self.lrms_save_var, fg_color=COLORS["accent_green"]).pack(pady=5)
        
        ctk.CTkButton(self.lrms_frame, text="🗑️ Delete", width=100, height=28, fg_color="transparent", border_width=1, border_color=COLORS["border_subtle"], command=self.delete_lrms_cred).pack(pady=(3, 15))
        
        # Login Button
        self.login_btn = NeonButton(self.tab_login, text="🚀  Start Login Process", command=self.start_login, glow_color=COLORS["accent_cyan"], width=250)
        self.login_btn.grid(row=1, column=0, columnspan=2, pady=20)
    
    def create_extraction_tab(self):
        """Create the Extraction tab content."""
        # Main container
        extract_container = ctk.CTkFrame(self.tab_extract, fg_color="transparent")
        extract_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== OUTPUT FILE SECTION =====
        file_frame = ctk.CTkFrame(extract_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        file_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(file_frame, text="📁 OUTPUT FILE", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))
        
        self.file_option = StringVar(value="new")
        
        # New file option
        new_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        new_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkRadioButton(new_frame, text="Create New File (auto-named: DDMMYY_HHMMSS.xlsx)", variable=self.file_option, value="new", fg_color=COLORS["accent_cyan"]).pack(anchor="w")
        
        # Resume option
        resume_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        resume_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkRadioButton(resume_frame, text="Resume to Existing:", variable=self.file_option, value="resume", fg_color=COLORS["accent_cyan"]).pack(side="left")
        
        self.excel_path_label = ctk.CTkLabel(resume_frame, text="No file selected", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.excel_path_label.pack(side="left", padx=10)
        
        ctk.CTkButton(resume_frame, text="Browse...", width=80, height=28, command=self.browse_excel).pack(side="left", padx=5)
        
        # ===== PAGE SELECTION SECTION =====
        page_frame = ctk.CTkFrame(extract_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        page_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(page_frame, text="📄 PAGE SELECTION", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))
        
        self.page_option = StringVar(value="all")
        
        # All pages option
        all_frame = ctk.CTkFrame(page_frame, fg_color="transparent")
        all_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkRadioButton(all_frame, text="Extract All Pages (from Page 1)", variable=self.page_option, value="all", fg_color=COLORS["accent_orange"]).pack(anchor="w")
        
        # Start from page option
        start_frame = ctk.CTkFrame(page_frame, fg_color="transparent")
        start_frame.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkRadioButton(start_frame, text="Start from Page:", variable=self.page_option, value="from", fg_color=COLORS["accent_orange"]).pack(side="left")
        
        self.start_page_entry = ctk.CTkEntry(start_frame, width=60, height=30, fg_color=COLORS["bg_card"])
        self.start_page_entry.pack(side="left", padx=10)
        self.start_page_entry.insert(0, "1")
        
        # ===== BUTTONS SECTION =====
        buttons_frame = ctk.CTkFrame(extract_container, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        self.extract_btn = NeonButton(buttons_frame, text="📥  Start Extraction", command=self.start_extraction, glow_color=COLORS["accent_orange"], width=220)
        self.extract_btn.pack(side="left", padx=10)
        
        self.stop_btn = NeonButton(buttons_frame, text="🛑  Stop Extraction", command=self.stop_extraction, glow_color="#ff4444", width=180)
        self.stop_btn.pack(side="left", padx=10)
        self.stop_btn.configure(state="disabled")
        
        # ===== PROGRESS SECTION =====
        progress_frame = ctk.CTkFrame(extract_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        progress_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(progress_frame, text="📊 PROGRESS", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready", font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"])
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=500, height=20, progress_color=COLORS["accent_orange"], fg_color=COLORS["bg_card"])
        self.progress_bar.pack(pady=(5, 10))
        self.progress_bar.set(0)
        
        self.file_label = ctk.CTkLabel(progress_frame, text="File: None", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.file_label.pack(pady=(0, 15))
    
    def create_setup_tab(self):
        """Create the Setup tab content."""
        # Main scrollable container
        setup_container = ctk.CTkScrollableFrame(self.tab_setup, fg_color="transparent")
        setup_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== STEP 1: EXCEL UPLOAD =====
        step1_frame = ctk.CTkFrame(setup_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        step1_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(step1_frame, text="📁 STEP 1: UPLOAD EXCEL FILE", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(step1_frame, text="Excel should have 'Action' column (last column): F=Forward, R=Reject", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(pady=(0, 10))
        
        upload_frame = ctk.CTkFrame(step1_frame, fg_color="transparent")
        upload_frame.pack(pady=10)
        
        self.fwd_excel_btn = ctk.CTkButton(upload_frame, text="📂 Browse Excel...", width=150, command=self.browse_forward_excel)
        self.fwd_excel_btn.pack(side="left", padx=5)
        
        self.fwd_excel_label = ctk.CTkLabel(upload_frame, text="No file selected", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.fwd_excel_label.pack(side="left", padx=10)
        
        self.detect_btn = ctk.CTkButton(step1_frame, text="🔍 Detect Cases", width=150, fg_color=COLORS["accent_cyan"], command=self.detect_cases)
        self.detect_btn.pack(pady=(5, 15))
        
        # ===== DETECTED CASES DISPLAY =====
        cases_frame = ctk.CTkFrame(setup_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        cases_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(cases_frame, text="📊 DETECTED CASES", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))
        
        # Forward cases section
        fwd_header = ctk.CTkFrame(cases_frame, fg_color="transparent")
        fwd_header.pack(fill="x", padx=20)
        ctk.CTkLabel(fwd_header, text="🟢 FORWARD CASES:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["accent_green"]).pack(side="left")
        self.fwd_count_label = ctk.CTkLabel(fwd_header, text="0 cases", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.fwd_count_label.pack(side="right")
        
        self.fwd_cases_text = ctk.CTkTextbox(cases_frame, height=100, font=ctk.CTkFont(family="Consolas", size=11), fg_color=COLORS["bg_card"])
        self.fwd_cases_text.pack(fill="x", padx=20, pady=5)
        
        # Reject cases section
        rej_header = ctk.CTkFrame(cases_frame, fg_color="transparent")
        rej_header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(rej_header, text="🔴 REJECT CASES:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ff6b6b").pack(side="left")
        self.rej_count_label = ctk.CTkLabel(rej_header, text="0 cases", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.rej_count_label.pack(side="right")
        
        self.setup_rej_cases_text = ctk.CTkTextbox(cases_frame, height=100, font=ctk.CTkFont(family="Consolas", size=11), fg_color=COLORS["bg_card"])
        self.setup_rej_cases_text.pack(fill="x", padx=20, pady=(5, 15))
        
        # ===== STEP 2: PDF UPLOAD (FORWARD) =====
        step2_frame = ctk.CTkFrame(setup_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        step2_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(step2_frame, text="📄 STEP 2: UPLOAD PDFs (FORWARD CASES)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(step2_frame, text="Upload and map PDFs for Forward cases.", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(pady=(0, 10))
        
        pdf_btn_frame = ctk.CTkFrame(step2_frame, fg_color="transparent")
        pdf_btn_frame.pack(pady=10)
        
        self.pdf_upload_btn = ctk.CTkButton(pdf_btn_frame, text="📂 Browse Forward PDFs...", width=180, command=self.browse_pdfs_forward)
        self.pdf_upload_btn.pack(side="left", padx=5)
        
        self.pdf_count_label_fwd = ctk.CTkLabel(pdf_btn_frame, text="0 PDFs selected", font=ctk.CTkFont(size=11), text_color=COLORS["accent_green"])
        self.pdf_count_label_fwd.pack(side="left", padx=10)
        
        # Mapping Section Forward
        ctk.CTkLabel(step2_frame, text="📎 MAPPING (FORWARD):", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
        self.mapping_scroll_frame_fwd = ctk.CTkScrollableFrame(step2_frame, height=180, fg_color=COLORS["bg_card"])
        self.mapping_scroll_frame_fwd.pack(fill="x", padx=20, pady=(0, 15))
        
        # ===== STEP 3: PDF UPLOAD (REJECT) =====
        step3_frame = ctk.CTkFrame(setup_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        step3_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(step3_frame, text="🚫 STEP 3: UPLOAD PDFs (REJECT CASES)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ff6b6b").pack(pady=(15, 5))
        ctk.CTkLabel(step3_frame, text="Upload and map PDFs for Reject cases.", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(pady=(0, 10))
        
        pdf_rej_btn_frame = ctk.CTkFrame(step3_frame, fg_color="transparent")
        pdf_rej_btn_frame.pack(pady=10)
        
        self.pdf_upload_btn_rej = ctk.CTkButton(pdf_rej_btn_frame, text="📂 Browse Reject PDFs...", width=180, fg_color="#ff4444", hover_color="#cc3333", command=self.browse_pdfs_reject)
        self.pdf_upload_btn_rej.pack(side="left", padx=5)
        
        self.pdf_count_label_rej = ctk.CTkLabel(pdf_rej_btn_frame, text="0 PDFs selected", font=ctk.CTkFont(size=11), text_color="#ff6b6b")
        self.pdf_count_label_rej.pack(side="left", padx=10)
        
        # Mapping Section Reject
        ctk.CTkLabel(step3_frame, text="📎 MAPPING (REJECT):", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
        self.mapping_scroll_frame_rej = ctk.CTkScrollableFrame(step3_frame, height=180, fg_color=COLORS["bg_card"])
        self.mapping_scroll_frame_rej.pack(fill="x", padx=20, pady=(0, 15))
        
        # Available PDFs (Common Log)
        ctk.CTkLabel(setup_container, text="📋 Processed PDFs Log:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(15, 5), padx=20, anchor="w")
        self.pdf_list_text = ctk.CTkTextbox(setup_container, height=80, font=ctk.CTkFont(family="Consolas", size=10), fg_color=COLORS["bg_card"])
        self.pdf_list_text.pack(fill="x", padx=20, pady=(0, 10))
        
        # Store mapping dropdowns
        self.available_pdfs_fwd = []  # List of PDF paths for Forward
        self.available_pdfs_rej = []  # List of PDF paths for Reject
        
        # ===== CONFIRM BUTTON =====
        self.confirm_btn = NeonButton(setup_container, text="✅ Confirm & Proceed", command=self.confirm_forward_reject, glow_color=COLORS["accent_green"], width=220)
        self.confirm_btn.pack(pady=20)
    
    def create_valuation_tab(self):
        """Create the Valuation Check tab content."""
        # Main scrollable container
        valuation_container = ctk.CTkScrollableFrame(self.tab_valuation, fg_color="transparent")
        valuation_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== LOAD DATA BUTTON (TOP) =====
        load_frame = ctk.CTkFrame(valuation_container, corner_radius=12, fg_color=COLORS["accent_cyan"], border_width=0)
        load_frame.pack(fill="x", pady=(0, 15))
        
        self.load_valuation_btn = ctk.CTkButton(load_frame, text="🔄 LOAD DATA FROM SETUP TAB", width=400, height=40, font=ctk.CTkFont(size=14, weight="bold"), fg_color="transparent", hover_color=COLORS["accent_cyan_dark"], command=self.load_valuation_data)
        self.load_valuation_btn.pack(pady=10)
        
        # ===== STEP 1: OPEN WEBSITE & SELECT =====
        location_frame = ctk.CTkFrame(valuation_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        location_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(location_frame, text="📍 STEP 1: SELECT DISTRICT & RO FROM WEBSITE", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(location_frame, text="Click button to open IGR website → Select District & RO from dropdowns → Click Detect", font=ctk.CTkFont(size=10), text_color=COLORS["text_secondary"]).pack(pady=(0, 10))
        
        # Browser buttons
        browser_btn_frame = ctk.CTkFrame(location_frame, fg_color="transparent")
        browser_btn_frame.pack(pady=10)
        
        self.open_igr_btn = ctk.CTkButton(browser_btn_frame, text="🌐 Open IGR Website", width=180, fg_color="#1E90FF", hover_color="#1873CC", command=self.open_igr_website)
        self.open_igr_btn.pack(side="left", padx=10)
        
        self.detect_selection_btn = ctk.CTkButton(browser_btn_frame, text="🔍 Detect Selection", width=150, fg_color="#32CD32", hover_color="#28A428", command=self.detect_district_ro_selection)
        self.detect_selection_btn.pack(side="left", padx=10)
        
        self.pull_villages_btn = ctk.CTkButton(browser_btn_frame, text="📥 Pull Villages", width=150, fg_color="#FF8C00", hover_color="#CC7000", command=self.pull_villages)
        self.pull_villages_btn.pack(side="left", padx=10)
        
        # Detected values display
        detected_frame = ctk.CTkFrame(location_frame, fg_color=COLORS["bg_card"])
        detected_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        ctk.CTkLabel(detected_frame, text="Detected:", font=ctk.CTkFont(size=11)).pack(side="left", padx=10, pady=10)
        self.district_label = ctk.CTkLabel(detected_frame, text="District: (not selected)", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.district_label.pack(side="left", padx=10)
        self.ro_label = ctk.CTkLabel(detected_frame, text="RO: (not selected)", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.ro_label.pack(side="left", padx=10)
        self.villages_count_label = ctk.CTkLabel(detected_frame, text="Villages: 0", font=ctk.CTkFont(size=11), text_color=COLORS["accent_cyan"])
        self.villages_count_label.pack(side="left", padx=10)
        
        # Hidden entries to store values
        self.detected_district = ""
        self.detected_ro = ""
        
        # ===== STEP 2: VILLAGE MAPPING =====
        mapping_frame = ctk.CTkFrame(valuation_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        mapping_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(mapping_frame, text="🗺️ STEP 2: MAP ODIA MOUZA → ENGLISH VILLAGE", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(mapping_frame, text="Match Odia Mouza names from Excel with English Village names from website", font=ctk.CTkFont(size=10), text_color=COLORS["text_secondary"]).pack(pady=(0, 10))
        
        # Mapping status
        self.mapping_status = ctk.CTkLabel(mapping_frame, text="📊 Villages: 0 loaded | Mouza: 0 to map", font=ctk.CTkFont(size=11), text_color=COLORS["accent_orange"])
        self.mapping_status.pack(pady=5)
        
        # Mapping scrollable area
        self.village_mapping_frame = ctk.CTkScrollableFrame(mapping_frame, height=150, fg_color=COLORS["bg_card"])
        self.village_mapping_frame.pack(fill="x", padx=15, pady=10)
        
        # Confirm mapping button
        self.confirm_mapping_btn = ctk.CTkButton(mapping_frame, text="✅ Confirm Village Mapping", width=200, fg_color="#32CD32", hover_color="#28A428", command=self.confirm_village_mapping)
        self.confirm_mapping_btn.pack(pady=(5, 15))
        
        # ===== CASE DETAILS TABLE =====
        table_frame = ctk.CTkFrame(valuation_container, corner_radius=12, fg_color=COLORS["bg_dark"], border_width=1, border_color=COLORS["border_subtle"])
        table_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(table_frame, text="📋 FORWARD CASE DETAILS", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        
        # Summary
        self.valuation_summary = ctk.CTkLabel(table_frame, text="📊 Forward: 0 | Reject: 0", font=ctk.CTkFont(size=11), text_color=COLORS["accent_cyan"])
        self.valuation_summary.pack(pady=5)
        
        # Table header - with Area column
        header_row = ctk.CTkFrame(table_frame, fg_color=COLORS["bg_card"])
        header_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(header_row, text="Case No", width=80, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Mouza", width=100, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Village", width=100, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Plot", width=80, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Val Plot", width=60, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Area", width=50, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Benchmark", width=80, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Conv Fee", width=70, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        ctk.CTkLabel(header_row, text="Total", width=70, font=ctk.CTkFont(size=10, weight="bold"), anchor="w").pack(side="left", padx=3)
        
        # Scrollable table content
        self.valuation_table = ctk.CTkScrollableFrame(table_frame, height=200, fg_color=COLORS["bg_card"])
        self.valuation_table.pack(fill="x", padx=15, pady=(0, 15))
        
        # ===== ACTION BUTTONS =====
        btn_frame = ctk.CTkFrame(valuation_container, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        
        # Action Buttons
        self.valuation_check_btn = NeonButton(btn_frame, text="🔍 Start Valuation Check", command=self.go_valuation_check, glow_color=COLORS["accent_orange"], width=200)
        self.valuation_check_btn.pack(side="left", padx=10)
        
        self.retry_btn = ctk.CTkButton(btn_frame, text="🔄 Retry Failures", width=120, fg_color="#FF4500", hover_color="#CC3700", command=self.go_retry_failures)
        self.retry_btn.pack(side="left", padx=10)
        
        self.resume_valuation_btn = ctk.CTkButton(btn_frame, text="▶️ Resume", width=120, fg_color="#666666", command=self.resume_valuation)
        self.resume_valuation_btn.pack(side="left", padx=10)
        
        # Force Refresh Checkbox
        self.refresh_cache_var = ctk.BooleanVar(value=False)
        self.refresh_cache_chk = ctk.CTkCheckBox(btn_frame, text="Force Refresh Cache", variable=self.refresh_cache_var, font=ctk.CTkFont(size=12))
        self.refresh_cache_chk.pack(side="left", padx=10)

        # PROCEED BUTTON
        self.proceed_btn = ctk.CTkButton(btn_frame, text="➡️ PROCEED TO FORWARDING", command=self.proceed_to_forwarding, fg_color=COLORS["accent_blue"], font=ctk.CTkFont(weight="bold"))
        self.proceed_btn.pack(side="left", padx=10)
        
        # Store village data
        self.villages_list = []  # List of English village names from website
        self.village_mappings = {}  # {odia_mouza: english_village}
        self.village_dropdowns = {}  # UI dropdowns for mapping
        self.igr_driver = None  # Browser for IGR website


    def create_forwarding_tab(self):
        """Create the Unified Forwarding & Rejection Dashboard."""
        self.forwarding_tab = self.tabview.tab("📤 Forwarding")
        
        # Grid: Left (List) vs Right (Controls)
        self.forwarding_tab.grid_columnconfigure(0, weight=3) # List area
        self.forwarding_tab.grid_columnconfigure(1, weight=2) # Details/Control area
        self.forwarding_tab.grid_rowconfigure(0, weight=1)
        
        # ==================== LEFT: UNIFIED CASE DASHBOARD ====================
        dashboard_frame = ctk.CTkFrame(self.forwarding_tab, fg_color="transparent")
        dashboard_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 1. Top Loader
        loader_frame = ctk.CTkFrame(dashboard_frame, fg_color=COLORS["bg_card"], height=50)
        loader_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(loader_frame, text="📁 Source Data:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
        
        self.fwd_excel_label = ctk.CTkLabel(loader_frame, text="No Excel Loaded", text_color="gray")
        self.fwd_excel_label.pack(side="left", padx=5)
        
        ctk.CTkButton(loader_frame, text="📂 Load Valuation Excel", width=120, command=self.browse_forward_excel, fg_color=COLORS["accent_blue"]).pack(side="right", padx=10, pady=5)
        
        # 2. Case List (Forward & Reject)
        # Using a TabView inside for Forward / Reject List separation (Cleaner than side-by-side for "Huge Box")
        # User said "Load Forward Cases Rejection Cases"
        
        self.dash_tabs = ctk.CTkTabview(dashboard_frame, fg_color=COLORS["bg_card"])
        self.dash_tabs.pack(fill="both", expand=True)
        
        self.tab_fwd_list = self.dash_tabs.add("✅ Forward Cases")
        self.tab_rej_list = self.dash_tabs.add("🚫 Reject Cases")
        
        # Forward List Frame
        self.fwd_scroll = ctk.CTkScrollableFrame(self.tab_fwd_list, fg_color="transparent")
        self.fwd_scroll.pack(fill="both", expand=True)
        
        # Reject List Frame
        self.rej_scroll = ctk.CTkScrollableFrame(self.tab_rej_list, fg_color="transparent")
        self.rej_scroll.pack(fill="both", expand=True)
        
        # ==================== RIGHT: CONTROL CENTER (SCROLLABLE) ====================
        control_frame = ctk.CTkScrollableFrame(self.forwarding_tab, fg_color=COLORS["bg_card"])
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)

        # Title
        ctk.CTkLabel(control_frame, text="⚙️ CASE DETAILS & ACTIONS", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["accent_cyan"]).pack(fill="x", pady=10)

        # BATCH START BUTTONS (AT TOP FOR VISIBILITY)
        batch_top_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        batch_top_frame.pack(fill="x", padx=10, pady=(0, 10))

        # TEST MODE REMOVED - Always production mode
        # ctk.CTkButton(batch_top_frame, text="🧪 START TEST LOOP (Save Only)",
        #              fg_color=COLORS["accent_orange"], height=40,
        #              font=ctk.CTkFont(weight="bold"),
        #              command=lambda: self.run_dashboard_batch(test_mode=True)).pack(fill="x", pady=3)

        ctk.CTkButton(batch_top_frame, text="🚀 START BATCH FORWARDING",
                     fg_color=COLORS["accent_green"], height=40,
                     font=ctk.CTkFont(weight="bold"),
                     command=lambda: self.run_dashboard_batch(test_mode=False)).pack(fill="x", pady=3)

        ctk.CTkLabel(batch_top_frame, text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", text_color="#444").pack(pady=5)

        # 1. Selected Case Info
        details = ctk.CTkFrame(control_frame, fg_color="transparent")
        details.pack(fill="x", padx=10)
        
        self.sel_case_label = ctk.CTkLabel(details, text="Select a Case...", font=ctk.CTkFont(size=16, weight="bold"))
        self.sel_case_label.pack(anchor="w")
        
        self.sel_name_entry = ctk.CTkEntry(details, placeholder_text="Applicant Name")
        self.sel_name_entry.pack(fill="x", pady=5)
        
        # 2. Case-Specific Answers
        config_box = ctk.CTkFrame(control_frame, fg_color=COLORS["bg_dark"])
        config_box.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(config_box, text="Rules (Case Override)", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=5)
        
        grid = ctk.CTkFrame(config_box, fg_color="transparent")
        grid.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(grid, text="Q4. NH/SH:").grid(row=0, column=0, sticky="w");
        self.sel_q4_var = StringVar(value="No")
        ctk.CTkSegmentedButton(grid, values=["No", "Yes"], variable=self.sel_q4_var, width=80).grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(grid, text="Q5. Juris.:").grid(row=1, column=0, sticky="w", pady=5);
        self.sel_q5_var = StringVar(value="Municipality")
        ctk.CTkComboBox(grid, values=["Municipality", "Municipal Corporation", "Rural Area", "NAC", "Development Authority"], variable=self.sel_q5_var, width=120).grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(grid, text="Purpose:").grid(row=2, column=0, sticky="w");
        self.sel_pur_entry = ctk.CTkEntry(grid, width=120)
        self.sel_pur_entry.insert(0, "HOMESTEAD")
        self.sel_pur_entry.grid(row=2, column=1, padx=5)
        
        # 3. Valuation & Fees (Read-Only/Edit)
        fee_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        fee_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(fee_frame, text="💰 Valuation Data", font=ctk.CTkFont(weight="bold", size=11)).pack(anchor="w")
        
        fgrid = ctk.CTkFrame(fee_frame, fg_color="transparent")
        fgrid.pack(fill="x")
        ctk.CTkLabel(fgrid, text="Rent:").grid(row=0, column=0); self.vis_rent = ctk.CTkEntry(fgrid, width=60); self.vis_rent.grid(row=0, column=1, padx=2)
        ctk.CTkLabel(fgrid, text="Cess:").grid(row=0, column=2); self.vis_cess = ctk.CTkEntry(fgrid, width=60); self.vis_cess.grid(row=0, column=3, padx=2)
        ctk.CTkLabel(fgrid, text="Conv:").grid(row=0, column=4); self.vis_conv = ctk.CTkEntry(fgrid, width=60); self.vis_conv.grid(row=0, column=5, padx=2)
        
        # 4. PDF Status
        self.vis_pdf_label = ctk.CTkLabel(control_frame, text="📎 No PDF Linked", text_color="gray")
        self.vis_pdf_label.pack(pady=5)
        
        # 5. Order Sheet
        # 5. Order Sheet Templates
        ctk.CTkLabel(control_frame, text="📝 Forward Order Sheet", font=ctk.CTkFont(weight="bold", size=11)).pack(anchor="w", padx=10)
        self.dash_os_text = ctk.CTkTextbox(control_frame, height=80, font=ctk.CTkFont(size=10))
        self.dash_os_text.pack(fill="x", padx=10, pady=2)
        
        # NEW: Forward Template (matches order.md)
        fwd_tpl = """<name> applied for conversion of below mentioned land scheduled with <plots 1>, <plots 2>, of <village>. An inquiry was conducted regarding the conversion of the subject land for homestead. Following a thorough local investigation, it has been determined that the land in question is indeed suitable for conversion without impeding natural water flow or neighboring irrigation activities. Furthermore, there is no risk of water logging post-conversion, and the accessibility of an approach road eliminates any logistical concerns. Notably, the absence of high tension electric lines passing over the land adds to its suitability.

Considering that the land falls under category 5 of the OLR Act, as per section 8(a), the applicable premium rate stands at 1% of the market value, as outlined in Notification No. 008-2023-773, issued by R&DM on January 6, 2024. This premium, along with the calculated LR (Land Revenue) and cess (75% of the LR), shall be payable. Hence total premium and fees fixed after checking valuation from IGR Odisha is as LR <LR> Cess <CESS> and premium <CONVERSION FEE>, the conversion is hereby recommended subject to approval by the concerned authority and payment of the aforementioned conversion fees. The case records are accordingly being returned to the Tahasildar for necessary action at the appropriate level. The completed case report has been forwarded to the Tahasildar."""
        self.dash_os_text.insert("1.0", fwd_tpl)

        ctk.CTkLabel(control_frame, text="📝 Reject Order Sheet (Fill Below)", font=ctk.CTkFont(weight="bold", size=11)).pack(anchor="w", padx=10, pady=(10,0))
        self.rej_order_sheet_text = ctk.CTkTextbox(control_frame, height=80, font=ctk.CTkFont(size=10), fg_color="#3a2a2a")
        self.rej_order_sheet_text.pack(fill="x", padx=10, pady=2)
        # Starts BLANK - user fills it manually
        
        # 6. Action Buttons
        act_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        act_frame.pack(fill="x", padx=10, pady=20)
        
        self.btn_save_case = ctk.CTkButton(act_frame, text="💾 Save Override (This Case)", fg_color=COLORS["bg_dark"], height=30, command=self.save_dash_case_edits)
        self.btn_save_case.pack(fill="x", pady=5)
        
        self.btn_apply_global = ctk.CTkButton(act_frame, text="🌍 Apply Control Rules to Global", fg_color="#555555", height=30, command=self.apply_controls_to_global)
        self.btn_apply_global.pack(fill="x", pady=5)
        
        ctk.CTkLabel(act_frame, text="━━━━━━━━━━━━━━━━━━").pack()
        
        self.interactive_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(act_frame, text="Interactive (Confirm Action)", variable=self.interactive_var).pack(pady=5)

        # TEST MODE REMOVED - Always production mode
        # self.btn_test_loop = ctk.CTkButton(act_frame, text="🧪 START TEST LOOP (Skip Submit)", fg_color=COLORS["accent_orange"], height=40, command=lambda: self.run_dashboard_batch(test_mode=True))
        # self.btn_test_loop.pack(fill="x", pady=5)

        self.btn_real_batch = ctk.CTkButton(act_frame, text="🚀 START BATCH FORWARDING", fg_color=COLORS["accent_green"], height=40, font=ctk.CTkFont(weight="bold"), command=lambda: self.run_dashboard_batch(test_mode=False))
        self.btn_real_batch.pack(fill="x", pady=5)

        # Export Status Log Button
        self.btn_export_log = ctk.CTkButton(act_frame, text="📊 Export Status Log", fg_color="#555555", height=30, command=self.export_batch_results)
        self.btn_export_log.pack(fill="x", pady=(10, 5))

        # Log (Small)
        self.fwd_log_text = ctk.CTkTextbox(control_frame, height=100)
        self.fwd_log_text.pack(fill="x", padx=10, pady=10)
        
        # Internal State
        self.current_sel_case = None

    def populate_forward_list(self):
        """Populate the Unified Dashboard List."""
        for w in self.fwd_scroll.winfo_children(): w.destroy()

        if not hasattr(self, 'forward_cases_grouped'):
            self.log("⚠️ populate_forward_list: No forward_cases_grouped attribute")
            return

        count = len(self.forward_cases_grouped)
        self.log(f"📋 Populating Forward List: {count} cases")

        for case in self.forward_cases_grouped:
            self._create_dash_row(self.fwd_scroll, case, is_rej=False)

        self.log(f"✅ Added {count} forward cases to Forwarding tab")

    def populate_reject_list(self):
        for w in self.rej_scroll.winfo_children(): w.destroy()
        if not hasattr(self, 'reject_cases_grouped'):
            self.log("⚠️ populate_reject_list: No reject_cases_grouped attribute")
            return

        count = len(self.reject_cases_grouped)
        self.log(f"📋 Populating Reject List: {count} cases")

        for case in self.reject_cases_grouped:
            self._create_dash_row(self.rej_scroll, case, is_rej=True)

        self.log(f"✅ Added {count} reject cases to Forwarding tab")
            
    def _create_dash_row(self, parent, case, is_rej):
        c_no = case['case_no']
        row = ctk.CTkButton(parent, text=f"{c_no} | {case['name'][:15]}", fg_color="transparent", border_width=1, border_color="#444", anchor="w", command=lambda c=case, r=is_rej: self.select_dash_case(c, r))
        row.pack(fill="x", pady=2)
    
    def select_dash_case(self, case, is_rej):
        """Load case into Right Control Panel."""
        self.current_sel_case = case
        self.current_is_rej = is_rej  # Track if this is a reject case

        # Update case label with type indicator
        type_indicator = "🔴 REJECT" if is_rej else "🟢 FORWARD"
        self.sel_case_label.configure(text=f"{type_indicator}: {case['case_no']}")

        self.sel_name_entry.delete(0, "end")
        self.sel_name_entry.insert(0, case['name'])

        # Valuation Populate
        self.vis_rent.delete(0, "end"); self.vis_rent.insert(0, str(case.get('rent', 0)))
        self.vis_cess.delete(0, "end"); self.vis_cess.insert(0, str(case.get('cess', 0)))
        self.vis_conv.delete(0, "end"); self.vis_conv.insert(0, str(case.get('conversion_fee', 0)))

        # PDF
        path = case.get('pdf_path')
        if path:
            self.vis_pdf_label.configure(text=f"📎 {os.path.basename(path)}", text_color="green")
        else:
            self.vis_pdf_label.configure(text="⚠️ No PDF Linked", text_color="red")

        # LOAD CASE-SPECIFIC OVERRIDES OR DEFAULTS into UI controls
        case_no = case['case_no']
        overrides = getattr(self, 'fwd_case_edits', {}).get(case_no, {})

        # Set Q4 (NH/SH) - use override > global > default "No"
        q4_val = overrides.get("q4", getattr(self, 'global_q4', 'No'))
        self.sel_q4_var.set(q4_val)

        # Set Q5 (Jurisdiction) - use override > global > default "Municipality"
        q5_val = overrides.get("q5", getattr(self, 'global_q5', 'Municipality'))
        self.sel_q5_var.set(q5_val)

        # Set Purpose - use override > global > default "HOMESTEAD"
        pur_val = overrides.get("purpose", getattr(self, 'global_pur', 'HOMESTEAD'))
        self.sel_pur_entry.delete(0, "end")
        self.sel_pur_entry.insert(0, pur_val)

        # Load per-case order sheet text for REJECT cases (override > global > blank)
        if is_rej:
            os_text = overrides.get("order_sheet_text", getattr(self, 'global_reject_order_sheet', ''))
            self.rej_order_sheet_text.delete("1.0", "end")
            if os_text:
                self.rej_order_sheet_text.insert("1.0", os_text)
            
    def apply_controls_to_global(self):
        """Update Global Defaults from current Control Panel values."""
        q4 = self.sel_q4_var.get()
        q5 = self.sel_q5_var.get()
        pur = self.sel_pur_entry.get()
        
        # We don't have explicit global vars anymore (removed in Dashboard refactor, using sel_ vars as current context)
        # But `_generic_batch_processor` looks at `overrides` or defaults.
        # Wait, I removed `fwd_q4_var` etc during the Unified Dashboard refactor and used `sel_q4_var` only for selection.
        # But `_generic_batch_processor` tried to read `self.fwd_q4_var` in my previous edit?
        # NO, I need to check `_generic_batch_processor`.
        # If I want "Change Universally", I should set a class-level default that `_generic_batch_processor` falls back to.
        
        self.global_q4 = q4
        self.global_q5 = q5
        self.global_pur = pur
        self.log_fwd(f"🌍 Global Defaults Updated: Q4={q4}, Q5={q5}, Pur={pur}")

        # Also save global reject order sheet (for all reject cases)
        rej_os = self.rej_order_sheet_text.get("1.0", "end-1c").strip()
        if rej_os:
            self.global_reject_order_sheet = rej_os
            self.log_fwd(f"🌍 Global Reject Order Sheet set ({len(rej_os)} chars)")
        
    def save_dash_case_edits(self):
        """Save edits from Control Panel back to case dict."""
        if not self.current_sel_case: return

        c_no = self.current_sel_case['case_no']
        is_rej = getattr(self, 'current_is_rej', False)

        # Build edits dict
        edits = {
            "q4": self.sel_q4_var.get(),
            "q5": self.sel_q5_var.get(),
            "purpose": self.sel_pur_entry.get()
        }

        # For reject cases, also save the order sheet text
        if is_rej:
            os_text = self.rej_order_sheet_text.get("1.0", "end-1c").strip()
            edits["order_sheet_text"] = os_text

        self.fwd_case_edits[c_no] = edits

        # Visual feedback - Change button temporarily
        original_text = self.btn_save_case.cget("text")
        original_color = self.btn_save_case.cget("fg_color")

        # Show success state
        self.btn_save_case.configure(
            text="✅ Saved!",
            fg_color=COLORS["accent_green"]
        )

        # Log the save with details
        type_str = "REJECT" if is_rej else "FORWARD"
        self.log_fwd(f"💾 Saved {type_str} Override for {c_no}: Q4={edits['q4']}, Q5={edits['q5']}, Purpose={edits['purpose']}")

        # Reset button after 1 second
        self.after(1000, lambda: self.btn_save_case.configure(
            text=original_text,
            fg_color=original_color
        ))

    def run_dashboard_batch(self, test_mode=False):
        """Run batch for currently visible list."""

        # BROWSER SETUP - Always use LRMS browser from Login tab
        # Close any IGR browser that might be lingering from Valuation tab
        if hasattr(self, 'igr_driver') and self.igr_driver:
            try:
                # Check if this is the IGR browser (different from Login browser)
                if hasattr(self, 'automation') and self.automation and self.automation.driver:
                    if self.igr_driver != self.automation.driver:
                        self.log_fwd("🔄 Closing IGR valuation browser...")
                        self.igr_driver.quit()
                        self.igr_driver = None
            except:
                pass

        # Use LRMS browser from Login tab
        if hasattr(self, 'automation') and self.automation and self.automation.driver:
            self.igr_driver = self.automation.driver
            self.log_fwd("✅ Using LRMS browser from Login tab")
        else:
            messagebox.showerror("Error",
                "Please login first via the Login tab!\n\n" +
                "The system needs an active LRMS browser session.")
            return

        # Determine which list is active (Forward or Reject)
        selected_tab = self.dash_tabs.get()
        is_rejection = "Reject" in selected_tab

        cases = self.reject_cases_grouped if is_rejection else self.forward_cases_grouped
        
        if not cases:
             messagebox.showwarning("Empty", f"No cases in {selected_tab}")
             return
             
        threading.Thread(target=self._fwd_batch_process_thread, args=(cases, test_mode, is_rejection), daemon=True).start()
        
    def log_fwd(self, message):
        """Log to BOTH Forwarding tab AND Status Log tab."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"[{timestamp}] {message}\n"

        # Log to Forwarding tab
        self.fwd_log_text.insert("end", msg)
        self.fwd_log_text.see("end")

        # ALSO log to Status Log tab
        if hasattr(self, 'log_text'):
            self.log_text.insert("end", msg)
            self.log_text.see("end")
    
    # ==================== FORWARDING LOGIC ====================
    
    def run_forwarding_dry_run(self):
        """Execute Dry Run on specific test case."""
        case_no = self.test_case_entry.get().strip()
        if not case_no:
            messagebox.showwarning("Error", "Enter case number!")
            return
            
        # Fallback Check: If logged in via Login Tab, use that driver
        if not self.igr_driver and hasattr(self, 'automation') and self.automation and self.automation.driver:
            self.igr_driver = self.automation.driver

        if not self.igr_driver:
            messagebox.showwarning("Error", "Browser not started! Go to Login tab.")
            return

        if not messagebox.askyesno("Confirm Dry Run", f"Start Dry Run for Case {case_no}?\n\nThis will fill the form but STOP before final submission."):
            return
            
        threading.Thread(target=self._fwd_process_thread, args=(case_no, True), daemon=True).start()
    
    def _fwd_process_thread(self, case_no, dry_run=False):
        """Background thread for forwarding process."""
        try:
            self.log_fwd("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log_fwd(f"🚀 STARTING {'DRY RUN' if dry_run else 'FORWARDING'} - Case {case_no}")
            self.log_fwd("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # 1. Navigate to OLR 8A (OnlineCasesFromTah)
            self.log_fwd("📍 Navigating to OLR 8A...")
            try:
                # Direct link or Menu Click? Using direct check first
                if "Onlinecasesfromtah.aspx" not in self.igr_driver.current_url:
                    self.igr_driver.get("https://lrmsodisha.saccess.nic.in/Bhulekh/Onlinecasesfromtah.aspx")
                    time.sleep(2)
            except:
                self.log_fwd("⚠️ Navigation failed. Please ensure you are logged in and on OLR 8A page.")
            
            # 2. Search Case
            self.log_fwd(f"🔎 Searching Case: {case_no}")
            try:
                 search_box = self.igr_driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_txtsearchcase"]')
                 search_box.clear()
                 search_box.send_keys(case_no)
                 
                 search_btn = self.igr_driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_btnSearchMutcase"]')
                 search_btn.click()
                 time.sleep(2)
            except Exception as e:
                 self.log_fwd(f"❌ Search Failed: {e}")
                 return
            
            # 3. Click View
            # Note: If multiple results, picking first.
            try:
                view_btn = self.igr_driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_gvForward_ctl02_btn_Show"]')
                view_btn.click()
                time.sleep(3)
                self.log_fwd("✅ Case Opened.")
            except:
                self.log_fwd("❌ 'View' button not found! Case might not exist.")
                return

            # 4. Form Filling
            self.log_fwd("📝 Filling Form (20 Questions)...")
            
            # Static Answers (No) - Q1-3, 8-10, 13-14, 16-18, 20
            # IDs from CSV:
            # Q1: nWaterSource, Q2: nWaterCourse, Q3: waterCourseLayout
            # Q8: agriOperation, Q9: obstructPassage, Q10: ArchaeologicalLandscape
            # Q13: ayacutArea, Q14: floodZone
            # Q16: notifiedArea, Q17: highTowerElectricity, Q18: khataStatus
            # Q20: ddlexemption
            no_ids = [
                "nWaterSource", "nWaterCourse", "waterCourseLayout", "agriOperation", 
                "obstructPassage", "ArchaeologicalLandscape", "ayacutArea", "floodZone",
                "notifiedArea", "highTowerElectricity", "khataStatus", "ddlexemption"
            ]
            
            for eid in no_ids:
                try:
                    sel = Select(self.igr_driver.find_element(By.ID, f"ctl00_ContentPlaceHolder1_{eid}"))
                    sel.select_by_visible_text("No")
                except: pass
            
            # Static Answers (Yes) - Q11, Q15, Q19
            # Q11: accessRoad, Q15: publicEasement, Q19: suitableforconversion
            yes_ids = ["accessRoad", "publicEasement", "suitableforconversion"]
            for eid in yes_ids:
                try:
                    sel = Select(self.igr_driver.find_element(By.ID, f"ctl00_ContentPlaceHolder1_{eid}"))
                    sel.select_by_visible_text("Yes")
                except: pass

            # Dynamic Q4 (NH/SH)
            try:
                val = self.fwd_q4_var.get() # "Yes" or "No"
                Select(self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_NHSH")).select_by_visible_text(val)
            except: pass
            
            # Dynamic Q5 (Jurisdiction)
            try:
                val = self.fwd_q5_var.get()
                Select(self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_landJurisdiction")).select_by_visible_text(val)
            except: pass
            
            # Dynamic Q12 (Purpose)
            try:
                val = self.fwd_q12_entry.get().strip()
                self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_Purpose").clear()
                self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_Purpose").send_keys(val)
            except: pass
            
            # Q6 (Date) - Assuming today/auto-filled for now, or just click field?
            # User CSV said "click todays date".
            # XPath: //*[@id="ctl00_ContentPlaceHolder1_actualDate"]
            try:
                date_input = self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_actualDate")
                # Attempt to set value directly first for speed
                today_str = datetime.now().strftime("%d/%m/%Y")
                self.igr_driver.execute_script(f"arguments[0].value = '{today_str}';", date_input)
            except: pass

            # Q7 (Market Value) - ID: ctl00_ContentPlaceHolder1_marketValue
            # Dry Run: Enter "100000" dummy
            try:
                mv_input = self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_marketValue")
                mv_input.clear()
                mv_input.send_keys("100000")
            except: pass


            # Fees (Type Logic - No Copy Paste)
            # Dry Run: Dummy Values
            fees = {
                "txtrent": "10",
                "txtcess": "5",
                "txtconvfee": "1000",
                "txtpaymenttotal": "1015"
            }
            
            self.log_fwd(f"💰 Entering Fees: {fees}")
            
            for eid, val in fees.items():
                try:
                    elem = self.igr_driver.find_element(By.ID, f"ctl00_ContentPlaceHolder1_{eid}")
                    elem.clear()
                    # Simulate Typing
                    for char in val:
                        elem.send_keys(char)
                        time.sleep(0.1) # Human-like typing
                except Exception as e:
                    self.log_fwd(f"⚠️ Fee Error ({eid}): {e}")

            # 5. Order Sheet Sequence
            self.log_fwd("💾 Clicking Initial Save...")
            try:
                self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnsave").click()
                time.sleep(3)
            except Exception as e:
                self.log_fwd(f"❌ Initial Save Failed: {e}")
            
            # Wait for Order Sheet Textbox (txtTotal per User)
            self.log_fwd("⏳ Waiting for Order Sheet Box (txtTotal)...")
            try:
                # Polling for element
                WebDriverWait(self.igr_driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtTotal"))
                )
                
                os_box = self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtTotal")
                template = self.fwd_order_sheet_entry.get()
                os_box.clear()
                os_box.send_keys(template)
                self.log_fwd("📝 Order Sheet Filled.")
                
            except Exception as e:
                self.log_fwd(f"❌ Order Sheet Box not found/interactable: {e}")
            
            if dry_run:
                self.log_fwd("🛑 DRY RUN STOPPED. (Did not click Final Submit)")
                messagebox.showinfo("Dry Run", "Form filled! Proceed manually to Verify and Submit.")
                return
                
            # Final Submit
            # self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btn_submit").click()
            
        except Exception as e:
            self.log_fwd(f"❌ Error: {e}")


        
    def run_forwarding_batch(self):
        """Start Batch Forwarding for SELECTED cases found in UI list."""
        if not hasattr(self, 'forward_cases_grouped'):
            messagebox.showwarning("Error", "No Forward cases found! Load data first.")
            return

        # Filter Selected
        selected_cases = [c for c in self.forward_cases_grouped if self.fwd_case_vars.get(c['case_no']) and self.fwd_case_vars[c['case_no']].get()]
        
        if not selected_cases:
            messagebox.showwarning("Error", "No cases selected!")
            return

        # Fallback Check
        if not self.igr_driver and hasattr(self, 'automation') and self.automation and self.automation.driver:
            self.igr_driver = self.automation.driver
            
        if not self.igr_driver:
            messagebox.showwarning("Error", "Browser not started! Go to Login tab.")
            return

        count = len(selected_cases)
        if not messagebox.askyesno("Confirm Batch", f"Start Forwarding for {count} Selected cases?"):
            return
            
        threading.Thread(target=self._fwd_batch_process_thread, args=(selected_cases,), daemon=True).start()

    def run_rejection_batch(self):
        """Start Batch Rejection for SELECTED cases."""
        if not hasattr(self, 'reject_cases_grouped'):
            messagebox.showwarning("Error", "No Reject cases found! Load data first.")
            return

        # Filter Selected
        selected_cases = [c for c in self.reject_cases_grouped if self.rej_case_vars.get(c['case_no']) and self.rej_case_vars[c['case_no']].get()]

        if not selected_cases:
            messagebox.showwarning("Error", "No cases selected!")
            return

        # Fallback Check
        if not self.igr_driver and hasattr(self, 'automation') and self.automation and self.automation.driver:
            self.igr_driver = self.automation.driver
            
        if not self.igr_driver:
            messagebox.showwarning("Error", "Browser not started! Go to Login tab.")
            return
            
        count = len(selected_cases)
        if not messagebox.askyesno("Confirm Reject Batch", f"Start REJECTION for {count} Selected cases?\n\nThis will Upload PDF and click REJECT."):
            return
            
        threading.Thread(target=self._rej_batch_process_thread, args=(selected_cases,), daemon=True).start()

    def proceed_to_forwarding(self):
        """Transition from Valuation to Forwarding."""
        # 1. Login Check
        if not hasattr(self, 'igr_driver') or not self.igr_driver:
            # Try to grab from automation
            if hasattr(self, 'automation') and self.automation and self.automation.driver:
                self.igr_driver = self.automation.driver
            else:
                if not messagebox.askyesno("Login Check", "Are you logged into OLR 8A?\n\nIf Yes, we will proceed to Forwarding.\nIf No, please Login first."):
                    return

        # 2. Auto-Load Excel
        if hasattr(self, 'last_save_path') and self.last_save_path and os.path.exists(self.last_save_path):
            self.fwd_excel_path = self.last_save_path
            self.fwd_excel_label.configure(text=os.path.basename(self.last_save_path))
            self.log(f"🔄 Auto-loaded Valuation Data: {self.last_save_path}")
            
            # Trigger Detection (for Forward cases from Valuation Excel)
            self.detect_cases()

            # Load Reject cases from Setup tab (they're not in Valuation Excel)
            if hasattr(self, 'setup_reject_cases') and self.setup_reject_cases:
                self.reject_cases_grouped = list(self.setup_reject_cases)
                self.reject_cases = list(self.setup_reject_cases)
                self.log(f"✅ Loaded {len(self.reject_cases_grouped)} Reject cases from Setup tab")
                if hasattr(self, 'populate_reject_list'):
                    self.populate_reject_list()

            # Switch Tab
            self.tabview.set("📤 Forwarding")
            self.log_fwd("🚀 Switched to Forwarding Tab with Data Loaded.")
            
        else:
             messagebox.showwarning("No Data", "No generated Valuation Excel found.\nPlease Generate Excel first or Load manually in Forwarding Tab.")
             self.tabview.set("📤 Forwarding")

    # ==================== FORWARDING LOGIC ====================
    
    # ... (dry run methods) ...

    def _fwd_batch_process_thread(self, cases_to_process, test_mode=False, is_rejection=False):
        """Unified Batch processing thread."""
        action = "REJECTION" if is_rejection else "FORWARDING"
        mode = "TEST LOOP (No Submit)" if test_mode else "REAL BATCH"

        self.log_fwd("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log_fwd(f"🚀 STARTING {action} - {mode}")
        self.log_fwd(f"📊 Count: {len(cases_to_process)} cases")
        self.log_fwd("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # LOCK TO LRMS WINDOW - Prevents tab shifting issues
        try:
            self.lrms_window_handle = self.igr_driver.current_window_handle
            all_handles = self.igr_driver.window_handles
            self.log_fwd(f"🔒 Locked to LRMS window (Total windows: {len(all_handles)})")
        except:
            self.lrms_window_handle = None
            self.log_fwd("⚠️ Could not lock window handle")

        flat_cases = self.reject_cases if is_rejection else self.forward_cases
        self._generic_batch_processor(cases_to_process, flat_cases, is_rejection, test_mode)

    def _generic_batch_processor(self, grouped_cases, flat_cases, is_rejection=False, test_mode=False):
        """Shared logic for Forward/Reject batch."""
        success_count = 0
        fail_count = 0
        interactive = self.interactive_var.get()

        action_name = "REJECT" if is_rejection else "FORWARD"

        # Initialize batch results tracking
        if not hasattr(self, 'batch_results'):
            self.batch_results = []

        # Determine Order Sheet Text Source (for reject cases - from UI textbox)
        rej_os_text = self.rej_order_sheet_text.get("1.0", "end-1c") if is_rejection else ""

        def ensure_correct_window():
            """
            STRICT WINDOW MANAGEMENT & ALERT PROTECTION
            1. Never touch VPN window.
            2. Force focus to LRMS window.
            3. Inject JS to kill blocking alerts.
            """
            try:
                # 1. Identify Handles
                current = self.igr_driver.current_window_handle
                
                # Check if we accidentally fell onto VPN window
                if hasattr(self, 'vpn_window_handle') and current == self.vpn_window_handle:
                    self.log_fwd("⚠️ On VPN Window! Switching to LRMS...")
                    if hasattr(self, 'lrms_window_handle') and self.lrms_window_handle:
                         self.igr_driver.switch_to.window(self.lrms_window_handle)
                    else:
                         # Panic: Try to find any other window
                         for h in self.igr_driver.window_handles:
                             if h != self.vpn_window_handle:
                                 self.igr_driver.switch_to.window(h)
                                 self.lrms_window_handle = h
                                 break
                
                # 2. Force Focus to LRMS (if defined)
                elif hasattr(self, 'lrms_window_handle') and self.lrms_window_handle and current != self.lrms_window_handle:
                    self.log_fwd("↻ Correcting Focus to LRMS...")
                    self.igr_driver.switch_to.window(self.lrms_window_handle)
                
                # 3. SAFETY NET: Inject JS to suppress blocking alerts & CAPTURE TEXT
                # This fixes the 120s hang by making alerts non-blocking on the browser side
                try:
                    self.igr_driver.execute_script("""
                        if (!window.isAlertOverridden) {
                            window.lastAlertText = null;
                            window.originalAlert = window.alert;
                            window.alert = function(msg) { 
                                window.lastAlertText = msg; 
                                console.log("Blocked Alert: " + msg);
                                return true; 
                            };
                            window.confirm = function(msg) {
                                window.lastAlertText = msg;
                                return true; 
                            };
                            window.isAlertOverridden = true;
                        }
                    """)
                except: pass
                
            except Exception as e:
                self.log_fwd(f"⚠️ Window Focus Error: {e}")

        def check_js_alert(wait_seconds=3):
            """Poll for JS-captured alert text OR native alert (Hybrid approach)."""
            start_time = time.time()
            found_text = None
            
            while time.time() - start_time < wait_seconds:
                # 1. Check JS variable (Preferred - Non-blocking)
                try:
                    txt = self.igr_driver.execute_script("return window.lastAlertText;")
                    if txt:
                        # Clear it instantly
                        self.igr_driver.execute_script("window.lastAlertText = null;")
                        found_text = txt
                        break
                except: pass
                
                # 2. Check Native Alert (Fallback if JS injection failed)
                try:
                    alert = self.igr_driver.switch_to.alert
                    txt = alert.text
                    alert.accept() # Auto-accept native alert
                    found_text = txt
                    break
                except: pass
                
                time.sleep(0.2)
            
            return found_text

        # FORCE INITIAL SWITCH (User requirement: Visual confirmation)
        if hasattr(self, 'lrms_window_handle') and self.lrms_window_handle:
            try:
                self.igr_driver.switch_to.window(self.lrms_window_handle)
                time.sleep(1)
            except: pass

        for idx, case in enumerate(grouped_cases, 1):
            case_no = case['case_no']
            self.log_fwd(f"\n[{idx}/{len(grouped_cases)}] Processing {case_no} ({action_name})...")
            
            try:
                # 1. Navigation
                ensure_correct_window()
                current_url = self.igr_driver.current_url
                if "Onlinecasesfromtah.aspx" not in current_url:
                     self.igr_driver.get("https://lrmsodisha.saccess.nic.in/Bhulekh/Onlinecasesfromtah.aspx")
                     time.sleep(2)

                # 2. Search
                ensure_correct_window()
                try:
                    search_box = self.igr_driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_txtsearchcase"]')
                    search_box.clear()
                    search_box.send_keys(case_no)
                    self.igr_driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_btnSearchMutcase"]').click()
                    time.sleep(2)
                except Exception as e:
                    self.log_fwd(f"❌ Search Error: {e}")
                    fail_count += 1
                    continue

                # 3. View Button
                ensure_correct_window()
                try:
                    view_btn = self.igr_driver.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_gvForward_ctl02_btn_Show"]')
                    view_btn.click()
                    self.log_fwd("✅ Clicked View button. Waiting for form to load...")
                    time.sleep(4)  # Increased wait time for form to fully load
                except:
                    self.log_fwd("❌ 'View' button missing. Skipping.")
                    fail_count += 1
                    continue

                # Check for "No application pending" message
                try:
                    page_text = self.igr_driver.page_source
                    if "no application pending" in page_text.lower() or "no record" in page_text.lower():
                        self.log_fwd(f"⚠️ {case_no}: No application pending. Skipping.")
                        continue
                except:
                    pass

                # Check for Dashboard Overrides OR Global Defaults
                overrides = self.fwd_case_edits.get(case_no, {})

                # 4. FILL QUESTIONS IN SERIAL ORDER (Q1-Q20)
                # Prepare values first
                case_rows = [c for c in flat_cases if c['case_no'] == case_no]
                total_benchmark = sum(c.get('benchmark', 0) or 0 for c in case_rows)
                t_rent = sum(float(c.get('rent', 0) or 0) for c in case_rows)
                t_cess = sum(float(c.get('cess', 0) or 0) for c in case_rows)
                t_conv = sum(float(c.get('conversion_fee', 0) or 0) for c in case_rows)
                t_total = t_rent + t_cess + t_conv

                # For REJECT cases: Set fees to 0 (they won't be filled anyway)
                if is_rejection:
                    t_rent = t_cess = t_conv = t_total = 0
                    total_benchmark = 0

                val_q4 = overrides.get("q4", getattr(self, 'global_q4', 'No'))
                val_q5 = overrides.get("q5", getattr(self, 'global_q5', 'Municipality'))
                val_pur = overrides.get("purpose", getattr(self, 'global_pur', 'HOMESTEAD'))

                # Serial question filling (Q1-Q20)
                ensure_correct_window()

                if is_rejection:
                    self.log_fwd("📝 REJECT: Filling ALL questions with 'No' (Q1-Q20)...")
                    # REJECT CASES: ALL questions answered "No"
                    question_map = [
                        (1, "nWaterSource", "dropdown", "No"),
                        (2, "nWaterCourse", "dropdown", "No"),
                        (3, "waterCourseLayout", "dropdown", "No"),
                        (4, "NHSH", "dropdown", "No"),
                        (5, "landJurisdiction", "dropdown", val_q5),  # Keep jurisdiction from UI
                        (6, "actualDate", "date", datetime.now().strftime('%d/%m/%Y')),
                        (7, "marketValue", "text", "500000"),  # Fixed value for reject
                        (8, "agriOperation", "dropdown", "No"),
                        (9, "obstructPassage", "dropdown", "No"),
                        (10, "ArchaeologicalLandscape", "dropdown", "No"),
                        (11, "accessRoad", "dropdown", "No"),  # No for reject
                        (12, "Purpose", "text", val_pur),  # Keep purpose from UI
                        (13, "ayacutArea", "dropdown", "No"),
                        (14, "floodZone", "dropdown", "No"),
                        (15, "publicEasement", "dropdown", "No"),  # No for reject
                        (16, "notifiedArea", "dropdown", "No"),
                        (17, "highTowerElectricity", "dropdown", "No"),
                        (18, "khataStatus", "dropdown", "No"),
                        (19, "suitableforconversion", "dropdown", "No"),  # No for reject
                        (20, "ddlexemption", "dropdown", "No"),
                    ]
                else:
                    self.log_fwd("📝 Filling questions in serial order (Q1-Q20)...")
                    # FORWARD CASES: Normal logic with some Yes answers
                    question_map = [
                        (1, "nWaterSource", "dropdown", "No"),
                        (2, "nWaterCourse", "dropdown", "No"),
                        (3, "waterCourseLayout", "dropdown", "No"),
                        (4, "NHSH", "dropdown", val_q4),
                        (5, "landJurisdiction", "dropdown", val_q5),
                        (6, "actualDate", "date", datetime.now().strftime('%d/%m/%Y')),
                        (7, "marketValue", "text", str(int(total_benchmark))),
                        (8, "agriOperation", "dropdown", "No"),
                        (9, "obstructPassage", "dropdown", "No"),
                        (10, "ArchaeologicalLandscape", "dropdown", "No"),
                        (11, "accessRoad", "dropdown", "Yes"),
                        (12, "Purpose", "text", val_pur),
                        (13, "ayacutArea", "dropdown", "No"),
                        (14, "floodZone", "dropdown", "No"),
                        (15, "publicEasement", "dropdown", "Yes"),
                        (16, "notifiedArea", "dropdown", "No"),
                        (17, "highTowerElectricity", "dropdown", "No"),
                        (18, "khataStatus", "dropdown", "No"),
                        (19, "suitableforconversion", "dropdown", "Yes"),
                        (20, "ddlexemption", "dropdown", "No"),
                    ]

                filled_count = 0
                for q_num, field_id, field_type, value in question_map:
                    try:
                        ensure_correct_window()
                        full_id = f"ctl00_ContentPlaceHolder1_{field_id}"

                        # Wait for element
                        elem = WebDriverWait(self.igr_driver, 5).until(
                            EC.presence_of_element_located((By.ID, full_id))
                        )

                        if field_type == "dropdown":
                            Select(elem).select_by_visible_text(value)
                        elif field_type == "date":
                            self.igr_driver.execute_script(f"arguments[0].value = '{value}';", elem)
                        elif field_type == "text":
                            elem.clear()
                            elem.send_keys(value)

                        filled_count += 1
                        # self.log_fwd(f"   ✓ Q{q_num} ({field_id}) = {value}")

                    except Exception as e:
                        self.log_fwd(f"   ⚠️ Q{q_num} ({field_id}) FAILED: {str(e)[:80]}")
                        # Dismiss alert if present
                        try:
                            alert = self.igr_driver.switch_to.alert
                            alert.accept()
                            self.log_fwd("   ⚠️ Dismissed alert")
                        except:
                            pass

                self.log_fwd(f"✅ Filled {filled_count}/20 questions")

                # Dismiss any alerts that appeared during question filling
                try:
                    alert = self.igr_driver.switch_to.alert
                    alert_text = alert.text
                    self.log_fwd(f"⚠️ Alert after questions: {alert_text[:100]}")
                    alert.accept()
                    self.log_fwd("✅ Clicked OK on alert")
                except:
                    pass  # No alert

                if filled_count < 18:
                    self.log_fwd(f"❌ Too many questions failed ({20-filled_count} missing)")
                    fail_count += 1
                    continue

                # 5. PDF UPLOAD (with retry)
                pdf_path = case.get('pdf_path')

                # ENSURE ABSOLUTE PATH
                if pdf_path and not os.path.isabs(pdf_path):
                    self.log_fwd(f"⚠️ PDF path is relative: {pdf_path}")
                    if os.path.exists(pdf_path):
                        pdf_path = os.path.abspath(pdf_path)
                        self.log_fwd(f"✓ Converted to absolute: {pdf_path}")
                    else:
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        alt_path = os.path.join(script_dir, pdf_path)
                        if os.path.exists(alt_path):
                            pdf_path = alt_path
                            self.log_fwd(f"✓ Found in script dir: {pdf_path}")
                        else:
                            pdf_path = None
                            self.log_fwd(f"❌ PDF file not found")

                upload_success = False
                if pdf_path and os.path.exists(pdf_path):
                    file_size_kb = os.path.getsize(pdf_path) / 1024
                    self.log_fwd(f"📎 Uploading PDF: {os.path.basename(pdf_path)} ({file_size_kb:.1f} KB)")
                    self.log_fwd(f"   Full path: {pdf_path}")

                    # Upload with retry (max 2 attempts) - USER'S FIX
                    for attempt in range(2):
                        try:
                            ensure_correct_window()

                            # Dismiss any existing alerts first
                            if check_js_alert(0.5):
                                 self.log_fwd("   ⚠️ Dismissed existing alert")

                            # Find upload element
                            file_input = WebDriverWait(self.igr_driver, 10).until(
                                EC.presence_of_element_located((By.ID, "fileUpload"))
                            )

                            # USER'S FIX 1: Make element visible (critical for hidden inputs)
                            self.log_fwd("   📤 Making element visible...")
                            self.igr_driver.execute_script(
                                "arguments[0].style.display = 'block';", file_input
                            )
                            self.igr_driver.execute_script(
                                "arguments[0].style.visibility = 'visible';", file_input
                            )
                            time.sleep(0.3)

                            # Send absolute path
                            abs_path = os.path.abspath(pdf_path)
                            self.log_fwd(f"   📁 Sending path: {abs_path}")
                            file_input.send_keys(abs_path)
                            time.sleep(1)

                            # USER'S FIX 2: Trigger 'change' event (critical - tells page file selected)
                            self.log_fwd("   🔄 Triggering change event...")
                            self.igr_driver.execute_script(
                                "arguments[0].dispatchEvent(new Event('change'));", file_input
                            )
                            time.sleep(1)

                            # VERIFICATION: Check if filename in element value
                            uploaded_value = file_input.get_attribute('value')
                            filename = os.path.basename(pdf_path)

                            if filename in str(uploaded_value):
                                self.log_fwd(f"   ✅ VERIFIED: '{filename}' in element value")
                                upload_success = True
                            elif pdf_path in str(uploaded_value):
                                self.log_fwd(f"   ✅ VERIFIED: Full path in element value")
                                upload_success = True
                            else:
                                self.log_fwd(f"   ⚠️ WARNING: Filename not in value ('{uploaded_value}')")
                                upload_success = True  # Proceed anyway, server will validate

                            # Wait for server processing (increased from 3s to 5s)
                            self.log_fwd("   ⏳ Waiting 5 seconds for server...")
                            time.sleep(5)
                            
                            # Check for immediate upload error
                            err = check_js_alert(1)
                            if err:
                                self.log_fwd(f"   ⚠️ Uplod Alert: {err}")
                                
                            break  # Success

                        except Exception as e:
                            self.log_fwd(f"   ⚠️ Upload attempt {attempt+1} failed: {str(e)[:80]}")
                            # Dismiss alert if present
                            check_js_alert(1)
                            if attempt < 1:
                                time.sleep(2)
                            if attempt < 1:
                                time.sleep(2)

                    if upload_success:
                        self.log_fwd("   ✅ Upload complete")
                    else:
                        self.log_fwd(f"   ❌ PDF upload failed after {attempt+1} attempts")

                else:
                    self.log_fwd("⚠️ No PDF provided or file missing")

                # 6. FEE FIELDS (with anti-stale protection)
                if not is_rejection:
                    self.log_fwd("💰 Filling fee fields...")
                    ensure_correct_window()

                    fees_map = {
                        "txtrent": str(int(t_rent)),
                        "txtcess": str(int(t_cess)),
                        "txtconvfee": str(int(t_conv)),
                        "txtpaymenttotal": str(int(t_total))
                    }

                    fees_filled = 0
                    for field_name, value in fees_map.items():
                        for retry in range(3):  # 3 retries per field
                            try:
                                ensure_correct_window()

                                # Fresh element lookup each time
                                elem = WebDriverWait(self.igr_driver, 10).until(
                                    EC.presence_of_element_located(
                                        (By.ID, f"ctl00_ContentPlaceHolder1_{field_name}")
                                    )
                                )

                                elem.clear()
                                time.sleep(0.2)

                                # Send value character by character
                                for char in value:
                                    elem.send_keys(char)
                                    time.sleep(0.05)

                                fees_filled += 1
                                # self.log_fwd(f"   ✓ {field_name} = {value}")
                                break  # Success, move to next field

                            except Exception as e:
                                if retry == 2:  # Last retry
                                    self.log_fwd(f"   ⚠️ {field_name} failed: {str(e)[:50]}")
                                else:
                                    time.sleep(0.5)  # Wait before retry

                    self.log_fwd(f"✅ Filled {fees_filled}/4 fee fields")

                    # Dismiss any alerts that appeared during fee filling
                    try:
                        alert = self.igr_driver.switch_to.alert
                        alert_text = alert.text
                        self.log_fwd(f"⚠️ Alert after fees: {alert_text[:100]}")
                        alert.accept()
                        self.log_fwd("✅ Clicked OK on alert")
                    except:
                        pass  # No alert

                    if fees_filled < 4:
                        self.log_fwd(f"⚠️ Some fee fields incomplete ({4-fees_filled} missing)")
                        # Don't fail - continue anyway

                # 7. Action Sequence (Same for Forward and Reject cases)
                # FORWARDING LOGIC (New JS-Alert System)
                ensure_correct_window()
                save_success = False

                for save_attempt in range(3):
                    self.log_fwd(f"💾 Clicking FIRST SAVE (attempt {save_attempt+1}/3)...")
                    ensure_correct_window()

                    # 1. Click Save (Alerts are suppressed by JS)
                    try:
                        self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnsave").click()
                    except Exception as e:
                        self.log_fwd(f"   ⚠️ Click ignored (maybe alert open?): {str(e)[:50]}")

                    # 2. Check JS Alert
                    alert_text = check_js_alert(10)  # Increased wait to 10s

                    if alert_text:
                        self.log_fwd(f"   🔔 Alert Captured: '{alert_text}'")

                        text_lower = alert_text.lower()
                        is_success = any(k in text_lower for k in ["success", "saved", "record updated", "data saved"])
                        is_failure = any(k in text_lower for k in ["not saved", "fail", "error", "upload", "sketch", "map", "file"])

                        # Prioritize failure detection
                        if is_failure:
                            self.log_fwd("   ⚠️ ERROR Alert detected")
                            if any(k in text_lower for k in ["upload", "sketch", "map", "file"]):
                                self.log_fwd("   ⚠️ UPLOAD ERROR - Will re-upload")
                                time.sleep(2)

                                # RE-UPLOAD LOGIC
                                if pdf_path and os.path.exists(pdf_path):
                                    try:
                                        ensure_correct_window()
                                        file_input = WebDriverWait(self.igr_driver, 5).until(EC.presence_of_element_located((By.ID, "fileUpload")))
                                        self.igr_driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", file_input)
                                        file_input.send_keys(os.path.abspath(pdf_path))
                                        self.igr_driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", file_input)
                                        time.sleep(4)
                                        # Clear potential upload alert
                                        check_js_alert(1)
                                    except Exception as e:
                                        self.log_fwd(f"   ❌ Re-upload failed: {e}")
                                else:
                                    self.log_fwd("   ❌ PDF missing, cannot re-upload")
                                    break
                            else:
                                self.log_fwd(f"   ⚠️ Generic Failure: {alert_text}")
                                # Retry save

                        elif is_success:
                            self.log_fwd("   ✅ SUCCESS - Save completed")
                            save_success = True
                            break

                        else:
                            self.log_fwd(f"   ⚠️ Unknown Alert: {alert_text} - Retrying Save...")
                            time.sleep(1)
                    else:
                        self.log_fwd("   ⚠️ No alert detected. Checking if Order Sheet appeared anyway...")
                        # FALLBACK: Check if Order Sheet exists (Success Indicator)
                        try:
                            os_elem = self.igr_driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtTotal")
                            if os_elem and os_elem[0].is_displayed():
                                self.log_fwd("   ✅ Order Sheet Found! Save was successful (Silent).")
                                save_success = True
                                break
                        except: pass

                        self.log_fwd("   ❌ No Order Sheet found. Retrying Save...")

                    time.sleep(1)

                if not save_success:
                    self.log_fwd("❌ First save failed after 3 attempts")
                    fail_count += 1

                    # RECOVERY: Force Reload Search Page
                    try:
                        self.log_fwd("   🔙 Recovery: Reloading Search Page...")
                        self.igr_driver.get("https://lrmsodisha.saccess.nic.in/Bhulekh/Onlinecasesfromtah.aspx")
                        time.sleep(2)
                    except: pass
                    continue

                # Step 2: Wait for and Fill Order Sheet (with extended timeout and retry)
                os_filled = False
                for attempt in range(3):  # 3 attempts
                    try:
                        self.log_fwd(f"📝 Waiting for order sheet (attempt {attempt+1}/3)...")
                        ensure_correct_window()

                        os_box = WebDriverWait(self.igr_driver, 30).until(
                            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtTotal"))
                        )

                        # Verify it's visible and enabled
                        if not os_box.is_displayed() or not os_box.is_enabled():
                            raise Exception("Order sheet not visible/enabled")

                        # Get template from dashboard
                        # REJECT LOGIC: Use rej_order_sheet_text (Universal Template) or per-case override
                        if is_rejection:
                            # Check if this specific case has a custom order sheet saved in case dict
                            template = case.get('order_sheet_text', '')
                            if not template:
                                # Fallback to the Global Reject Template Box (filled by user in UI)
                                template = self.rej_order_sheet_text.get("1.0", "end-1c")

                            if not template or template.strip() == "":
                                self.log_fwd("⚠️ Reject Order Sheet Empty! Using placeholder.")
                                template = "Application rejected due to discrepancies."
                        else:
                            # FORWARD LOGIC
                            template = self.dash_os_text.get("1.0", "end-1c")

                        if not template or template.strip() == "":
                            self.log_fwd("⚠️ Order Sheet Template is EMPTY! Using default.")
                            # UPDATED FORMAT per User Request
                            template = f"<name>\nLR <LR> Cess <CESS>\nConversion: <CONVERSION FEE>"

                        # Get Data
                        c_name = str(case.get('name', 'Unknown'))
                        c_rows = [c for c in flat_cases if c['case_no'] == case_no]
                        rent_val = sum(float(c.get('rent', 0) or 0) for c in c_rows)
                        cess_val = sum(float(c.get('cess', 0) or 0) for c in c_rows)
                        conv_val = sum(float(c.get('conversion_fee', 0) or 0) for c in c_rows)

                        # Build plots list from case rows
                        plots_list = []
                        for row in c_rows:
                            plot_no = row.get('plot_no', '')
                            if plot_no:
                                plots_list.append(f"Plot {plot_no}")

                        # Get village from case data (FORCE STRING)
                        village = str(c_rows[0].get('village_english') or c_rows[0].get('mouza') or '') if c_rows else ''

                        # Perform all replacements (FORCE STR check)
                        final_text = template.replace("<name>", str(c_name or ""))
                        final_text = final_text.replace("<plots 1>", str(plots_list[0]) if len(plots_list) > 0 else "Plot N/A")
                        final_text = final_text.replace("<plots 2>", str(plots_list[1]) if len(plots_list) > 1 else "")
                        final_text = final_text.replace("<village>", str(village))
                        final_text = final_text.replace("<LR>", f"{rent_val:.2f}")
                        final_text = final_text.replace("<CESS>", f"{cess_val:.2f}")
                        final_text = final_text.replace("<CONVERSION FEE>", f"{conv_val:.2f}")

                        os_box.clear()
                        os_box.send_keys(final_text)
                        self.log_fwd("✅ Order sheet filled")
                        os_filled = True
                        break

                    except Exception as e:
                        self.log_fwd(f"⚠️ Order sheet attempt {attempt+1} failed: {str(e)[:80]}")

                        # Check for alerts blocking the order sheet
                        try:
                            alert = self.igr_driver.switch_to.alert
                            alert_text = alert.text
                            self.log_fwd(f"   ⚠️ ALERT blocking order sheet: '{alert_text}'")
                            alert.accept()
                            self.log_fwd("   ✅ Clicked OK on blocking alert")
                        except:
                            pass  # No alert

                if not os_filled:
                    self.log_fwd(f"❌ Order sheet failed after 3 attempts")
                    fail_count += 1
                    continue

                # Step 3: Save Order Sheet (both test and real mode)
                try:
                    self.log_fwd("💾 Clicking SAVE ORDER SHEET...")
                    ensure_correct_window()
                    self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btn_submit").click()
                    time.sleep(2)

                    # Handle order sheet save alert (intelligent)
                    try:
                        WebDriverWait(self.igr_driver, 5).until(EC.alert_is_present())
                        alert = self.igr_driver.switch_to.alert
                        alert_text = alert.text
                        self.log_fwd(f"   🔔 Alert after order sheet save: '{alert_text}'")

                        if "Ordersheet Saved" in alert_text or "saved" in alert_text.lower():
                            alert.accept()
                            time.sleep(1)  # Buffer time for page to process alert dismissal
                            self.log_fwd("   ✅ Order sheet saved successfully")
                        else:
                            alert.accept()
                            time.sleep(1)  # Buffer time for page to process alert dismissal
                            self.log_fwd(f"   ⚠️ Unexpected alert: '{alert_text}' - continuing anyway")

                    except TimeoutException:
                        self.log_fwd("   ✓ No alert after order sheet save")
                    except Exception as e:
                        self.log_fwd(f"   ⚠️ Alert error: {str(e)[:80]}")

                    self.log_fwd("✅ Order sheet saved")
                except Exception as e:
                    self.log_fwd(f"❌ Save order sheet failed: {e}")
                    fail_count += 1
                    continue

                # Step 4: Forward to Mutation Officer (BOTH Forward and Reject cases)
                try:
                    type_str = "REJECT" if is_rejection else "FORWARD"
                    self.log_fwd(f"🚀 Clicking FORWARD TO MUTATION OFFICER ({type_str})...")
                    ensure_correct_window()
                    self.igr_driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_Button3").click()
                    time.sleep(2)

                    # Handle forward alert (intelligent)
                    try:
                        WebDriverWait(self.igr_driver, 5).until(EC.alert_is_present())
                        alert = self.igr_driver.switch_to.alert
                        alert_text = alert.text
                        self.log_fwd(f"   🔔 Alert after forward: '{alert_text}'")

                        if "Application Forwarded" in alert_text or "forwarded" in alert_text.lower():
                            alert.accept()
                            time.sleep(1)  # Buffer time for page to process alert dismissal
                            self.log_fwd("   ✅ Application forwarded successfully")
                        else:
                            alert.accept()
                            time.sleep(1)  # Buffer time for page to process alert dismissal
                            self.log_fwd(f"   ⚠️ Unexpected alert: '{alert_text}' - continuing anyway")

                    except TimeoutException:
                        self.log_fwd("   ✓ No alert after forward")
                    except Exception as e:
                        self.log_fwd(f"   ⚠️ Alert error: {str(e)[:80]}")

                    # Verify we're back on search page
                    time.sleep(2)
                    if "Onlinecasesfromtah.aspx" in self.igr_driver.current_url:
                        self.log_fwd("   ✅ Returned to search page")
                    else:
                        self.log_fwd(f"   ⚠️ Unexpected page: {self.igr_driver.current_url}")

                    self.log_fwd(f"✅ {type_str} FORWARDED to mutation officer")
                    success_count += 1

                    # Track result
                    self.batch_results.append({
                        "case_no": case_no,
                        "type": "Reject" if is_rejection else "Forward",
                        "status": "Success",
                        "error": "",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                except Exception as e:
                    self.log_fwd(f"❌ Forward failed: {e}")
                    fail_count += 1

                    # Track result
                    self.batch_results.append({
                        "case_no": case_no,
                        "type": "Reject" if is_rejection else "Forward",
                        "status": "Failed",
                        "error": str(e)[:100],
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

            except Exception as e:
                self.log_fwd(f"❌ Unhandled Error: {e}")
                fail_count += 1

                # Track result
                self.batch_results.append({
                    "case_no": case_no if 'case_no' in locals() else "Unknown",
                    "type": "Reject" if is_rejection else "Forward",
                    "status": "Failed",
                    "error": str(e)[:100],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        self.log_fwd("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log_fwd(f"🏁 BATCH COMPLETE. Success: {success_count}, Failed: {fail_count}")

        # Send telemetry usage event
        if TELEMETRY_AVAILABLE:
            try:
                # Count forward vs reject based on is_rejection flag
                fwd_count = sum(1 for r in self.batch_results if r.get('type') == 'Forward' and r.get('status') == 'Success')
                rej_count = sum(1 for r in self.batch_results if r.get('type') == 'Reject' and r.get('status') == 'Success')
                send_usage_event(fwd_count, rej_count)
            except Exception as e:
                print(f"Telemetry error: {e}")

    def export_batch_results(self):
        """Export batch processing results to Excel file."""
        if not hasattr(self, 'batch_results') or not self.batch_results:
            messagebox.showinfo("Export", "No batch results to export. Run a batch first.")
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment

            # Create workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Batch Results"

            # Headers
            headers = ["Case No", "Type", "Status", "Error", "Timestamp"]
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Data rows
            success_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            fail_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

            for row_idx, result in enumerate(self.batch_results, 2):
                ws.cell(row=row_idx, column=1, value=result.get("case_no", ""))
                ws.cell(row=row_idx, column=2, value=result.get("type", ""))
                ws.cell(row=row_idx, column=3, value=result.get("status", ""))
                ws.cell(row=row_idx, column=4, value=result.get("error", ""))
                ws.cell(row=row_idx, column=5, value=result.get("timestamp", ""))

                # Color code rows
                fill = success_fill if result.get("status") == "Success" else fail_fill
                for col in range(1, 6):
                    ws.cell(row=row_idx, column=col).fill = fill

            # Adjust column widths
            ws.column_dimensions['A'].width = 15
            ws.column_dimensions['B'].width = 10
            ws.column_dimensions['C'].width = 10
            ws.column_dimensions['D'].width = 50
            ws.column_dimensions['E'].width = 20

            # Summary row
            summary_row = len(self.batch_results) + 3
            success_count = sum(1 for r in self.batch_results if r.get("status") == "Success")
            fail_count = sum(1 for r in self.batch_results if r.get("status") == "Failed")

            ws.cell(row=summary_row, column=1, value="SUMMARY:")
            ws.cell(row=summary_row, column=1).font = Font(bold=True)
            ws.cell(row=summary_row + 1, column=1, value=f"Total: {len(self.batch_results)}")
            ws.cell(row=summary_row + 2, column=1, value=f"Success: {success_count}")
            ws.cell(row=summary_row + 3, column=1, value=f"Failed: {fail_count}")

            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"batch_results_{timestamp}.xlsx"

            filepath = filedialog.asksaveasfilename(
                title="Save Batch Results",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=default_filename,
                initialdir=AppPaths.EXPORTS_DIR
            )

            if filepath:
                wb.save(filepath)
                self.log_fwd(f"📊 Exported {len(self.batch_results)} results to: {filepath}")
                messagebox.showinfo("Export", f"Batch results exported successfully!\n\n{filepath}")

                # Clear results after export (optional - ask user?)
                if messagebox.askyesno("Clear Results", "Clear batch results from memory?"):
                    self.batch_results = []
                    self.log_fwd("🗑️ Batch results cleared from memory")

        except ImportError:
            messagebox.showerror("Export Error", "openpyxl library not installed.\nRun: pip install openpyxl")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")
            self.log_fwd(f"❌ Export failed: {e}")

    def create_log_tab(self):
        """Create the Status Log tab content."""
        # Header
        log_header = ctk.CTkFrame(self.tab_log, fg_color="transparent")
        log_header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(log_header, text="📋 STATUS LOG", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        ctk.CTkButton(log_header, text="🗑️ Clear Log", width=100, height=28, fg_color="transparent", border_width=1, border_color=COLORS["border_subtle"], command=self.clear_log).pack(side="right")
        
        # Log text area (LARGE)
        self.log_text = ctk.CTkTextbox(
            self.tab_log, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["bg_dark"], text_color=COLORS["accent_cyan"],
            border_width=1, border_color=COLORS["border_subtle"], corner_radius=10
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def browse_excel(self):
        """Browse for existing Excel file."""
        filepath = filedialog.askopenfilename(
            title="Select Excel file to resume",
            filetypes=[("Excel files", "*.xlsx")],
            initialdir=AppPaths.EXPORTS_DIR
        )
        if filepath:
            self.selected_excel_path = filepath
            self.excel_path_label.configure(text=os.path.basename(filepath))
            self.file_option.set("resume")
    
    def stop_extraction(self):
        """Stop the extraction process."""
        if self.automation:
            self.automation.stop_extraction = True
            self.log("🛑 Stop requested... finishing current case...")
            self.stop_btn.configure(state="disabled")
    
    # ==================== SETUP TAB METHODS ====================
    
    def calculate_valuation_plot(self, plot_no):
        """Calculate valuation plot number from original plot number.
        
        Rules:
        - If plot has comma (64,66) -> keep all parts: "64, 66"
        - If plot has / (189/3054) -> take first part only: "189"
        - If plot has multiple / (189/67/76) -> take first part: "189"
        - Apply / rule to each comma-separated part
        """
        if not plot_no or plot_no == "N/A":
            return "N/A"
        
        # Split by comma first
        parts = [p.strip() for p in plot_no.split(",")]
        
        valuation_parts = []
        for part in parts:
            # If part contains /, take only first segment
            if "/" in part:
                valuation_parts.append(part.split("/")[0].strip())
            else:
                valuation_parts.append(part.strip())
        
        return ", ".join(valuation_parts)
    
    def browse_forward_excel(self, path=None):
        """Browse or Load Excel file."""
        if path:
            filepath = path
        else:
            filepath = filedialog.askopenfilename(
                title="Select Excel file with Action column",
                filetypes=[("Excel files", "*.xlsx")],
                initialdir=AppPaths.EXPORTS_DIR
            )
            
        if filepath:
            self.fwd_excel_path = filepath
            self.fwd_excel_label.configure(text=os.path.basename(filepath))
            # Force redraw to ensure "No file selected" disappears immediately
            self.fwd_excel_label.update()
            
            # Auto-detect if manually browsed
            if not path:
                self.detect_cases()
                # Load Reject cases from Setup tab if not found in loaded Excel
                if hasattr(self, 'setup_reject_cases') and self.setup_reject_cases:
                    if not hasattr(self, 'reject_cases_grouped') or not self.reject_cases_grouped:
                        self.reject_cases_grouped = list(self.setup_reject_cases)
                        self.reject_cases = list(self.setup_reject_cases)
                        self.log(f"✅ Loaded {len(self.reject_cases_grouped)} Reject cases from Setup tab")
                        if hasattr(self, 'populate_reject_list'):
                            self.populate_reject_list()

    def detect_cases(self):
        """Detect Forward and Reject cases from Excel."""
        if not hasattr(self, 'fwd_excel_path') or not self.fwd_excel_path:
            messagebox.showerror("Error", "Please select an Excel file first!")
            return
        
        try:
            from openpyxl import load_workbook
            
            wb = load_workbook(self.fwd_excel_path)
            sheet = wb.active
            
            self.forward_cases = []
            self.reject_cases = []
            self.all_cases = []
            
            # Grouped lists for UI (Unique Cases)
            self.forward_cases_grouped = []
            self.reject_cases_grouped = []
            
            # Tracking sets for uniqueness
            seen_fwd = set()
            seen_rej = set()
            
            # Get headers from first row
            headers = [cell.value for cell in sheet[1]]
            
            # Find columns
            case_col = None
            name_col = None
            mouza_col = None
            village_col = None
            plot_col = None
            action_col = len(headers) - 1 # Auto-detect last column if possible, or search 'Action'
            
            # Valuation Columns (Optional)
            rent_col = None
            cess_col = None
            conv_col = None
            bench_col = None
            mv_col = None
            
            area_col = 6 # Default
            
            for i, h in enumerate(headers):
                if not h: continue
                h_lower = str(h).lower()
                if "case" in h_lower: case_col = i
                if "applicant" in h_lower: name_col = i
                if "mouza" in h_lower: mouza_col = i
                if "village" in h_lower and "english" in h_lower: village_col = i
                if "plot" in h_lower and "valuation" not in h_lower: plot_col = i
                if "action" in h_lower: action_col = i
                
                # Check for Valuation Data (improved specificity)
                if "rent" in h_lower or "lease" in h_lower: rent_col = i
                if "cess" in h_lower and "pro" not in h_lower: cess_col = i
                # Match both "Conv Fee" (abbreviated) and "Conversion Fee" (full)
                if "conv" in h_lower and "fee" in h_lower:
                    conv_col = i
                if "benchmark" in h_lower: bench_col = i
                if "market value" in h_lower: mv_col = i

            # Logic for PDF Map Access (Try to load if not in memory)
            pdf_map = getattr(self, 'pdf_map', {})

            self.log(f"ℹ️ Columns Detected: Case={case_col}, Rent={rent_col}, Cess={cess_col}, Conv={conv_col}")

            if case_col is None:
                case_col = 0

            # Helper function for robust float conversion
            def safe_float(val):
                """Convert value to float, handling strings, numbers, and None"""
                if val is None:
                    return 0.0
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    try:
                        # Remove commas and whitespace, then convert
                        return float(val.strip().replace(',', ''))
                    except (ValueError, AttributeError):
                        return 0.0
                return 0.0

            # Process each row (skip header)
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row: continue
                
                # Get action
                action = str(row[action_col] if action_col < len(row) and row[action_col] else "").strip().upper()
                if not action: continue # Skip rows with no action? Or assume Forward? User implied Excel has Action.
                
                case_no = str(row[case_col] if row[case_col] else "").strip()
                name = str(row[name_col] if name_col is not None and row[name_col] else "N/A").strip()
                mouza = str(row[mouza_col] if mouza_col is not None and row[mouza_col] else "N/A").strip()
                village_english = str(row[village_col] if village_col is not None and row[village_col] else "").strip()
                plot_no = str(row[plot_col] if plot_col is not None and row[plot_col] else "N/A").strip()
                area = str(row[area_col] if area_col < len(row) and row[area_col] else "0").strip()
                
                # Valuation Data Reading (using safe_float for robust conversion)
                rent = safe_float(row[rent_col] if rent_col is not None and rent_col < len(row) else None)
                cess = safe_float(row[cess_col] if cess_col is not None and cess_col < len(row) else None)
                conv = safe_float(row[conv_col] if conv_col is not None and conv_col < len(row) else None)
                benchmark = safe_float(row[bench_col] if bench_col is not None and bench_col < len(row) else None)
                # Prefer dedicated Market Value column if it exists
                if mv_col is not None and mv_col < len(row):
                    benchmark = safe_float(row[mv_col])

                # PDF Link
                pdf_target = None
                # Check mapping
                if case_no in pdf_map:
                    pdf_target = pdf_map[case_no]
                # Fallback: Check if user mapped by name? Unlikely.
                
                valuation_plot = self.calculate_valuation_plot(plot_no)
                
                case_data = {
                    "case_no": case_no,
                    "name": name,
                    "mouza": mouza,
                    "plot_no": plot_no,
                    "valuation_plot": valuation_plot,
                    "area": area,
                    "row": row_idx,
                    "pdf_path": pdf_target,
                    "village_english": village_english,
                    "benchmark": benchmark,      # Now populated from Excel
                    "conversion_fee": conv,      # Now populated from Excel
                    "rent": rent,                # Now populated from Excel
                    "cess": cess,                # Now populated from Excel
                    "total": rent + cess + conv,
                    "source": "Excel"
                }
                
                self.all_cases.append(case_data)
                
                if action.startswith("F"):
                    self.forward_cases.append(case_data) 
                    if case_no not in seen_fwd:
                        seen_fwd.add(case_no)
                        self.forward_cases_grouped.append(case_data) # Use first row as representative
                        
                elif action.startswith("R") or "REJECT" in action:
                    self.reject_cases.append(case_data)
                    # Mark as Rejection in case data for easier processing
                    case_data["is_rejection"] = True
                    if case_no not in seen_rej:
                        seen_rej.add(case_no)
                        self.reject_cases_grouped.append(case_data)

            self.log(f"✅ Found {len(self.forward_cases)} Forward cases ({len(self.forward_cases_grouped)} unique)")
            self.log(f"✅ Found {len(self.reject_cases)} Reject cases ({len(self.reject_cases_grouped)} unique)")

            # Store reject cases for Forwarding tab (only if found - don't overwrite Setup tab data)
            if self.reject_cases_grouped:
                self.setup_reject_cases = list(self.reject_cases_grouped)

            # Update UI Lists
            if hasattr(self, 'populate_forward_list'):
                self.populate_forward_list()
            if hasattr(self, 'populate_reject_list'):
                self.populate_reject_list()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel: {e}")
            self.log(f"❌ Error reading Excel: {e}")
            
        finally:
            if 'wb' in locals():
                wb.close()
            
            # Update Setup Tab UI Labels (if they exist)
            if hasattr(self, 'fwd_count_label'):
                self.fwd_count_label.configure(text=f"{len(getattr(self, 'forward_cases_grouped', []))} unique cases")
            if hasattr(self, 'rej_count_label'):
                self.rej_count_label.configure(text=f"{len(getattr(self, 'reject_cases_grouped', []))} unique cases")
            
            # Update Forwarding Tab Lists
            if hasattr(self, 'populate_forward_list'):
                self.populate_forward_list()
            if hasattr(self, 'populate_reject_list'):
                self.populate_reject_list()

            # Populate Setup Tab Textboxes with Simple List of Case Numbers
            if hasattr(self, 'fwd_cases_text') and hasattr(self, 'forward_cases_grouped'):
                self.fwd_cases_text.delete("1.0", "end")
                for i, case in enumerate(self.forward_cases_grouped, 1):
                    self.fwd_cases_text.insert("end", f"{i}. {case['case_no']}\n")

            if hasattr(self, 'setup_rej_cases_text') and hasattr(self, 'reject_cases_grouped'):
                self.setup_rej_cases_text.delete("1.0", "end")
                for i, case in enumerate(self.reject_cases_grouped, 1):
                    self.setup_rej_cases_text.insert("end", f"{i}. {case['case_no']}\n")

            # PRESERVE PDF mappings if they exist from previous Setup tab work
            if hasattr(self, 'pdf_dropdowns_fwd') and self.pdf_dropdowns_fwd:
                # We have existing PDF mappings - restore them to newly loaded cases
                old_pdf_map = {}
                for case_no, widgets in self.pdf_dropdowns_fwd.items():
                    pdf_name = widgets["var"].get()
                    if pdf_name != "(No PDF selected)":
                        # Find the full path from available PDFs
                        for pdf_path in getattr(self, 'available_pdfs_fwd', []):
                            if os.path.basename(pdf_path) == pdf_name:
                                old_pdf_map[case_no] = pdf_path
                                break

                # Apply preserved PDF paths to newly loaded cases
                for case in self.forward_cases_grouped:
                    if case["case_no"] in old_pdf_map:
                        case["pdf_path"] = old_pdf_map[case["case_no"]]

                self.log(f"✅ Restored {len(old_pdf_map)} PDF mappings from Setup tab")

            # Clear PDF mapping

    
    def process_uploaded_pdfs(self, title_msg):
        """Generic helper to browse and process PDFs (compress/size check)."""
        filepaths = filedialog.askopenfilenames(
            title=title_msg,
            filetypes=[("PDF files", "*.pdf")],
            initialdir=AppPaths.EXPORTS_DIR
        )
        
        if not filepaths:
            return None, None
            
        self.log("")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log(f"📄 PROCESSING PDFs for {'Forward' if 'Forward' in title_msg else 'Reject'}")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Check compression method
        method = get_compression_method()
        if method:
            self.log(f"🗜️ Compression method: {method}")
        else:
            self.log("⚠️ No compression method available!")
            self.log("   Large PDFs will not be compressed.")
        self.log(f"📏 Size limit: {PDF_MAX_SIZE_KB}KB")
        self.log("")
        
        # Process each PDF - check size and compress if needed
        processed_pdfs = []
        compression_results = []
        
        for pdf_path in filepaths:
            pdf_name = os.path.basename(pdf_path)
            size_kb = get_file_size_kb(pdf_path)
            
            if size_kb <= PDF_MAX_SIZE_KB:
                # PDF is within limit
                processed_pdfs.append(pdf_path)
                compression_results.append({
                    "name": pdf_name,
                    "original_size": size_kb,
                    "final_size": size_kb,
                    "compressed": False,
                    "path": pdf_path
                })
                self.log(f"✅ {pdf_name}: {size_kb:.1f}KB (OK)")
            else:
                # PDF needs compression
                self.log(f"⚠️ {pdf_name}: {size_kb:.1f}KB > {PDF_MAX_SIZE_KB}KB - Compressing...")
                
                # Create compressed filename
                compressed_name = f"compressed_{pdf_name}"
                compressed_path = os.path.join(COMPRESSED_PDF_FOLDER, compressed_name)
                
                # Compress the PDF
                success = compress_pdf(pdf_path, compressed_path)
                
                if success and os.path.exists(compressed_path):
                    new_size_kb = get_file_size_kb(compressed_path)
                    
                    if new_size_kb <= PDF_MAX_SIZE_KB:
                        processed_pdfs.append(compressed_path)
                        compression_results.append({
                            "name": pdf_name,
                            "original_size": size_kb,
                            "final_size": new_size_kb,
                            "compressed": True,
                            "path": compressed_path
                        })
                        reduction = ((size_kb - new_size_kb) / size_kb) * 100
                        self.log(f"   ✅ Compressed: {size_kb:.1f}KB → {new_size_kb:.1f}KB ({reduction:.0f}% reduced)")
                    else:
                        # Still too large after compression
                        self.log(f"   ❌ Still too large after compression: {new_size_kb:.1f}KB")
                        self.log(f"   ⚠️ WARNING: {pdf_name} is {new_size_kb:.1f}KB (>{PDF_MAX_SIZE_KB}KB limit) - May fail upload!")
                        compression_results.append({
                            "name": pdf_name,
                            "original_size": size_kb,
                            "final_size": new_size_kb,
                            "compressed": True,
                            "path": compressed_path,
                            "still_large": True
                        })
                        processed_pdfs.append(compressed_path)  # Use anyway, user can decide
                else:
                    # Compression failed
                    self.log(f"   ❌ Compression failed! Using original.")
                    self.log(f"      (Is Ghostscript installed? Install from https://ghostscript.com)")
                    processed_pdfs.append(pdf_path)
                    compression_results.append({
                        "name": pdf_name,
                        "original_size": size_kb,
                        "final_size": size_kb,
                        "compressed": False,
                        "failed": True,
                        "path": pdf_path
                    })
        
        return processed_pdfs, compression_results

    def browse_pdfs_forward(self):
        """Browse for Forward PDFs."""
        if not self.forward_cases_grouped:
            messagebox.showwarning("Warning", "Please detect cases first!")
            return
            
        processed, results = self.process_uploaded_pdfs("Select PDF files for Forward cases")
        if processed is None:
            return
            
        # Store available PDFs
        self.available_pdfs_fwd = processed
        self.pdf_count_label_fwd.configure(text=f"{len(processed)} PDFs ready")
        
        # Display list
        self.update_common_log(results)
        
        # Update mapping
        self.update_pdf_mapping() # Default Fwd logic
        
    def browse_pdfs_reject(self):
        """Browse for Reject PDFs."""
        if not self.reject_cases_grouped:
            messagebox.showwarning("Warning", "Please detect cases first!")
            return
            
        processed, results = self.process_uploaded_pdfs("Select PDF files for Reject cases")
        if processed is None:
            return
            
        # Store available PDFs
        self.available_pdfs_rej = processed
        self.pdf_count_label_rej.configure(text=f"{len(processed)} PDFs ready")
        
        # Display list
        self.update_common_log(results)
        
        # Update mapping
        self.update_reject_pdf_mapping()
        
    def update_common_log(self, compression_results):
        """Update the common PDF log text box."""
        self.pdf_list_text.delete("1.0", "end")
        for result in compression_results:
            name = result["name"]
            if result.get("compressed"):
                status = f"🗜️ {result['original_size']:.0f}KB→{result['final_size']:.0f}KB"
            else:
                status = f"✅ {result['final_size']:.0f}KB"
            self.pdf_list_text.insert("end", f"• {name} {status}\n")

    def find_matching_pdf(self, case_no, available_pdfs):
            """Try to find matching PDF with flexible matching."""
            # Try exact match: 1000/25 -> 1000-25.pdf
            expected1 = case_no.replace("/", "-") + ".pdf"
            # Try without year: 1000/25 -> 1000.pdf
            expected2 = case_no.split("/")[0] + ".pdf" if "/" in case_no else None
            # Try with underscore: 1000/25 -> 1000_25.pdf
            expected3 = case_no.replace("/", "_") + ".pdf"
            
            for pdf_path in available_pdfs:
                pdf_name = os.path.basename(pdf_path).lower()
                if pdf_name == expected1.lower():
                    return pdf_path
                if expected2 and pdf_name == expected2.lower():
                    return pdf_path
                if pdf_name == expected3.lower():
                    return pdf_path
                # Partial match: if case number is in filename
                case_num = case_no.split("/")[0] if "/" in case_no else case_no
                if case_num in pdf_name:
                    return pdf_path
            return None
            
            # Store available PDFs (processed versions)
            self.available_pdfs = processed_pdfs
            self.pdf_count_label.configure(text=f"{len(processed_pdfs)} PDFs ready")
            
            # Display PDF list with sizes
            self.pdf_list_text.delete("1.0", "end")
            for result in compression_results:
                name = result["name"]
                if result.get("compressed"):
                    status = f"🗜️ {result['original_size']:.0f}KB→{result['final_size']:.0f}KB"
                else:
                    status = f"✅ {result['final_size']:.0f}KB"
                self.pdf_list_text.insert("end", f"• {name} {status}\n")
            
            self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log("")
            
            # Update mapping with dropdowns
            self.update_pdf_mapping()
    
    def update_pdf_mapping(self):
        """Create dropdown mappings for each Forward case (Grouped/Unique)."""
        # Clear existing dropdowns for Fwd
        for widget in self.mapping_scroll_frame_fwd.winfo_children():
            widget.destroy()
        self.pdf_dropdowns_fwd = {}
        
        # PDF names for dropdown
        pdf_names = ["(No PDF selected)"] + [os.path.basename(p) for p in self.available_pdfs_fwd]
        
        # Create a row for each Unique Forward case
        for i, case in enumerate(self.forward_cases_grouped):
            case_no = case["case_no"]
            name = case["name"][:25]
            
            row_frame = ctk.CTkFrame(self.mapping_scroll_frame_fwd, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            # Case info label
            ctk.CTkLabel(row_frame, text=f"{case_no} - {name}", font=ctk.CTkFont(size=11), width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text="→", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
            
            # Dropdown
            pdf_var = StringVar(value="(No PDF selected)")
            
            # Try auto-match
            matched_pdf = self.find_matching_pdf(case_no, self.available_pdfs_fwd)
            if matched_pdf:
                pdf_var.set(os.path.basename(matched_pdf))
                case["pdf_path"] = matched_pdf
            else:
                case["pdf_path"] = None
            
            dropdown = ctk.CTkComboBox(
                row_frame, values=pdf_names, variable=pdf_var, width=250, font=ctk.CTkFont(size=10),
                command=lambda val, c=case: self.on_pdf_change_fwd(val, c)
            )
            dropdown.pack(side="left", padx=5)
            
            # Status
            status_label = ctk.CTkLabel(row_frame, text="✅" if matched_pdf else "❌", font=ctk.CTkFont(size=12), width=30)
            status_label.pack(side="left", padx=5)
            
            self.pdf_dropdowns_fwd[case_no] = {"dropdown": dropdown, "var": pdf_var, "status": status_label}
        
        # Log status
        matched_count = sum(1 for c in self.forward_cases_grouped if c["pdf_path"])
        total_count = len(self.forward_cases_grouped)
        self.log(f"📎 Auto-matched {matched_count}/{total_count} Forward cases.")

    def update_reject_pdf_mapping(self):
        """Create dropdown mappings for each Reject case (Grouped/Unique)."""
        # Clear existing dropdowns for Rej
        for widget in self.mapping_scroll_frame_rej.winfo_children():
            widget.destroy()
        self.pdf_dropdowns_rej = {}
        
        # PDF names
        pdf_names = ["(No PDF selected)"] + [os.path.basename(p) for p in self.available_pdfs_rej]
        
        # Create row for each Unique Reject case
        for i, case in enumerate(self.reject_cases_grouped):
            case_no = case["case_no"]
            name = case["name"][:25]
            
            row_frame = ctk.CTkFrame(self.mapping_scroll_frame_rej, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row_frame, text=f"{case_no} - {name}", font=ctk.CTkFont(size=11), width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text="→", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
            
            pdf_var = StringVar(value="(No PDF selected)")
            matched_pdf = self.find_matching_pdf(case_no, self.available_pdfs_rej)
            
            if matched_pdf:
                pdf_var.set(os.path.basename(matched_pdf))
                case["pdf_path"] = matched_pdf
            else:
                case["pdf_path"] = None
            
            dropdown = ctk.CTkComboBox(
                row_frame, values=pdf_names, variable=pdf_var, width=250, font=ctk.CTkFont(size=10),
                command=lambda val, c=case: self.on_pdf_change_rej(val, c)
            )
            dropdown.pack(side="left", padx=5)
            
            status_label = ctk.CTkLabel(row_frame, text="✅" if matched_pdf else "❌", font=ctk.CTkFont(size=12), width=30)
            status_label.pack(side="left", padx=5)
            
            self.pdf_dropdowns_rej[case_no] = {"dropdown": dropdown, "var": pdf_var, "status": status_label}
            
        matched_count = sum(1 for c in self.reject_cases_grouped if c["pdf_path"])
        total_count = len(self.reject_cases_grouped)
        self.log(f"📎 Auto-matched {matched_count}/{total_count} Reject cases.")

    def on_pdf_change_fwd(self, value, case):
        """Handle Forward dropdown change."""
        self._handle_pdf_change(value, case, self.available_pdfs_fwd, self.pdf_dropdowns_fwd)

    def on_pdf_change_rej(self, value, case):
        """Handle Reject dropdown change."""
        self._handle_pdf_change(value, case, self.available_pdfs_rej, self.pdf_dropdowns_rej)

    def _handle_pdf_change(self, value, case, available_pdfs, dropdowns):
        """Generic handler."""
        case_no = case["case_no"]
        if value == "(No PDF selected)":
            case["pdf_path"] = None
            if case_no in dropdowns:
                dropdowns[case_no]["status"].configure(text="❌")
        else:
            for pdf_path in available_pdfs:
                if os.path.basename(pdf_path) == value:
                    case["pdf_path"] = pdf_path
                    if case_no in dropdowns:
                        dropdowns[case_no]["status"].configure(text="✅")
                    break

    def confirm_forward_reject(self):
        """Confirm selections, sync to flat lists, and proceed."""
        if not self.forward_cases_grouped and not self.reject_cases_grouped:
            messagebox.showwarning("Warning", "No cases detected!")
            return
        
        # 1. Validate Forward Cases
        fwd_with_pdf = [c for c in self.forward_cases_grouped if c.get("pdf_path")]
        fwd_without_pdf = [c for c in self.forward_cases_grouped if not c.get("pdf_path")]
        
        if fwd_without_pdf:
            missing_msg = f"{len(fwd_without_pdf)} Forward cases don't have PDFs assigned:\n"
            for c in fwd_without_pdf[:5]:
                missing_msg += f"  • {c['case_no']}\n"
            if len(fwd_without_pdf) > 5:
                missing_msg += f"  ... and {len(fwd_without_pdf) - 5} more\n"
            missing_msg += "\nThese will be SKIPPED from Valuation. Continue?"
            if not messagebox.askyesno("Warning", missing_msg):
                return
        
        # 2. Sync Logic - Filter Flat List based on Grouped selection
        valid_fwd_nos = set(c["case_no"] for c in fwd_with_pdf)
        final_forward_cases = [] # New flat list
        
        # Map case_no -> pdf_path for fast lookup
        fwd_pdf_map = {c["case_no"]: c["pdf_path"] for c in fwd_with_pdf}
        
        for flat_case in self.forward_cases:
            c_no = flat_case["case_no"]
            if c_no in valid_fwd_nos:
                # Sync PDF path
                flat_case["pdf_path"] = fwd_pdf_map[c_no]
                final_forward_cases.append(flat_case)
        
        # Update the main flat list
        self.forward_cases = final_forward_cases
        
        # 3. Reject Sync (Optional, but good for records)
        rej_with_pdf = [c for c in self.reject_cases_grouped if c.get("pdf_path")]
        rej_pdf_map = {c["case_no"]: c["pdf_path"] for c in rej_with_pdf}
        for flat_case in self.reject_cases:
            c_no = flat_case["case_no"]
            if c_no in rej_pdf_map:
                flat_case["pdf_path"] = rej_pdf_map[c_no]
        
        # Confirmation
        msg = f"Ready to process:\n\n"
        msg += f"🟢 FORWARD: {len(self.forward_cases)} plot rows (from {len(valid_fwd_nos)} unique cases)\n"
        if fwd_without_pdf:
            msg += f"⚠️ SKIPPED: {len(fwd_without_pdf)} unique Forward cases (no PDF)\n"
        msg += f"🔴 REJECT: {len(self.reject_cases)} plot rows (uploaded {len(rej_with_pdf)} PDFs)\n\n"
        msg += "Proceed to Phase 2 (Valuation Check)?"
        
        if messagebox.askyesno("Confirm", msg):
            self.log("")
            self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log("✅ PHASE 1 COMPLETE!")
            self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log(f"   Forward: {len(self.forward_cases)} cases ready")
            for c in self.forward_cases:
                self.log(f"     • {c['case_no']} → {os.path.basename(c['pdf_path'])}")
            self.log(f"   Reject: {len(self.reject_cases)} cases ready")
            for c in self.reject_cases:
                self.log(f"     • {c['case_no']}")
            self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log("")
            self.log("📋 Ready for Phase 2: Valuation Check")
            self.log("   Go to Valuation tab to proceed")
            
            # Switch to Valuation tab
            self.tabview.set("🔍 Valuation")
    
    # ==================== VALUATION TAB METHODS ====================
    
    def load_valuation_data(self):
        """Load case data from Setup tab into Valuation tab display."""
        if not self.forward_cases:
            messagebox.showwarning("Warning", "No data found! Please complete Setup tab first:\n1. Upload Excel\n2. Detect Cases\n3. Upload PDFs")
            return
        
        # Update summary
        self.valuation_summary.configure(
            text=f"📊 Forward: {len(self.forward_cases)} | Reject: {len(self.reject_cases)}"
        )
        
        # Clear existing table rows
        for widget in self.valuation_table.winfo_children():
            widget.destroy()
        
        # Also create village mapping dropdowns
        self.create_village_mapping_ui()
        
        # Populate table with forward cases
        for i, case in enumerate(self.forward_cases):
            row_bg = COLORS["bg_dark"] if i % 2 == 0 else COLORS["bg_card"]
            row_frame = ctk.CTkFrame(self.valuation_table, fg_color=row_bg, height=30)
            row_frame.pack(fill="x", pady=1)
            row_frame.pack_propagate(False)
            
            ctk.CTkLabel(row_frame, text=case.get("case_no", "N/A")[:10], width=80, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=case.get("mouza", "N/A")[:12], width=100, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=case.get("village_english", "-")[:12] if case.get("village_english") else "-", width=100, font=ctk.CTkFont(size=9), anchor="w", text_color=COLORS["accent_cyan"]).pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=case.get("plot_no", "N/A")[:10], width=80, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=case.get("valuation_plot", "N/A")[:8], width=60, font=ctk.CTkFont(size=9), anchor="w", text_color=COLORS["accent_green"]).pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=case.get("area", "0")[:6], width=50, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("benchmark", "-"))[:10] if case.get("benchmark") else "-", width=80, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("conversion_fee", "-"))[:8] if case.get("conversion_fee") else "-", width=70, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("total", "-"))[:8] if case.get("total") else "-", width=70, font=ctk.CTkFont(size=9), anchor="w", text_color=COLORS["accent_orange"]).pack(side="left", padx=3)
        
        self.log(f"✅ Loaded {len(self.forward_cases)} cases into Valuation tab")
    
    def create_village_mapping_ui(self):
        """Create UI for mapping Odia Mouza to English Village names with search."""
        # Clear existing
        for widget in self.village_mapping_frame.winfo_children():
            widget.destroy()
        self.village_dropdowns = {}
        
        # Get unique Mouza names from forward cases
        unique_mouzas = list(set(c.get("mouza", "") for c in self.forward_cases if c.get("mouza") and c.get("mouza") != "N/A"))
        
        if not unique_mouzas:
            ctk.CTkLabel(self.village_mapping_frame, text="No Mouza data found. Load data from Setup first.", text_color=COLORS["text_secondary"]).pack(pady=20)
            return
        
        # Create dropdown for each unique Mouza with search
        village_options = ["(Select Village)"] + self.villages_list if self.villages_list else ["(Pull villages first)"]
        
        for mouza in unique_mouzas:
            row = ctk.CTkFrame(self.village_mapping_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            ctk.CTkLabel(row, text=mouza[:20], width=150, font=ctk.CTkFont(size=10), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text="→", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
            
            # Search entry for filtering
            search_var = StringVar()
            search_entry = ctk.CTkEntry(row, width=100, placeholder_text="Type to search...", font=ctk.CTkFont(size=9), textvariable=search_var)
            search_entry.pack(side="left", padx=2)
            
            # Dropdown
            dropdown_var = StringVar(value=self.village_mappings.get(mouza, "(Select Village)"))
            dropdown = ctk.CTkComboBox(row, values=village_options, variable=dropdown_var, width=180, font=ctk.CTkFont(size=10))
            dropdown.pack(side="left", padx=2)
            
            # Bind search to filter dropdown
            def on_search_change(event, dd=dropdown, sv=search_var, opts=self.villages_list):
                search_text = sv.get().lower()
                if search_text and len(search_text) >= 2:
                    filtered = ["(Select Village)"] + [v for v in opts if v.lower().startswith(search_text)]
                    dd.configure(values=filtered if filtered else ["(No match)"])
                else:
                    dd.configure(values=["(Select Village)"] + opts)
            
            search_entry.bind("<KeyRelease>", on_search_change)
            
            self.village_dropdowns[mouza] = {"dropdown": dropdown, "var": dropdown_var, "search": search_var}
        self.mapping_status.configure(text=f"📊 Villages: {len(self.villages_list)} loaded | Mouza: {len(unique_mouzas)} to map")
    
    def go_valuation_check(self):
        """Start valuation check automation."""
        if not self.forward_cases:
            messagebox.showwarning("Warning", "No cases loaded! Click 'Load Data from Setup' first.")
            return
        
        # Check if village mappings are confirmed
        unmapped = [c for c in self.forward_cases if not c.get("village_english")]
        if unmapped:
            messagebox.showwarning("Warning", f"{len(unmapped)} cases don't have village mapping!\n\nPlease confirm village mapping first.")
            return
        
        if not self.igr_driver:
            messagebox.showwarning("Warning", "Please open IGR website first!")
            return
        
        # Confirm start
        if not messagebox.askyesno("Start Valuation Check", f"Start valuation check for {len(self.forward_cases)} cases?\n\nThis will:\n1. Select village for each case\n2. Enter area\n3. Get benchmark value\n4. Calculate fees"):
            return
        
        
        # CAPTURE REFRESH STATE SAFELY
        self.force_refresh_active = self.refresh_cache_var.get()
        if self.force_refresh_active:
             self.log("⚠️ FORCE REFRESH ENABLED: Scraper will bypass cache.")
        
        # Run in thread
        threading.Thread(target=self.run_valuation_check, daemon=True).start()
    
    def go_retry_failures(self):
        """Retry only the cases that failed (benchmark 0 or None)."""
        if not self.forward_cases:
            messagebox.showwarning("Warning", "No cases loaded.")
            return
            
        # Filter Failures
        failures = [c for c in self.forward_cases if not c.get("benchmark") or c.get("benchmark") == 0]
        
        if not failures:
            messagebox.showinfo("Info", "No failed cases found to retry! All cases have benchmarks.")
            return
            
        if not messagebox.askyesno("Retry Failures", f"Found {len(failures)} cases with 0/missing value.\n\nRetry these cases now?"):
            return
            
        # Clear existing errors on these cases to start fresh (optional)
        # But crucially, we pass this list to run_valuation_check
        
        # Check refresh state
        # Check refresh state - FORCE TRUE FOR RETRY
        self.refresh_cache_var.set(True) # Auto-check the UI box
        self.force_refresh_active = True
        
        threading.Thread(target=self.run_valuation_check, args=(failures,), daemon=True).start()
    
    def run_valuation_check(self, cases_to_process=None):
        """Execute the valuation check automation (Refactored for Robustness & Retry)."""
        
        # Determine scope
        target_cases = cases_to_process if cases_to_process is not None else self.forward_cases
        is_retry = cases_to_process is not None
        
        self.log("")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log(f"🔍 VALUATION { 'RETRY' if is_retry else 'CHECK' } STARTED (Rows: {len(target_cases)})")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 1. Sort Target Cases (Village -> CaseNo)
        target_cases.sort(key=lambda x: (x.get("village_english", ""), x.get("case_no", "")))
        
        # [REMOVED] Refresh logic (User Request) to preserve District/RO
        # if is_retry: ... (removed)
        
        # Group cases by village for efficiency
        cases_by_village = {}
        for case in target_cases:
            village = case.get("village_english", "")
            if village not in cases_by_village:
                cases_by_village[village] = []
            cases_by_village[village].append(case)
        
        self.log(f"📊 Processing {len(target_cases)} rows in {len(cases_by_village)} villages")
        
        completed = 0
        errors = 0
        last_benchmark_val = 0 # For Double-Check Logic
        
        try:
            from selenium.webdriver.support.ui import Select
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time
            
            for village, cases in cases_by_village.items():
                self.log(f"\n🏘️ Processing village: {village} ({len(cases)} rows)")
                
                try:
                    # Select village in dropdown
                    village_dropdown = WebDriverWait(self.igr_driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="ContentPlaceHolder1_ddlvillage"]'))
                    )
                    village_select = Select(village_dropdown)
                    
                    # SOFT RESET / WAKE UP (For Retry or First Run)
                    # If the form is stagnant, selecting the *same* village might not trigger the update.
                    # Strategy: Select Index 1 (if available and not target), wait, then select Target.
                    if is_retry:
                        try:
                            # Wake up the form
                            if len(village_select.options) > 1:
                                dummy_opt = village_select.options[1].text
                                if dummy_opt != village:
                                    self.log(f"   💤 Waking up form with '{dummy_opt}'...")
                                    village_select.select_by_index(1) 
                                    time.sleep(2)
                                    # Handle alert if any
                                    try: self.igr_driver.switch_to.alert.accept()
                                    except: pass
                        except Exception as wake_err:
                            self.log(f"   ⚠️ Wake up attempt failed: {wake_err}")
                            
                    # Capture OLD plot element to detect refresh
                    try:
                        old_plot_dd = self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_DdlPlot"]')
                    except:
                        old_plot_dd = None

                    # Select ACTUAL Village
                    village_select.select_by_visible_text(village)
                    
                    # Wait for STALENESS + NEW LOAD
                    if old_plot_dd:
                        try:
                            WebDriverWait(self.igr_driver, 10).until(EC.staleness_of(old_plot_dd))
                        except: pass
                    
                    # Wait for new plots to load
                    WebDriverWait(self.igr_driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="ContentPlaceHolder1_DdlPlot"]/option[2]'))
                    )
                    
                    # Safety buffer for options population
                    time.sleep(1.5)

                    self.log(f"   📍 Village Ready: {village}")
                    
                    # Get available plots for this village (Cached)
                    plot_dropdown = self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_DdlPlot"]')
                    available_plots = self.get_village_plots(village, plot_dropdown)
                    
                    # Process each case row in this village
                    for case in cases:
                        try:
                            # CRITICAL: Reset per-row variables
                            benchmark = 0
                            selected_plot = ""
                            
                            c_no = case.get("case_no", "")
                            val_plot = str(case.get("valuation_plot", "")).strip()
                            area = str(case.get("area", "")).strip()
                            
                            self.log(f"      👉 Case {c_no} | Plot: {val_plot} | Area: {area}")
                            
                            if not val_plot or not area:
                                self.log(f"      ⚠️ Missing plot/area")
                                errors += 1
                                continue

                            # Select Plot Logic (Unified ID)
                            plot_select = Select(self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_DdlPlot"]'))
                            plot_found = False
                            
                            # 1. Try exact match
                            if val_plot in available_plots:
                                plot_select.select_by_visible_text(val_plot)
                                plot_found = True
                                selected_plot = val_plot
                            else:
                                # 2. Try partial match
                                for opt in available_plots:
                                    if val_plot in opt:
                                        plot_select.select_by_visible_text(opt)
                                        plot_found = True
                                        selected_plot = opt
                                        break
                                    # Handle "101" finding "101/22"
                                    # Split opt byspace or /
                                    opt_parts = opt.replace('/', ' ').split()
                                    if val_plot in opt_parts:
                                        plot_select.select_by_visible_text(opt)
                                        plot_found = True
                                        selected_plot = opt
                                        break
                            
                            if not plot_found:
                                # 3. Closest Logic (Find Nearest Higher Plot)
                                try:
                                    # Use regex to extract number robustly
                                    import re
                                    match = re.search(r'\d+', val_plot)
                                    target_num = int(match.group()) if match else 0
                                    
                                    closest_plot = None
                                    min_diff = float('inf')
                                    
                                    if target_num > 0:
                                        for opt in available_plots:
                                            try:
                                                # Clean "1041/222" -> 1041, "1041 (Type)" -> 1041
                                                opt_clean = opt.split('/')[0].split(' ')[0]
                                                opt_num = int(opt_clean)
                                                
                                                # Find smallest POSITIVE difference (Next Higher)
                                                diff = opt_num - target_num
                                                if diff >= 0 and diff < min_diff:
                                                    min_diff = diff
                                                    closest_plot = opt
                                            except: continue
                                    
                                    if closest_plot:
                                        plot_select.select_by_visible_text(closest_plot)
                                        plot_found = True
                                        selected_plot = closest_plot
                                        self.log(f"      ℹ️ Plot {val_plot} not found. Used closest higher (+{min_diff}): {closest_plot}")
                                except: pass
                            
                            if not plot_found:
                                # STRICT FALLBACK: SKIP (If no higher plot found)
                                self.log(f"      ❌ Plot '{val_plot}' NOT FOUND (and no higher plot available). Skipping.")
                                errors += 1
                                continue
                            
                            # Log Selection
                            if selected_plot:
                                self.log(f"      ✅ Selected Plot: {selected_plot}")
                            
                            # >>> Interaction Logic (Refactored) <<<
                            
                            # Check Cache Rate? (Check Refresh Var)
                            cached_bm = self.get_cached_benchmark(village, selected_plot, area)
                            if cached_bm:
                                benchmark = cached_bm
                                self.log(f"      ⚡ Used Cached Benchmark: ₹{benchmark:,}")
                                case["source"] = "Cache" # Mark as Cached
                                result_valid = True
                            else:
                                # SCRAPE
                                # 1. Input Area
                                area_input = self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_txtArea"]')
                                self.igr_driver.execute_script("arguments[0].value = '';", area_input)
                                area_input.send_keys(str(area))
                                
                                # 2. Unit
                                unit_dropdown = self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_ddlUnit"]')
                                Select(unit_dropdown).select_by_visible_text("Acre")
                                
                                # 3. Wait/Double-Check Loop
                                result_valid = False
                                for attempt in range(2): # Up to 1 retry (Double Check)
                                    # Click Show (JS Click)
                                    show_btn = self.igr_driver.find_element(By.XPATH, '//*[@id="btnProceed"]')
                                    try:
                                        self.igr_driver.execute_script("arguments[0].scrollIntoView(true);", show_btn)
                                        show_btn.click()
                                    except:
                                        self.igr_driver.execute_script("arguments[0].click();", show_btn)
                                    
                                    # FORCE WAIT 3.0s (User Request)
                                    time.sleep(3.0) 
                                    
                                    # Read Result - MULTIPLE RETRIES FOR VALUE APPEARANCE
                                    current_val = 0
                                    
                                    # Try reading for up to 2 seconds (polling 0.5s)
                                    for _ in range(4):
                                        xpaths_to_try = [
                                            '//*[@id="DivAmount"]/div/div/div[1]/div/div[2]/span[2]', # Latest Correct
                                            '//*[@id="DivAmount"]/div/div/div[1]/div/div[2]', 
                                            '//*[@id="DivAmount"]'
                                        ]
                                        for xpath in xpaths_to_try:
                                            try:
                                                elem = self.igr_driver.find_element(By.XPATH, xpath)
                                                txt = elem.text.strip()
                                                if txt:
                                                    parsed = self.parse_currency(txt)
                                                    if parsed > 0:
                                                        current_val = parsed
                                                        break
                                            except: continue
                                        
                                        if current_val > 0: break
                                        time.sleep(0.5)
                                    
                                    # LOGIC: Double Check "Same Value"
                                    if current_val > 0:
                                        # If it's the same as the PREVIOUS case's value, it might be stale.
                                        # Trigger ONE retry click.
                                        if current_val == last_benchmark_val and attempt == 0:
                                            self.log(f"      🔄 Value matches previous ({current_val}). Double-checking...")
                                            continue # Loop again -> Click Again -> Wait Again
                                        else:
                                            # Valid
                                            benchmark = current_val
                                            last_benchmark_val = benchmark
                                            result_valid = True
                                            break
                                    else:
                                        # 0 Value
                                        self.log("      ⚠️ Returned 0 (Raw Text Empty/Invalid). Trying again...")
                                        # Loop again
                                
                                if benchmark > 0:
                                    # Cache Rate
                                    self.cache_benchmark(village, selected_plot, benchmark, area)
                                    case["source"] = "Web" # Mark as Scraped
                                else:
                                    self.log("      ⚠️ Failed to get valid benchmark.")
                                        
                            if benchmark > 0:
                                case["benchmark"] = benchmark
                                self.log(f"      ✅ Value: ₹{benchmark:,}")
                                completed += 1
                            else:
                                case["source"] = "Failed"
                                errors += 1
                                
                        except Exception as case_err:
                            self.log(f"      ❌ Case Error: {case_err}")
                            errors += 1
                    
                except Exception as e:
                    self.log(f"   ❌ Village error: {e}")
                    errors += len(cases)
        
        except Exception as e:
            self.log(f"❌ Critical error: {e}")
        
        # Summary
        self.log("")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log("✅ VALUATION CHECK COMPLETE")
        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log(f"   ✅ Completed Rows: {completed}")
        self.log(f"   ❌ Errors: {errors}")
        self.log("")
        
        # Refresh table
        self.after(0, self.load_valuation_data)
        
        # Export to Excel (Aggregated)
        self.export_valuation_results()
        
        self.after(0, lambda: messagebox.showinfo("Complete", f"Valuation check complete!\n\n✅ Rows: {completed}\n❌ Errors: {errors}\n\nResults saved to Excel."))
    
    def parse_currency(self, text):
        """Parse currency string to number using Regex (Robust)."""
        import re
        try:
            # Find number pattern: digits, commas, optional decimals
            match = re.search(r'[0-9,]+(\.[0-9]+)?', text)
            if match:
                clean = match.group(0).replace(",", "")
                return float(clean)
            return 0.0
        except:
            return 0.0
    
    def export_valuation_results(self):
        """Export aggregated valuation results to Excel file (One row per Case)."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from datetime import datetime
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Valuation Results"
            
            # Headers - Added 'Action'
            headers = ["Case No", "Applicant Name", "Mouza", "Village (English)", "Plots", "Valuation Plots", "Total Area", "Total Benchmark", "Conv Fee (1%)", "Rent (1%)", "Cess (75%)", "Grand Total", "Remarks", "Action"]
            ws.append(headers)
            
            # Style headers
            for col in range(1, len(headers) + 1):
                ws.cell(row=1, column=col).font = Font(bold=True)
                ws.cell(row=1, column=col).fill = PatternFill(start_color="1E90FF", end_color="1E90FF", fill_type="solid")
            
            # 1. Aggregate Data
            aggregated_data = {}
            
            # Sort self.forward_cases to ensure grouping order (optional but good)
            sorted_cases = sorted(self.forward_cases, key=lambda x: x.get("case_no", ""))
            
            for case in sorted_cases:
                c_no = case.get("case_no", "Unknown")
                
                if c_no not in aggregated_data:
                    aggregated_data[c_no] = {
                        "case_no": c_no,
                        "name": case.get("name", ""),
                        "mouza": case.get("mouza", ""),
                        "village": case.get("village_english", ""),
                        "plots": [],
                        "val_plots": [],
                        "total_area": 0.0,
                        "total_benchmark": 0.0,
                        "sources": [] # Collect sources
                    }
                
                agg = aggregated_data[c_no]
                agg["plots"].append(str(case.get("plot_no", "")))
                agg["val_plots"].append(str(case.get("valuation_plot", "")))
                
                # Aggregate Sources
                if case.get("source"):
                     agg["sources"].append(case.get("source"))
                
                # Sum Area
                try:
                    area_val = float(case.get("area", 0))
                    agg["total_area"] += area_val
                except:
                    pass
                    
                # Sum Benchmark
                bm = case.get("benchmark", 0)
                if bm:
                    agg["total_benchmark"] += bm
            
            # 2. Calculate Fees & Write Rows
            for c_no, data in aggregated_data.items():
                total_bm = data["total_benchmark"]
                
                # Calculate Fees on TOTAL Benchmark
                conversion_fee = math.ceil(total_bm * 0.01)
                rent = math.ceil(conversion_fee * 0.01)
                cess = math.ceil(rent * 0.75)
                # FIX: Grand Total excludes benchmark as per request
                grand_total = conversion_fee + rent + cess
                
                # Format Lists
                plots_str = ", ".join(data["plots"])
                val_plots_str = ", ".join(data["val_plots"])
                
                # --- AGGREGATE REMARKS (Mix of Web/Cache) ---
                sources = data.get("sources", [])
                if not sources:
                    remarks = "Pending"
                else:
                    s_set = set(sources)
                    if len(s_set) == 1:
                        remarks = list(s_set)[0] # "Web" or "Cache"
                    else:
                        # Mixed sources (e.g. Web, Cache)
                        sorted_s = sorted(list(s_set))
                        remarks = ", ".join(sorted_s) # "Cache, Web"
                
                row = [
                    data["case_no"],
                    data["name"],
                    data["mouza"],
                    data["village"],
                    plots_str,
                    val_plots_str,
                    round(data["total_area"], 3),
                    total_bm,
                    conversion_fee,
                    rent,
                    cess,
                    grand_total,
                    remarks,
                    "Forward" # Default Action for Valuation Success
                ]
                ws.append(row)
            
            # --- SAVE LOGIC (Overwrite Persistence) ---
            target_file = ""
            
            # 1. Try to reuse last file if it exists, otherwise use safe EXPORTS_DIR
            if hasattr(self, "last_export_path") and self.last_export_path and os.path.exists(self.last_export_path):
                target_file = self.last_export_path
            else:
                # New file in SAFE exports directory
                timestamp_str = datetime.now().strftime("Valuation Results (%d%m%y) (%H%M).xlsx")
                target_file = os.path.join(AppPaths.EXPORTS_DIR, timestamp_str)
            
            # Save (Attempt 1)
            try:
                wb.save(target_file)
                self.last_export_path = target_file
                self.last_save_path = target_file # Sync for Proceed Button
                self.log(f"✅ Excel Saved Successfully: {target_file}")
                
                # Auto-open file
                try:
                    os.startfile(target_file)
                    self.log("🚀 Auto-opened Excel file")
                except Exception as e:
                    self.log(f"⚠️ Could not auto-open file: {e}")
                
            except PermissionError:
                # File is OPEN - Save to new name
                new_name = f"Valuation_Results_{datetime.now().strftime('%H%M%S')}.xlsx"
                new_path = os.path.join(AppPaths.EXPORTS_DIR, new_name)
                
                self.log(f"⚠️ Could not save to {target_file} (File Open?). Saving to {new_path} instead...")
                wb.save(new_path)
                self.last_export_path = new_path
                self.last_save_path = new_path
                self.log(f"✅ Saved to alternative: {new_path}")
                
                try: os.startfile(new_path)
                except: pass
            
            except Exception as e:
                self.log(f"❌ Save Failed: {e}")

        except Exception as e:
            self.log(f"❌ Export Process Failed: {e}")

    # ==================== CACHING HELPERS ====================

    def load_village_plots_cache(self):
        """Load the persistent plot cache from JSON."""
        if os.path.exists(VILLAGE_CACHE_FILE):
            try:
                with open(VILLAGE_CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_village_plots_cache(self, data):
        """Save the plot cache to JSON."""
        try:
            with open(VILLAGE_CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def get_village_plots(self, village_name, plot_dropdown_element):
        """Get plots for a village from cache or website."""
        from selenium.webdriver.support.ui import Select
        
        # Check cache
        cache = self.load_village_plots_cache()
        if village_name in cache and not self.refresh_cache_var.get():
            self.log(f"   ⚡ Using cached plots list for {village_name} ({len(cache[village_name])} plots)")
            return cache[village_name]
        
        # Scrape
        self.log(f"   🌐 Scanning plots from website for {village_name}...")
        try:
            select = Select(plot_dropdown_element)
            # wait for options to be populated? Assuming element is ready.
            plots = [opt.text.strip() for opt in select.options if opt.text.strip() and opt.text.strip() != "--Select--"]
            
            if plots:
                # Update cache
                cache[village_name] = plots
                self.save_village_plots_cache(cache)
                self.log(f"   💾 Cached {len(plots)} plots for {village_name}")
                
                # Reset refresh switch if it was on
                if self.refresh_cache_var.get():
                     # Must be done in UI thread usually, but Var is thread safe? 
                     # Tkinter Var is NOT thread safe. run_valuation_check runs in thread.
                     # Setting it might crash. Better to just ignore it for next.
                     pass 
            else:
                 self.log(f"   ⚠️ Warning: No plots found to cache.")
                 
            return plots
        except Exception as e:
            self.log(f"   ❌ Failed to scan plots: {e}")
            return []

    # ==================== BENCHMARK CACHE HELPERS ====================

    def load_benchmark_cache(self):
        """Load the benchmark value cache from JSON."""
        if os.path.exists(BENCHMARK_CACHE_FILE):
            try:
                with open(BENCHMARK_CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_benchmark_cache(self, data):
        """Save the benchmark value cache to JSON."""
        try:
            with open(BENCHMARK_CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save benchmark cache: {e}")

    def get_cached_benchmark(self, village, plot, area):
        """Get cached benchmark value based on Rate * Area."""
        # Thread-safe check using captured state
        if getattr(self, "force_refresh_active", False):
            self.log(f"      ℹ️ Cache Skipped: Force Refresh Active")
            return None
        # Fallback to variable if attribute missing (UI thread)
        try:
             if self.refresh_cache_var.get(): 
                 self.log(f"      ℹ️ Cache Skipped: Refresh Checkbox Checked")
                 return None
        except: pass
        
        try:
            area_val = float(area)
            if area_val <= 0: return None
            
            cache = self.load_benchmark_cache()
            key = f"{village}|{plot}"
            
            # Cache stores RATE PER ACRE
            rate = cache.get(key)
            
            if rate is not None:
                value = rate * area_val
                # Minimum value clamp
                return max(100, value)
                
            return None
        except:
            return None

    def cache_benchmark(self, village, plot, value, area):
        """Save benchmark RATE to cache (Rate = Value / Area)."""
        try:
            val_float = float(value)
            area_float = float(area)
            
            if val_float <= 0 or area_float <= 0: return
            
            # Calculate Rate
            rate = val_float / area_float
            
            cache = self.load_benchmark_cache()
            key = f"{village}|{plot}"
            cache[key] = rate
            self.save_benchmark_cache(cache)
            
        except Exception as e:
            self.log(f"⚠️ Failed to cache rate: {e}")

    
    def save_valuation_excel_incremental(self):
        """Save valuation results incrementally after each case."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Valuation Results"
            
            # Headers
            headers = ["Case No", "Mouza", "Village", "Plot No", "Val Plot", "Area", "Benchmark", "Conv Fee", "Rent", "Cess", "Total"]
            ws.append(headers)
            
            # Style headers
            for col in range(1, len(headers) + 1):
                ws.cell(row=1, column=col).font = Font(bold=True, color="FFFFFF")
                ws.cell(row=1, column=col).fill = PatternFill(start_color="1E90FF", end_color="1E90FF", fill_type="solid")
            
            # Data rows
            for case in self.forward_cases:
                row = [
                    case.get("case_no", ""),
                    case.get("mouza", ""),
                    case.get("village_english", ""),
                    case.get("plot_no", ""),
                    case.get("valuation_plot", ""),
                    case.get("area", ""),
                    case.get("benchmark", ""),
                    case.get("conversion_fee", ""),
                    case.get("rent", ""),
                    case.get("cess", ""),
                    case.get("total", "")
                ]
                ws.append(row)
            
            # Save file (overwrite same file)
            filename = "Valuation_Results_Current.xlsx"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            wb.save(filepath)
            
        except Exception as e:
            pass  # Silent fail for incremental save
    
    def refresh_valuation_table_row(self, row_idx=None):
        """Refresh the valuation table to show updated values."""
        # Clear and rebuild table
        for widget in self.valuation_table.winfo_children():
            widget.destroy()
        
        # Populate table with current forward cases data
        for i, case in enumerate(self.forward_cases):
            row_bg = COLORS["bg_dark"] if i % 2 == 0 else COLORS["bg_card"]
            
            # Highlight if benchmark found
            if case.get("benchmark"):
                row_bg = "#1a3d2e"  # Green tint for completed
            
            row_frame = ctk.CTkFrame(self.valuation_table, fg_color=row_bg, height=30)
            row_frame.pack(fill="x", pady=1)
            row_frame.pack_propagate(False)
            
            ctk.CTkLabel(row_frame, text=str(case.get("case_no", "N/A"))[:10], width=80, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("mouza", "N/A"))[:12], width=100, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("village_english", "-"))[:12] if case.get("village_english") else "-", width=100, font=ctk.CTkFont(size=9), anchor="w", text_color=COLORS["accent_cyan"]).pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("plot_no", "N/A"))[:10], width=80, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("valuation_plot", "N/A"))[:8], width=60, font=ctk.CTkFont(size=9), anchor="w", text_color=COLORS["accent_green"]).pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("area", "0"))[:6], width=50, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            
            # Benchmark with green highlight if found
            bm_text = f"₹{case.get('benchmark'):,}" if case.get("benchmark") else "-"
            ctk.CTkLabel(row_frame, text=bm_text[:12], width=80, font=ctk.CTkFont(size=9), anchor="w", text_color="#32CD32" if case.get("benchmark") else COLORS["text_secondary"]).pack(side="left", padx=3)
            
            ctk.CTkLabel(row_frame, text=str(case.get("conversion_fee", "-"))[:8] if case.get("conversion_fee") else "-", width=70, font=ctk.CTkFont(size=9), anchor="w").pack(side="left", padx=3)
            ctk.CTkLabel(row_frame, text=str(case.get("total", "-"))[:8] if case.get("total") else "-", width=70, font=ctk.CTkFont(size=9), anchor="w", text_color=COLORS["accent_orange"] if case.get("total") else COLORS["text_secondary"]).pack(side="left", padx=3)
    
    def open_igr_website(self):
        """Open IGR website in browser for user to select District and RO."""
        try:
            self.log("🌐 Opening IGR website...")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_experimental_option("detach", True)
            chrome_options.add_argument("--start-maximized")
            
            # Create driver (use pre-prepared path if available)
            if CHROMEDRIVER_PATH:
                service = Service(CHROMEDRIVER_PATH)
            else:
                service = Service(ChromeDriverManager().install())

            self.igr_driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Navigate to IGR website
            self.igr_driver.get("https://www.igrodisha.gov.in/viewfeevalue.aspx")
            
            time.sleep(2)
            
            self.log("✅ IGR website opened!")
            self.log("👆 Please select District and Registration Office from the dropdowns")
            self.log("   Then click 'Detect Selection' button")
            
            messagebox.showinfo("Website Opened", "IGR Website is open!\n\n1. Select DISTRICT from dropdown\n2. Select REGISTRATION OFFICE from dropdown\n3. Click 'Detect Selection' button")
            
        except Exception as e:
            self.log(f"❌ Failed to open website: {e}")
            messagebox.showerror("Error", f"Failed to open website: {e}")
    
    def detect_district_ro_selection(self):
        """Detect what District and RO user has selected on the website."""
        if not self.igr_driver:
            messagebox.showwarning("Warning", "Please open IGR website first!")
            return
        
        try:
            # Get selected District
            district_dropdown = self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_ddldist"]')
            from selenium.webdriver.support.ui import Select
            district_select = Select(district_dropdown)
            self.detected_district = district_select.first_selected_option.text
            
            # Get selected RO
            ro_dropdown = self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_ddlRO"]')
            ro_select = Select(ro_dropdown)
            self.detected_ro = ro_select.first_selected_option.text
            
            # Update UI
            if self.detected_district and self.detected_district != "--Select--":
                self.district_label.configure(text=f"District: {self.detected_district}", text_color=COLORS["accent_green"])
            else:
                self.district_label.configure(text="District: (not selected)", text_color=COLORS["text_secondary"])
                
            if self.detected_ro and self.detected_ro != "--Select--":
                self.ro_label.configure(text=f"RO: {self.detected_ro}", text_color=COLORS["accent_green"])
            else:
                self.ro_label.configure(text="RO: (not selected)", text_color=COLORS["text_secondary"])
            
            self.log(f"🔍 Detected: District = '{self.detected_district}', RO = '{self.detected_ro}'")
            
            # Save combination
            if self.detected_district and self.detected_ro and self.detected_district != "--Select--" and self.detected_ro != "--Select--":
                self.save_district_ro_combo(self.detected_district, self.detected_ro)
                messagebox.showinfo("Detected", f"District: {self.detected_district}\nRO: {self.detected_ro}\n\nNow click 'Pull Villages' to get village list!")
            else:
                messagebox.showwarning("Warning", "Please select both District and Registration Office on the website first!")
            
        except Exception as e:
            self.log(f"❌ Detection failed: {e}")
            messagebox.showerror("Error", f"Failed to detect selection: {e}")
    
    def pull_villages(self):
        """Pull villages from IGR website for selected District and RO."""
        if not self.detected_district or not self.detected_ro or self.detected_district == "--Select--" or self.detected_ro == "--Select--":
            messagebox.showwarning("Warning", "Please detect District and RO selection first!")
            return
        
        district = self.detected_district
        ro = self.detected_ro
        
        # Create cache key
        cache_key = f"{district}_{ro}"
        
        # Check if cached
        cache_file = os.path.join(os.path.dirname(__file__), "villages_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                if cache_key in cache:
                    self.villages_list = cache[cache_key]
                    self.log(f"✅ Loaded {len(self.villages_list)} villages from cache for {district} / {ro}")
                    self.villages_count_label.configure(text=f"Villages: {len(self.villages_list)}")
                    self.create_village_mapping_ui()
                    self.load_saved_village_mappings()
                    return
            except:
                pass
        
        # Pull from browser
        if not self.igr_driver:
            messagebox.showwarning("Warning", "Please open IGR website first!")
            return
        
        try:
            self.log(f"📥 Pulling villages for: {district} / {ro}")
            
            # Wait for village dropdown to be populated
            time.sleep(1)
            
            # Get village dropdown
            village_dropdown = self.igr_driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_ddlvillage"]')
            from selenium.webdriver.support.ui import Select
            village_select = Select(village_dropdown)
            
            # Get all options
            self.villages_list = []
            for option in village_select.options:
                value = option.text.strip()
                if value and value != "--Select--" and value != "Select":
                    self.villages_list.append(value)
            
            self.log(f"✅ Pulled {len(self.villages_list)} villages!")
            self.villages_count_label.configure(text=f"Villages: {len(self.villages_list)}")
            
            # Save to cache
            cache = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache = json.load(f)
                except:
                    pass
            
            cache[cache_key] = self.villages_list
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            
            self.log(f"💾 Villages cached for {district} / {ro}")
            
            # Update UI
            self.create_village_mapping_ui()
            self.load_saved_village_mappings()
            
            messagebox.showinfo("Success", f"Pulled {len(self.villages_list)} villages!\n\nNow map Odia Mouza names to English village names.")
            
        except Exception as e:
            self.log(f"❌ Failed to pull villages: {e}")
            messagebox.showerror("Error", f"Failed to pull villages: {e}")
    
    def save_district_ro_combo(self, district, ro):
        """Save District and RO combination for resume functionality."""
        combo_file = os.path.join(os.path.dirname(__file__), "district_ro_combo.json")
        try:
            data = {"district": district, "ro": ro, "timestamp": datetime.now().isoformat()}
            with open(combo_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.log(f"💾 Saved District/RO combo: {district} / {ro}")
        except Exception as e:
            self.log(f"⚠️ Failed to save combo: {e}")
    
    def load_saved_village_mappings(self):
        """Load village mappings from JSON cache (Safe Path)."""
        mapping_file = AppPaths.MAPPINGS_FILE # Safe Path
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self.village_mappings = json.load(f)
                self.log(f"✅ Loaded {len(self.village_mappings)} village mappings from cache")
                
                # Update dropdowns with saved mappings
                for mouza, english in self.village_mappings.items():
                    if mouza in self.village_dropdowns:
                        self.village_dropdowns[mouza]["var"].set(english)
                
                # Apply to forward cases
                for case in self.forward_cases:
                    mouza = case.get("mouza", "")
                    if mouza in self.village_mappings:
                        case["village_english"] = self.village_mappings[mouza]
            except:
                pass
    
    def confirm_village_mapping(self):
        """Confirm and save village mappings."""
        if not self.village_dropdowns:
            messagebox.showwarning("Warning", "No mapping to confirm! Load data first.")
            return
        
        # Collect mappings from dropdowns
        self.village_mappings = {}
        unmapped = []
        
        for mouza, data in self.village_dropdowns.items():
            selected = data["var"].get()
            if selected and selected not in ["(Select Village)", "(Pull villages first)"]:
                self.village_mappings[mouza] = selected
            else:
                unmapped.append(mouza)
        
        if unmapped:
            msg = f"{len(unmapped)} Mouza(s) not mapped:\n"
            for m in unmapped[:5]:
                msg += f"  • {m}\n"
            if len(unmapped) > 5:
                msg += f"  ... and {len(unmapped) - 5} more\n"
            msg += "\nContinue anyway?"
            
            if not messagebox.askyesno("Warning", msg):
                return
        
        # Save to JSON for persistence (Safe Path)
        mapping_file = AppPaths.MAPPINGS_FILE
        try:
            # Load existing first to merge (don't overwrite others)
            existing = {}
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            existing.update(self.village_mappings)
            
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            
            self.log(f"💾 Saved {len(self.village_mappings)} village mappings")
        except Exception as e:
            self.log(f"⚠️ Failed to save mappings: {e}")
        
        # Apply mappings to forward cases
        for case in self.forward_cases:
            mouza = case.get("mouza", "")
            if mouza in self.village_mappings:
                case["village_english"] = self.village_mappings[mouza]
        
        # Refresh table
        self.load_valuation_data()
        
        messagebox.showinfo("Success", f"Mapping confirmed!\n\n{len(self.village_mappings)} villages mapped.\n{len(unmapped)} not mapped.")
    
    def resume_valuation(self):
        """Resume valuation from last saved state."""
        progress_file = os.path.join(AppPaths.CACHE_DIR, "valuation_progress.json")
        
        if not os.path.exists(progress_file):
            messagebox.showinfo("Info", "No saved progress found to resume.")
            return
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            self.log("📂 Loading saved progress...")
            self.log(f"   Last case: {progress.get('last_case', 'N/A')}")
            self.log(f"   Completed: {progress.get('completed_count', 0)}")
            self.log(f"   Remaining: {progress.get('remaining_count', 0)}")
            
            # Load District/RO
            if progress.get("district"):
                self.detected_district = progress["district"]
                self.district_label.configure(text=f"District: {self.detected_district}", text_color=COLORS["accent_green"])
            if progress.get("ro"):
                self.detected_ro = progress["ro"]
                self.ro_label.configure(text=f"RO: {self.detected_ro}", text_color=COLORS["accent_green"])
            
            messagebox.showinfo("Resume", f"Progress loaded!\n\nDistrict: {self.detected_district}\nRO: {self.detected_ro}\n\nCompleted: {progress.get('completed_count', 0)}\nRemaining: {progress.get('remaining_count', 0)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load progress: {e}")
    
    def save_valuation_progress(self, completed_count, remaining_count, last_case):
        """Save valuation progress for resume."""
        progress_file = os.path.join(AppPaths.CACHE_DIR, "valuation_progress.json")
        
        try:
            district = self.detected_district
            ro = self.detected_ro
            
            progress = {
                "district": district,
                "ro": ro,
                "completed_count": completed_count,
                "remaining_count": remaining_count,
                "last_case": last_case,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
            
            self.log(f"💾 Progress saved: {completed_count} completed, {remaining_count} remaining")
        except Exception as e:
            self.log(f"⚠️ Failed to save progress: {e}")
    
    # ==================== END SETUP/VALUATION METHODS ====================
    
    def clear_log(self):
        """Clear the status log."""
        self.log_text.delete("1.0", "end")
    
    def load_saved_credentials(self):
        saccess_users = self.cred_manager.get_saccess_users()
        lrms_users = self.cred_manager.get_lrms_users()
        
        self.saccess_user_combo.configure(values=saccess_users)
        self.lrms_user_combo.configure(values=lrms_users)
        
        if saccess_users:
            self.saccess_user_var.set(saccess_users[0])
            self.on_saccess_user_select(saccess_users[0])
        
        if lrms_users:
            self.lrms_user_var.set(lrms_users[0])
            self.on_lrms_user_select(lrms_users[0])
    
    def on_saccess_user_select(self, username):
        password = self.cred_manager.get_saccess_password(username)
        self.saccess_pass_entry.delete(0, "end")
        self.saccess_pass_entry.insert(0, password)
    
    def on_lrms_user_select(self, username):
        password = self.cred_manager.get_lrms_password(username)
        self.lrms_pass_entry.delete(0, "end")
        self.lrms_pass_entry.insert(0, password)
    
    def delete_saccess_cred(self):
        username = self.saccess_user_var.get()
        if username:
            self.cred_manager.delete_saccess(username)
            self.saccess_user_var.set("")
            self.saccess_pass_entry.delete(0, "end")
            self.load_saved_credentials()
            self.log("🗑️ Deleted SACCESS credentials for: " + username)
    
    def delete_lrms_cred(self):
        username = self.lrms_user_var.get()
        if username:
            self.cred_manager.delete_lrms(username)
            self.lrms_user_var.set("")
            self.lrms_pass_entry.delete(0, "end")
            self.load_saved_credentials()
            self.log("🗑️ Deleted LRMS credentials for: " + username)
    
    def log(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
    
    def update_status(self, message):
        self.after(0, lambda: self.log(message))
    
    def update_progress(self, current, total, filename=""):
        def _update():
            if total > 0:
                progress = min(current / total, 1.0)
                self.progress_bar.set(progress)
                self.progress_label.configure(text=f"Progress: {current}/{total} cases ({int(progress*100)}%)")
            if filename:
                self.file_label.configure(text=f"File: {filename}")
        self.after(0, _update)
    
    def start_login(self):
        saccess_user = self.saccess_user_var.get()
        saccess_pass = self.saccess_pass_entry.get()
        lrms_user = self.lrms_user_var.get()
        lrms_pass = self.lrms_pass_entry.get()
        
        if not saccess_user or not saccess_pass:
            messagebox.showerror("Error", "Please enter SACCESS credentials!")
            return
        
        if self.saccess_save_var.get():
            self.cred_manager.add_saccess(saccess_user, saccess_pass)
        
        if self.lrms_save_var.get() and lrms_user and lrms_pass:
            self.cred_manager.add_lrms(lrms_user, lrms_pass)
        
        self.load_saved_credentials()
        self.clear_log()
        self.login_btn.configure(state="disabled")
        
        # Switch to log tab
        self.tabview.set("📋 Status Log")
        
        def run_automation():
            try:
                self.automation = LoginAutomation(
                    status_callback=self.update_status,
                    progress_callback=self.update_progress
                )
                self.automation.initialize_browser()
                success = self.automation.login_saccess(saccess_user, saccess_pass)
                
                if success:
                    self.automation.monitor_for_lrms(lrms_user, lrms_pass)
                
                self.after(0, lambda: self.login_btn.configure(state="normal"))
                
            except Exception as e:
                self.update_status(f"❌ Error: {str(e)}")
                self.after(0, lambda: self.login_btn.configure(state="normal"))
        
        threading.Thread(target=run_automation, daemon=True).start()
    
    def start_extraction(self):
        if not self.automation or not self.automation.driver:
            messagebox.showerror("Error", "Please login first! Browser must be open.")
            return
        
        # Determine Excel file path
        if self.file_option.get() == "new":
            timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
            # Use Safe Exports Directory
            excel_filepath = os.path.join(AppPaths.EXPORTS_DIR, f"{timestamp}.xlsx")
            is_resume = False
        else:
            if not self.selected_excel_path:
                messagebox.showerror("Error", "Please select an Excel file to resume!")
                return
            excel_filepath = self.selected_excel_path
            is_resume = True
        
        # Determine start page
        if self.page_option.get() == "all":
            start_page = 1
        else:
            try:
                start_page = int(self.start_page_entry.get())
                if start_page < 1:
                    start_page = 1
            except:
                start_page = 1
        
        self.extract_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting...")
        
        # Switch to log tab
        self.tabview.set("📋 Status Log")
        
        def run_extraction():
            try:
                self.automation.extract_olr_8a_cases(excel_filepath, start_page, is_resume)
            except Exception as e:
                self.update_status(f"❌ Error: {str(e)}")
            finally:
                self.after(0, lambda: self.extract_btn.configure(state="normal"))
                self.after(0, lambda: self.stop_btn.configure(state="disabled"))
        
        threading.Thread(target=run_extraction, daemon=True).start()
    
    def on_closing(self):
        if self.automation:
            self.automation.close()
        self.destroy()


def main():
    app = LRMSApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
