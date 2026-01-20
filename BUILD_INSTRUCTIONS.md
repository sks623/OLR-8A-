# OLR 8A - Build Instructions

## Prerequisites

### 1. Install PyInstaller
```bash
pip install pyinstaller
```

### 2. Install Inno Setup
Download and install from: https://jrsoftware.org/isdl.php

### 3. Download GhostScript Installer
Download `gs10031w64.exe` from: https://ghostscript.com/releases/gsdnld.html
Place it in `D:\coding\8a\` folder (same folder as installer.iss)

### 4. Create App Icon (Optional)
Create or download an `icon.ico` file and place it in `D:\coding\8a\`

---

## Build Steps

### Step 1: Build EXE with PyInstaller
Open Command Prompt in `D:\coding\8a` and run:

```bash
pyinstaller OLR8A.spec --clean
```

This creates `dist\OLR8A.exe`

### Step 2: Build Installer with Inno Setup
1. Open Inno Setup Compiler
2. Open `D:\coding\8a\installer.iss`
3. Click "Compile" (or press Ctrl+F9)

This creates `Output\OLR8A_Setup_v1.0.0.exe`

---

## Alternative: One-Click Build Script

Run `build.bat` which does everything automatically:

```bash
build.bat
```

---

## Folder Structure After Build

```
D:\coding\8a\
├── lrms_app.py           # Main app source
├── telemetry.py          # Telemetry module
├── gsheet_creds.json     # Google Sheets credentials
├── OLR8A.spec            # PyInstaller spec
├── installer.iss         # Inno Setup script
├── gs10031w64.exe        # GhostScript installer (download this!)
├── icon.ico              # App icon (optional)
├── build\                # PyInstaller temp files
├── dist\
│   └── OLR8A.exe         # Built application
└── Output\
    └── OLR8A_Setup_v1.0.0.exe  # Final installer!
```

---

## What the Installer Does

1. **Installs OLR8A.exe** to `C:\Program Files\OLR8A\`
2. **Installs GhostScript** (if not already installed)
3. **Adds GhostScript to PATH** (so app can find `gswin64c.exe`)
4. **Creates Desktop Shortcut**
5. **Creates Start Menu Entry**

---

## Testing the Installer

1. Run `OLR8A_Setup_v1.0.0.exe` as Administrator
2. Follow the wizard
3. Launch from Desktop shortcut
4. Check your Google Sheet for the INSTALL telemetry event

---

## Troubleshooting

### "GhostScript not found" after install
- Restart your computer (PATH changes need restart)
- Or manually add `C:\Program Files\gs\gs10.03.1\bin` to system PATH

### PyInstaller errors
- Make sure all imports work: `python lrms_app.py`
- Install missing packages: `pip install -r requirements.txt`

### Inno Setup errors
- Make sure `dist\OLR8A.exe` exists (run PyInstaller first)
- Make sure `gs10031w64.exe` is in the folder
