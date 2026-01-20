# Quick Start Guide

Get the OLR 8A Automation Tool running in 5 minutes.

## Installation

### Step 1: Download
Download `OLR8A_Setup.exe` from the releases page.

### Step 2: Run Installer
1. Right-click the installer → "Run as Administrator"
2. Accept Windows security prompts
3. Follow the installation wizard
4. GhostScript will be installed automatically

### Step 3: Launch
Double-click the "OLR 8A Automation" shortcut on your desktop.

---

## First Run

### 1. Browser Opens
A Chrome browser window will open automatically.

### 2. Login to SACCESS
1. Navigate to the SACCESS portal
2. Enter your credentials
3. Complete OTP verification manually
4. Click on LRMS_Odisha application

### 3. Return to App
After logging in, return to the OLR 8A application window.

---

## Loading Cases

### Step 1: Go to Setup Tab
Click on the "Setup" tab in the application.

### Step 2: Load Excel File
1. Click "Load Excel"
2. Select your case data file
3. Cases will be displayed:
   - **Green** = Forward cases (approval)
   - **Red** = Reject cases (rejection)

### Step 3: Map PDF Folder
1. Click "Select PDF Folder"
2. Choose the folder containing your sketch map PDFs
3. PDFs should be named with case numbers (e.g., `10001-25.pdf`)

---

## Processing Cases

### Step 1: Go to Forwarding Tab
Click on the "Forwarding" tab.

### Step 2: Choose Case Type
- Click "Forward Cases" sub-tab for approvals
- Click "Reject Cases" sub-tab for rejections

### Step 3: Configure Settings
1. Set Q4 (Legal Dispute): Usually "No"
2. Set Q5 (Jurisdiction): "Municipality" or "GP/NAC"
3. Set Purpose: Usually "HOMESTEAD"
4. Click "Apply Global" to save as defaults

### Step 4: Start Batch
1. Click "Start Batch"
2. Watch the log for progress
3. Wait for completion

### Step 5: Export Results
1. Click "Export Status Log"
2. Choose save location
3. Excel file with results will be created

---

## Folder Structure

Organize your files like this:

```
Your_Work_Folder/
├── Cases.xlsx              # Your case data
├── PDFs/                   # Sketch map PDFs
│   ├── 10001-25.pdf
│   ├── 10002-25.pdf
│   └── ...
└── compressed_pdfs/        # Auto-created
```

---

## Tips

1. **PDF Names:** Name PDFs with case numbers for automatic matching
2. **PDF Size:** Keep PDFs under 295KB (GhostScript will try to compress larger ones)
3. **Internet:** Ensure stable internet connection during batch processing
4. **Don't Close Browser:** Keep the Chrome window open during processing

---

## Next Steps

- Read [User Manual](USER_MANUAL.md) for detailed instructions
- Check [Technical Documentation](CLAUDE.md) for troubleshooting
