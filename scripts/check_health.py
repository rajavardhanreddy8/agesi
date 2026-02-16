import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://outing-backend-api.azurewebsites.net"

def check_system_health():
    print(f"Checking system health at {BASE_URL}...")
    try:
        # 1. Check Health Endpoint
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print("✅ System Health: CLOUD ONLINE")
            print(f"   Database: {data.get('database')}")
            print(f"   Queue Size: {data.get('queue_size')}")
            print(f"   Timestamp: {data.get('timestamp')}")
        else:
            print(f"❌ System Health Check Failed: {resp.status_code}")
            print(resp.text)

        # 2. Check a sample task status (if you have one)
        # print("\nChecking specific task status...")
        # task_resp = requests.get(f"{BASE_URL}/api/task-status/TASK_ID")
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    check_system_health()
