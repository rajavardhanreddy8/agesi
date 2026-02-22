import requests
import json
import random
import string

BASE_URL = "https://outing-backend-api.azurewebsites.net"

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_test():
    email = f"test_{random_string()}@example.com"
    password = "TestPassword123!"
    
    print(f"Testing with user: {email}")

    # 1. Register
    reg_data = {
        "email": email,
        "password": password,
        "full_name": "Test User",
        "roll_number": f"WOX{random_string(4)}",
        "school": "Technology",
        "academic_year": "2024-2025",
        "programme": "B.Tech",
        "specialization": "CSE",
        "student_phone": "1234567890",
        "parent1_name": "Test Parent",
        "parent1_email": "parent@example.com",
        "parent1_phone": "0987654321",
        "outlook_password": "OutlookPass123!"
    }
    
    print("Registering...")
    # Using verify=False because sometimes SSL issues in limited environments, but should verify=True ideally
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/api/auth/register", json=reg_data)
    print(f"Register Status: {resp.status_code}")
    if resp.status_code != 201:
        print(f"Register Failed: {resp.text}")
        return

    # 2. Login
    print("Logging in...")
    resp = session.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        print(f"Login Failed: {resp.text}")
        return
        
    token = resp.json()['token']
    headers = {"Authorization": f"Bearer {token}"}
    print("Login Success. Token acquired.")

    # 3. Get Plans
    print("Fetching Plans...")
    resp = session.get(f"{BASE_URL}/api/subscription/plans")
    print(f"Plans Status: {resp.status_code}")
    print(f"Plans Data: {resp.text[:100]}...")

    # 4. Initiate Upgrade (Razorpay Order)
    print("Initiating Upgrade (Creating Razorpay Order)...")
    upgrade_data = {"plan_type": "basic"}
    resp = session.post(f"{BASE_URL}/api/subscription/upgrade", json=upgrade_data, headers=headers)
    
    print(f"Upgrade Status: {resp.status_code}")
    print(f"Upgrade Response: {resp.text}")
    
    if resp.status_code == 200 and 'order_id' in resp.json():
        print("SUCCESS: Payment Gateway Order Created!")
    else:
        print("FAILURE: Could not create order.")

if __name__ == "__main__":
    run_test()
