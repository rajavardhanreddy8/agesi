from playwright.sync_api import sync_playwright
import os
import time

STATE_FILE = 'browser_state_guntaka_reddy_2028_woxsen_edu_in.json'
FORM_URL = 'https://forms.office.com/r/sXXXCpkSWY'

def reproduce():
    if not os.path.exists(STATE_FILE):
        print(f"State file {STATE_FILE} not found. Cannot reproduce stale session issue.")
        return

    print(f"Using state file: {STATE_FILE}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=STATE_FILE)
        page = context.new_page()
        
        print(f"Navigating to {FORM_URL}...")
        page.goto(FORM_URL)
        page.wait_for_load_state('networkidle')
        time.sleep(5)
        
        print(f"Current URL: {page.url}")
        
        if "login.microsoftonline.com" in page.url:
            print("FAILURE REPRODUCED: Redirected to login page despite having state file.")
            page.screenshot(path="repro_failure.png")
        elif "forms.office.com" in page.url:
             # Check if we are actually on the form or some error page
             if page.locator('text=Sign in').count() > 0:
                 print("FAILURE: On forms.office.com but 'Sign in' button visible.")
             else:
                 print("SUCCESS: Seem to be on form page.")
        else:
            print(f"Unknown state. URL: {page.url}")
            
        browser.close()

if __name__ == "__main__":
    reproduce()
