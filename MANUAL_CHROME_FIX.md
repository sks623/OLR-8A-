# 🐢 Manual Chrome Driver Fix (For Slow Internet/Old Laptops)

If the app hangs at "Initializing Chrome..." for more than 2 minutes, the auto-downloader is struggling. You can fix this manually once, and it will work forever.

## Step 1: Check your Chrome Version
1. Open **Google Chrome**.
2. Click the 3 dots (top right) -> **Help** -> **About Google Chrome**.
3. Note the version (e.g., `120.0.6099.109`).

## Step 2: Download the Driver
1. Go to this official site:
   - For Chrome 115 and newer: [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
   - For older Chrome: [Chromedriver Downloads](https://chromedriver.chromium.org/downloads)
2. Find the version that matches yours (e.g., `120...`).
3. Click to download the **win32** or **win64** `chromedriver.zip`.

## Step 3: Install it
1. Unzip the downloaded file. You will see `chromedriver.exe`.
2. Copy `chromedriver.exe`.
3. Paste it into the **same folder** where your `OLR8A.exe` (or python script) is located.
   *(Or paste it into `C:\Windows\System32` to make it global)*

## Step 4: Restart App
Run the app again. It will find the local file instantly and skip the download. 🚀
