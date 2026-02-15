"""
Debug script to inspect Microsoft Forms field structure
This will help us understand why "Name of the Student" is not being found
"""

from playwright.sync_api import sync_playwright
import time

def inspect_form():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to the form
        form_url = "https://forms.office.com/r/sXXXCpkSWY"
        print(f"Navigating to: {form_url}")
        page.goto(form_url)
        
        # Wait for form to load
        time.sleep(5)
        
        print("\n=== Inspecting Form Structure ===\n")
        
        # Strategy 1: Find all question headings
        print("1. All question headings (role=heading):")
        headings = page.locator('div[role="heading"]').all()
        for i, heading in enumerate(headings):
            text = heading.inner_text()
            print(f"   [{i}] {text}")
        
        # Strategy 2: Find all inputs with aria-label
        print("\n2. All inputs with aria-label:")
        inputs = page.locator('input[aria-label]').all()
        for i, inp in enumerate(inputs):
            label = inp.get_attribute('aria-label')
            print(f"   [{i}] aria-label: {label}")
        
        # Strategy 3: Find all question items
        print("\n3. All question items (data-automation-id=questionItem):")
        questions = page.locator('div[data-automation-id="questionItem"]').all()
        for i, q in enumerate(questions):
            text = q.inner_text()[:100]  # First 100 chars
            print(f"   [{i}] {text}")
        
        # Strategy 4: Look for specific text patterns
        print("\n4. Searching for 'Name' or 'Student' text:")
        name_elements = page.locator('text=/.*[Nn]ame.*[Ss]tudent.*/').all()
        for i, elem in enumerate(name_elements):
            text = elem.inner_text()
            print(f"   [{i}] {text}")
        
        # Strategy 5: Get page HTML structure (first question only)
        print("\n5. HTML structure of first question:")
        if questions:
            html = questions[0].evaluate('el => el.outerHTML')
            print(html[:500])  # First 500 chars
        
        print("\n=== Waiting 30s for manual inspection ===")
        time.sleep(30)
        
        browser.close()

if __name__ == "__main__":
    inspect_form()
