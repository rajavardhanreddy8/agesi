import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Get a user who is on 'basic' plan
def test_free_plan_downgrade():
    
    # 1. Register a test user directly via API
    register_url = 'http://127.0.0.1:5000/api/auth/register'
    test_email = 'free_downgrade_tester_2@college.edu.in'
    
    reg_data = {
        'email': test_email,
        'password': 'password123',
        'outlook_password': 'password123',
        'full_name': 'Free Tester',
        'phone': '1234567890',
        'school': 'SOET',
        'programme': 'B.Tech',
        'specialization': 'CSE',
        'father_name': 'Father',
        'father_email': 'father@test.com',
        'father_phone': '1234567890',
        'mother_name': 'Mother',
        'mother_email': 'mother@test.com',
        'mother_phone': '1234567890'
    }
    
    r = requests.post(register_url, json=reg_data)
    print("Register Response:", r.json())
    
    # login to get token
    login_url = 'http://127.0.0.1:5000/api/auth/login'
    login_data = {'email': test_email, 'password': 'password123'}
    r = requests.post(login_url, json=login_data)
    token = r.json().get('token')
    
    if not token:
        print("Login failed!")
        return
        
    # Upgrade to 'free' plan
    upgrade_url = 'http://127.0.0.1:5000/api/subscription/upgrade'
    headers = {'Authorization': f'Bearer {token}'}
    
    # Send upgrade request
    print("Testing upgrade to 'free'...")
    r = requests.post(upgrade_url, json={'plan_type': 'free'}, headers=headers)
    
    response_data = r.json()
    print("Upgrade Response:", response_data)
    
    if response_data.get('gateway') == 'free' and response_data.get('success'):
        print("SUCCESS! Endpoint properly bypassed Razorpay for amount 0.")
    else:
        print("FAILED! Did not bypass Razorpay.")
        
if __name__ == '__main__':
    test_free_plan_downgrade()
