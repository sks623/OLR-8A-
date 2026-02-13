# Quick Build Instructions

## ⚡ Fast Track: Build the EXE

### Step 1: Prerequisites (One-time Setup)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install PyInstaller (if not in requirements.txt)
pip install pyinstaller
```

### Step 2: Download GhostScript Installer (Optional but Recommended)
- Download: https://ghostscript.com/releases/gsdnld.html
- Get file: `gs10060w64.exe` (~54 MB)
- Place in project root: `/home/user/OLR-8A-/`

### Step 3: Build
```bash
# Option A: Automated (Recommended)
build_complete.bat

# Option B: Manual
python -m PyInstaller OLR8A.spec --clean --noconfirm
```

### Step 4: Test
```bash
dist\OLR8A.exe
```

**Done! Your EXE is ready.**

---

## 📁 Key Files

| File | What It Does |
|------|--------------|
| `lrms_app.py` | Main application code |
| `OLR8A.spec` | PyInstaller build configuration |
| `build_complete.bat` | Automated build script |
| `requirements.txt` | Python dependencies |
| `gs_installer.py` | GhostScript auto-installer |

---

## 🎯 Build Outputs

After building, you'll have:

```
dist/
└── OLR8A.exe          # Standalone executable (~50 MB)

Output/                 # If Inno Setup installed
└── OLR8A_Setup_v1.0.0.exe  # Windows installer (~70 MB)
```

---

## 🔧 What Gets Included

**Bundled in EXE:**
- Python interpreter
- All packages (customtkinter, selenium, pandas, etc.)
- Your code (lrms_app, telemetry, gs_installer)
- Icon and resources
- GhostScript installer (if gs10060w64.exe is in root)

**Downloaded at Runtime:**
- ChromeDriver (~20 MB) - auto-downloads on first run
- Chrome browser - user must install separately

---

## 🐛 Common Issues

**"Module not found" error:**
```bash
# Add to OLR8A.spec hiddenimports:
hiddenimports=[
    'your_missing_module',
]
```

**"PyInstaller failed":**
```bash
# Clean and rebuild
rmdir /S /Q build dist
python -m PyInstaller OLR8A.spec --clean --noconfirm
```

**"Antivirus blocking":**
- Add project folder to antivirus exclusions

---

## 📚 Full Documentation

- **BUILD_GUIDE.md** - Complete build guide with directory map
- **DIRECTORY_MAP.txt** - Visual directory structure
- **BUILD_INSTRUCTIONS.md** - Detailed build instructions

---

## ✅ Quick Checklist

Before building:
- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] GhostScript installer downloaded (optional)
- [ ] Code tested in development mode

Build:
- [ ] Run `build_complete.bat` or `python -m PyInstaller OLR8A.spec`
- [ ] Check `dist\OLR8A.exe` exists
- [ ] Test the EXE

---

**Build Time:** 3-5 minutes
**Output Size:** ~50 MB (EXE) or ~70 MB (installer)
