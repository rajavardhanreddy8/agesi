import json
import logging
from ms_form_automation import MSFormAutomation

logging.basicConfig(level=logging.INFO)

dummy_data = {
    'student_name': 'Test User',
    'roll_number': '2024XYZ123',
    'school': 'School of Technology',
    'programme': 'B.Tech',
    'academic_session': '2024-2028',
    'parent_name': 'Test Parent',
    'parent_email': 'parent@example.com',
    'parent_phone': '9876543210',
    'student_email': 'test.user_2024@woxsen.edu.in',
    'student_phone': '9876543211',
    'leave_start_date': '03/10/2026',
    'leave_end_date': '03/12/2026',
    'reason': 'Testing the bot'
}

def cb(msg, pct, _):
    print(f"[{pct}%] {msg}")

auto = MSFormAutomation(headless=True)
success = auto.run_automation(
    form_url="https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X62J9sRC8oxAu69or0JA3nxUNzUxN0ZFUUZIR0hLMU9XR1RaMVVHUkpQWS4u",
    email="test.user_2024@woxsen.edu.in", 
    password="DummyPassword123#",
    form_data=dummy_data,
    pdf_path="dummy.pdf",
    status_callback=cb
)
print(f"Success: {success}")
