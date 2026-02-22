import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from ms_form_automation import MSFormAutomation

def diagnostics():
    bot = MSFormAutomation(headless=True)
    
    # We use red_2028 since that's the one we know the state exists for
    email = "guntaka.reddy_2028@woxsen.edu.in"
    print(f"Setting up for {email}...")
    
    # Init browser
    bot.start_browser(email)
    
    # Navigate
    print("Navigating to form...")
    form_url = "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u"
    bot.page.goto(form_url, wait_until='networkidle')
    bot.wait_for_loading_screen()
    
    print("Getting all span texts for radio buttons on the entire page...")
    options = bot.page.evaluate('''() => {
        const labels = Array.from(document.querySelectorAll('[role="radio"]')).map(el => {
            return String(el.getAttribute('aria-label') || "NO_ARIA") + " | " + String(el.getAttribute('value') || "NO_VAL");
        });
        return labels;
    }''')
    
    print("ALL RADIOS:")
    for opt in options:
        print(" ->", opt)
        
    bot.browser.close()

if __name__ == "__main__":
    diagnostics()
