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
    
    label_locator = bot.page.locator('text=/School Name/i').first
    container = label_locator.locator('xpath=./ancestor::div[contains(@class, "office-form-question")]').first
    
    print("Container structure:")
    print("Comboboxes inside:", container.locator('[role="combobox"]').count())
    print("ChevronDown inside:", container.locator('i[data-icon-name="ChevronDown"]').count())
    print("Radios inside:", container.locator('[role="radio"]').count())
    print("Select tags inside:", container.locator('select').count())
    print("Div with tabindex inside:", container.locator('div[tabindex="0"]').count())
    print("Input text inside:", container.locator('input[type="text"]').count())
    
    bot.browser.close()

if __name__ == "__main__":
    diagnostics()
