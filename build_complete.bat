@echo off
REM ============================================================
REM OLR 8A - Complete Automated Build Script
REM Builds EXE and creates installer package
REM ============================================================

echo.
echo ============================================================
echo            OLR 8A - COMPLETE BUILD SCRIPT
echo ============================================================
echo.
echo This script will:
echo  1. Check all prerequisites
echo  2. Build EXE with PyInstaller
echo  3. Create installer with Inno Setup
echo  4. Package everything for distribution
echo.
pause

REM ============================================================
REM STEP 1: Environment Check
REM ============================================================
echo.
echo [1/6] Checking Prerequisites...
echo ============================================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found:
python --version

REM Check PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INSTALLING] PyInstaller not found, installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller found

REM Check required files
if not exist "lrms_app.py" (
    echo [ERROR] lrms_app.py not found in current directory!
    echo Please run this script from the project root folder
    pause
    exit /b 1
)
echo [OK] lrms_app.py found

if not exist "telemetry.py" (
    echo [ERROR] telemetry.py not found!
    pause
    exit /b 1
)
echo [OK] telemetry.py found

if not exist "gsheet_creds.json" (
    echo [WARNING] gsheet_creds.json not found!
    echo The application will work but telemetry will be disabled
    echo Press any key to continue or Ctrl+C to cancel...
    pause
)
echo [OK] gsheet_creds.json found

if not exist "OLR8A.spec" (
    echo [ERROR] OLR8A.spec not found!
    pause
    exit /b 1
)
echo [OK] OLR8A.spec found

if not exist "icon.ico" (
    echo [WARNING] icon.ico not found!
    echo EXE will be built without custom icon
    pause
)
echo [OK] icon.ico found

REM ============================================================
REM STEP 2: Clean Previous Builds
REM ============================================================
echo.
echo [2/6] Cleaning Previous Builds...
echo ============================================================

if exist "build" (
    echo Removing old build folder...
    rmdir /S /Q build
)

if exist "dist" (
    echo Removing old dist folder...
    rmdir /S /Q dist
)

if exist "Output" (
    echo Removing old Output folder...
    rmdir /S /Q Output
)

echo [OK] Clean complete

REM ============================================================
REM STEP 3: Install Dependencies
REM ============================================================
echo.
echo [3/6] Installing/Verifying Dependencies...
echo ============================================================

if exist "requirements.txt" (
    echo Installing from requirements.txt...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [WARNING] Some dependencies failed to install
        echo Continuing anyway...
    ) else (
        echo [OK] Dependencies installed
    )
) else (
    echo [WARNING] requirements.txt not found, skipping dependency check
)

REM ============================================================
REM STEP 4: Build EXE with PyInstaller
REM ============================================================
echo.
echo [4/6] Building EXE with PyInstaller...
echo ============================================================
echo This may take 3-5 minutes...
echo.

python -m PyInstaller OLR8A.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build FAILED!
    echo.
    echo Common causes:
    echo  - Missing dependencies (run: pip install -r requirements.txt)
    echo  - Antivirus blocking PyInstaller
    echo  - Insufficient disk space
    echo.
    pause
    exit /b 1
)

if not exist "dist\OLR8A.exe" (
    echo [ERROR] dist\OLR8A.exe was not created!
    pause
    exit /b 1
)

echo.
echo [OK] EXE built successfully: dist\OLR8A.exe
echo.

REM ============================================================
REM STEP 5: Check Inno Setup
REM ============================================================
echo.
echo [5/6] Preparing Installer with Inno Setup...
echo ============================================================

set ISCC=

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup\ISCC.exe"
)

if "%ISCC%"=="" (
    echo [WARNING] Inno Setup not found!
    echo.
    echo To create the installer:
    echo  1. Download Inno Setup from: https://jrsoftware.org/isdl.php
    echo  2. Install it
    echo  3. Run this script again
    echo.
    echo [BUILD COMPLETE - EXE ONLY]
    echo EXE Location: dist\OLR8A.exe
    echo.
    pause
    exit /b 0
)

echo [OK] Inno Setup found: %ISCC%

REM Check GhostScript installer
if not exist "gs10060w64.exe" (
    echo [WARNING] gs10060w64.exe not found!
    echo.
    echo The installer will work, but GhostScript won't be bundled.
    echo.
    echo To bundle GhostScript:
    echo  1. Download from: https://ghostscript.com/releases/gsdnld.html
    echo  2. Get file: gs10060w64.exe
    echo  3. Place it in this folder
    echo  4. Run this script again
    echo.
    echo Press any key to continue WITHOUT GhostScript bundling...
    echo Or Ctrl+C to cancel and download it now
    pause
) else (
    echo [OK] GhostScript installer found
)

REM ============================================================
REM STEP 6: Build Installer
REM ============================================================
echo.
echo Building installer...
echo.

%ISCC% installer.iss

if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup compilation FAILED!
    echo.
    echo Check installer.iss for errors
    echo.
    pause
    exit /b 1
)

REM ============================================================
REM BUILD COMPLETE
REM ============================================================
echo.
echo ============================================================
echo                  BUILD SUCCESSFUL!
echo ============================================================
echo.
echo Files created:
echo.

if exist "dist\OLR8A.exe" (
    echo  [OK] Standalone EXE: dist\OLR8A.exe
    dir /B dist\OLR8A.exe | find /V "" >nul && for %%I in ("dist\OLR8A.exe") do echo       Size: %%~zI bytes
)

if exist "Output\OLR8A_Setup_v1.0.0.exe" (
    echo  [OK] Installer: Output\OLR8A_Setup_v1.0.0.exe
    for %%I in ("Output\OLR8A_Setup_v1.0.0.exe") do echo       Size: %%~zI bytes
) else (
    echo  [ ] Installer: Not created (Inno Setup or GhostScript missing)
)

echo.
echo Next steps:
echo  1. Test the EXE: Run dist\OLR8A.exe
echo  2. Test the installer: Run Output\OLR8A_Setup_v1.0.0.exe
echo  3. Distribute the installer to users
echo.
echo ============================================================
pause
