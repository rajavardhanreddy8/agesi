
import requests
import json
import sys

# URL = "http://localhost:5000/api/auth/register" # Local
URL = "https://outing-backend-api.azurewebsites.net/api/auth/register" # Live Azure

def test_live_registration():
    email = "guntaka.reddy_2028@woxsen.edu.in"
    password = "K@nni:18"
    
    print(f"Testing Registration on: {URL}", flush=True)
    print(f"User: {email}", flush=True)

    payload = {
        "email": email,
        "password": password,
        "outlook_password": password, # Assuming same for now
        "full_name": "Guntaka Reddy",
        "roll_number": "WU-2028-2029", # Dummy to satisfy constraint if any
        "school": "School of Technology",
        "academic_year": "2024-2028",
        "programme": "B.Tech", 
        "specialization": "CSE",
        "student_phone": "9988776655", # Dummy
        "parent1_name": "Parent Guntaka",
        "parent1_email": "parent.g@test.com",
        "parent1_phone": "9988776655"
    }

    try:
        print("Sending request...", flush=True)
        response = requests.post(URL, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}", flush=True)
        print(f"Response Text: {response.text}", flush=True)

    except Exception as e:
        print(f"Request Failed: {e}", flush=True)

if __name__ == "__main__":
    test_live_registration()
