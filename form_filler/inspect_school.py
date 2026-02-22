from playwright.sync_api import sync_playwright
import time
import json
import os

URL = "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u"
BROWSER_STATE = "browser_state_guntaka_reddy_2028_woxsen_edu_in.json"

def get_school_options():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context_args = {'viewport': {'width': 1280, 'height': 800}}
        if os.path.exists(BROWSER_STATE):
            context_args['storage_state'] = BROWSER_STATE
        context = browser.new_context(**context_args)
        page = context.new_page()
        print("Navigating to form...")
        page.goto(URL, wait_until='networkidle')
        
        # Wait for form to load
        try:
            page.wait_for_selector('text="3. School Name"', timeout=10000)
            print("Found 'School Name' heading.")
        except:
            print("Could not find 'School Name' heading. Maybe not logged in?")
            browser.close()
            return
            
        print("Extracting radio options for School Name...")
        options = page.evaluate('''() => {
            const getQ = (text) => Array.from(document.querySelectorAll('span')).find(s => s.textContent.includes(text));
            const qSpan = getQ('3. School Name');
            if (!qSpan) return [];
            
            // Go up to the question container
            const container = qSpan.closest('.office-form-question');
            if (!container) return [];
            
            // Find all radio label spans inside this container
            const labels = Array.from(container.querySelectorAll('input[type="radio"]')).map(el => {
                const wrapper = el.closest('label');
                return wrapper ? wrapper.textContent.trim() : 'Unknown';
            });
            return labels;
        }''')
        
        print("OPTIONS FOUND:", json.dumps(options, indent=2))
        browser.close()

if __name__ == "__main__":
    get_school_options()
