import time
import requests
import json
import sys

def poll():
    health_url = "https://outing-backend-api.azurewebsites.net/health"
    log_url = "https://outing-backend-api.azurewebsites.net/api/admin/worker-log"
    diagnose_url = "https://outing-backend-api.azurewebsites.net/api/admin/diagnose"
    
    print("Starting poll...")
    for i in range(30): # 30 attempts, 10s delay = 5 mins
        try:
            r = requests.get(health_url, timeout=10)
            if r.status_code == 200:
                print(f"Health check OK: {r.status_code}")
                # Check for worker-log endpoint
                r_log = requests.get(log_url, timeout=10)
                if r_log.status_code == 200 or (r_log.status_code == 404 and 'Log file not found' in r_log.text):
                     print("Worker Log endpoint is ACTIVE!")
                     return True
                else:
                     print(f"Worker Log endpoint status: {r_log.status_code}")
            else:
                print(f"Health check status: {r.status_code}")
        except Exception as e:
            print(f"Request failed: {e}")
            
        time.sleep(10)
    return False

if __name__ == "__main__":
    if poll():
        sys.exit(0)
    else:
        sys.exit(1)
