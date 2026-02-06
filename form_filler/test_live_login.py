
import requests
import json
import sys

URL = "https://outing-backend-api.azurewebsites.net/api/auth/login"

def test_live_login():
    email = "guntaka.reddy_2028@woxsen.edu.in"
    password = "K@nni:18"
    
    print(f"Testing Login on: {URL}", flush=True)
    print(f"User: {email}", flush=True)

    payload = {
        "email": email,
        "password": password
    }

    try:
        print("Sending request...", flush=True)
        response = requests.post(URL, json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}", flush=True)
        print(f"Response Text: {response.text}", flush=True)

    except Exception as e:
        print(f"Request Failed: {e}", flush=True)

if __name__ == "__main__":
    test_live_login()
