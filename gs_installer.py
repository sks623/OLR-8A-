"""
OLR 8A - GhostScript Installation Manager
Handles GhostScript detection, installation, and PATH management.

Features:
- Detects existing GhostScript installations
- Extracts bundled gs10060w64.exe from PyInstaller bundle
- Installs GhostScript silently
- Configures PATH automatically
- Fallback to winget/choco if bundled installer missing
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Constants
GS_INSTALLER_FILENAME = "gs10060w64.exe"
GS_COMMON_PATHS = [
    r"C:\Program Files\gs\gs10.06.0\bin",
    r"C:\Program Files\gs\gs10.03.1\bin",
    r"C:\Program Files\gs\gs10.02.1\bin",
    r"C:\Program Files (x86)\gs\gs10.06.0\bin",
    r"C:\Program Files (x86)\gs\gs10.03.1\bin",
    r"C:\Program Files (x86)\gs\gs10.02.1\bin",
]


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in normal Python environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def find_ghostscript():
    """
    Find GhostScript executable.

    Returns:
        str: Path to GhostScript executable (gswin64c.exe or gs.exe), or False if not found
    """
    # Try common commands
    for gs_cmd in ["gswin64c", "gswin32c", "gs"]:
        try:
            result = subprocess.run(
                [gs_cmd, "--version"],
                capture_output=True,
                timeout=5,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
                stdin=subprocess.DEVNULL
            )
            if result.returncode == 0:
                print(f"[GhostScript] Found: {gs_cmd}")
                return gs_cmd
        except:
            continue

    # Try common installation paths
    for gs_path in GS_COMMON_PATHS:
        for exe_name in ["gswin64c.exe", "gswin32c.exe", "gs.exe"]:
            gs_exe = os.path.join(gs_path, exe_name)
            if os.path.exists(gs_exe):
                print(f"[GhostScript] Found: {gs_exe}")
                return gs_exe

    return False


def extract_bundled_installer():
    """
    Extract GhostScript installer from PyInstaller bundle.

    Returns:
        str: Path to extracted installer, or None if not bundled
    """
    try:
        # Check if installer is bundled
        bundled_path = get_resource_path(os.path.join("resources", GS_INSTALLER_FILENAME))

        if not os.path.exists(bundled_path):
            print("[GhostScript] Installer not bundled in EXE")
            return None

        # Extract to temp folder
        temp_dir = os.path.join(os.getenv('TEMP'), 'OLR8A_Install')
        os.makedirs(temp_dir, exist_ok=True)

        temp_installer = os.path.join(temp_dir, GS_INSTALLER_FILENAME)

        # Copy installer if not already extracted
        if not os.path.exists(temp_installer):
            print(f"[GhostScript] Extracting bundled installer to {temp_installer}")
            shutil.copy2(bundled_path, temp_installer)

        return temp_installer

    except Exception as e:
        print(f"[GhostScript] Failed to extract bundled installer: {e}")
        return None


def install_ghostscript_bundled(installer_path):
    """
    Install GhostScript using bundled installer.

    Args:
        installer_path (str): Path to gs10060w64.exe

    Returns:
        bool: True if installation successful
    """
    try:
        print(f"[GhostScript] Installing from bundled installer...")

        # Run installer with silent flag
        result = subprocess.run(
            [installer_path, "/S"],  # /S = Silent installation
            capture_output=True,
            timeout=300,  # 5 minutes
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            stdin=subprocess.DEVNULL
        )

        if result.returncode == 0:
            print("[GhostScript] Installation completed successfully")
            return True
        else:
            print(f"[GhostScript] Installation returned error code: {result.returncode}")
            return False

    except Exception as e:
        print(f"[GhostScript] Installation failed: {e}")
        return False


def install_ghostscript_winget():
    """
    Install GhostScript using Windows Package Manager (winget).

    Returns:
        bool: True if installation successful
    """
    try:
        print("[GhostScript] Attempting installation via winget...")

        result = subprocess.run(
            ["winget", "install", "-e", "--id", "ArtifexSoftware.GhostScript",
             "--silent", "--accept-package-agreements", "--accept-source-agreements"],
            capture_output=True,
            text=True,
            timeout=300,
            creationflags=0x08000000,
            stdin=subprocess.DEVNULL
        )

        if result.returncode == 0:
            print("[GhostScript] Installed successfully via winget")
            return True
        else:
            print(f"[GhostScript] winget failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"[GhostScript] winget installation failed: {e}")
        return False


def install_ghostscript_choco():
    """
    Install GhostScript using Chocolatey package manager.

    Returns:
        bool: True if installation successful
    """
    try:
        print("[GhostScript] Attempting installation via chocolatey...")

        result = subprocess.run(
            ["choco", "install", "ghostscript", "-y"],
            capture_output=True,
            text=True,
            timeout=300,
            creationflags=0x08000000,
            stdin=subprocess.DEVNULL
        )

        if result.returncode == 0:
            print("[GhostScript] Installed successfully via chocolatey")
            return True
        else:
            print("[GhostScript] Chocolatey installation failed")
            return False

    except Exception as e:
        print(f"[GhostScript] Chocolatey installation failed: {e}")
        return False


def ensure_ghostscript_installed():
    """
    Ensure GhostScript is installed.
    Tries: bundled installer → winget → chocolatey → manual prompt

    Returns:
        str|bool: Path to GhostScript executable, or False if not available
    """
    # First, check if already installed
    gs_path = find_ghostscript()
    if gs_path:
        return gs_path

    print("[GhostScript] Not found. Attempting auto-installation...")

    # Try bundled installer first
    bundled_installer = extract_bundled_installer()
    if bundled_installer:
        if install_ghostscript_bundled(bundled_installer):
            # Check again after installation
            gs_path = find_ghostscript()
            if gs_path:
                return gs_path

    # Try winget
    if install_ghostscript_winget():
        gs_path = find_ghostscript()
        if gs_path:
            return gs_path

    # Try chocolatey
    if install_ghostscript_choco():
        gs_path = find_ghostscript()
        if gs_path:
            return gs_path

    # All methods failed
    print("[GhostScript] Auto-installation failed")
    print("[GhostScript] Please install manually from: https://ghostscript.com/releases/gsdnld.html")

    return False


def get_ghostscript_version(gs_path):
    """Get GhostScript version string."""
    try:
        result = subprocess.run(
            [gs_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=0x08000000,
            stdin=subprocess.DEVNULL
        )
        return result.stdout.strip() if result.returncode == 0 else "Unknown"
    except:
        return "Unknown"


# Self-test
if __name__ == "__main__":
    print("=== GhostScript Installation Manager Test ===")
    print()

    print("1. Searching for existing GhostScript installation...")
    gs = find_ghostscript()
    if gs:
        print(f"   Found: {gs}")
        print(f"   Version: {get_ghostscript_version(gs)}")
    else:
        print("   Not found")

    print()
    print("2. Checking for bundled installer...")
    bundled = extract_bundled_installer()
    if bundled:
        print(f"   Found: {bundled}")
    else:
        print("   Not bundled")

    print()
    print("3. Full installation test (if not installed)...")
    result = ensure_ghostscript_installed()
    if result:
        print(f"   SUCCESS: {result}")
        print(f"   Version: {get_ghostscript_version(result)}")
    else:
        print("   FAILED: Manual installation required")
