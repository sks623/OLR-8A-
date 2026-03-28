# OLR 8A - Complete Build Guide

## 📁 Directory Structure

```
OLR-8A-/
├── 📄 Core Application Files
│   ├── lrms_app.py              # Main application (262 KB)
│   ├── telemetry.py             # Usage tracking module (6.1 KB)
│   ├── saccess_login.py         # SACCESS portal login (8.9 KB)
│   └── gs_installer.py          # GhostScript installer helper (NEW - 8.5 KB)
│
├── 🎨 Resources
│   ├── icon.ico                 # Application icon (11 KB)
│   ├── create_icon.py           # Icon generator utility
│   └── 20 questions logic.csv   # Form automation logic (3.5 KB)
│
├── 🔧 Build Configuration
│   ├── requirements.txt         # Python dependencies (1.0 KB)
│   ├── OLR8A.spec              # PyInstaller build spec (1.5 KB)
│   ├── build_complete.bat      # Automated build script (7.4 KB)
│   └── installer.iss           # Inno Setup installer script (3.9 KB)
│
├── 📚 Documentation
│   ├── README.md               # Project overview (3.3 KB)
│   ├── INSTALLATION_GUIDE.md   # User installation guide (15 KB)
│   ├── BUILD_INSTRUCTIONS.md   # Developer build guide (2.6 KB)
│   ├── USER_MANUAL.md          # User manual (8.0 KB)
│   ├── QUICK_START.md          # 5-minute quick start (2.7 KB)
│   ├── MANUAL_CHROME_FIX.md    # ChromeDriver troubleshooting (1.2 KB)
│   ├── BROWSER ERROR.md        # Browser error handling (25 KB)
│   ├── ALERT_HANDLING.md       # Alert handling notes (30 bytes)
│   └── project details.md      # Technical documentation (45 KB)
│
└── 🔐 Version Control
    ├── .git/                   # Git repository
    └── .gitignore             # Git ignore rules (1.2 KB)

📦 Build Outputs (Generated during build - not in git)
├── build/                      # PyInstaller build artifacts
├── dist/                       # Distribution folder
│   └── OLR8A.exe              # Final executable (~50 MB)
└── Output/                     # Inno Setup installer output
    └── OLR8A_Setup_v1.0.0.exe # Windows installer (~70 MB)

📥 Required Download (Manual)
└── gs10060w64.exe             # GhostScript installer (~54 MB)
                                # Download from: https://ghostscript.com/releases/gsdnld.html
```

---

## 📋 File Descriptions

### Core Application Files

| File | Size | Purpose | Required |
|------|------|---------|----------|
| `lrms_app.py` | 262 KB | Main application with GUI, automation logic, Proclamation PDF upload | ✅ Critical |
| `telemetry.py` | 6.1 KB | Google Sheets telemetry tracking | ⚠️ Optional |
| `saccess_login.py` | 8.9 KB | Legacy SACCESS login module | ✅ Required |
| `gs_installer.py` | 8.5 KB | GhostScript auto-installer helper | ✅ Required |

### Build Configuration

| File | Purpose | When to Edit |
|------|---------|--------------|
| `requirements.txt` | Lists all Python dependencies | When adding new packages |
| `OLR8A.spec` | PyInstaller configuration | To change bundled files or build settings |
| `build_complete.bat` | Automated build script | To add build steps or validation |
| `installer.iss` | Inno Setup installer config | To change installer behavior |

### Documentation

| File | Audience | Purpose |
|------|----------|---------|
| `README.md` | Everyone | Project overview, quick start |
| `INSTALLATION_GUIDE.md` | End users | Step-by-step installation |
| `BUILD_INSTRUCTIONS.md` | Developers | How to build from source |
| `USER_MANUAL.md` | End users | Detailed usage guide |
| `QUICK_START.md` | New users | 5-minute getting started |

---

## 🛠️ Build Instructions

### Prerequisites

Before building, ensure you have:

1. **Python 3.10 or higher**
   ```bash
   python --version
   # Should show: Python 3.10.x or higher
   ```

2. **Git** (for version control)
   ```bash
   git --version
   ```

3. **All Python dependencies installed**
   ```bash
   pip install -r requirements.txt
   ```

4. **PyInstaller** (should be installed from requirements.txt)
   ```bash
   pip install pyinstaller
   ```

5. **Inno Setup** (for creating Windows installer - optional)
   - Download from: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

