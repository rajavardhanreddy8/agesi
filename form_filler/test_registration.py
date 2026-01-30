import requests
import json

# Test registration endpoint
url = "http://localhost:5000/api/register"
test_data = {
    "email": "test@woxsen.edu.in",
    "password": "testpass123",
    "outlook_password": "testpass123",
    "full_name": "Test User",
    "roll_number": "24WU0100001",
    "school": "School of Technology",
    "academic_year": "2024-2028",
    "programme": "B.Tech",
    "specialization": "CSE",
    "student_phone": "9999999999",
    "parent1_name": "Parent One",
    "parent1_email": "parent1@test.com",
    "parent1_phone": "8888888888"
}

print("Testing registration endpoint...")
try:
    response = requests.post(url, json=test_data, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to backend. Is it running on port 5000?")
except Exception as e:
    print(f"ERROR: {e}")
