import os
import sys
import time

sys.path.insert(0, 'c:/Users/admin/Documents/outing/agent 4.0/form_filler')
from ms_form_automation import MSFormAutomation
from dotenv import load_dotenv

def test_programme_options():
    load_dotenv()
    print("Testing MS Form Options extraction...")
    auto = MSFormAutomation(headless=False)
    try:
        auto.start_browser()
        
        email = os.getenv('AGENT_TEST_EMAIL', 'guntaka.reddy_2028@woxsen.edu.in') 
        password = os.getenv('AGENT_TEST_PASSWORD', 'Omsai@123') 
        
        # Proper MS login flow
        print("Executing full login flow...")
        auto.page.goto('https://forms.office.com/Pages/ResponsePage.aspx?id=tBKaGT-LpUaL6J7H8fJ4d0eTq_GIn5JDrVz8rts7QYtUQlFLMUtZVjkwMVcxMVAwSVNGRFVEUTZMRi4u')
        
        try:
             auto.microsoft_login(email, password)
        except Exception as e:
             print(f"Login Note: {e}")
             
        time.sleep(5)
        
        print("Looking for Programme Name field on URL:", auto.page.url)
        
        # Let's extract all radio buttons
        items = auto.page.locator('div[data-automation-id="questionItem"]').all()
        print(f"Found {len(items)} questions.")
        
        for i, item in enumerate(items):
            title = item.locator('.question-title-box, .text-format-content, span:not([class])').first.inner_text().strip()
            print(f"Question {i+1}: '{title}'")
            if "Programme" in title or "Program" in title:
                print("  --- Found Programme Field ---")
                radios = item.locator('div[role="radio"]').all()
                for r in radios:
                    aria = r.get_attribute('aria-label')
                    val = r.get_attribute('value')
                    text = r.inner_text().strip()
                    print(f"    Radio => text: '{text}', aria-label: '{aria}', value: '{val}'")
                print("  --- End of Radios ---")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if auto.browser:
            auto.browser.close()
        if auto.playwright_instance:
            auto.playwright_instance.stop()

if __name__ == "__main__":
    test_programme_options()
