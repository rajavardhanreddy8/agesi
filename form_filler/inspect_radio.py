
import sys
import os
import logging
import time

try:
    from ms_form_automation import MSFormAutomation
except ImportError:
    sys.path.append(os.getcwd())
    from ms_form_automation import MSFormAutomation

URL = "https://forms.office.com/r/sXXXCpkSWY"
EMAIL = "guntaka.reddy_2028@woxsen.edu.in"

print("Starting HTML inspection...")
auto = MSFormAutomation(headless=True)
auto.start_browser(email=EMAIL)
auto.page.goto(URL)
auto.microsoft_login(EMAIL, "K@nni:18")
auto.wait_for_loading_screen()


print("🔍 Inspecting 'Programme Name' question...")
try:
    # 1. Select School of Business to trigger conditional questions
    print("Selecting 'School of Business'...")
    auto.page.click('text="School of Business"', force=True)
    print("Waiting 5 seconds for conditional fields...")
    time.sleep(5)
    
    # 2. Dump all text to find what appeared
    print("\n=== PAGE TEXT DUMP ===")
    content = auto.page.content()
    # Simple text extraction for debug
    import re
    text = auto.page.inner_text('body')
    print(text)
    print("======================\n")
    
    # 3. Try to find "B.B.A" or similar
    print("Checking for BBA variations...")
    for variant in ["B.B.A", "BBA", "Bachelor of Business Administration", "Programme Name"]:
        found = auto.page.locator(f'text="{variant}"').count()
        print(f"'{variant}': Found {found} times")

    # 4. Dump HTML of the container if found
    q_text = auto.page.locator('text="Programme Name"').first
    if q_text.count() > 0:
        container = q_text.locator('xpath=./ancestor::div[@data-automation-id="questionItem"]').first
        if container.count() > 0:
            print("\n=== HTML DUMP OF PROGRAMME NAME QUESTON ===")
            print(container.inner_html())
            print("===========================================\n")
    else:
        print("❌ 'Programme Name' label NOT found after waiting.")

except Exception as e:
    print(f"❌ Error: {e}")

auto.browser.close()
