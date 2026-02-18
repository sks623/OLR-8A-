# -*- mode: python ; coding: utf-8 -*-
"""
OLR 8A - PyInstaller Spec File
Run: pyinstaller OLR8A.spec
"""

import os

block_cipher = None

# Get the directory containing the spec file
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# Build list of data files (only include if they exist)
datas_list = [
    ('telemetry.py', '.'),       # Telemetry module
    ('saccess_login.py', '.'),   # SACCESS login module
    ('gs_installer.py', '.'),    # GhostScript installer helper
    ('20 questions logic.csv', '.'),  # Form logic data
]

# Optional: Include Google Sheets credentials if present
gsheet_creds = os.path.join(spec_dir, 'gsheet_creds.json')
if os.path.exists(gsheet_creds):
    datas_list.append(('gsheet_creds.json', '.'))
    print("[BUILD] Including gsheet_creds.json (telemetry enabled)")
else:
    print("[BUILD] gsheet_creds.json not found (telemetry will be disabled)")

# Optional: Bundle GhostScript installer if present
gs_installer = os.path.join(spec_dir, 'gs10060w64.exe')
if os.path.exists(gs_installer):
    datas_list.append(('gs10060w64.exe', 'resources'))
    print("[BUILD] Bundling gs10060w64.exe (offline GhostScript installation supported)")
else:
    print("[BUILD] gs10060w64.exe not found (GhostScript will auto-install via winget at runtime)")

a = Analysis(
    ['lrms_app.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        # Local modules
        'telemetry',
        'saccess_login',
        'gs_installer',
        # Google Sheets (telemetry)
        'gspread',
        'google.oauth2.service_account',
        'google.auth.transport.requests',
        'google.auth',
        # GUI
        'customtkinter',
        'PIL',
        'PIL.Image',
        # Data processing
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'pandas',
        # Browser automation
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.common.exceptions',
        'webdriver_manager',
        'webdriver_manager.chrome',
        # Utilities
        'requests',
        'psutil',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OLR8A',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists(os.path.join(spec_dir, 'icon.ico')) else None,
)
