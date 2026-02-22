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
    bot.wait_for_loading_screen()
    
    # Try selecting it using the bot's own internal method
    result = bot.select_radio("School Name", "School of Technology")
    print(f"Result of bot.select_radio: {result}")
    
    bot.browser.close()

if __name__ == "__main__":
    diagnostics()
