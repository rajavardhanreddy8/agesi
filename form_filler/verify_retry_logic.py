from ms_form_automation import MSFormAutomation
import logging
import os
import time

# Mocking the logging to seeing output
logging.basicConfig(level=logging.INFO)

class MockAutomation(MSFormAutomation):
    def __init__(self):
        self.headless = True
        self.login_attempts = 0
        self.browser_started = 0
        self.min_delay = 0
        self.max_delay = 0
        self.page = MockPage()
        
    def start_browser(self, email=None):
        self.browser_started += 1
        print(f"MOCK: start_browser called (Call #{self.browser_started})")
        self.browser = MockBrowser()
        
    def microsoft_login(self, email, password):
        self.login_attempts += 1
        print(f"MOCK: microsoft_login called (Attempt #{self.login_attempts})")

class MockBrowser:
    def close(self):
        print("MOCK: Browser closed")

class MockPage:
    def __init__(self):
        self.url = "https://forms.office.com/r/xyz"
        self.title_text = "Form"
        
    def goto(self, url, timeout=None):
        print(f"MOCK: Navigated to {url}")
        
    def wait_for_selector(self, selector, timeout=None):
        # Simulate failure on first attempt (State file bad -> redirect to login)
        # We need to simulate the 'checks' inside run_automation
        pass
        
    def screenshot(self, path=None, type=None, quality=None):
        print(f"MOCK: Screenshot taken")
        return b'fakebytes'
        
    def title(self):
        return self.title_text

def test_retry_logic():
    auto = MockAutomation()
    
    # We need to override the method on the instance or subclass, 
    # but run_automation is what we are testing.
    # The logic inside run_automation calls:
    # 1. start_browser
    # 2. page.goto
    # 3. microsoft_login
    # 4. wait_for_loading_screen
    # 5. validation (wait_for_selector)
    
    # We need to inject the failure in step 5 (validation)
    
    # Let's monkeypatch the 'page' object's attributes to simulate the state
    # unexpected change of URL
    
    original_wait_for_selector = auto.page.wait_for_selector
    
    attempt_counter = [0]
    
    def mock_wait_for_selector(*args, **kwargs):
        attempt_counter[0] += 1
        print(f"MOCK: wait_for_selector called (Attempt {attempt_counter[0]})")
        
        if attempt_counter[0] == 1:
            # First attempt: Simulate redirect to login
            auto.page.url = "https://login.microsoftonline.com/common/oauth2/..."
            print("MOCK: URL changed to login.microsoftonline.com")
            # The code checks self.page.url AFTER this call returns (or if it succeeds)
            # functionality in run_automation:
            # self.page.wait_for_selector(...)
            # if "login..." in self.page.url: raise Exception(...)
            return # Return successfully, but with wrong URL
        else:
            # Second attempt: Success
            auto.page.url = "https://forms.office.com/r/xyz"
            print("MOCK: URL stayed on form")
            return

    auto.page.wait_for_selector = mock_wait_for_selector
    
    # Mock wait_for_loading_screen to do nothing
    auto.wait_for_loading_screen = lambda: None
    
    # Mock fill_form/upload/submit to skip them
    auto.fill_form = lambda x: print("MOCK: fill_form skipped")
    auto.upload_pdf = lambda x: print("MOCK: upload_pdf skipped")
    auto.submit_form = lambda x: print("MOCK: submit_form skipped")
    
    print("\n--- STARTING TEST ---")
    try:
        # Pass dummy data
        auto.run_automation(
            form_url="https://forms.office.com/r/xyz",
            email="test@example.com",
            password="password",
            form_data={},
            pdf_path="dummy.pdf"
        )
        print("\n--- TEST PASSED: run_automation completed successfully ---")
    except Exception as e:
        print(f"\n--- TEST FAILED: {e} ---")

if __name__ == "__main__":
    test_retry_logic()