6. **GhostScript Installer** (for bundling - recommended)
   - Download `gs10060w64.exe` (~54 MB) from: https://ghostscript.com/releases/gsdnld.html
   - Place in project root folder: `/home/user/OLR-8A-/gs10060w64.exe`

---

## 📦 Building the EXE

### Method 1: Automated Build (Recommended)

**Step 1:** Ensure all prerequisites are met

**Step 2:** Download GhostScript installer (one-time)
```bash
# Download gs10060w64.exe from https://ghostscript.com/releases/gsdnld.html
# Place it in the project root folder
```

**Step 3:** Run the automated build script
```bash
build_complete.bat
```

The script will:
- ✅ Validate Python environment
- ✅ Check all dependencies
- ✅ Clean previous build artifacts
- ✅ Build EXE with PyInstaller
- ✅ Create Windows installer with Inno Setup
- ✅ Show detailed build summary

**Build Output:**
- `dist\OLR8A.exe` - Standalone executable (~50 MB)
- `Output\OLR8A_Setup_v1.0.0.exe` - Windows installer (~70 MB)

**Build Time:** 3-5 minutes

---

### Method 2: Manual Build (Step-by-Step)

If you prefer manual control or troubleshooting:

**Step 1: Clean previous builds**
```bash
# Remove build artifacts
rmdir /S /Q build
rmdir /S /Q dist
rmdir /S /Q Output
del /Q *.pyc
```

**Step 2: Install dependencies**
```bash
pip install -r requirements.txt --upgrade
```

**Step 3: Build with PyInstaller**
```bash
# Using the spec file (recommended)
python -m PyInstaller OLR8A.spec --clean --noconfirm

# OR manually (not recommended)
pyinstaller --onefile --windowed --icon=icon.ico --name=OLR8A lrms_app.py
```

**Step 4: Verify EXE created**
```bash
# Check if EXE exists
dir dist\OLR8A.exe
```

**Step 5: Create installer (optional)**
```bash
# If Inno Setup is installed
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 🧪 Testing the Build

### Test Standalone EXE

```bash
# Navigate to dist folder
cd dist

# Run the EXE
OLR8A.exe
```

**What to verify:**
- [ ] App launches without errors
- [ ] No console window appears (GUI mode)
- [ ] ChromeDriver downloads on first run (~30-60 seconds)
- [ ] GhostScript auto-installs if not present
- [ ] Login to SACCESS works
- [ ] Excel file loading works
- [ ] PDF upload works (regular + Proclamation)
- [ ] Batch processing works

### Test Windows Installer

```bash
# Run as Administrator
Output\OLR8A_Setup_v1.0.0.exe
```

**What to verify:**
- [ ] Installer wizard launches
- [ ] GhostScript installs silently
- [ ] Desktop shortcut created
- [ ] Start Menu entry created
- [ ] App launches from shortcuts
- [ ] All features work

---

## 📐 What Gets Bundled in the EXE

### Included in EXE:
- ✅ Python 3.10+ interpreter
- ✅ All Python packages (customtkinter, selenium, pandas, openpyxl, etc.)
- ✅ Application modules (telemetry, gs_installer)
- ✅ Icon file (icon.ico)
- ✅ Logic CSV (20 questions logic.csv)
- ✅ Google Sheets credentials (gsheet_creds.json) - if present
- ✅ GhostScript installer (gs10060w64.exe) - if present in root

### NOT Bundled (Downloaded at Runtime):
- ❌ ChromeDriver (~20 MB) - auto-downloaded by webdriver-manager on first run
- ❌ Google Chrome browser - user must install separately

### Why ChromeDriver is not bundled:
- Chrome updates frequently, requiring matching ChromeDriver versions
- Auto-download ensures compatibility with user's Chrome version
- Keeps EXE size smaller

---

## 🔍 Troubleshooting Build Issues

### Issue: "Python not found"
**Solution:**
```bash
# Check Python installation
python --version

# Ensure Python is in PATH
# Add to PATH: C:\Python310\ and C:\Python310\Scripts\
```

### Issue: "pip not found"
**Solution:**
```bash
# Install pip
python -m ensurepip --upgrade

# Or reinstall Python with "Add to PATH" checked
```

### Issue: "PyInstaller failed"
**Solution:**
```bash
# Clear cache and retry
rmdir /S /Q build
rmdir /S /Q dist
python -m PyInstaller OLR8A.spec --clean --noconfirm

# If still fails, check antivirus - may be blocking PyInstaller
# Add exclusion for project folder
```

### Issue: "Import errors in built EXE"
**Solution:**
```bash
# Edit OLR8A.spec and add missing module to hiddenimports:
hiddenimports=[
    'missing_module_name',
    # ... other modules
]

