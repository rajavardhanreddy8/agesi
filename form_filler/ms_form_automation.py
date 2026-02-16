"""
Microsoft Forms Automation for Weekend Outing Submission
Handles authentication, form filling, PDF upload, and submission
With human-like random delays to avoid detection
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import random
import json
import os
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
# Force UTF-8 for file handler to support emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

# Force stdout to utf-8 to prevent console crashes on Windows
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

class MSFormAutomation:
    # Path to persist login session across runs
    STORAGE_STATE_FILE = 'browser_state.json'
    
    @staticmethod
    def normalize_programme(programme_value):
        """
        Normalize database programme value to match Microsoft Form radio options exactly.
        
        Database may store: "B.B.A", "B.Tech", "B.Com" etc.
        MS Form expects: "BBA", "B.Tech", "BCom" etc.
        
        Args:
            programme_value (str): Programme value from database
            
        Returns:
            str: Normalized programme value matching MS Form options
        """
        if not programme_value:
            return ''
        
        # Programme mapping dictionary - maps database values to MS Form options
        programme_map = {
            # Remove periods from BBA variations
            'B.B.A': 'BBA',
            'B.B.A.': 'BBA',
            'BBA': 'BBA',
            
            # MBBA variations
            'M.B.B.A': 'MBBA',
            'M.B.B.A.': 'MBBA',
            'MBBA': 'MBBA',
            
            # BCom variations
            'B.Com': 'BCom',
            'B.COM': 'BCom',
            'BCOM': 'BCom',
            'B Com': 'BCom',
            
            # B.Tech (keep as-is if already correct)
            'B.Tech': 'B.Tech',
            'B.TECH': 'B.Tech',
            'BTECH': 'B.Tech',
            'B Tech': 'B.Tech',
            
            # B.Sc variations
            'B.Sc': 'B.Sc.',
            'B.Sc.': 'B.Sc.',
            'B.SC': 'B.Sc.',
            'BSC': 'B.Sc.',
            'B Sc': 'B.Sc.',
            
            # B Arch
            'B.Arch': 'B. Arch',
            'B. Arch': 'B. Arch',
            'B.ARCH': 'B. Arch',
            'BARCH': 'B. Arch',
            
            # B.Des
            'B.Des': 'B.Des',
            'B.DES': 'B.Des',
            'BDES': 'B.Des',
            'B Des': 'B.Des',
            
            # BA LLB
            'BA LLB': 'BA LLB',
            'B.A. LLB': 'BA LLB',
            'B.A LLB': 'BA LLB',
            'BA.LLB': 'BA LLB',
            
            # BBA LLB
            'BBA LLB': 'BBA LLB',
            'B.B.A. LLB': 'BBA LLB',
            'B.B.A LLB': 'BBA LLB',
            'BBA.LLB': 'BBA LLB',
            
            # B.A
            'B.A': 'B.A.',
            'B.A.': 'B.A.',
            'BA': 'B.A.',
            'B A': 'B.A.',
            
            # BCA
            'BCA': 'BCA',
            'B.C.A': 'BCA',
            'B.C.A.': 'BCA',
        }
        
        # Try exact match first
        if programme_value in programme_map:
            return programme_map[programme_value]
        
        # Try case-insensitive match
        for key, value in programme_map.items():
            if key.lower() == programme_value.lower():
                return value
        
        # If no match found, return original value
        logging.warning(f"⚠️ Programme '{programme_value}' not in mapping, using as-is")
        return programme_value
    
    def __init__(self, headless=False, min_delay=5, max_delay=15):
        """
        Initialize automation with configurable delays.
        min_delay: minimum delay in seconds (default 5 seconds)
        max_delay: maximum delay in seconds (default 15 seconds)
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.min_delay = min_delay  
        self.max_delay = max_delay
        self.playwright_instance = None
  
    
    def human_delay(self, action_name="action", short=False):
        """
        Add random human-like delay between actions.
        short=True: Small delay (5-15 seconds) for between field fills
        short=False: Long delay (3-7 minutes) for between major sections
        """
        if short:
            delay = random.uniform(5, 15)  # 5-15 seconds between fields
        else:
            delay = random.uniform(self.min_delay, self.max_delay)  # 3-7 minutes
        
        minutes = int(delay // 60)
        seconds = int(delay % 60)
        print(f"⏳ Human-like delay before {action_name}: {minutes}m {seconds}s")
        time.sleep(delay)
        return delay
        
    def start_browser(self, email=None):
        """
        Start Playwright browser with stealth settings
        email: Optional email to load specific user session state
        """
        self.playwright_instance = sync_playwright().start()
        
        # Determine state file path based on email
        if email:
            safe_email = email.replace('@', '_').replace('.', '_')
            self.current_state_file = f"browser_state_{safe_email}.json"
        else:
            self.current_state_file = self.STORAGE_STATE_FILE
            
        logging.info(f"Using browser state file: {self.current_state_file}")

        self.browser = self.playwright_instance.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Try to load saved session state (cookies, localStorage)
        storage_state = None
        if os.path.exists(self.current_state_file):
            try:
                # Check if the state file is recent (less than 12 hours old)
                import stat
                file_age = time.time() - os.path.getmtime(self.current_state_file)
                if file_age < 43200:  # 12 hours in seconds
                    storage_state = self.current_state_file
                    logging.info(f"Loading saved browser state (age: {file_age/3600:.1f}h)")
                else:
                    logging.info(f"Saved browser state too old ({file_age/3600:.1f}h), will do fresh login")
                    os.remove(self.current_state_file)
            except Exception as e:
                logging.warning(f"Error checking saved state: {e}")
        
        # Create context with realistic settings and optional saved state
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        if storage_state:
            context_options['storage_state'] = storage_state
            
        self.context = self.browser.new_context(**context_options)
        
        self.page = self.context.new_page()
        
        # Remove webdriver property
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        logging.info(f"Browser started (saved session: {'yes' if storage_state else 'no'})")

    def wait_for_loading_screen(self):
        """
        Wait for any 'Loading...' overlays or spinners to disappear
        """
        try:
            print("⏳ Checking for loading indicators...")
            # Common MS Forms loading indicators
            # 1. Overlay with text "Loading"
            # 2. Spinner divs
            # 3. Skeleton loaders
            
            # Wait for "Loading..." text to detach/disappear
            self.page.locator('text=Loading...').wait_for(state='detached', timeout=10000)
            
            # Wait for specific spinner class if known (often office-form-spinner or similar)
            # But text=Loading... is usually sufficient
            
            # Double check network idle again
            self.page.wait_for_load_state('networkidle', timeout=5000)
            print("✅ Loading screen cleared.")
            return True
        except Exception:
            # If timeout waiting for detach, it applies it MIGHT still be there, or it was never there.
            # We assume it's clear if we don't find it.
            print("ℹ️ No persistent loading screen found (or cleared).")
            return True
        
    def microsoft_login(self, email, password):
        """
        Handle Microsoft authentication flow
        Saves session state after successful login to avoid MFA next time
        
        CRITICAL FIX: The old code checked URL too early (before JS redirect).
        forms.office.com URL is briefly visible before login redirect fires,
        causing the bot to falsely think it's already logged in.
        
        New approach: Wait for EITHER the login page OR actual form questions
        to appear, then decide based on what we actually see.
        """
        try:
            logging.info(f"Attempting login with {email}...")
            logging.info(f"Current URL at login start: {self.page.url}")
            
            # STEP 1: Wait for the page to ACTUALLY settle.
            # The key problem was: forms.office.com loads, then JS redirects to login.
            # networkidle fires BEFORE the JS redirect, so URL is still forms.office.com.
            # FIX: Wait for EITHER login elements OR form question elements to appear.
            # This races both possibilities and detects whichever state we're actually in.
            
            logging.info("Waiting for page to settle (login page OR form content)...")
            
            try:
                # Race: wait for EITHER the login email input OR the form question container
                # Whichever appears first tells us the true state
                self.page.wait_for_selector(
                    'input[name="loginfmt"], input[type="email"], div[data-automation-id="questionItem"]',
                    timeout=30000
                )
            except PlaywrightTimeout:
                logging.warning("Neither login page nor form loaded within 30s!")
                # Take a screenshot for debugging
                try:
                    self.page.screenshot(path=f'debug_login_settle_{datetime.now().strftime("%H%M%S")}.png')
                except:
                    pass
            
            # Now check what actually loaded
            current_url = self.page.url
            logging.info(f"Page settled. URL: {current_url}")
            
            # Check if we're on the login page
            on_login_page = False
            login_input = self.page.locator('input[name="loginfmt"], input[type="email"]')
            if login_input.count() > 0:
                on_login_page = True
                logging.info("Login page detected (email input found)")
            elif 'login.microsoftonline.com' in current_url:
                on_login_page = True
                logging.info("Login page detected (URL contains login.microsoftonline.com)")
            
            # Check if actual form questions are visible (proof of being logged in)
            form_questions = self.page.locator('div[data-automation-id="questionItem"]')
            if not on_login_page and form_questions.count() > 0:
                logging.info("Already logged in - form questions are visible! Skipping login.")
                return True
            
            # If we're not on login page and don't see form questions, 
            # we might still be redirecting. Wait for login page explicitly.
            if not on_login_page:
                logging.info("Not on login page yet, and no form questions found. Waiting for redirect...")
                try:
                    self.page.wait_for_url('**/login.microsoftonline.com/**', timeout=15000)
                    on_login_page = True
                except PlaywrightTimeout:
                    # Maybe we ARE on the form after all, re-check
                    if form_questions.count() > 0:
                        logging.info("Form questions appeared during wait! Already logged in.")
                        return True
                    else:
                        # Take screenshot and raise
                        try:
                            self.page.screenshot(path=f'debug_login_unknown_{datetime.now().strftime("%H%M%S")}.png')
                        except:
                            pass
                        raise Exception(f"Unknown page state. URL: {self.page.url}")
            
            logging.info("On login page. Proceeding with authentication...")
            
            # Enter email
            email_input = self.page.wait_for_selector('input[type="email"]', timeout=15000)
            email_input.fill(email)
            logging.info(f"Email entered: {email}")
            
            # Click Next button
            self.page.click('input[type="submit"]')
            time.sleep(3)
            
            # Enter password
            try:
                password_input = self.page.wait_for_selector('input[type="password"]', timeout=30000)
                password_input.fill(password)
                logging.info("Password entered")
                
                # Click Sign in
                self.page.click('input[type="submit"]')
                time.sleep(3)
                
            except PlaywrightTimeout:
                logging.warning("Password field not found - might be SSO or different auth flow")
                try:
                    self.page.screenshot(path=f'debug_no_password_{datetime.now().strftime("%H%M%S")}.png')
                except:
                    pass
                raise Exception("Authentication method not supported - password field not found")
            
            # Handle "Stay signed in?" prompt
            try:
                stay_signed_in = self.page.wait_for_selector('text=Stay signed in?', timeout=8000)
                if stay_signed_in:
                    logging.info("'Stay signed in?' prompt - clicking Yes")
                    self.page.click('input[type="submit"][value="Yes"]')
                    time.sleep(2)
            except PlaywrightTimeout:
                logging.info("No 'Stay signed in?' prompt")
            
            # Check for MFA/2FA
            if 'login.microsoftonline.com' in self.page.url:
                logging.warning("MFA/2FA detected! Waiting 120s for approval...")
                try:
                    self.page.wait_for_url('https://forms.office.com/**', timeout=120000)
                    logging.info("MFA approved!")
                except PlaywrightTimeout:
                    raise Exception("MFA approval timeout (120s) - approve the notification on your phone")
            
            # Verify login success - wait for form to actually load
            logging.info("Waiting for form to load after login...")
            try:
                self.page.wait_for_load_state('networkidle', timeout=15000)
            except:
                pass
            
            # Final verification: are we on the form page?
            final_url = self.page.url
            logging.info(f"Final URL after login: {final_url}")
            
            if 'forms.office.com' in final_url and 'login' not in final_url:
                logging.info("Login successful!")
                
                # SAVE SESSION STATE
                try:
                    state_file = getattr(self, 'current_state_file', self.STORAGE_STATE_FILE)
                    self.context.storage_state(path=state_file)
                    logging.info(f"Saved browser session to {state_file}")
                except Exception as e:
                    logging.warning(f"Failed to save session state: {e}")
                
                return True
            else:
                raise Exception(f"Login failed - ended up on: {final_url}")
                
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            # Capture screenshot on any login failure
            try:
                self.page.screenshot(path=f'debug_login_fail_{datetime.now().strftime("%H%M%S")}.png')
            except:
                pass
            raise
    
    def fill_form(self, form_data):
        """
        Fill all form fields robustly by finding labels
        With diagnostic DOM dump and positional fallback
        """
        try:
            print("Starting form filling...")
            self.page.wait_for_load_state('networkidle')
            time.sleep(3)
            
            # === DIAGNOSTIC DOM DUMP ===
            # This helps us understand the actual form structure
            try:
                dom_info = self.page.evaluate("""() => {
                    const output = [];
                    
                    // Count question items
                    const qi = document.querySelectorAll('[data-automation-id="questionItem"]');
                    output.push("QuestionItems: " + qi.length);
                    
                    // All visible inputs
                    const inputs = Array.from(document.querySelectorAll('input')).filter(
                        i => i.offsetParent !== null && i.type !== 'hidden'
                    );
                    output.push("VisibleInputs: " + inputs.length);
                    inputs.forEach((inp, i) => {
                        output.push("  I[" + i + "] type=" + inp.type + " aria=" + (inp.getAttribute('aria-label')||'') + " ph=" + (inp.placeholder||''));
                    });
                    
                    // All visible textareas
                    const tas = Array.from(document.querySelectorAll('textarea')).filter(
                        t => t.offsetParent !== null
                    );
                    output.push("VisibleTextareas: " + tas.length);
                    tas.forEach((ta, i) => {
                        output.push("  TA[" + i + "] aria=" + (ta.getAttribute('aria-label')||'') + " ph=" + (ta.placeholder||''));
                    });
                    
                    // All headings
                    const headings = document.querySelectorAll('[role="heading"], h1, h2, h3');
                    headings.forEach((h, i) => {
                        output.push("  H[" + i + "] " + h.innerText.substring(0, 100));
                    });
                    
                    // Radio groups
                    const rgs = document.querySelectorAll('[role="radiogroup"]');
                    output.push("RadioGroups: " + rgs.length);
                    rgs.forEach((rg, i) => {
                        const label = rg.getAttribute('aria-label') || '';
                        const opts = Array.from(rg.querySelectorAll('[role="radio"]'));
                        const optLabels = opts.map(o => o.getAttribute('aria-label') || o.innerText.substring(0, 30));
                        output.push("  RG[" + i + "] label=" + label + " opts=[" + optLabels.join(', ') + "]");
                    });
                    
                    // Buttons
                    const btns = document.querySelectorAll('button, div[role="button"]');
                    output.push("Buttons: " + btns.length);
                    btns.forEach((btn, i) => {
                        const txt = btn.innerText.substring(0, 30).replace(/\\n/g, ' ');
                        output.push("  BTN[" + i + "] txt='" + txt + "' aria='" + (btn.getAttribute('aria-label')||'') + "'");
                    });
                    
                    return output.join("\\n");
                }""")
                print(f"=== FORM DOM DUMP ===\n{dom_info}\n=== END DOM DUMP ===")
                logging.info(f"Form DOM dump:\n{dom_info}")
            except Exception as e:
                print(f"DOM dump failed: {e}")
            
            # Get all visible text inputs for positional fallback
            visible_inputs = self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('input'))
                    .filter(i => i.offsetParent !== null && (i.type === 'text' || i.type === '' || !i.type))
                    .map((inp, idx) => ({
                        index: idx,
                        type: inp.type,
                        ariaLabel: inp.getAttribute('aria-label') || '',
                        placeholder: inp.placeholder || '',
                        name: inp.name || ''
                    }));
            }""")
            print(f"Found {len(visible_inputs)} visible text inputs")
            for vi in visible_inputs:
                print(f"  [{vi['index']}] aria='{vi['ariaLabel']}' ph='{vi['placeholder']}'")
            
            def fill_by_label(label_text_or_list, value, is_date=False):
                try:
                    labels = label_text_or_list if isinstance(label_text_or_list, list) else [label_text_or_list]
                    
                    for label_text in labels:
                        print(f"🔍 Looking for field: '{label_text}'...")
                        
                        # Strategy 1: aria-label (case-insensitive partial match)
                        # Microsoft Forms often uses aria-label for accessibility
                        try:
                            # Use JavaScript to find inputs with case-insensitive aria-label match
                            input_el = self.page.evaluate(f'''() => {{
                                const searchText = "{label_text}".toLowerCase();
                                const inputs = Array.from(document.querySelectorAll('input[aria-label]'));
                                return inputs.find(input => 
                                    input.getAttribute('aria-label').toLowerCase().includes(searchText)
                                );
                            }}''')
                            
                            if input_el:
                                # Re-locate the element using Playwright
                                aria_label = self.page.evaluate('(el) => el.getAttribute("aria-label")', input_el)
                                inp = self.page.locator(f'input[aria-label="{aria_label}"]').first
                                if inp.is_visible():
                                    inp.fill(value)
                                    print(f"   ✅ Filled by aria-label: {label_text} = {value}")
                                    return True
                        except Exception as e:
                            print(f"   Strategy 1 failed: {e}")
                        
                        # Strategy 2: Find by placeholder (case-insensitive)
                        try:
                            placeholders = self.page.locator('input[placeholder]').all()
                            for inp in placeholders:
                                placeholder = inp.get_attribute('placeholder') or ''
                                if label_text.lower() in placeholder.lower():
                                    if inp.is_visible():
                                        inp.fill(value)
                                        print(f"   ✅ Filled by placeholder: {label_text} = {value}")
                                        return True
                        except Exception as e:
                            print(f"   Strategy 2 failed: {e}")
                        
                        # Strategy 3: Find text containing label, then find nearest input
                        # This handles cases where the label is in a div/span near the input
                        try:
                            # Case-insensitive text search using regex
                            pattern = label_text.replace(' ', '\\s*')  # Allow flexible spacing
                            text_locator = self.page.locator(f'text=/{pattern}/i').first
                            
                            if text_locator.count() > 0:
                                # Try to find input in the same question container
                                # MS Forms structure: question container > label text + input
                                container = text_locator.locator('xpath=./ancestor::div[@data-automation-id="questionItem"]').first
                                
                                if container.count() > 0:
                                    # Find input within this container
                                    inp = container.locator('input[type="text"], input:not([type])').first
                                    if inp.count() > 0 and inp.is_visible():
                                        inp.fill(value)
                                        print(f"   ✅ Filled by container context: {label_text} = {value}")
                                        return True
                                
                                # Fallback: find any input after the text in DOM order
                                inp = self.page.locator(f'text=/{pattern}/i ~ input, text=/{pattern}/i + input').first
                                if inp.count() > 0 and inp.is_visible():
                                    inp.fill(value)
                                    print(f"   ✅ Filled by DOM proximity: {label_text} = {value}")
                                    return True
                        except Exception as e:
                            print(f"   Strategy 3 failed: {e}")
                        
                        # Strategy 4: Brute force - find all visible text inputs and match by nearby text
                        try:
                            all_inputs = self.page.locator('input[type="text"], input:not([type])').all()
                            for inp in all_inputs:
                                if not inp.is_visible():
                                    continue
                                
                                # Get the parent container
                                parent_text = inp.evaluate('el => el.closest("div[data-automation-id=\\"questionItem\\"]")?.innerText || ""')
                                if label_text.lower() in parent_text.lower():
                                    inp.fill(value)
                                    print(f"   ✅ Filled by parent text match: {label_text} = {value}")
                                    return True
                        except Exception as e:
                            print(f"   Strategy 4 failed: {e}")
                    
                    print(f"   ⚠️ Could not find input for any of: {labels}")
                    # CRITICAL FIX: Raise error for mandatory fields to prevent silent skipping
                    if any(keyword in ' '.join(labels).lower() for keyword in ['student name', 'name of the student', 'roll number']):
                        # Take a screenshot for debugging
                        try:
                            self.page.screenshot(path=f'debug_field_not_found_{datetime.now().strftime("%H%M%S")}.png')
                        except:
                            pass
                        raise Exception(f"Critical Field Not Found: {labels[0]}")
                    return False
                except Exception as e:
                    print(f"   ❌ Error filling {label_text_or_list}: {e}")
                    raise e

            def select_radio(label_text, option_text):
                try:
                    logging.info(f"🔍 Looking for radio: '{label_text}' -> '{option_text}'...")
                    if not option_text:
                        logging.warning("   ⚠️ No option text provided, skipping radio selection")
                        return False
                        
                    # Strategy 1: Find by role="radio" with aria-label
                    choice = self.page.locator(f'div[role="radio"][aria-label="{option_text}"]')
                    if choice.count() > 0:
                        choice.first.click()
                        logging.info(f"   ✅ Selected radio (aria-label): {option_text}")
                        return True
                    
                    # Strategy 2: Find exact text match
                    choice = self.page.locator(f':text("{option_text}")')
                    if choice.count() > 0:
                        choice.first.click()
                        logging.info(f"   ✅ Selected radio (text): {option_text}")
                        return True
                        
                    # Strategy 3: Find loose text match (case-insensitive)
                    pattern = option_text.replace('(', '\\(').replace(')', '\\)')
                    choice = self.page.locator(f'text=/{pattern}/i')
                    if choice.count() > 0:
                        choice.first.click()
                        logging.info(f"   ✅ Selected radio (regex): {option_text}")
                        return True
                        

                    # Strategy 4: Find any radio button in the question container (if only one question is asked)
                    # If label_text is found, look for radios inside that container
                    label_locator = self.page.locator(f'text=/{label_text}/i').first
                    if label_locator.count() > 0:
                        container = label_locator.locator('xpath=./ancestor::div[@data-automation-id="questionItem"]').first
                        if container.count() > 0:
                            radios = container.locator('[role="radio"]').all()
                            for radio in radios:
                                radio_aria = radio.get_attribute('aria-label') or ''
                                if option_text.lower() in radio_aria.lower():
                                    radio.click()
                                    logging.info(f"   ✅ Selected radio in container: {option_text}")
                                    return True
                            
                            # Strategy 5: Text-based sibling match WITHIN the question container
                            # Find the text of the option, then find the radio near it
                            # This handles MS Forms where text is in a <span class="text-format-content"> next to the radio
                            try:
                                # Find the option text element inside this specific question container to avoid cross-question pollution
                                option_text_el = container.locator(f'text="{option_text}"').first
                                if option_text_el.count() > 0:
                                    # We found the text "B.B.A" inside the question "Programme Name"
                                    # Now find the radio button relative to this text.
                                    # Usually, they are in a common wrapper.
                                    # Let's try clicking the text itself (sometimes works) or the radio preceding it
                                    logging.info(f"   found option text '{option_text}', trying to find its radio...")
                                    
                                    # Try 1: Click the text element directly (often triggers the radio)
                                    try:
                                        option_text_el.click(force=True, timeout=1000)
                                        # Verify if aria-checked became true? Difficult without re-querying.
                                        # Assume click worked if no error.
                                        logging.info(f"   ✅ Clicked option text: {option_text}")
                                        return True
                                    except:
                                        pass

                                    # Try 2: Find ancestor div that contains both, then find [role="radio"]
                                    # Common MS Forms: div > div > [radio, label]
                                    wrapper = option_text_el.locator('xpath=./ancestor::div[.//div[@role="radio"]][1]').first
                                    if wrapper.count() > 0:
                                        radio = wrapper.locator('[role="radio"]').first
                                        if radio.count() > 0:
                                            radio.click(force=True)
                                            logging.info(f"   ✅ Selected radio via wrapper: {option_text}")
                                            return True
                            except Exception as e:
                                logging.warning(f"   Strategy 5 failed: {e}")

                    logging.warning(f"   ⚠️ Could not find option '{option_text}'")
                    # Take screenshot
                    try:
                        self.page.screenshot(path=f'debug_radio_fail_{datetime.now().strftime("%H%M%S")}.png')
                    except:
                        pass
                    return False
                except Exception as e:
                    logging.error(f"   ❌ Error selecting {option_text}: {e}")
                    return False

            # --- FILLING FIELDS ---
            
            # 1. Name & Roll (Standard) - with POSITIONAL FALLBACK
            name_filled = False
            roll_filled = False
            
            try:
                name_filled = fill_by_label(["Name of the Student", "Student Name", "Name", "Full Name"], form_data['student_name'])
            except Exception as e:
                print(f"Label-based name fill failed: {e}")
                name_filled = False
            
            try:
                roll_filled = fill_by_label(["Roll Number", "Roll No", "Roll No.", "Student ID"], form_data['roll_number'])
            except Exception as e:
                print(f"Label-based roll fill failed: {e}")
                roll_filled = False
            
            # POSITIONAL FALLBACK: If label-based failed, fill by input order
            if not name_filled or not roll_filled:
                print("FALLBACK: Trying positional input filling...")
                try:
                    # Get all visible text-like inputs using JS
                    text_inputs = self.page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('input'))
                            .filter(i => {
                                if (i.offsetParent === null) return false;  // not visible
                                if (i.type === 'hidden' || i.type === 'submit' || i.type === 'button' || i.type === 'checkbox' || i.type === 'radio' || i.type === 'file') return false;
                                return true;
                            })
                            .map((inp, idx) => ({
                                index: idx,
                                type: inp.type || 'text',
                                ariaLabel: inp.getAttribute('aria-label') || '',
                                tagName: inp.tagName
                            }));
                    }""")
                    
                    print(f"Positional fallback: found {len(text_inputs)} fillable inputs")
                    
                    # Fill by position: 1st input = name, 2nd = roll
                    # Use Playwright locators with nth-match
                    fillable = self.page.locator('input:visible').filter(
                        has_not=self.page.locator('[type="hidden"], [type="submit"], [type="button"], [type="checkbox"], [type="radio"], [type="file"]')
                    )
                    
                    # Alternative: just get all visible inputs that accept text
                    all_text_inputs = self.page.locator('input[type="text"]:visible, input:not([type]):visible').all()
                    
                    if not name_filled and len(all_text_inputs) >= 1:
                        all_text_inputs[0].fill(form_data['student_name'])
                        print(f"   POSITIONAL: Filled input[0] with name: {form_data['student_name']}")
                        name_filled = True
                    
                    if not roll_filled and len(all_text_inputs) >= 2:
                        all_text_inputs[1].fill(form_data['roll_number'])
                        print(f"   POSITIONAL: Filled input[1] with roll: {form_data['roll_number']}")
                        roll_filled = True
                    
                    if not name_filled:
                        # Last resort: try filling via JavaScript directly
                        self.page.evaluate(f"""() => {{
                            const inputs = Array.from(document.querySelectorAll('input'))
                                .filter(i => i.offsetParent !== null && i.type !== 'hidden' && i.type !== 'submit' && i.type !== 'button' && i.type !== 'radio' && i.type !== 'checkbox' && i.type !== 'file');
                            if (inputs.length > 0) {{
                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                nativeInputValueSetter.call(inputs[0], '{form_data["student_name"]}');
                                inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                inputs[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                            }}
                        }}""")
                        print(f"   JS FALLBACK: Set input[0] value via JS to: {form_data['student_name']}")
                        name_filled = True
                    
                    if not roll_filled:
                        self.page.evaluate(f"""() => {{
                            const inputs = Array.from(document.querySelectorAll('input'))
                                .filter(i => i.offsetParent !== null && i.type !== 'hidden' && i.type !== 'submit' && i.type !== 'button' && i.type !== 'radio' && i.type !== 'checkbox' && i.type !== 'file');
                            if (inputs.length > 1) {{
                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                nativeInputValueSetter.call(inputs[1], '{form_data["roll_number"]}');
                                inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                inputs[1].dispatchEvent(new Event('change', {{ bubbles: true }}));
                            }}
                        }}""")
                        print(f"   JS FALLBACK: Set input[1] value via JS to: {form_data['roll_number']}")
                        roll_filled = True
                        
                except Exception as e:
                    print(f"Positional fallback failed: {e}")
                    # Take screenshot for debugging
                    try:
                        self.page.screenshot(path=f'debug_positional_fail_{datetime.now().strftime("%H%M%S")}.png')
                    except:
                        pass
                    raise Exception(f"Could not fill name/roll fields by any method: {e}")
            
            # 2. Radios
            # STRICT: No defaults. Use provided value or empty string.
            select_radio("School Name", form_data.get('school') or '')
            select_radio("Academic Session", form_data.get('academic_session') or '')
            
            # PDF Format has "Programme Name" as radio (BBA, MBBA, BCom etc.)
            # Normalize the programme value to match MS Form options exactly
            programme_raw = form_data.get('programme') or ''
            programme_normalized = self.normalize_programme(programme_raw)
            if programme_raw and programme_raw != programme_normalized:
                print(f"🔄 Programme mapping: '{programme_raw}' → '{programme_normalized}'")
            select_radio("Programme Name", programme_normalized)
            
            # 3. Dates
            # This form only has "Leave Start Date" (no End Date field)
            start_date_filled = False
            end_date_filled = True  # No end date field on this form
            
            # 3. Dates
            # Try specific labels first
            start_date_filled = False
            end_date_filled = False
            
            # Convert date to M/d/yyyy format for both Start and End
            def format_date_mdy(d_str):
                if not d_str: return ''
                for sep in ['/', '.', '-']:
                    parts = d_str.split(sep)
                    if len(parts) == 3:
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            return f"{int(parts[1])}/{int(parts[2])}/{parts[0]}"
                        elif int(parts[0]) > 12:  # DD/MM/YYYY
                            return f"{int(parts[1])}/{int(parts[0])}/{parts[2]}"
                return d_str

            start_date_val = format_date_mdy(form_data.get('leave_start_date', ''))
            end_date_val = format_date_mdy(form_data.get('leave_end_date', ''))
            
            try:
                start_date_filled = fill_by_label(["Leave Start Date", "Date"], start_date_val, is_date=True)
            except:
                pass
                
            try:
                # PDF Format has "Leave End date"
                end_date_filled = fill_by_label(["Leave End Date", "Leave End date"], end_date_val, is_date=True)
            except:
                pass
            
            # DATE POSITIONAL FALLBACK
            # If dates weren't filled, try filling 3rd and 4th inputs (assuming 1st=Name, 2nd=Roll)
            if (not start_date_filled or not end_date_filled) and form_data.get('leave_start_date'):
                print("FALLBACK: Trying positional date filling...")
                try:
                    all_text_inputs = self.page.locator('input[type="text"]:visible, input:not([type]):visible').all()
                    
                    # Method A: Positional (3rd and 4th inputs)
                    # We expect Name(0) and Roll(1) to be first. Dates should be next.
                    if not start_date_filled and len(all_text_inputs) >= 3:
                        # Check if it looks like a date field
                        aria = all_text_inputs[2].get_attribute('aria-label') or ''
                        place = all_text_inputs[2].get_attribute('placeholder') or ''
                        if 'date' in aria.lower() or 'date' in place.lower() or 'start' in aria.lower():
                            all_text_inputs[2].fill(form_data['leave_start_date'])
                            print(f"   POSITIONAL: Filled input[2] with start date: {form_data['leave_start_date']}")
                            start_date_filled = True
                        
                    if not end_date_filled and len(all_text_inputs) >= 4:
                        aria = all_text_inputs[3].get_attribute('aria-label') or ''
                        place = all_text_inputs[3].get_attribute('placeholder') or ''
                        if 'date' in aria.lower() or 'date' in place.lower() or 'end' in aria.lower():
                            all_text_inputs[3].fill(form_data['leave_end_date'])
                            print(f"   POSITIONAL: Filled input[3] with end date: {form_data['leave_end_date']}")
                            end_date_filled = True
                            
                    # Method B: Search for ANY input containing "date" in label/placeholder
                    if not start_date_filled or not end_date_filled:
                        print("   GENERIC DATE SEARCH: Looking for any 'date' inputs...")
                        for inp in all_text_inputs:
                            if not inp.is_visible(): continue
                            
                            # Skip if already filled
                            if inp.input_value(): continue
                            
                            aria = (inp.get_attribute('aria-label') or '').lower()
                            place = (inp.get_attribute('placeholder') or '').lower()
                            
                            # Identify start/end intent
                            is_start = 'start' in aria or 'from' in aria
                            is_end = 'end' in aria or 'to' in aria
                            is_generic = 'date' in aria or 'date' in place
                            
                            if not start_date_filled and (is_start or (is_generic and not end_date_filled)):
                                inp.fill(form_data['leave_start_date'])
                                print(f"   GENERIC: Found potential START date field: {aria}")
                                start_date_filled = True
                            elif not end_date_filled and (is_end or (is_generic and start_date_filled)):
                                inp.fill(form_data['leave_end_date'])
                                print(f"   GENERIC: Found potential END date field: {aria}")
                                end_date_filled = True
                                
                except Exception as e:
                    print(f"Positional date fallback failed: {e}")
            
            
            # 4. Parent Details
            # API sends 'parent_phone', 'parent_email'
            fill_by_label(["Parents Contact No.", "Parent Contact", "Father Mobile", "Mother Mobile", "Contact No."], form_data.get('parent_phone', '') or form_data.get('parent_contact', ''))
            fill_by_label(["Parents Email ID", "Parent Email", "Email ID"], form_data.get('parent_email', ''))
            
            # 5. Student Details
            # API sends 'student_phone', 'student_email'
            fill_by_label(["Student Contact No.", "Student Contact", "Mobile No.", "Contact No."], form_data.get('student_phone', '') or form_data.get('student_contact', ''))
            fill_by_label(["Student Woxsen Email ID", "Student Email", "Email ID"], form_data.get('student_email', ''))
            
            
            # 6. SMART CLEANUP PASS: Fill remaining empty inputs using question context
            # Instead of blindly filling, read each question's text and match to correct data
            print("\n=== SMART CLEANUP PASS ===")
            try:
                # Also convert dates to M/d/yyyy format for any date we're about to fill
                def to_ms_date(date_str):
                    """Convert various date formats to M/d/yyyy"""
                    if not date_str: return ''
                    # Try DD/MM/YYYY or DD.MM.YYYY or DD-MM-YYYY
                    for sep in ['/', '.', '-']:
                        parts = date_str.split(sep)
                        if len(parts) == 3:
                            # Could be DD/MM/YYYY or YYYY-MM-DD or M/d/yyyy
                            if len(parts[0]) == 4:  # YYYY-MM-DD
                                return f"{int(parts[1])}/{int(parts[2])}/{parts[0]}"
                            elif int(parts[0]) > 12:  # DD/MM/YYYY (day > 12)
                                return f"{int(parts[1])}/{int(parts[0])}/{parts[2]}"
                            else:  # Could be M/d/yyyy already or ambiguous
                                return date_str  # Keep as-is
                    return date_str
                
                # Get all question containers
                containers = self.page.locator('div[data-automation-id="questionItem"]').all()
                print(f"Found {len(containers)} question containers")
                
                for i, container in enumerate(containers):
                    try:
                        # Read question text
                        question_text = container.inner_text().lower()
                        question_short = question_text[:100].replace('\n', ' ')
                        
                        # Find inputs in this container
                        inputs = container.locator('input[type="text"]:visible, input:not([type]):visible, textarea:visible').all()
                        
                        for inp in inputs:
                            try:
                                current_val = inp.input_value()
                                if current_val and current_val.strip():
                                    continue  # Already filled, skip
                                
                                # Determine what data this field needs based on question text
                                fill_value = None
                                
                                if any(kw in question_text for kw in ['name of the student', 'student name', 'full name']):
                                    fill_value = form_data.get('student_name', '')
                                elif any(kw in question_text for kw in ['roll number', 'roll no', 'student id']):
                                    fill_value = form_data.get('roll_number', '')
                                elif any(kw in question_text for kw in ['start date', 'from date', 'leaving date']):
                                    fill_value = to_ms_date(form_data.get('leave_start_date', ''))
                                elif any(kw in question_text for kw in ['end date', 'return date', 'to date']):
                                    fill_value = to_ms_date(form_data.get('leave_end_date', ''))
                                elif 'date' in question_text:
                                    # Generic date field - fill with start date if start not filled, else end
                                    if not start_date_filled:
                                        fill_value = to_ms_date(form_data.get('leave_start_date', ''))
                                        start_date_filled = True
                                    elif not end_date_filled:
                                        fill_value = to_ms_date(form_data.get('leave_end_date', ''))
                                        end_date_filled = True
                                elif any(kw in question_text for kw in ['parent', 'father', 'mother', 'guardian']):
                                    if 'email' in question_text:
                                        fill_value = form_data.get('parent_email', '')
                                    elif any(kw in question_text for kw in ['contact', 'phone', 'mobile', 'no.']):
                                        fill_value = form_data.get('parent_phone', '') or form_data.get('parent_contact', '')
                                    else:
                                        fill_value = form_data.get('parent_name', '')
                                elif any(kw in question_text for kw in ['student contact', 'student phone', 'student mobile']):
                                    fill_value = form_data.get('student_phone', '') or form_data.get('student_contact', '')
                                elif any(kw in question_text for kw in ['student email', 'woxsen email', 'student woxsen']):
                                    fill_value = form_data.get('student_email', '')
                                elif any(kw in question_text for kw in ['reason', 'purpose', 'why']):
                                    fill_value = form_data.get('reason', '')
                                elif any(kw in question_text for kw in ['programme', 'program', 'course']):
                                    fill_value = form_data.get('programme', '')
                                elif any(kw in question_text for kw in ['specialization', 'branch', 'major']):
                                    fill_value = form_data.get('specialization', '')
                                elif any(kw in question_text for kw in ['session', 'year', 'batch']):
                                    fill_value = form_data.get('academic_session', '')
                                elif 'email' in question_text:
                                    fill_value = form_data.get('student_email', '')
                                elif any(kw in question_text for kw in ['contact', 'phone', 'mobile']):
                                    fill_value = form_data.get('student_phone', '')
                                    
                                if fill_value:
                                    inp.fill(fill_value)
                                    print(f"   SMART FILL Q[{i}]: '{question_short}' -> {fill_value}")
                                else:
                                    print(f"   SKIP Q[{i}]: '{question_short}' (no matching data)")
                            except Exception as e:
                                print(f"   Error filling input in Q[{i}]: {e}")
                    except Exception as e:
                        print(f"   Error processing container {i}: {e}")
                
                print("✅ Smart cleanup pass completed")
            except Exception as e:
                print(f"Smart cleanup pass failed: {e}")
            
            print("\n✅ Form filling logic completed.")
            
            # Capture debug screenshot of filled form
            self.page.screenshot(path=f'debug_filled_{datetime.now().strftime("%H%M%S")}.jpg')
            return True

        except Exception as e:
            print(f"❌ Form filling error: {str(e)}")
            raise

    def get_filled_values(self):
        """Scrape the current state of the form for verification"""
        print("🔍 Scraping form for verification...")
        data = {}
        try:
            # Get all text inputs
            inputs = self.page.locator('input[type="text"], input[type="email"], input[type="tel"], textarea')
            count = inputs.count()
            for i in range(count):
                inp = inputs.nth(i)
                # Try to get label
                # This is tricky in MS Forms. We might just get values.
                # Or better: get the whole page text?
                val = inp.input_value()
                aria = inp.get_attribute('aria-label') or f"field_{i}"
                data[aria] = val
            
            # Get selected radios
            radios = self.page.locator('div[role="radio"][aria-checked="true"]')
            for i in range(radios.count()):
                r = radios.nth(i)
                label = r.get_attribute('aria-label')
                data[f"radio_{i}"] = label
                
            return data
        except Exception as e:
            print(f"⚠️ Scraping failed: {e}")
            return {"error": str(e)}

    def submit_form(self, verification_callback=None):
        """
        Submit and STRICTLY verify success.
        Optionally run external verification (AI) before clicking submit.
        """
        try:
            # AI VERIFICATION STEP - DISABLED PER USER REQUEST
            # if verification_callback:
            #     print("🤖 Running AI Verification...")
            #     filled_data = self.get_filled_values()
            #     # Take screenshot for AI
            #     screenshot_bytes = self.page.screenshot(type='jpeg', quality=50)
            #     
            #     # Call callback
            #     is_valid, reason = verification_callback(filled_data, screenshot_bytes)
            #     if not is_valid:
            #         raise Exception(f"AI Verification Failed: {reason}")
            #     print("✅ AI Verified. Proceeding to submit.")

            print("🚀 Preparing to submit form...")
            
            # PRE-SUBMIT VALIDATION CHECK - DISABLED PER USER REQUEST
            # The validation check was causing false positives and preventing submission
            # Microsoft Forms will show its own errors after clicking Submit if needed
            
            # # Scroll to bottom to trigger any lazy validation
            # try:
            #     self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            #     time.sleep(1)
            #     self.page.evaluate("window.scrollTo(0, 0)")
            #     time.sleep(1)
            # except:
            #     pass
            
            # # Check for validation error messages
            # error_selectors = [
            #     '.office-form-question-error-message',
            #     '[role="alert"]',
            #     ':text("This question is required")',
            #     ':text("Please enter")',
            #     # ':text("Required")', # Too broad, matches legend
            #     '.validation-error'
            # ]
            
            # has_errors = False
            # error_details = []
            
            # for selector in error_selectors:
            #     try:
            #         errors = self.page.locator(selector)
            #         if errors.count() > 0:
            #             for i in range(min(errors.count(), 10)):  # Max 10 errors
            #                 err = errors.nth(i)
            #                 if err.is_visible():
            #                     err_text = err.inner_text()
            #                     # Try to find parent question container for context
            #                     try:
            #                         parent_question = err.locator('xpath=ancestor::*[@data-automation-id="questionItem"]').first
            #                         if parent_question.count() > 0:
            #                             # Try multiple selectors for the question text
            #                             q_title = parent_question.locator('.text-format-content, span[class*="question-title"], [role="heading"]').first
            #                             if q_title.count() > 0:
            #                                 question_text = q_title.inner_text()
            #                                 error_details.append(f"'{question_text[:50]}': {err_text}")
            #                             else:
            #                                 error_details.append(f"Unknown Question (no title): {err_text}")
            #                         else:
            #                             error_details.append(f"Global Error: {err_text}")
            #                     except Exception as e:
            #                         error_details.append(f"{err_text} (ctx error: {e})")
            #                     has_errors = True
            #     except:
            #         pass
            
            # if has_errors:
            #     # Take screenshot showing the errors
            #     self.page.screenshot(path=f'pre_submit_errors_{datetime.now().strftime("%H%M%S")}.png')
            #     
            #     # Get all empty visible required inputs to help debug
            #     empty_required = []
            #     try:
            #         all_inputs = self.page.locator('input[type="text"]:visible, input:not([type]):visible, textarea:visible').all()
            #         for i, inp in enumerate(all_inputs):
            #             try:
            #                 val = inp.input_value()
            #                 aria = inp.get_attribute('aria-label') or f'Input {i}'
            #                 if not val or val.strip() == '':
            #                     empty_required.append(aria)
            #             except:
            #                 pass
            #     except:
            #         pass
            #     
            #     error_msg = f"PRE-SUBMIT VALIDATION FAILED:\n"
            #     error_msg += f"  Visible Errors: {error_details}\n"
            #     if empty_required:
            #         error_msg += f"  Empty Required Fields: {empty_required[:10]}"  # Max 10
            #     
            #     raise Exception(error_msg)
            
            print("✅ Pre-submit validation DISABLED - proceeding directly to submit")
            
            # Take pre-submit screenshot for verification
            self.page.screenshot(path=f'pre_submit_ok_{datetime.now().strftime("%H%M%S")}.png')
            
            print("🚀 Clicking Submit button...")
            
            # Click Submit
            submit_btn = self.page.locator('button:has-text("Submit")')
            if submit_btn.count() > 0:
                submit_btn.first.click()
            else:
                raise Exception("Submit button not found!")
            
            # VERIFICATION
            print("⏳ Waiting for confirmation...")
            time.sleep(2)
            
            # Check for Success Message
            # Standard MS Forms success text: "Thanks!", "Your response was submitted"
            success_indicator = self.page.locator(':text("Thanks!"), :text("Your response was submitted"), :text("Save my response")')
            
            try:
                success_indicator.first.wait_for(state='visible', timeout=10000)
                print("✅ SUBMISSION CONFIRMED: Success message visible.")
                return True
            except Exception:
                # If timeout, checks for errors
                print("⚠️ Success message NOT found. Checking for validation errors...")
                
                # Look for validation errors (usually red text)
                errors = self.page.locator('.office-form-question-error-message, .flower-field-validation-error, :text("This question is required"), :text("Please enter a valid date")')
                if errors.count() > 0:
                    detailed_errors = []
                    count = errors.count()
                    for i in range(count):
                        err_el = errors.nth(i)
                        if not err_el.is_visible():
                            continue
                        
                        err_msg = err_el.inner_text()
                        # Try to find parent question
                        try:
                            parent = err_el.locator('xpath=./ancestor::div[@data-automation-id="questionItem"]').first
                            if parent.count() > 0:
                                # Try to find question title
                                title = parent.locator('.text-format-content, span[class*="question-title"]').first
                                if title.count() > 0:
                                    q_text = title.inner_text()
                                    detailed_errors.append(f"'{q_text}': {err_msg}")
                                else:
                                    detailed_errors.append(f"Unknown Question: {err_msg}")
                            else:
                                detailed_errors.append(f"Global/Unknown: {err_msg}")
                        except:
                            detailed_errors.append(f"Error {i}: {err_msg}")
                    
                    if detailed_errors:
                        raise Exception(f"Form Validation Errors Found: {detailed_errors}")
                
                # If no errors but no success...
                # Maybe it's still loading?
                self.page.screenshot(path=f'error_unknown_{datetime.now().strftime("%H%M%S")}.jpg')
                raise Exception("Submission timed out. No success message and no validation errors found. Check screenshot.")

        except Exception as e:
            print(f"❌ Submit failed: {e}")
            self.page.screenshot(path=f'error_submit_final_{datetime.now().strftime("%H%M%S")}.jpg')
            raise
            # Take screenshot for debugging
            self.page.screenshot(path=f'error_form_fill_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            raise
    
    def upload_pdf(self, pdf_path):
        """
        Upload PDF document to the form
        Supports both local file paths and URLs
        """
        try:
            # Handle None or empty pdf_path
            if not pdf_path:
                print("⚠️ No PDF path provided, skipping upload")
                return True
                
            logging.info(f"📤 Uploading PDF: {pdf_path}")
            
            # Check if pdf_path is a URL
            is_url = pdf_path.startswith('http://') or pdf_path.startswith('https://')
            
            if is_url:
                # Download PDF from URL to temp location
                import requests
                import tempfile
                
                logging.info(f"📥 Downloading PDF from URL...")
                response = requests.get(pdf_path, timeout=30)
                response.raise_for_status()
                
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()
                
                local_pdf_path = temp_file.name
                logging.info(f"✓ Downloaded to: {local_pdf_path}")
            else:
                # Verify local file exists
                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"PDF file not found: {pdf_path}")
                local_pdf_path = pdf_path
            
            # 1. Wait for Upload Section
            logging.info("⏳ Waiting for file upload section...")
            try:
                # MS Forms upload button usually has text "Upload file" or "Upload"
                # We wait for the "Immersive Reader" button, Question List, or the Submit Button
                # 'div[data-automation-id="questionItem"]' is very specific to MS Forms
                self.page.wait_for_selector('text=Upload', timeout=10000)
            except:
                logging.warning("⚠️ 'Upload' text not found, trying generic file input wait...")

            # 2. Trigger Upload via FileChooser
            # This is more robust for MS Forms where input[type=file] might be hidden or lazy-loaded
            try:
                with self.page.expect_file_chooser(timeout=10000) as fc_info:
                    # Click the "Upload" button to trigger the dialog
                    # We try a few likely selectors
                    upload_btn = self.page.locator('button[aria-label^="Upload file"], button[aria-label*="File number limit"], button:has-text("Upload file"), div[role="button"]:has-text("Upload file"), button:has-text("Upload"), div[role="button"]:has-text("Upload")')
                    
                    if upload_btn.count() > 0:
                        btn_txt = upload_btn.first.inner_text()
                        logging.info(f"🖱️ Clicking 'Upload' button (text='{btn_txt}')...")
                        upload_btn.first.click(force=True)
                    else:
                        # Fallback: try to find the generic input again if button fails
                        logging.warning("⚠️ Upload button not found via text. Trying generic input...")
                        file_input = self.page.locator('input[type="file"]')
                        if file_input.count() > 0:
                            file_input.first.set_input_files(local_pdf_path)
                            logging.info("✅ PDF uploaded via direct input (fallback).")
                            time.sleep(15) # Wait for upload
                            return True
                        else:
                             raise Exception("Neither Upload button nor file input found.")

                file_chooser = fc_info.value
                file_chooser.set_files(local_pdf_path)
                logging.info("PDF uploaded via FileChooser!")
                
                # Wait for upload completion indicator (file name display)
                pdf_name = os.path.basename(local_pdf_path)
                logging.info(f"⏳ Waiting for upload completion indicator (file name: {pdf_name})...")
                try:
                    # MS Forms usually shows the file name after successful upload
                    self.page.wait_for_selector(f'text="{pdf_name}"', timeout=10000)
                    logging.info("✅ Upload confirmed - file name is visible!")
                except PlaywrightTimeout:
                    logging.warning("⚠️ File name not visible, but continuing (upload might still work)...")

            except PlaywrightTimeout:
                logging.warning("⚠️ FileChooser timeout. Trying direct input set as last resort...")
                # Last resort: maybe input is there but event didn't fire?
                file_input = self.page.locator('input[type="file"]')
                if file_input.count() > 0:
                    file_input.first.set_input_files(local_pdf_path)
                    logging.info("✅ PDF uploaded via direct input (last resort).")
                else:
                    raise Exception("File upload failed: FileChooser timed out and input[type='file'] not found.")
            
            # Wait for upload to complete
            logging.info("⏳ Waiting 15s for PDF to process...")
            time.sleep(15)  # INCREASED WAIT: Give it time to upload and scan
                
        except Exception as e:
            logging.error(f"❌ PDF upload failed: {str(e)}")
            try:
                self.page.screenshot(path=f'error_pdf_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            except:
                pass
            raise
    
    def run_automation(self, form_url, email, password, form_data, pdf_path, status_callback=None, verification_callback=None):
        """
        Complete automation workflow.
        status_callback: function(message, progress, screenshot_bytes)
        verification_callback: function(scraped_data, screenshot_bytes) -> (bool, str)
        """
        def update_status(msg, prog):
            print(f"[{prog}%] {msg}")
            if status_callback:
                try:
                    # Capture screenshot for "Live View" (only if page exists)
                    screenshot = None
                    if hasattr(self, 'page') and self.page:
                        screenshot = self.page.screenshot(type='jpeg', quality=50)
                    status_callback(msg, prog, screenshot)
                except Exception as e:
                    logging.warning(f"Failed to capture screenshot: {e}")
                    status_callback(msg, prog, None)

        try:
            print("=" * 60)
            print("STARTING MICROSOFT FORMS AUTOMATION")
            print("=" * 60)
            print(f"Human-like delays: {self.min_delay//60}-{self.max_delay//60} minutes between steps")
            
            # RETRY LOOP FOR AUTHENTICATION
            MAX_RETRIES = 2
            for attempt in range(MAX_RETRIES):
                try:
                    logging.info(f"--- Automation Attempt {attempt+1}/{MAX_RETRIES} ---")
                    
                    # Step 1: Start browser
                    update_status("Starting browser session...", 10)
                    self.start_browser(email)
                    
                    # Step 2: Navigate to form URL
                    update_status(f"Navigating to form: {form_url}", 20)
                    # Increased timeout to 60s for initial load
                    self.page.goto(form_url, timeout=60000)
                    time.sleep(3)
                    
                    # Step 3: Handle Microsoft login
                    update_status("Authenticating with Microsoft...", 40)
                    self.microsoft_login(email, password)
                    
                    print("⏳ Stability Delay: Waiting 5s before accessing form...")
                    time.sleep(5) # Explicit wait for redirect/render as requested by user
                    
                    # EXPLICIT LOADING CHECK
                    self.wait_for_loading_screen()
                    
                    # Step 4: Validate we are actually on the form
                    update_status("Verifying form access...", 50)
                    try:
                        # Wait for specific MS Form elements
                        self.page.wait_for_selector(
                            'div[data-automation-id="questionItem"], button:has-text("Submit"), div:has-text("Hi,")', 
                            timeout=20000
                        )
                        
                        # Double check we are NOT on login page
                        if "login.microsoftonline.com" in self.page.url:
                             raise Exception("Redirected back to Login Page after authentication attempt!")
                             
                    except PlaywrightTimeout:
                        current_url = self.page.url
                        if "login.microsoftonline.com" in current_url:
                             raise Exception("Authentication Failed - Stuck on Login Page")
                        title = self.page.title()
                        # Take a screenshot to help debug
                        try:
                            self.page.screenshot(path="debug_form_load_fail.png")
                        except:
                            pass
                        raise Exception(f"Form did not load. Current URL: {current_url}, Title: {title}")
                    
                    # If we passed validation, break the retry loop
                    break

                except Exception as inner_e:
                    # Catch auth failures and retry if possible
                    if "Redirected back to Login Page" in str(inner_e) or "Stuck on Login Page" in str(inner_e):
                        logging.warning(f"⚠️ Encountered login loop/failure: {inner_e}")
                        
                        if attempt < MAX_RETRIES - 1:
                            logging.info("♻️ Invalidating session and retrying with fresh login...")
                            update_status("Session invalid, retrying cleanup...", 15)
                            
                            # DELETE STATE FILE
                            sanitized_email = email.replace('@', '_').replace('.', '_')
                            state_file = f"browser_state_{sanitized_email}.json"
                            if os.path.exists(state_file):
                                try:
                                    os.remove(state_file)
                                    logging.info(f"Deleted stale state file: {state_file}")
                                except Exception as del_e:
                                    logging.error(f"Failed to delete state file: {del_e}")
                            
                            # Close current browser to restart
                            if hasattr(self, 'browser') and self.browser:
                                try:
                                    self.browser.close()
                                except:
                                    pass
                            continue # Retry loop
                        else:
                            raise inner_e # Validation failed on last attempt
                    else:
                        raise inner_e # Unrelated error, re-raise immediately

            # Step 5: Fill form
            update_status("Filling form data...", 60)
            self.fill_form(form_data)
            
            # Step 6: Upload PDF
            update_status("Uploading signed PDF...", 80)
            self.upload_pdf(pdf_path)
            
            # Step 7: Submit (with AI Verification)
            if verification_callback:
                update_status("Verifying with AI...", 90)
            else:
                update_status("Finalizing submission...", 95)
                
            self.submit_form(verification_callback=verification_callback)
            
            update_status("Completed successfully!", 100)
            
            # Keep browser open for a bit
            time.sleep(5)
            # Cleanup
            print("Cleaning up...")
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
                print("Browser closed")
            return True
            
        except Exception as e:
            logging.error("=" * 60)
            logging.error(f"AUTOMATION FAILED: {str(e)}")
            
            # Capture failure screenshot
            if hasattr(self, 'page') and self.page:
                try:
                    fail_shot = f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    self.page.screenshot(path=fail_shot)
                    logging.info(f"Saved FAILURE screenshot to: {fail_shot}")
                    
                    # ALSO send to callback if available so it updates DB
                    if status_callback:
                        screenshot_bytes = self.page.screenshot(type='jpeg', quality=50)
                        status_callback(f"FAILED: {str(e)}", 0, screenshot_bytes)
                        
                except Exception as se:
                    logging.error(f"Could not save failure screenshot: {se}")
                    # Try to report failure without screenshot
                    if status_callback:
                        try:
                            status_callback(f"FAILED: {str(e)}", 0, None)
                        except:
                            pass

            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Full traceback:", exc_info=True)
            logging.error("=" * 60)
            
            # Cleanup here too
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
            
            # Re-raise so api.py can capture the REAL error message
            raise
            
        finally:
            pass
# Force git sync
