
import sys
import os
import time

try:
    from ms_form_automation import MSFormAutomation
except ImportError:
    sys.path.append(os.getcwd())
    from ms_form_automation import MSFormAutomation

URL = "https://forms.office.com/r/sXXXCpkSWY"
EMAIL = "guntaka.reddy_2028@woxsen.edu.in"
PASSWORD = "K@nni:18"

print("Starting dump...")
auto = MSFormAutomation(headless=True)
auto.start_browser(email=EMAIL)
auto.page.goto(URL)
auto.microsoft_login(EMAIL, PASSWORD)
auto.wait_for_loading_screen()

time.sleep(5) # Wait for load

print("Selecting 'School of Business'...")
try:
    auto.page.click('text="School of Business"', force=True)
    time.sleep(5)
except Exception as e:
    print(f"Failed to select School: {e}")

print("Saving dumps...")
with open("dump.html", "w", encoding="utf-8") as f:
    f.write(auto.page.content())

with open("dump.txt", "w", encoding="utf-8") as f:
    f.write(auto.page.inner_text("body"))

print("Dumps saved to dump.html and dump.txt")
auto.browser.close()
