import os
import sys
import uuid
import requests
from dotenv import load_dotenv

load_dotenv('.env')

# We'll use the API for login and submission
BASE_URL = 'http://127.0.0.1:5000/api'

def run_test():
    # 1. Register User directly using API to test full E2E flow
    uid = str(uuid.uuid4())[:8]
    test_email = f"limit_test_{uid}@example.com"
    data = {
        'email': test_email,
        'password': 'password123',
        'outlook_password': 'outlook_password123',
        'full_name': 'Test User Trial',
        'roll_number': f'12345{uid}',
        'school': 'SOET',
        'academic_year': '1st Year',
        'programme': 'B.Tech',
        'specialization': 'CSE',
        'student_phone': '9999999999',
        'parent1_name': 'Parent Test',
        'parent1_email': 'parent@example.com',
        'parent1_phone': '8888888888'
    }

    print(f"[*] Registering user {test_email}...")
    # NOTE: The python register_user function sets the user up. We can just use requests against /auth/register
    resp = requests.post(f"{BASE_URL}/auth/register", json=data)
    print("Registration HTTP Status:", resp.status_code)
    
    # 2. Login to get token
    print("\n[*] Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={'email': test_email, 'password': 'password123'})
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return
        
    token = resp.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    print("Got access token!")

    # 3. Submit a form for the first time
    print("\n[*] Submitting first form...")
    form_data = {
        'form_url': 'https://forms.office.com/Pages/ResponsePage.aspx?id=example',
        'leave_start_date': '2026-03-05',
        'leave_end_date': '2026-03-07',
        'reason': 'Going home for the weekend'
    }
    resp1 = requests.post(f"{BASE_URL}/submit-form", json=form_data, headers=headers)
    print(f"Submit 1 Status: {resp1.status_code}")
    print(f"Submit 1 Response: {resp1.json()}")
    
    if not resp1.json().get('success'):
        print("[!] Failed on first submission. Is the setup right?")
        return

    # 4. Try submitting a second time immediately
    print("\n[*] Submitting second form (spamming)...")
    resp2 = requests.post(f"{BASE_URL}/submit-form", json=form_data, headers=headers)
    print(f"Submit 2 Status: {resp2.status_code}")
    print(f"Submit 2 Response: {resp2.json()}")
    
    if resp2.status_code == 403:
        print("\n[SUCCESS] Server successfully blocked the second submission as expected!")
    else:
        print("\n[FAIL] Server allowed the second submission!")


if __name__ == "__main__":
    run_test()
