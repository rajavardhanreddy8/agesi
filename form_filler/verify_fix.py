
import requests
import uuid
import sys

URL = "https://outing-backend-api.azurewebsites.net/api/auth/register"

def verify_fix_registration():
    # Use a random email to bypass "User already exists" check
    random_id = uuid.uuid4().hex[:6]
    email = f"verify_fix_{random_id}@woxsen.edu.in"
    password = "TestPassword123!"
    
    print(f"Testing Registration with NEW user: {email}", flush=True)

    payload = {
        "email": email,
        "password": password,
        "outlook_password": password, 
        "full_name": "Verify Fix User",
        "roll_number": f"FIX-{random_id}",
        "school": "School of Technology",
        "academic_year": "2024-2028",
        "programme": "B.Tech", 
        "specialization": "CSE",
        "student_phone": "9988776655", 
        "parent1_name": "Parent Fix",
        "parent1_email": "parent.fix@test.com",
        "parent1_phone": "9988776655"
    }

    try:
        print("Sending request...", flush=True)
        response = requests.post(URL, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}", flush=True)
        print(f"Response Text: {response.text}", flush=True)
        
        if response.status_code in [200, 201]:
            print("SUCCESS: Registration went through!", flush=True)
        else:
            print("FAILURE: Validation still blocking or other error.", flush=True)

    except Exception as e:
        print(f"Request Failed: {e}", flush=True)

if __name__ == "__main__":
    verify_fix_registration()
