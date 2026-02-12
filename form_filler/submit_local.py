
from ms_form_automation import MSFormAutomation
import os

# CONFIGURATION
PDF_PATH = r"C:\Users\admin\Music\Outing Form - GUNTAKA. RAJAVARDHAN REDDY.pdf"
FORM_URL = "https://forms.office.com/r/sXXXCpkSWY"

# DUMMY DATA (Since the PDF is already filled, we just need to fill the form fields)
# You might want to update these values if they need to match the PDF
FORM_DATA = {
    "student_name": "GUNTAKA RAJAVARDHAN REDDY",
    "roll_number": "24110010",
    "school": "School of Technology",
    "academic_session": "2024-2028",
    "programme": "B.Tech",
    "specialization": "CSE",
    "reason": "Home Visit",
    "leave_start_date": "14-02-2025",  # DD-MM-YYYY format for MS Forms usually
    "leave_end_date": "16-02-2025"
}

def run_local_submission():
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found at: {PDF_PATH}")
        return

    print("🚀 Starting local submission...")
    print(f"📄 PDF: {PDF_PATH}")
    
    # Initialize automation (HEADED so you can see it)
    # We pass None for delays to use defaults, but we can make it faster
    automation = MSFormAutomation(headless=False, min_delay=2, max_delay=5)
    
    try:
        automation.start_browser()
        
        # 1. Login (should use saved state, or fall back to these creds)
        print("🔐 Logging in...")
        # Using the credentials you provided
        automation.microsoft_login("guntaka.reddy_2028@woxsen.edu.in", "k@nni:18")
        
        # 2. Fill Form
        print("📝 Filling form...")
        automation.fill_form(FORM_DATA)
        
        # 3. Upload PDF
        print("📤 Uploading PDF...")
        automation.upload_pdf(PDF_PATH)
        
        # 4. Submit
        print("🚀 Submitting...")
        automation.submit_form()
        
        print("\n✅ Local submission completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Submission failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Keep browser open for a bit to see result
        import time
        time.sleep(5)
        if automation.browser:
            automation.browser.close()

if __name__ == "__main__":
    run_local_submission()
