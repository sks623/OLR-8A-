"""
SACCESS NIC Login Automation Script (OTP Version)
==================================================
This script automates the login process for saccess.nic.in
The website uses OTP-based authentication (no captcha).

Login Flow:
    1. Enter username/password
    2. Click Sign-in
    3. OTP screen appears
    4. Click "Send OTP" button
    5. Enter OTP received on mobile
    6. Click Sign-in to complete login

Requirements:
    pip install selenium webdriver-manager
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class SACCESSLogin:
    def __init__(self, headless=False):
        """Initialize the browser with optional headless mode."""
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the driver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        self.wait = WebDriverWait(self.driver, 20)
        
    def navigate_to_site(self):
        """Navigate to the saccess.nic.in website."""
        print("🌐 Navigating to saccess.nic.in...")
        self.driver.get("https://saccess.nic.in")
        time.sleep(3)
        print("✅ Page loaded successfully!")
        return True
    
    def switch_to_login_frame(self):
        """Switch to the 'base' frame that contains the login form."""
        print("🔄 Switching to login frame...")
        try:
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "base")))
            print("✅ Switched to login frame!")
            return True
        except Exception as e:
            print(f"❌ Failed to switch to frame: {e}")
            return False
    
    def enter_credentials(self, username, password):
        """Enter login credentials (username and password only)."""
        try:
            # Enter username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "uname"))
            )
            username_field.clear()
            username_field.send_keys(username)
            print(f"👤 Username entered: {username}")
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            print("🔑 Password entered")
            
            return True
        except Exception as e:
            print(f"❌ Failed to enter credentials: {e}")
            return False
    
    def click_first_signin(self):
        """Click the first Sign-in button to proceed to OTP screen."""
        try:
            login_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "sendloginhello"))
            )
            login_btn.click()
            print("🚀 First Sign-in clicked! Waiting for OTP screen...")
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Failed to click Sign-in: {e}")
            return False
    
    def click_send_otp(self):
        """Click the Send OTP / Resend OTP button."""
        try:
            # Try to find and click the Send OTP or Resend OTP button
            otp_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btn_otp"))
            )
            otp_btn.click()
            print("📱 OTP sent to your mobile!")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"⚠️ Could not click Send OTP button: {e}")
            return False
    
    def enter_otp(self, otp):
        """Enter the OTP received on mobile."""
        try:
            otp_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "otp_text"))
            )
            otp_field.clear()
            otp_field.send_keys(otp)
            print(f"🔐 OTP entered: {otp}")
            return True
        except Exception as e:
            print(f"❌ Failed to enter OTP: {e}")
            return False
    
    def click_final_signin(self):
        """Click the final Sign-in button after OTP entry."""
        try:
            # The final Sign-in button on OTP page
            signin_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign-in')] | //input[@value='Sign-in']"))
            )
            signin_btn.click()
            print("✅ Final Sign-in clicked!")
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Failed to click final Sign-in: {e}")
            return False
    
    def login(self, username, password):
        """
        Complete login process with OTP.
        User will manually click buttons and enter OTP.
        """
        # Navigate to site
        if not self.navigate_to_site():
            return False
        
        # Switch to login frame
        if not self.switch_to_login_frame():
            return False
        
        # Enter credentials
        if not self.enter_credentials(username, password):
            return False
        
        # Let user click the first Sign-in button
        print("\n" + "="*60)
        print("✅ CREDENTIALS ENTERED!")
        print("👆 Step 1: Click the 'Sign-in' button in the browser")
        print("="*60)
        input("\nPress ENTER after clicking Sign-in...")
        
        # Now on OTP screen - let user click Send OTP
        print("\n" + "="*60)
        print("📱 OTP SCREEN")
        print("👆 Step 2: Click 'Send OTP' or 'Resend OTP' button")
        print("="*60)
        input("\nPress ENTER after clicking Send OTP...")
        
        # Get OTP from user
        print("\n" + "="*60)
        print("📲 CHECK YOUR MOBILE FOR OTP")
        print("="*60)
        otp = input("\n🔐 Enter the OTP you received: ").strip()
        
        if not otp:
            print("❌ OTP is required!")
            return False
        
        # Switch back to frame if needed (page may have refreshed)
        try:
            self.driver.switch_to.default_content()
            self.switch_to_login_frame()
        except:
            pass
        
        # Enter OTP
        if not self.enter_otp(otp):
            print("⚠️ Could not auto-enter OTP. Please enter it manually in the browser.")
        
        # Let user click final Sign-in
        print("\n" + "="*60)
        print("✅ OTP ENTERED!")
        print("👆 Step 3: Click the 'Sign-in' button to complete login")
        print("="*60)
        input("\nPress ENTER after clicking Sign-in and logging in successfully...")
        
        print("\n✅ LOGIN PROCESS COMPLETED!")
        return True
    
    def keep_browser_open(self):
        """Keep the browser open for manual interaction."""
        print("\n" + "="*60)
        print("🌐 Browser is now open for your use.")
        print("   Tell me what you want to do next!")
        print("   Press Ctrl+C in the terminal when done.")
        print("="*60 + "\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Closing browser...")
            self.close()
    
    def close(self):
        """Close the browser."""
        self.driver.quit()
        print("🔒 Browser closed.")


def main():
    """Main function to run the login automation."""
    print("\n" + "="*60)
    print("         SACCESS NIC LOGIN AUTOMATION (OTP Version)")
    print("         saccess.nic.in")
    print("="*60 + "\n")
    
    # Get credentials from user
    username = input("📧 Enter your Username/Email: ").strip()
    password = input("🔑 Enter your Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required!")
        return
    
    # Initialize and run login
    login_handler = SACCESSLogin(headless=False)
    
    try:
        success = login_handler.login(username, password)
        
        if success:
            print("\n✅ You are now logged in!")
            login_handler.keep_browser_open()
        else:
            print("\n❌ Login may have failed. Please check the browser.")
            login_handler.keep_browser_open()
            
    except Exception as e:
        print(f"\n❌ Error during login: {e}")
        login_handler.close()


if __name__ == "__main__":
    main()
