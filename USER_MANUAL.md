# OLR 8A - User Manual

Complete guide to using the LRMS Automation Tool.

---

## Table of Contents

1. [Installation](#installation)
2. [File Locations](#file-locations)
3. [First Run Setup](#first-run-setup)
4. [Using the Application](#using-the-application)
5. [Features](#features)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### Step 1: Download
Download `OLR8A_Setup.exe` from the releases page.

### Step 2: Run Installer
1. Right-click → "Run as Administrator"
2. Accept Windows security prompts if they appear
3. Follow the installation wizard:
   - Choose installation directory (default: `C:\Program Files\OLR8A\`)
   - Select Start Menu folder
   - Choose whether to create desktop shortcut
4. Click "Install"

### Step 3: GhostScript Installation
The installer will automatically install GhostScript for PDF compression.
- **Location:** `C:\Program Files\gs\gs10.02.1\`
- **No manual setup required**

### Step 4: ChromeDriver
ChromeDriver updates automatically on each launch.
- No manual download needed
- Always matches your Chrome version
- Stored in: `C:\Users\[YourName]\.wdm\drivers\`

---

## File Locations

### Installation Directory
`C:\Program Files\OLR8A\`
```
OLR8A/
├── OLR8A.exe           # Main application
├── telemetry.py        # Usage tracking
├── gsheet_creds.json   # API credentials (do not delete)
└── _internal/          # Application resources
```

### User Data Directory
`C:\Users\[YourName]\AppData\Roaming\OLR8A\`
```
OLR8A/
├── installed.flag      # Installation marker
├── machine_id          # Unique machine identifier
├── settings.json       # Your preferences (if saved)
└── logs/               # Application logs
```

### Compressed PDFs
`[Your Excel Directory]\compressed_pdfs\`
- Created automatically when processing PDFs
- Contains compressed versions of sketch maps
- Safe to delete after processing

### ChromeDriver Cache
`C:\Users\[YourName]\.wdm\drivers\chromedriver\`
- Automatically managed
- Updated when Chrome updates

---

## First Run Setup

### 1. Launch Application
Double-click "OLR 8A Automation" from desktop or Start Menu.

### 2. Chrome Browser Opens
A new Chrome window will open automatically for automation.

### 3. Login to SACCESS Portal
1. Navigate to the SACCESS portal URL
2. Enter your username and password
3. Complete OTP verification (manual step)
4. Click on "LRMS_Odisha" application

### 4. Return to Application
After logging in, the browser stays open. Return to the OLR 8A window.

---

## Using the Application

### Tab 1: Setup

#### Loading Excel File
1. Click "Load Excel"
2. Select your case data file (.xlsx or .xls)
3. Required columns:
   - Case No
   - Name
   - Plot No
   - Village (English) or Mouza

#### Previewing Cases
After loading:
- **Green rows** = Forward cases (eligible for approval)
- **Red rows** = Reject cases (to be rejected)
- **Gray rows** = Issues (missing data, etc.)

#### Mapping PDFs
1. Click "Select PDF Folder"
2. Choose folder containing sketch maps
3. PDFs should be named: `[CaseNo].pdf` (e.g., `10001-25.pdf`)
4. Status shows matched/unmatched PDFs

---

### Tab 2: Valuation

#### Running IGR Valuations
1. Select cases to valuate (or use "Select All")
2. Click "Start Valuation"
3. System will:
   - Open IGR Odisha portal
   - Search each case
   - Extract market values
   - Calculate fees automatically

#### Fee Calculations
- **LR (Land Revenue)** = Market Value × 0.01%
- **Cess** = LR × 75%
- **Conversion Fee** = Market Value × 1%

#### Exporting Results
Click "Export to Excel" to save valuation results.

---

### Tab 3: Forwarding

#### Selecting Case Type
- **Forward Cases sub-tab:** For approval cases
- **Reject Cases sub-tab:** For rejection cases

#### Global Settings
Configure default values for all cases:
1. **Q4 (Legal Dispute):** Usually "No"
2. **Q5 (Jurisdiction):** "Municipality" or "GP/NAC"
3. **Purpose:** "HOMESTEAD", "COMMERCIAL", etc.
4. Click "Apply Global" to save

#### Per-Case Overrides
To set different values for specific cases:
1. Select the case in the list
2. Modify Q4, Q5, Purpose as needed
3. Click "Save Override"

#### Order Sheet Template
1. Write your order sheet template in the text box
2. Use placeholders:
   - `<name>` - Applicant name
   - `<plots 1>`, `<plots 2>` - Plot numbers
   - `<village>` - Village name
   - `<LR>`, `<CESS>`, `<CONVERSION FEE>` - Fee values
3. Click "Apply Global" to use for all cases

#### Starting Batch Processing
1. Ensure browser is logged into LRMS portal
2. Click "Start Batch"
3. Watch the log panel for progress
4. **Do not close the browser during processing**

#### Exporting Results
After batch completes:
1. Click "Export Status Log"
2. Choose save location
3. Excel file created with:
   - Case No
   - Type (Forward/Reject)
   - Status (Success/Failed)
   - Error message (if any)
   - Timestamp

---

## Features

### Automatic PDF Compression
- PDFs over 295KB are automatically compressed
- Uses GhostScript with dynamic settings
- Tries `/ebook` first, then `/screen` if needed
- Warning shown if still over limit after compression

### Global vs Per-Case Settings
| Setting | Global | Per-Case |
|---------|--------|----------|
| Q4 | Apply to all | Override specific case |
| Q5 | Apply to all | Override specific case |
| Purpose | Apply to all | Override specific case |
| Order Sheet | Apply to all | Override specific case |

### Batch Processing Flow
1. Search for case number
2. Click "View" to open form
3. Fill 20 questions
4. Upload PDF
5. Fill fee fields
6. Click SAVE
7. Fill order sheet
8. Click SAVE ORDER SHEET
9. Click FORWARD TO MUTATION OFFICER
10. Repeat for next case

---

## Troubleshooting

### "ChromeDriver version mismatch"
**Cause:** Chrome browser updated but ChromeDriver hasn't updated yet.
**Solution:**
1. Close the application
2. Restart the application (auto-updates ChromeDriver)
3. If persists, delete `C:\Users\[YourName]\.wdm\` folder and restart

### "GhostScript not found"
**Cause:** GhostScript not installed or not in PATH.
**Solution:**
1. Reinstall the application, OR
2. Manually install GhostScript from [ghostscript.com](https://ghostscript.com)
3. Add to PATH: `C:\Program Files\gs\gs10.02.1\bin`

### "PDF still too large after compression"
**Cause:** PDF has high-resolution images that can't be compressed further.
**Solution:**
1. Open PDF in image editor
2. Reduce resolution/quality manually
3. Save and reload

### "Cases not appearing"
**Cause:** Excel file doesn't have required columns.
**Solution:**
1. Ensure these columns exist:
   - Case No
   - Name
   - Plot No
   - Village (English) OR Mouza
2. Check for typos in column headers

### "Upload sketchmap error"
**Cause:** PDF upload failed or wasn't detected.
**Solution:**
1. Check PDF exists in mapped folder
2. Check PDF name matches case number
3. Check PDF size is under 295KB
4. Retry the case

### "Alert timeout / 2-minute hang"
**Cause:** Multi-window focus issue (rare).
**Solution:**
1. Close IGR Odisha window if open
2. Keep only LRMS browser window open
3. Retry the batch

### "Order sheet None error"
**Cause:** Missing village data in Excel.
**Solution:**
1. Ensure "Village (English)" column has data
2. Or ensure "Mouza" column has data as fallback

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Load Excel | Ctrl+O |
| Start Batch | Ctrl+Enter |
| Stop Batch | Esc |
| Export Log | Ctrl+E |

---

## Support

For issues not covered here:
1. Check the log panel for specific error messages
2. Review [Technical Documentation](CLAUDE.md)
3. Contact the developer

---

**Version:** 1.0.0
**Last Updated:** January 2026
