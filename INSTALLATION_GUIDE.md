# OLR 8A - Complete Installation Guide for Older Computers

This guide provides step-by-step instructions for installing and running OLR 8A on older computers with limited resources or slow internet connections.

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Method 1: Using Pre-built EXE Setup (Recommended)](#method-1-exe-installer-recommended)
3. [Installation Method 2: Installing from GitHub Source](#method-2-installing-from-github-source)
4. [Manual ChromeDriver Installation](#manual-chromedriver-installation-optional)
5. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements:
- **Operating System:** Windows 7/8/10/11 (64-bit)
- **RAM:** 4 GB minimum, 8 GB recommended
- **Disk Space:** 500 MB free space
- **Internet:** Required for first-time ChromeDriver download and LRMS access
- **Software:** Google Chrome browser (latest version)

### Additional Requirements:
- Microsoft Edge WebView2 Runtime (usually pre-installed on Windows 10/11)
- GhostScript (automatically installed with EXE installer)

---

## Method 1: EXE Installer (Recommended)

This is the easiest method for older computers. The installer includes all dependencies.

### Step 1: Download the Installer

**Option A: From GitHub Releases (if available)**
1. Open your web browser
2. Go to: `https://github.com/sks623/OLR-8A-/releases`
3. Look for the latest release
4. Download the file: `OLR8A_Setup_v1.0.0.exe`
5. Save it to your `Downloads` folder

**Option B: From Developer**
If releases are not yet published, contact the developer to get the installer file.

### Step 2: Run the Installer

1. Navigate to your `Downloads` folder
2. **Right-click** on `OLR8A_Setup_v1.0.0.exe`
3. Select **"Run as administrator"**
   - ⚠️ Important: Administrator access is required to install GhostScript

4. If Windows SmartScreen appears:
   - Click **"More info"**
   - Click **"Run anyway"**

5. Follow the installation wizard:
   - Click **"Next"**
   - Choose installation location (default: `C:\Program Files\OLR8A`)
   - Select **"Create desktop icon"** (recommended)
   - Click **"Install"**

6. Wait for installation (2-3 minutes):
   - The installer will install the application
   - GhostScript will be installed automatically (if not already present)
   - PATH environment variables will be configured

7. Click **"Finish"** when installation completes
   - Check **"Launch OLR 8A Automation"** if you want to start immediately

### Step 3: First Launch

1. Double-click the **"OLR 8A Automation"** desktop icon

2. **First launch may take 30-60 seconds** on older computers because:
   - The app needs to download ChromeDriver (20-30 MB)
   - This happens only once
   - A message will appear: "⏳ Initializing ChromeDriver..."

3. If it takes too long (more than 2 minutes):
   - The app will show: "⚠ ChromeDriver preparation timed out"
   - Don't worry! It will try again when you click "Start Browser"
   - See [Manual ChromeDriver Installation](#manual-chromedriver-installation-optional) for faster setup

4. Once loaded, you should see the main application window

### Step 4: Verify Installation

1. Open the application
2. Go to **Tab 1: Setup**
3. Click **"Test Connection"** (if available)
4. If Chrome opens successfully, installation is complete ✓

---

## Method 2: Installing from GitHub Source

This method requires Python and is recommended for developers or users who need to customize the application.

### Step 1: Install Python

1. **Download Python 3.10 or 3.11:**
   - Go to: `https://www.python.org/downloads/`
   - Download **Python 3.10.11** (stable for older systems)
   - **Do NOT download Python 3.12** (may have compatibility issues)

2. **Run the Python installer:**
   - Check ☑ **"Add Python to PATH"** (VERY IMPORTANT!)
   - Click **"Install Now"**
   - Wait 3-5 minutes for installation

3. **Verify Python installation:**
   - Press `Windows + R`
   - Type: `cmd` and press Enter
   - Type: `python --version`
   - You should see: `Python 3.10.11` or similar

### Step 2: Install Git

1. **Download Git:**
   - Go to: `https://git-scm.com/download/win`
   - Download the installer (Git-2.43.0-64-bit.exe or later)

2. **Run Git installer:**
   - Use default settings (just click "Next" for everything)
   - Wait for installation to complete

3. **Verify Git installation:**
   - Open Command Prompt (Windows + R, type `cmd`)
   - Type: `git --version`
   - You should see: `git version 2.43.0` or similar

### Step 3: Download the Project from GitHub

1. **Create a folder for the project:**
   ```batch
   cd C:\
   mkdir Projects
   cd Projects
   ```

2. **Clone the repository:**
   ```batch
   git clone https://github.com/sks623/OLR-8A-.git
   cd OLR-8A-
   ```

   **If you have slow internet:**
   - This may take 5-10 minutes depending on connection speed
   - The download is approximately 50-100 MB

3. **Verify files are downloaded:**
   ```batch
   dir
   ```
   You should see files like:
   - `lrms_app.py`
   - `requirements.txt`
   - `README.md`
   - And many others

### Step 4: Install Python Dependencies

1. **Still in Command Prompt, in the project folder:**
   ```batch
   python -m pip install --upgrade pip
   ```

2. **Install all required packages:**
   ```batch
   pip install -r requirements.txt
   ```

   **On older computers:**
   - This may take 10-15 minutes
   - You'll see many packages being downloaded
   - Total download size: ~200-300 MB

   **If you get errors:**
   - Make sure you're connected to the internet
   - Try closing and reopening Command Prompt (run as Administrator)
   - Run: `pip install --upgrade setuptools wheel` then try again

### Step 5: Install GhostScript

**Option A: Automatic (Windows 10/11 with winget)**
```batch
winget install -e --id ArtifexSoftware.GhostScript
```

**Option B: Manual Installation (All Windows versions)**
1. Go to: `https://ghostscript.com/releases/gsdnld.html`
2. Download: **Ghostscript 10.06.0 for Windows (64 bit)**
3. Run the installer
4. Use default installation path: `C:\Program Files\gs\gs10.06.0`

### Step 6: Add Required Files

1. **Get Google Sheets credentials** (contact developer):
   - You need a file called `gsheet_creds.json`
   - Place it in the project folder: `C:\Projects\OLR-8A-\gsheet_creds.json`

2. **Verify file structure:**
   ```batch
   dir gsheet_creds.json
   ```
   You should see the file listed

### Step 7: Run the Application

1. **In Command Prompt, navigate to project folder:**
   ```batch
   cd C:\Projects\OLR-8A-
   ```

2. **Run the application:**
   ```batch
   python lrms_app.py
   ```

3. **First launch:**
   - May take 30-60 seconds to download ChromeDriver
   - You'll see: "⏳ Initializing ChromeDriver..."
   - Wait patiently (do NOT close the window)

4. **Application should open** with the main interface

### Step 8: Create Desktop Shortcut (Optional)

1. Right-click on Desktop
2. Select: **New → Shortcut**
3. For location, enter:
   ```
   python C:\Projects\OLR-8A-\lrms_app.py
   ```
4. Name it: `OLR 8A`
5. Click **Finish**

---

## Manual ChromeDriver Installation (Optional)

If ChromeDriver download is taking too long or failing on older computers, follow these steps to install it manually.

### Step 1: Check Your Chrome Version

1. Open Google Chrome
2. Click the three dots (⋮) in the top-right corner
3. Go to: **Help → About Google Chrome**
4. Note the version number (e.g., **120.0.6099.109**)
5. The first number is important (e.g., **120**)

### Step 2: Download Matching ChromeDriver

**For Chrome 115 and newer:**
1. Go to: `https://googlechromelabs.github.io/chrome-for-testing/`
2. Find your Chrome version (e.g., 120)
3. Under "Stable", find **chromedriver win64**
4. Click the download link
5. Download the ZIP file

**For Chrome 114 and older:**
1. Go to: `https://chromedriver.chromium.org/downloads`
2. Find the version matching your Chrome
3. Click the version number
4. Download: `chromedriver_win32.zip`

### Step 3: Extract ChromeDriver

1. Open the downloaded ZIP file
2. Extract `chromedriver.exe` to a permanent location:
   - Recommended: `C:\Program Files\ChromeDriver\chromedriver.exe`
   - Or: `C:\Tools\chromedriver.exe`

3. **Important:** Remember this path!

### Step 4: Add ChromeDriver to PATH

**Option A: Using System Environment Variables (Recommended)**

1. Press `Windows + R`
2. Type: `sysdm.cpl` and press Enter
3. Click **"Advanced"** tab
4. Click **"Environment Variables"**
5. Under **"System variables"**, find **"Path"**
6. Click **"Edit"**
7. Click **"New"**
8. Type: `C:\Program Files\ChromeDriver`
9. Click **"OK"** on all windows
10. **Restart Command Prompt** (close and reopen)

**Option B: Quick Test (Temporary)**

1. Open Command Prompt
2. Type:
   ```batch
   set PATH=%PATH%;C:\Program Files\ChromeDriver
   ```
3. This works only for current Command Prompt session

### Step 5: Verify ChromeDriver Installation

1. Open Command Prompt
2. Type:
   ```batch
   chromedriver --version
   ```
3. You should see: `ChromeDriver 120.0.6099.109` or similar

### Step 6: Configure OLR 8A to Use Manual ChromeDriver

If you installed ChromeDriver manually and webdriver_manager still causes issues:

1. Open: `C:\Projects\OLR-8A-\lrms_app.py` in Notepad
2. Search for: `Service(ChromeDriverManager().install())`
3. Replace with: `Service("C:\\Program Files\\ChromeDriver\\chromedriver.exe")`
4. Save the file
5. Run the application

**Note:** This disables automatic updates. You'll need to manually update ChromeDriver when Chrome updates.

---

## Troubleshooting

### Issue 1: Application Won't Start

**Symptoms:**
- Double-clicking does nothing
- Window opens then immediately closes

**Solutions:**

1. **Check Python installation (for source install):**
   ```batch
   python --version
   ```
   Should show Python 3.10 or 3.11

2. **Run from Command Prompt to see errors:**
   ```batch
   cd C:\Projects\OLR-8A-
   python lrms_app.py
   ```
   Read any error messages

3. **Missing dependencies:**
   ```batch
   pip install -r requirements.txt --force-reinstall
   ```

### Issue 2: Stuck on "Initializing ChromeDriver"

**Symptoms:**
- Application shows "⏳ Initializing ChromeDriver..." for more than 2 minutes
- Progress bar not moving

**Solutions:**

1. **Check internet connection:**
   - ChromeDriver downloads from Google servers (20-30 MB)
   - Requires stable internet connection

2. **Wait longer:**
   - On very slow connections (256 kbps), it may take 5-10 minutes
   - Look for progress messages in the console

3. **Manual ChromeDriver installation:**
   - Follow [Manual ChromeDriver Installation](#manual-chromedriver-installation-optional) section above

4. **Clear ChromeDriver cache:**
   - Press `Windows + R`
   - Type: `%USERPROFILE%\.wdm` and press Enter
   - Delete all folders inside
   - Restart the application

### Issue 3: Chrome Won't Open

**Symptoms:**
- Error: "Chrome failed to start"
- Error: "SessionNotCreatedException"

**Solutions:**

1. **Update Google Chrome:**
   - Open Chrome
   - Go to: chrome://settings/help
   - Wait for automatic update
   - Restart Chrome

2. **ChromeDriver version mismatch:**
   - Follow [Manual ChromeDriver Installation](#manual-chromedriver-installation-optional)
   - Ensure ChromeDriver version matches Chrome version

3. **Run as Administrator:**
   - Right-click application icon
   - Select "Run as administrator"

### Issue 4: GhostScript Not Found

**Symptoms:**
- Error: "GhostScript is not installed"
- PDF compression fails

**Solutions:**

1. **Verify GhostScript installation:**
   - Press `Windows + R`
   - Type: `gswin64c -version`
   - Should show version number

2. **Reinstall GhostScript:**
   - Go to: `https://ghostscript.com/releases/gsdnld.html`
   - Download and install latest version

3. **Add to PATH manually:**
   - Default location: `C:\Program Files\gs\gs10.06.0\bin`
   - Add to System PATH (see ChromeDriver PATH instructions)

### Issue 5: Permission Denied Errors

**Symptoms:**
- "Access denied" when running installer
- "Permission denied" when accessing files

**Solutions:**

1. **Run as Administrator:**
   - Right-click the application or installer
   - Select "Run as administrator"

2. **Check antivirus:**
   - Some antivirus software blocks Python/Selenium
   - Add exception for OLR8A folder

3. **Disable UAC temporarily (advanced users):**
   - Not recommended for security reasons
   - Only if other solutions fail

### Issue 6: Excel File Won't Load

**Symptoms:**
- "Failed to load Excel file"
- Cases not appearing

**Solutions:**

1. **Check Excel file format:**
   - Must be `.xlsx` or `.xls`
   - Must have correct column names (Case No, Name, Plot No, etc.)

2. **Close Excel file:**
   - Excel must NOT be open when loading into application
   - Close all Excel windows

3. **Check file permissions:**
   - Ensure file is not read-only
   - Right-click file → Properties → Uncheck "Read-only"

### Issue 7: Slow Performance on Older Computers

**Solutions:**

1. **Close unnecessary programs:**
   - Close Chrome tabs
   - Close other applications
   - Check Task Manager for CPU/Memory usage

2. **Increase virtual memory:**
   - Right-click "This PC" → Properties → Advanced system settings
   - Performance → Settings → Advanced → Virtual memory
   - Change → Custom size → Set to 8000 MB minimum and maximum

3. **Disable Windows visual effects:**
   - System Properties → Advanced → Performance Settings
   - Select "Adjust for best performance"

### Issue 8: Cannot Connect to LRMS Portal

**Symptoms:**
- Browser opens but site won't load
- Connection timeout errors

**Solutions:**

1. **Check LRMS portal status:**
   - Try accessing manually: `https://lrms.odisha.gov.in`
   - Portal may be down for maintenance

2. **Network issues:**
   - Check internet connection
   - Try different network (mobile hotspot)
   - Disable VPN if enabled

3. **Browser cache:**
   - Clear Chrome cache: `chrome://settings/clearBrowserData`

---

## Getting Help

If you continue to face issues:

1. **Check log files:**
   - Located in application folder
   - Look for `error.log` or console output

2. **Contact Developer:**
   - Provide error messages
   - Include Windows version and computer specs
   - Describe what you were doing when error occurred

3. **GitHub Issues:**
   - Report bugs at: `https://github.com/sks623/OLR-8A-/issues`
   - Search existing issues first

---

## Appendix: Offline ChromeDriver Installation

For computers with **no internet connection**, you can transfer ChromeDriver manually:

### On Computer with Internet:
1. Download ChromeDriver as described in [Manual ChromeDriver Installation](#manual-chromedriver-installation-optional)
2. Copy `chromedriver.exe` to USB drive

### On Offline Computer:
1. Copy `chromedriver.exe` from USB to: `C:\Program Files\ChromeDriver\`
2. Add to PATH (see Step 4 in Manual ChromeDriver Installation)
3. Follow Step 6 to modify `lrms_app.py` to use hardcoded path

---

## Version Information

- **Guide Version:** 1.0
- **Application Version:** 1.0.0
- **Last Updated:** January 2026
- **Tested On:** Windows 7, 8, 10, 11

---

**Developer:** Sushant
**License:** Proprietary - Unauthorized distribution prohibited
