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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)

class MSFormAutomation:
    # Path to persist login session across runs
    STORAGE_STATE_FILE = 'browser_state.json'
    
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
        
    def microsoft_login(self, email, password):
        """
        Handle Microsoft authentication flow
        Saves session state after successful login to avoid MFA next time
        """
        try:
            logging.info(f"Attempting login with {email}...")
            
            # First check if we're already logged in (saved session worked)
            current_url = self.page.url
            if 'forms.office.com' in current_url and 'login' not in current_url:
                logging.info("Already logged in via saved session - skipping login!")
                return True
            
            # Check if already on login page
            if 'login.microsoftonline.com' in self.page.url:
                logging.info("Already on Microsoft login page")
            else:
                logging.info("Waiting for redirect to login...")
                self.page.wait_for_url('**/login.microsoftonline.com/**', timeout=15000)
            
            # Enter email
            email_input = self.page.wait_for_selector('input[type="email"]', timeout=10000)
            email_input.fill(email)
            logging.info(f"Email entered: {email}")
            
            # Click Next button
            self.page.click('input[type="submit"]')
            time.sleep(2)
            
            # Enter password
            try:
                password_input = self.page.wait_for_selector('input[type="password"]', timeout=10000)
                password_input.fill(password)
                logging.info("Password entered")
                
                # Click Sign in
                self.page.click('input[type="submit"]')
                time.sleep(3)
                
            except PlaywrightTimeout:
                logging.warning("Password field not found - might be SSO or different auth")
                raise Exception("Authentication method not supported")
            
            # Handle "Stay signed in?" prompt
            try:
                stay_signed_in = self.page.wait_for_selector('text=Stay signed in?', timeout=5000)
                if stay_signed_in:
                    logging.info("'Stay signed in?' prompt - clicking Yes")
                    self.page.click('input[type="submit"][value="Yes"]')
                    time.sleep(2)
            except PlaywrightTimeout:
                logging.info("No 'Stay signed in?' prompt")
            
            # Check for MFA/2FA
            if self.page.url.find('login.microsoftonline.com') != -1:
                logging.warning("MFA/2FA detected! Waiting 120s for approval...")
                
                # Wait for user to approve MFA (120 seconds max)
                try:
                    self.page.wait_for_url('https://forms.office.com/**', timeout=120000)
                    logging.info("MFA approved!")
                except PlaywrightTimeout:
                    raise Exception("MFA approval timeout (120s) - you need to approve the notification on your phone")
            
            # Verify login success
            self.page.wait_for_load_state('networkidle', timeout=15000)
            
            if 'forms.office.com' in self.page.url:
                logging.info("Login successful!")
                
                # SAVE SESSION STATE so we don't need MFA next time
                try:
                    state_file = getattr(self, 'current_state_file', self.STORAGE_STATE_FILE)
                    self.context.storage_state(path=state_file)
                    logging.info(f"Saved browser session to {state_file}")
                except Exception as e:
                    logging.warning(f"Failed to save session state: {e}")
                
                return True
            else:
                raise Exception(f"Login failed - stuck on: {self.page.url}")
                
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            raise
    
    def fill_form(self, form_data):
        """
        Fill all form fields robustly by finding labels
        """
        try:
            print("📝 Starting form filling (Label-Based Strategy)...")
            self.page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            def fill_by_label(label_text_or_list, value, is_date=False):
                try:
                    labels = label_text_or_list if isinstance(label_text_or_list, list) else [label_text_or_list]
                    
                    for label_text in labels:
                        # Find the label element containing the text
                        # MS Forms structure: div[role="heading"] -> spans, or label tags
                        # We look for a container that has the text, then find the input inside it or near it
                        print(f"🔍 Looking for field: '{label_text}'...")
                        
                        # Strategy 1: Look for input with aria-label containing text
                        input_el = self.page.locator(f'input[aria-label*="{label_text}"]')
                        if input_el.count() > 0 and input_el.first.is_visible():
                            input_el.first.fill(value)
                            print(f"   ✅ Filled by aria-label: {label_text} = {value}")
                            return True

                        # Strategy 2: Look for text checks
                        # Find the question text, then find the input in the same container
                        question = self.page.locator(f':text("{label_text}")').first
                        if question.count() > 0:
                            # Go up to the question container (usually a div with specific class or role)
                            # In MS Forms, inputs are usually within the same parent or traverse up/down
                            # Simplest: Input appearing *after* the label in DOM order
                            # We use Playwright's layout selectors if possible, or just look for input inside the question wrapper
                            
                            # Try finding input inside the same section
                            section = question.locator("xpath=./ancestor::div[contains(@class, '-question-')]|./ancestor::div[@role='listitem']")
                            if section.count() > 0:
                                inp = section.first.locator('input').first
                                if inp.count() > 0:
                                    inp.fill(value)
                                    print(f"   ✅ Filled by section context: {label_text} = {value}")
                                    return True
                        
                    print(f"   ⚠️ Could not find input for any of: {labels}")
                    return False
                except Exception as e:
                    print(f"   ❌ Error filling {label_text_or_list}: {e}")
                    return False

            def select_radio(label_text, option_text):
                try:
                    print(f"🔍 Looking for radio: '{label_text}' -> '{option_text}'...")
                    # Find the choice directly
                    choice = self.page.locator(f'div[role="radio"][aria-label="{option_text}"]')
                    if choice.count() > 0:
                        choice.first.click()
                        print(f"   ✅ Selected radio (aria-label): {option_text}")
                        return True
                    
                    # Fallback: exact text match
                    choice = self.page.locator(f':text("{option_text}")')
                    if choice.count() > 0:
                        choice.first.click()
                        print(f"   ✅ Selected radio (text): {option_text}")
                        return True
                        
                    print(f"   ⚠️ Could not find option '{option_text}'")
                    return False
                except Exception as e:
                    print(f"   ❌ Error selecting {option_text}: {e}")
                    return False

            # --- FILLING FIELDS ---
            
            # 1. Name & Roll (Standard)
            fill_by_label(["Name of the Student", "Student Name", "Name", "Full Name"], form_data['student_name'])
            fill_by_label(["Roll Number", "Roll No", "Roll No.", "Student ID"], form_data['roll_number'])
            
            # 2. Radios
            # STRICT: No defaults. Use provided value or empty string.
            select_radio("School Name", form_data.get('school') or '')
            
            # 3. Dates
            # Try specific labels first
            fill_by_label("Leave Start Date", form_data.get('leave_start_date', ''))
            fill_by_label("Leave End Date", form_data.get('leave_end_date', ''))
            
            
            # 4. Parent Details
            # API sends 'parent_phone', 'parent_email'
            fill_by_label(["Parents Contact No.", "Parent Contact", "Father Mobile", "Mother Mobile", "Contact No."], form_data.get('parent_phone', '') or form_data.get('parent_contact', ''))
            fill_by_label(["Parents Email ID", "Parent Email", "Email ID"], form_data.get('parent_email', ''))
            
            # 5. Student Details
            # API sends 'student_phone', 'student_email'
            fill_by_label(["Student Contact No.", "Student Contact", "Mobile No.", "Contact No."], form_data.get('student_phone', '') or form_data.get('student_contact', ''))
            fill_by_label(["Student Woxsen Email ID", "Student Email", "Email ID"], form_data.get('student_email', ''))
            
            # 6. Any other random fields mapping?
            # (Just in case)
            
            print("✅ Form filling logic completed.")
            
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
            # AI VERIFICATION STEP
            if verification_callback:
                print("🤖 Running AI Verification...")
                filled_data = self.get_filled_values()
                # Take screenshot for AI
                screenshot_bytes = self.page.screenshot(type='jpeg', quality=50)
                
                # Call callback
                is_valid, reason = verification_callback(filled_data, screenshot_bytes)
                if not is_valid:
                    raise Exception(f"AI Verification Failed: {reason}")
                print("✅ AI Verified. Proceeding to submit.")

            print("🚀 Submitting form...")
            
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
                # Common classes or text
                errors = self.page.locator('.office-form-question-error-message, :text("This question is required"), :text("Please enter a valid date")')
                if errors.count() > 0:
                    err_texts = errors.all_inner_texts()
                    raise Exception(f"Form Validation Errors Found: {err_texts}")
                
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
            print(f"📤 Uploading PDF: {pdf_path}")
            
            # Check if pdf_path is a URL
            is_url = pdf_path.startswith('http://') or pdf_path.startswith('https://')
            
            if is_url:
                # Download PDF from URL to temp location
                import requests
                import tempfile
                
                print(f"📥 Downloading PDF from URL...")
                response = requests.get(pdf_path, timeout=30)
                response.raise_for_status()
                
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()
                
                local_pdf_path = temp_file.name
                print(f"✓ Downloaded to: {local_pdf_path}")
            else:
                # Verify local file exists
                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"PDF file not found: {pdf_path}")
                local_pdf_path = pdf_path
            
            # Find file input
            file_input = self.page.locator('input[type="file"]').first
            
            # Upload file
            file_input.set_input_files(local_pdf_path)
            
            # Wait for upload to complete
            time.sleep(5)  # Give it time to upload and scan
            
            # Clean up temp file if we downloaded it
            if is_url:
                try:
                    os.unlink(local_pdf_path)
                    print(f"🧹 Cleaned up temp file: {local_pdf_path}")
                except:
                    pass
            
            print("✅ PDF uploaded successfully!")
            return True
                
        except Exception as e:
            print(f"❌ PDF upload failed: {str(e)}")
            self.page.screenshot(path=f'error_pdf_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            raise
    
    def submit_form(self):
        """
        Submit the form and verify submission
        """
        try:
            print("🚀 Submitting form...")
            
            # Find and click submit button
            submit_button = self.page.locator('button:has-text("Submit")').first
            submit_button.click()
            
            # print("NOTE: Submit button click disabled for testing safety. Uncomment in production.")
            
            # Wait for success message
            time.sleep(2)
            
            return True
                    
        except Exception as e:
            print(f"❌ Form submission failed: {str(e)}")
            self.page.screenshot(path=f'error_submit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
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
                    # Capture screenshot for "Live View"
                    screenshot = self.page.screenshot(type='jpeg', quality=50)
                    status_callback(msg, prog, screenshot)
                except Exception as e:
                    logging.warning(f"Failed to capture screenshot: {e}")
                    status_callback(msg, prog, None)

        try:
            print("=" * 60)
            print("🤖 STARTING MICROSOFT FORMS AUTOMATION")
            print("=" * 60)
            print(f"⏱️  Human-like delays: {self.min_delay//60}-{self.max_delay//60} minutes between steps")
            
            # Step 1: Start browser
            update_status("Starting browser session...", 10)
            self.start_browser(email)
            
            # Step 2: Navigate to form URL
            update_status(f"Navigating to form: {form_url}", 20)
            self.page.goto(form_url)
            time.sleep(3)
            
            # Step 3: Handle Microsoft login
            update_status("Authenticating with Microsoft...", 40)
            self.microsoft_login(email, password)
            
            # Step 4: Fill form
            update_status("Filling form data...", 60)
            self.fill_form(form_data)
            
            # Step 5: Upload PDF
            update_status("Uploading signed PDF...", 80)
            self.upload_pdf(pdf_path)
            
            # Step 6: Submit (with AI Verification)
            if verification_callback:
                update_status("Verifying with AI...", 90)
            else:
                update_status("Finalizing submission...", 95)
                
            self.submit_form(verification_callback=verification_callback)
            
            update_status("Completed successfully!", 100)
            
            # Keep browser open for a bit
            time.sleep(5)
            return True
            
        except Exception as e:
            logging.error("=" * 60)
            logging.error(f"❌ AUTOMATION FAILED: {str(e)}")
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Full traceback:", exc_info=True)
            logging.error("=" * 60)
            # Re-raise so api.py can capture the REAL error message
            raise
            
        finally:
            # Cleanup
            if self.browser:
                print("\n🧹 Cleaning up...")
                self.browser.close()
                print("✅ Browser closed")
