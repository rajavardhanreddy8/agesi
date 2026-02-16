import requests
import time
import json
import sys

BASE_URL = "https://outing-backend-api.azurewebsites.net"

def poll():
    print("Polling for debug info...")
    for i in range(24): # 4 mins
        try:
            r = requests.get(f"{BASE_URL}/api/admin/worker-log", timeout=10)
            if r.status_code == 200:
                data = r.json()
                if 'debug' in data:
                    print("Debug info found! Deployment SUCCESS.")
                    print(json.dumps(data['debug'], indent=2))
                    return True
                else:
                    print("Endpoint active but no debug info yet (old version).")
            else:
                 print(f"Status: {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(10)
    return False

if __name__ == "__main__":
    poll()
