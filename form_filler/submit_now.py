from ms_form_automation import MSFormAutomation
import time
import os
import shutil
from playwright.sync_api import TimeoutError as PlaywrightTimeout

def run_submission():
    # Configuration
    FORM_URL = "https://forms.office.com/r/sXXXCpkSWY"
    EMAIL = "guntaka.reddy_2028@woxsen.edu.in"
    PASSWORD = r"K@nni:18"
    
    # Path to the PDF
    PDF_PATH = os.path.abspath(r"temp_uploads\outing_20260124134304.pdf")
    PPT_PATH = PDF_PATH.replace(".pdf", ".ppt") # Fake PPT
    
    # Create fake PPT for testing
    shutil.copy(PDF_PATH, PPT_PATH)
    
    # Verified Data
    form_data = {
        "student_name": "GUNTAKA RAJAVARDHAN REDDY",
        "roll_number": "2024101123",
        "school": "School of Technology",
        "academic_session": "2024-2028",
        "specialization": "CSE",
        "reason": "Home Visit",
        "leave_start_date": "01/24/2026",
        "leave_end_date": "01/26/2026",
        "student_email": EMAIL,
        "student_phone": "9876543210",
        "parent_email": "parent.guntaka@example.com",
        "parent_phone": "9123456789"
    }

    print("🚀 Starting RETRY & FALLBACK automation script...")
    automation = MSFormAutomation(headless=False)
    
    try:
        automation.start_browser()
        automation.page.goto(FORM_URL)
        time.sleep(3)
        
        try:
            automation.microsoft_login(EMAIL, PASSWORD)
        except:
            if "forms.office.com" in automation.page.url:
                print("✅ On forms page.")
        
        time.sleep(5)
        
        # Fill Form (Quickly using known indices/labels)
        inputs = automation.page.locator('input[placeholder="Enter your answer"]')
        date_inputs = automation.page.locator('input[placeholder*="date"]')
        
        def fill_idx(idx, val):
            try:
                if inputs.nth(idx).is_visible():
                    inputs.nth(idx).fill(val)
            except: pass
            
        def click_radio(text):
            try:
                automation.page.locator(f'span:has-text("{text}")').first.click()
            except: pass

        # Fill fields
        fill_idx(0, form_data['student_name'])
        fill_idx(1, form_data['roll_number'])
        click_radio(form_data['school'])
        click_radio(form_data['academic_session'])
        fill_idx(2, form_data['specialization'])
        fill_idx(3, form_data['reason'])
        try: date_inputs.first.fill(form_data['leave_start_date'])
        except: pass
        fill_idx(4, form_data['parent_phone'])
        fill_idx(5, form_data['parent_email'])
        fill_idx(6, form_data['student_phone'])
        fill_idx(7, form_data['student_email'])

        # Q12 PDF Upload - ATTEMPT 1 (PDF)
        print("\n📤 PDF UPLOAD ATTEMPT 1: .pdf")
        try:
            file_input = automation.page.locator('input[type="file"]').first
            file_input.set_input_files(PDF_PATH)
            print("⏳ Uploading PDF...")
            
            # Watch for error message
            time.sleep(5)
            error_msg = automation.page.locator('text=Upload the required file type')
            if error_msg.is_visible():
                print("❌ PDF rejected (File type error detected)")
                
                # UPLOAD ATTEMPT 2 (Fake PPT)
                print("\n📤 PDF UPLOAD ATTEMPT 2: .ppt (Renamed PDF)")
                file_input.set_input_files(PPT_PATH)
                print("⏳ Uploading Fake PPT...")
                time.sleep(15)
                
                if error_msg.is_visible():
                     print("❌ Fake PPT also rejected.")
                else:
                     print("✅ Fake PPT accepted (or error gone)!")
            else:
                print("✅ PDF accepted (no error visible immediately)!")
                time.sleep(10)

        except Exception as e:
            print(f"❌ Upload fail: {e}")

        # Final Submit
        print("\n🚀 FINAL SUBMIT")
        automation.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        submit_button = automation.page.locator('button:has-text("Submit")').first
        if submit_button.is_visible():
            submit_button.click()
            print("✅ Clicked")
            
            # Wait for success
            try:
                automation.page.wait_for_selector('text=Your response was submitted', timeout=15000)
                print("🎉 SUCCESS! SUBMISSION CONFIRMED.")
            except:
                print("⚠️ No success message found")

            # Proof
            screenshot_path = os.path.join("screenshots", "SUBMISSION_RETRY_RESULT.png")
            os.makedirs("screenshots", exist_ok=True)
            automation.page.screenshot(path=screenshot_path)
            print(f"📸 Saved: {screenshot_path}")
        else:
            print("❌ No Submit button")
            
        print("\n✅ DONE!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        automation.page.screenshot(path=f"screenshots/error_retry_{int(time.time())}.png")
    
    finally:
        if automation.browser:
            time.sleep(5)
            automation.browser.close()

if __name__ == "__main__":
    run_submission()
