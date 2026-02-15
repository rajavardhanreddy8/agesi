
import sys
import os
import logging

try:
    from ms_form_automation import MSFormAutomation
except ImportError:
    # Add current dir to path
    sys.path.append(os.getcwd())
    from ms_form_automation import MSFormAutomation

# Use actual form URL
FORM_URL = "https://forms.office.com/r/sXXXCpkSWY"
EMAIL = "guntaka.reddy_2028@woxsen.edu.in"
PASSWORD = "K@nni:18"

# Use M/d/yyyy format (what MS Forms expects)
form_data = {
    'student_name': 'GUNTAKA. RAJAVARDHAN REDDY',
    'roll_number': '24WU0101111',
    'school': 'School of Technology',
    'leave_start_date': '2/14/2026',
    'leave_end_date': '2/15/2026',
    'parent_phone': '8919455860',
    'parent_email': 'rrtradersind@gmail.com',
    'student_phone': '8639929405',
    'student_email': 'rajavardhanerddy@gmail.com',
    'reason': 'home',
    # 'programme': 'B.B.A', # Not present in form
    'specialization': 'CSE',
    'academic_session': '2024-2028',
    'parent_name': 'Raghunadha reddy'
}

print("Starting automation reproduction test...")
# Verify log file creation
if os.path.exists("automation.log"):
    print(f"Log file exists, size: {os.path.getsize('automation.log')} bytes")
else:
    print("Log file will be created...")

automation = MSFormAutomation(headless=True) # HEADLESS to match production
# automation.page.set_default_timeout(60000) # Maybe verify if this is set?

try:
    success = automation.run_automation(
        form_url=FORM_URL,
        email=EMAIL,
        password=PASSWORD,
        form_data=form_data,
        pdf_path=r"c:\Users\admin\Documents\outing\agent 4.0\doc_handle\public\Consent Form.pdf"
    )
    
    if success:
        print("\n✅ AUTOMATION SUCCESS!")
    else:
        print("\n❌ AUTOMATION FAILED")
        
except Exception as e:
    print(f"\n❌ CAUGHT ERROR: {e}")
    import traceback
    traceback.print_exc()

print(f"Final log file size: {os.path.getsize('automation.log') if os.path.exists('automation.log') else 'Not Found'}")
