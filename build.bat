@echo off
echo ========================================
echo OLR 8A - Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Check if required files exist
if not exist "lrms_app.py" (
    echo ERROR: lrms_app.py not found!
    pause
    exit /b 1
)

if not exist "telemetry.py" (
    echo ERROR: telemetry.py not found!
    pause
    exit /b 1
)

if not exist "gsheet_creds.json" (
    echo ERROR: gsheet_creds.json not found!
    pause
    exit /b 1
)

echo.
echo Step 1: Building EXE with PyInstaller...
echo ----------------------------------------
python -m PyInstaller OLR8A.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo Step 1 Complete: dist\OLR8A.exe created
echo.

REM Check if Inno Setup is installed
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup\ISCC.exe"
) else (
    echo.
    echo WARNING: Inno Setup not found!
    echo Please install from: https://jrsoftware.org/isdl.php
    echo Then manually compile installer.iss
    echo.
    echo EXE is ready at: dist\OLR8A.exe
    pause
    exit /b 0
)

REM Check if GhostScript installer exists
if not exist "gs10060w64.exe" (
    echo.
    echo WARNING: gs10060w64.exe not found!
    echo Download from: https://ghostscript.com/releases/gsdnld.html
    echo Place it in this folder, then run this script again.
    echo.
    echo EXE is ready at: dist\OLR8A.exe
    pause
    exit /b 0
)

echo Step 2: Building Installer with Inno Setup...
echo ----------------------------------------------
%ISCC% installer.iss

if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Installer ready at: Output\OLR8A_Setup_v1.0.0.exe
echo.
pause