# Rebuild
python -m PyInstaller OLR8A.spec --clean --noconfirm
```

### Issue: "EXE too large (>100 MB)"
**Solution:**
```bash
# Enable UPX compression in OLR8A.spec:
exe = EXE(
    # ...
    upx=True,  # Enable compression
    # ...
)

# Exclude unnecessary packages:
excludes=[
    'matplotlib',
    'scipy',
    'numpy',  # Only if pandas doesn't need it
]
```

### Issue: "Inno Setup not found"
**Solution:**
```bash
# Download and install Inno Setup from:
# https://jrsoftware.org/isdl.php

# Or skip installer creation and use standalone EXE:
dist\OLR8A.exe
```

---

## 📊 Build Artifact Sizes

| Artifact | Size | Description |
|----------|------|-------------|
| **Standalone EXE** | ~50 MB | Single-file executable (with UPX compression) |
| **Windows Installer** | ~70 MB | Includes EXE + GhostScript + docs |
| **GhostScript Bundled** | ~54 MB | Bundled in installer for offline installation |
| **ChromeDriver** | ~20 MB | NOT bundled, downloads on first run |

**Total Download for End Users:** ~70 MB (installer)

---

## 🚀 Distribution

### For End Users:

**Recommended:** Distribute the Windows installer
```
Output\OLR8A_Setup_v1.0.0.exe  (~70 MB)
```

**Advantages:**
- ✅ Automatic GhostScript installation
- ✅ Desktop and Start Menu shortcuts
- ✅ Uninstaller included
- ✅ Documentation bundled
- ✅ Professional user experience

**Alternative:** Distribute standalone EXE
```
dist\OLR8A.exe  (~50 MB)
```

**Advantages:**
- ✅ Smaller download
- ✅ No installation required (portable)
- ✅ Can run from USB stick

**Disadvantages:**
- ⚠️ User must install GhostScript manually (or app auto-installs via winget)
- ⚠️ No shortcuts created automatically

---

## 🔄 Updating the Application

### For New Features:

1. **Modify source code** (lrms_app.py)
2. **Test changes** in development
   ```bash
   python lrms_app.py
   ```

3. **Update version** in:
   - `installer.iss` → Line 2: `#define MyAppVersion "1.x.x"`
   - `OLR8A.spec` → Comments

4. **Rebuild**
   ```bash
   build_complete.bat
   ```

5. **Test the new build**
   ```bash
   dist\OLR8A.exe
   ```

6. **Commit and tag**
   ```bash
   git add -A
   git commit -m "Version 1.x.x - New feature description"
   git tag v1.x.x
   git push --tags
   ```

7. **Create GitHub Release**
   - Upload `Output\OLR8A_Setup_v1.x.x.exe`
   - Add release notes

---

## 📝 Customization

### Change Application Icon:

1. Replace `icon.ico` with your icon
2. Rebuild

### Change Application Name:

1. Edit `OLR8A.spec`:
   ```python
   name='YourAppName',
   ```

2. Edit `installer.iss`:
   ```pascal
   #define MyAppName "Your App Name"
   ```

3. Rebuild

### Add More Files to Bundle:

1. Edit `OLR8A.spec`, add to `datas_list`:
   ```python
   datas_list.append(('your_file.ext', 'destination_folder'))
   ```

2. Rebuild

---

## ✅ Build Checklist

Before building for release:

- [ ] All Python dependencies installed
- [ ] `requirements.txt` up to date
- [ ] All source code committed to git
- [ ] Version numbers updated (installer.iss)
- [ ] GhostScript installer downloaded (gs10060w64.exe)
- [ ] Tested application in development mode
- [ ] No hardcoded credentials in source code
- [ ] Documentation updated
- [ ] Release notes prepared

---

## 🎯 Quick Reference

**Build EXE only:**
```bash
python -m PyInstaller OLR8A.spec --clean --noconfirm
```

**Build installer only (requires EXE first):**
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

**Complete automated build:**
```bash
build_complete.bat
```

**Test EXE:**
```bash
dist\OLR8A.exe
```

**Clean all build artifacts:**
```bash
rmdir /S /Q build dist Output
```

---

## 📞 Support

- **Issues:** https://github.com/sks623/OLR-8A-/issues
- **Documentation:** See `/docs` folder in Start Menu after installation
- **Build Problems:** Check troubleshooting section above

---

**Last Updated:** 2026-02-13
**Build System Version:** 2.0
