
import os
import sys
import uuid
import logging

# Add parent dir to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from form_filler.auth_system_v2 import register_user

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_registration():
    unique_id = uuid.uuid4().hex[:8]
    email = f"debug_user_{unique_id}@woxsen.edu.in"
    print(f"Attempting to register user: {email}")

    test_data = {
        "email": email,
        "password": "Password123!",
        "outlook_password": "OutlookPassword123!",
        "full_name": "Debug User",
        "roll_number": f"DBG-{unique_id}",
        "school": "School of Technology",
        "academic_year": "2024-2028",
        "programme": "B.Tech",
        "specialization": "CSE",
        "student_phone": "1234567890",
        "parent1_name": "Debug Parent",
        "parent1_email": "parent@debug.com",
        "parent1_phone": "0987654321",
        "parent1_relation": "Father"
    }

    try:
        result = register_user(test_data)
        print("Registration Result:")
        print(result)
    except Exception as e:
        print(f"EXCEPTION during registration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registration()
