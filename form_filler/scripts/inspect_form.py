"""Quick script to inspect Microsoft Forms DOM structure"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://forms.office.com/r/sXXXCpkSWY')
    time.sleep(10)
    
    url = page.url
    print(f"URL: {url}")
    title = page.title()
    print(f"Title: {title}")
    
    # Use JavaScript to dump all form structure
    result = page.evaluate("""() => {
        const output = [];
        
        // Find all question containers
        const questions = document.querySelectorAll('[data-automation-id="questionItem"]');
        output.push("=== QUESTION ITEMS (data-automation-id=questionItem) ===");
        output.push("Found: " + questions.length);
        questions.forEach((q, i) => {
            const text = q.innerText.substring(0, 200);
            output.push("  Q[" + i + "]: " + text.replace(/\\n/g, ' | '));
        });
        
        // Find all inputs
        const inputs = document.querySelectorAll('input');
        output.push("\\n=== ALL INPUTS ===");
        output.push("Found: " + inputs.length);
        inputs.forEach((inp, i) => {
            const t = inp.type || 'none';
            const a = inp.getAttribute('aria-label') || 'none';
            const ph = inp.placeholder || 'none';
            const n = inp.name || 'none';
            const v = inp.offsetParent !== null;
            output.push("  Input[" + i + "]: type=" + t + ", aria=" + a + ", placeholder=" + ph + ", name=" + n + ", visible=" + v);
        });
        
        // Find all textareas
        const textareas = document.querySelectorAll('textarea');
        output.push("\\n=== ALL TEXTAREAS ===");
        output.push("Found: " + textareas.length);
        textareas.forEach((ta, i) => {
            const a = ta.getAttribute('aria-label') || 'none';
            const ph = ta.placeholder || 'none';
            output.push("  Textarea[" + i + "]: aria=" + a + ", placeholder=" + ph);
        });
        
        // Find all role=heading divs
        const headings = document.querySelectorAll('[role="heading"]');
        output.push("\\n=== HEADINGS ===");
        output.push("Found: " + headings.length);
        headings.forEach((h, i) => {
            output.push("  H[" + i + "]: " + h.innerText.substring(0, 150));
        });
        
        // Find all role=radiogroup divs
        const radiogroups = document.querySelectorAll('[role="radiogroup"]');
        output.push("\\n=== RADIO GROUPS ===");
        output.push("Found: " + radiogroups.length);
        radiogroups.forEach((rg, i) => {
            const label = rg.getAttribute('aria-label') || 'none';
            const options = rg.querySelectorAll('[role="radio"]');
            const optionTexts = Array.from(options).map(o => o.getAttribute('aria-label') || o.innerText.substring(0, 50));
            output.push("  RG[" + i + "]: label=" + label + ", options=[" + optionTexts.join(', ') + "]");
        });
        
        // Find all select/dropdown elements
        const selects = document.querySelectorAll('select, [role="listbox"], [role="combobox"]');
        output.push("\\n=== SELECTS/DROPDOWNS ===");
        output.push("Found: " + selects.length);
        selects.forEach((s, i) => {
            const a = s.getAttribute('aria-label') || 'none';
            output.push("  Select[" + i + "]: aria=" + a);
        });
        
        // Get first question HTML structure for debugging
        if (questions.length > 0) {
            output.push("\\n=== FIRST QUESTION HTML STRUCTURE ===");
            output.push(questions[0].outerHTML.substring(0, 1000));
        }
        
        return output.join("\\n");
    }""")
    
    print(result)
    page.screenshot(path='debug_form_inspect.png')
    print("\nScreenshot saved to debug_form_inspect.png")
    browser.close()
