import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from ms_form_automation import MSFormAutomation
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def diagnostics():
    bot = MSFormAutomation(headless=True)
    email = "guntaka.reddy_2028@woxsen.edu.in"
    bot.start_browser(email)
    
    print("Navigating to form...")
    form_url = "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u"
    bot.page.goto(form_url, wait_until='networkidle')
    
    # Wait for the form to actually render its question items
    bot.page.wait_for_selector('.office-form-question', timeout=20000)
    
    roles = bot.page.locator('[role="radio"]').count()
    inputs = bot.page.locator('input[type="radio"]').count()
    
    print(f"Count of [role='radio']: {roles}")
    print(f"Count of input[type='radio']: {inputs}")
    
    bot.browser.close()

if __name__ == "__main__":
    diagnostics()
