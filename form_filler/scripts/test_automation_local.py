"""
Local test script to run automation with full logging
This helps debug field detection issues
"""

import sys
import os
from ms_form_automation import MSFormAutomation
from datetime import datetime, timedelta

# Test data
FORM_URL = "https://forms.office.com/r/sXXXCpkSWY"  # Replace with actual URL
EMAIL = "guntaka.reddy_2028@woxsen.edu.in"
PASSWORD = "K@nni:18"

# Sample form data (using User 7's profile)
form_data = {
    'student_name': 'GUNTAKA. RAJAVARDHAN REDDY',
    'roll_number': '24WU0101111',
    'school': 'School of Technology',
    'academic_session': '2024-2028',
    'programme': 'B.Tech',
    'specialization': 'CSE',
    'student_phone': '8639929405',
    'student_email': 'rajavardhanerddy@gmail.com',
    'parent_name': 'Raghunadha reddy',
    'parent_phone': '8919455860',
    'parent_email': 'rrtradersind@gmail.com',
    'parent2_name': 'Pranitha',
    'parent2_phone': '9010787739',
    'reason': 'Weekend outing with family',
    'leave_start_date': (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y'),
    'leave_end_date': (datetime.now() + timedelta(days=2)).strftime('%d/%m/%Y')
}

# Dummy PDF path (you can create a test PDF or skip upload)
PDF_PATH = None  # Set to actual path if testing upload

print("=" * 60)
print("LOCAL AUTOMATION TEST")
print("=" * 60)
print(f"Form URL: {FORM_URL}")
print(f"Email: {EMAIL}")
print(f"Form Data:")
for k, v in form_data.items():
    print(f"  {k}: {v}")
print("=" * 60)

# Run automation
automation = MSFormAutomation(headless=False)  # Set to False to see browser

try:
    # Navigate and login
    automation.navigate_to_form(FORM_URL)
    automation.microsoft_login(EMAIL, PASSWORD)
    
    # Fill form
    print("\n=== FILLING FORM ===")
    automation.fill_form(form_data)
    
    # Upload PDF if provided
    if PDF_PATH and os.path.exists(PDF_PATH):
        print("\n=== UPLOADING PDF ===")
        automation.upload_pdf(PDF_PATH)
    
    # Submit (this will show pre-submit validation)
    print("\n=== SUBMITTING FORM ===")
    success = automation.submit_form()
    
    if success:
        print("\n✅ AUTOMATION SUCCESS!")
    else:
        print("\n❌ AUTOMATION FAILED")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Keep browser open for inspection
    input("\nPress Enter to close browser...")
    automation.close()
