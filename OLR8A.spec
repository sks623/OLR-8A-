# -*- mode: python ; coding: utf-8 -*-
"""
OLR 8A - PyInstaller Spec File
Run: pyinstaller OLR8A.spec
"""

import os

block_cipher = None

# Get the directory containing the spec file
spec_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['lrms_app.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        # Include telemetry module
        ('telemetry.py', '.'),
        # Include Google Sheets credentials
        ('gsheet_creds.json', '.'),
    ],
    hiddenimports=[
        'telemetry',
        'gspread',
        'google.oauth2.service_account',
        'google.auth.transport.requests',
        'customtkinter',
        'PIL',
        'openpyxl',
        'pandas',
        'selenium',
        'webdriver_manager',
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
