import sys
import os

# Add form_filler to path
sys.path.append(os.path.join(os.getcwd(), 'form_filler'))

from form_filler.create_pdf import generate_parent_consent_pdf
from datetime import datetime

data = {
    "student_name": "Test Student",
    "student_id": "TEST-001",
    "programme": "B.Tech",
    "specialization": "CSE",
    "academic_year": "2024-25",
    "parent_name": "Test Parent",
    "parent_phone": "9999999999",
    "leave_date_text": "20-Feb-2026, 09:00 AM",
    "return_date_text": "22-Feb-2026, 06:00 PM",
    "reason": "Test Reason",
    "student_contact": "Test Student, test@example.com, 8888888888",
    "signature_path": "signatures/test_sig.png" # verify this exists or handle missing
}

output_path = "temp_uploads/test_consent_form.pdf"
os.makedirs("temp_uploads", exist_ok=True)

try:
    generate_parent_consent_pdf(output_path, data)
    print(f"SUCCESS: PDF generated at {output_path}")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
