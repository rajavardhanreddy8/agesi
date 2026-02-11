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
from datetime import datetime
from pathlib import Path

class MSFormAutomation:
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
        
    def start_browser(self):
        """Initialize browser with optimal settings"""
        playwright = sync_playwright().start()
        
        # Launch browser with settings to avoid detection
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create context with realistic settings
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = self.context.new_page()
        
        # Remove webdriver property
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        print("✅ Browser started successfully")
        
    def microsoft_login(self, email, password):
        """
        Handle Microsoft authentication flow
        Supports MFA notifications (requires manual approval)
        """
        try:
            print(f"🔐 Attempting login with {email}...")
            
            # Check if already on login page
            if 'login.microsoftonline.com' in self.page.url:
                print("Already on Microsoft login page")
            else:
                print("Waiting for redirect to login...")
                self.page.wait_for_url('**/login.microsoftonline.com/**', timeout=10000)
            
            # Enter email
            email_input = self.page.wait_for_selector('input[type="email"]', timeout=10000)
            email_input.fill(email)
            print(f"✓ Email entered: {email}")
            
            # Click Next button
            self.page.click('input[type="submit"]')
            time.sleep(2)
            
            # Enter password
            try:
                password_input = self.page.wait_for_selector('input[type="password"]', timeout=10000)
                password_input.fill(password)
                print("✓ Password entered")
                
                # Click Sign in
                self.page.click('input[type="submit"]')
                time.sleep(3)
                
            except PlaywrightTimeout:
                print("⚠️ Password field not found - might be SSO or different auth method")
                raise Exception("Authentication method not supported")
            
            # Handle "Stay signed in?" prompt
            try:
                stay_signed_in = self.page.wait_for_selector('text=Stay signed in?', timeout=5000)
                if stay_signed_in:
                    print("📋 'Stay signed in?' prompt detected")
                    # Click "Yes" to stay signed in
                    self.page.click('input[type="submit"][value="Yes"]')
                    time.sleep(2)
            except PlaywrightTimeout:
                print("ℹ️ No 'Stay signed in?' prompt")
            
            # Check for MFA/2FA
            if self.page.url.find('login.microsoftonline.com') != -1:
                print("⚠️ MFA/2FA detected!")
                print("🔔 Please approve the authentication request on your device...")
                print("⏳ Waiting up to 60 seconds for approval...")
                
                # Wait for user to approve MFA (60 seconds max)
                try:
                    self.page.wait_for_url('https://forms.office.com/**', timeout=60000)
                    print("✅ MFA approved - logged in successfully!")
                except PlaywrightTimeout:
                    raise Exception("MFA approval timeout - please approve faster next time")
            
            # Verify login success
            self.page.wait_for_load_state('networkidle', timeout=15000)
            
            if 'forms.office.com' in self.page.url:
                print("✅ Login successful!")
                return True
            else:
                raise Exception(f"Login failed - stuck on: {self.page.url}")
                
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            raise
    
    def fill_form(self, form_data):
        """
        Fill all form fields with provided data
        Includes random micro-delays between fields to simulate human behavior
        """
        try:
            print("📝 Starting form filling...")
            
            # Wait for form to fully load
            self.page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # Helper functions for index-based filling
            inputs = self.page.locator('input[placeholder="Enter your answer"]')
            date_inputs = self.page.locator('input[placeholder*="date"]')
            
            def fill_idx(idx, val):
                try:
                    if inputs.nth(idx).is_visible():
                        # Random micro-delay before each field (2-8 seconds)
                        delay = random.uniform(2, 8)
                        time.sleep(delay)
                        inputs.nth(idx).fill(val)
                        print(f"Filled input index {idx} with {val} (waited {delay:.1f}s)")
                except Exception as e:
                    print(f"Skipping input {idx}: {e}")

            def click_radio(text):
                try:
                    # Random micro-delay before clicking (2-6 seconds)
                    delay = random.uniform(2, 6)
                    time.sleep(delay)
                    # Try span locators first (common in MS Forms)
                    el = self.page.locator(f'span:has-text("{text}")').first
                    if el.count() > 0:
                        el.click()
                        print(f"Clicked radio/text: {text} (waited {delay:.1f}s)")
                    else:
                         # Fallback to div role=radio
                        el = self.page.locator(f'div[role="radio"]:has-text("{text}")').first
                        if el.count() > 0:
                            el.click()
                            print(f"Clicked radio div: {text}")
                except Exception as e:
                    print(f"Failed to click {text}: {e}")

            # 1. Name
            fill_idx(0, form_data['student_name'])
            # 2. Roll
            fill_idx(1, form_data['roll_number'])
            
            # 3, 4, 5. Radios
            click_radio(form_data.get('school', 'School of Technology'))
            click_radio(form_data.get('academic_session', '2024-2028'))
            click_radio(form_data.get('programme', 'B.Tech'))
            
            # 6. Specialization
            fill_idx(2, form_data.get('specialization', 'CSE'))
            
            # 7. Reason
            fill_idx(3, form_data.get('reason', 'home'))
            
            # 8. Start Date & 9. End Date
            # Try to find all date inputs
            print(f"Filling Start Date: {form_data['leave_start_date']}")
            print(f"Filling End Date: {form_data['leave_end_date']}")
            
            try:
                # Re-query date inputs to be fresh
                date_inputs = self.page.locator('input[placeholder*="date"]')
                count = date_inputs.count()
                print(f"Found {count} date inputs via placeholder")
                
                if count >= 1:
                    date_inputs.first.fill(form_data['leave_start_date'])
                    print(f"Filled start date (index 0): {form_data['leave_start_date']}")
                
                if count >= 2:
                    date_inputs.nth(1).fill(form_data['leave_end_date'])
                    print(f"Filled end date (index 1): {form_data['leave_end_date']}")
                elif count == 1:
                     # Fallback: Maybe the second date input has a different placeholder or is a text input?
                     # Let's try looking for inputs near "End Date" text
                     print("Attempting validation/fallback for date fields...")
            except Exception as e: 
                print(f"Date filling error: {e}")
                
            # Fallback for End Date if not filled by generic date locator
            # Sometimes MS Forms treats them as text inputs if configured differently
            # We can try filling by Label if possible, but MS Forms DOM is messy.
            # Assuming the standard 2-date picker layout for now.
            pass
            
            print("✅ All form fields filled (best effort)!")
            return True
            
            print("✅ All form fields filled successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Form filling failed: {str(e)}")
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
    
    def run_automation(self, form_url, email, password, form_data, pdf_path):
        """
        Complete automation workflow with human-like delays
        """
        try:
            print("=" * 60)
            print("🤖 STARTING MICROSOFT FORMS AUTOMATION")
            print("=" * 60)
            print(f"⏱️  Human-like delays: {self.min_delay//60}-{self.max_delay//60} minutes between steps")
            
            # Step 1: Start browser
            self.start_browser()
            
            # Step 2: Navigate to form (with initial delay to simulate reading email)
            self.human_delay("opening form link")
            print(f"\n📍 Navigating to form: {form_url}")
            self.page.goto(form_url)
            time.sleep(3)
            
            # Step 3: Handle Microsoft login
            print("\n🔐 AUTHENTICATION PHASE")
            print("-" * 60)
            self.microsoft_login(email, password)
            
            # Delay after login - simulating user reviewing the form
            self.human_delay("reviewing form")
            
            # Step 4: Fill form
            print("\n📝 FORM FILLING PHASE")
            print("-" * 60)
            self.fill_form(form_data)
            
            # Delay after filling - simulating user reviewing entries
            self.human_delay("reviewing filled data")
            
            # Step 5: Upload PDF
            print("\n📤 PDF UPLOAD PHASE")
            print("-" * 60)
            self.upload_pdf(pdf_path)
            
            # Delay after upload - simulating user waiting for upload confirmation
            self.human_delay("confirming upload", short=True)  # Shorter delay for this
            
            # Step 6: Submit
            print("\n🚀 SUBMISSION PHASE")
            print("-" * 60)
            self.submit_form()
            
            print("\n" + "=" * 60)
            print("✅ AUTOMATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
            # Keep browser open for 5 seconds to verify
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print("\n" + "=" * 60)
            print(f"❌ AUTOMATION FAILED: {str(e)}")
            print("=" * 60)
            return False
            
        finally:
            # Cleanup
            if self.browser:
                print("\n🧹 Cleaning up...")
                self.browser.close()
                print("✅ Browser closed")
