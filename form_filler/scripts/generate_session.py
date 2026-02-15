
from playwright.sync_api import sync_playwright
import time
import json
import os

# CREDENTIALS (REPLACE THESE OR SET ENV VARS)
EMAIL = os.getenv("MS_EMAIL", "guntaka.reddy_2028@woxsen.edu.in")
PASSWORD = os.getenv("MS_PASSWORD", "k@nni:18")

# FORM URL (The one you want to automate)
FORM_URL = "https://forms.office.com/r/sXXXCpkSWY"

def generate_session():
    with sync_playwright() as p:
        print("🚀 Launching browser...")
        # Launch in HEADED mode
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"🌍 Navigating to: {FORM_URL}")
        page.goto(FORM_URL)

        print("\n" + "="*60)
        print("🚨 ACTION REQUIRED:")
        print("1. The browser is now open.")
        print("2. Please LOG IN manually inside the browser window.")
        print("3. Approve the MFA notification on your phone.")
        print("4. WAIT until you see the actual Form loaded on the screen.")
        print("="*60 + "\n")

        # Wait for user to complete login manually
        input("👉 Press ENTER in this terminal once the Form is visible on screen... ")

        # Prepare to save
        print("💾 Saving browser state to 'browser_state.json'...")
        
        # Verify we are on the right domain
        if "forms.office.com" not in page.url:
            print("⚠️ Warning: Current URL does not look like Microsoft Forms.")
            confirm = input("Are you sure you want to save this state? (y/n): ")
            if confirm.lower() != 'y':
                print("❌ Aborted.")
                browser.close()
                return

        context.storage_state(path="browser_state.json")
        
        print("\n✅ Session saved successfully!")
        print("📂 File created: browser_state.json")
        print("👉 Now, tell me you have this file, and I will upload it to the server.")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    generate_session()
