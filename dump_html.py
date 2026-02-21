import os
import sys
import time

sys.path.insert(0, 'c:/Users/admin/Documents/outing/agent 4.0/form_filler')
from ms_form_automation import MSFormAutomation
from dotenv import load_dotenv

def dump_form_html():
    load_dotenv()
    print("Dumping MS Form HTML...")
    auto = MSFormAutomation(headless=False)
    try:
        auto.start_browser()
        
        email = os.getenv('AGENT_TEST_EMAIL', 'guntaka.reddy_2028@woxsen.edu.in') 
        password = os.getenv('AGENT_TEST_PASSWORD', 'Omsai@123') 
        
        print("Opening form...")
        auto.page.goto('https://forms.office.com/Pages/ResponsePage.aspx?id=tBKaGT-LpUaL6J7H8fJ4d0eTq_GIn5JDrVz8rts7QYtUQlFLMUtZVjkwMVcxMVAwSVNGRFVEUTZMRi4u')
        
        try:
             auto.microsoft_login(email, password)
        except Exception as e:
             print(f"Login Note: {e}")
             
        # Wait a bit longer for form to be fully ready
        time.sleep(10)
        
        # Save HTML
        html = auto.page.content()
        with open('c:/Users/admin/Documents/outing/agent 4.0/form_dump.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print("HTML dumped to form_dump.html successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if auto.browser:
            auto.browser.close()
        if auto.playwright_instance:
            auto.playwright_instance.stop()

if __name__ == "__main__":
    dump_form_html()
