from ms_form_automation import MSFormAutomation
import time

def full_screenshot():
    FORM_URL = "https://forms.office.com/r/sXXXCpkSWY"
    EMAIL = "guntaka.reddy_2028@woxsen.edu.in"
    PASSWORD = r"K@nni:18"
    
    automation = MSFormAutomation(headless=False)
    
    try:
        automation.start_browser()
        automation.page.goto(FORM_URL)
        time.sleep(3)
        try:
            automation.microsoft_login(EMAIL, PASSWORD)
        except:
            pass
        
        time.sleep(5)
        
        # Take full page screenshot
        automation.page.screenshot(path="screenshots/FORM_FULL_LAYOUT.png", full_page=True)
        print("✅ Full layout screenshot saved")

    finally:
        automation.browser.close()

if __name__ == "__main__":
    full_screenshot()
