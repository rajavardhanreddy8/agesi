"""Quick test to see what error occurs"""
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
    'programme': 'B.B.A',
    'specialization': 'CSE',
    'academic_session': '2024-2028',
    'parent_name': 'Raghunadha reddy'
}

print("Starting automation test...")
automation = MSFormAutomation(headless=True)

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
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

input("\nPress Enter to close...")
