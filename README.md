# OLR 8A - LRMS Automation Tool

Automated Land Records Management System (LRMS) Odisha case processing tool for OLR Section 8A land conversion cases.

## Features

- Batch processing of Forward cases
- Batch processing of Reject cases
- IGR Odisha valuation extraction
- Automatic form filling (20 questions)
- PDF sketch map upload with GhostScript compression
- Order sheet generation from templates
- Status log export to Excel
- Global and per-case overrides
- Automatic ChromeDriver updates

## Requirements

- Windows 10/11
- Google Chrome browser (latest version)
- Python 3.10+ (if running from source)
- GhostScript (bundled with installer)

## Quick Start

### Option 1: Using Installer (Recommended)
1. Download `OLR8A_Setup.exe` from Releases
2. Run installer (installs app + GhostScript)
3. Launch "OLR 8A Automation" from desktop
4. Login to SACCESS portal manually (OTP required)
5. Load your Excel file with case data
6. Configure settings and run batch

### Option 2: Running from Source
```bash
# Clone repository
git clone https://github.com/sks623/OLR-8A-.git
cd OLR-8A-

# Install dependencies
pip install -r requirements.txt

# Run application
python lrms_app.py
```

## Excel File Format

Your case data Excel file should have these columns:
- Case No
- Name (Applicant name)
- Plot No
- Village (English)
- Mouza
- Area
- Market Value (optional - can be fetched from IGR)

## Usage

### Tab 1: Setup
- Load your Excel file with case data
- Map PDF folder containing sketch maps
- Preview cases (Forward in green, Reject in red)

### Tab 2: Valuation
- Run IGR Odisha valuations
- Extract market values automatically
- Calculate fees (LR, Cess, Conversion Fee)

### Tab 3: Forwarding
- **Forward Cases sub-tab:** Process approval cases
- **Reject Cases sub-tab:** Process rejection cases
- Configure global settings (Q4, Q5, Purpose)
- Click "Apply Global" to save defaults
- Click "Start Batch" to begin processing
- Click "Export Status Log" to save results

## Documentation

- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [User Manual](USER_MANUAL.md) - Detailed usage instructions
- [Project Details](project%20details.md) - Technical documentation

## File Structure

```
OLR-8A-/
├── lrms_app.py          # Main application
├── requirements.txt     # Python dependencies
├── project details.md   # Technical documentation
├── README.md            # This file
├── QUICK_START.md       # Quick start guide
└── USER_MANUAL.md       # User manual
```

## Troubleshooting

### ChromeDriver Issues
The app automatically downloads the correct ChromeDriver version. If issues persist, restart the application.

### GhostScript Not Found
Reinstall the application or manually install GhostScript from [ghostscript.com](https://ghostscript.com/releases/gsdnld.html)

### PDF Too Large After Compression
Some PDFs cannot be compressed further. Try reducing the PDF quality manually before loading.

### Cases Not Appearing
Ensure your Excel file has the correct column names. Check the log for specific errors.

## License

This software is proprietary. Unauthorized distribution is prohibited.

## Support

For issues and feature requests, contact the developer.

---

**Developer:** Sushant
**Version:** 1.0.0
**Last Updated:** January 2026
