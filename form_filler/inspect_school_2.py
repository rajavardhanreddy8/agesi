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
    
    print("Navigating to form...")
    form_url = "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u"
    bot.page.goto(form_url, wait_until='networkidle')
    bot.wait_for_loading_screen()
    
    print("Waiting for 'School Name'...")
    try:
        # Wait for the question container
        bot.page.wait_for_selector('text="3. School Name"', timeout=10000)
    except Exception as e:
        print("Could not find School Name heading.", e)
        bot.close()
        return

    # Evaluate JavaScript to grab the entire HTML of the question container
    html = bot.page.evaluate('''() => {
        const spans = Array.from(document.querySelectorAll('span'));
        const qSpan = spans.find(s => s.textContent.includes('3. School Name'));
        if (!qSpan) return "No span found";
        
        const container = qSpan.closest('.office-form-question');
        if (!container) return "No container found";
        
        return container.innerHTML;
    }''')
    
    with open("school_question_dom.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Dumped HTML to school_question_dom.html")
    bot.close()

if __name__ == "__main__":
    diagnostics()
