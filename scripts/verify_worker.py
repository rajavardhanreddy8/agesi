import requests
import time
import json
import sys

BASE_URL = "https://outing-backend-api.azurewebsites.net"

def check():
    print("Step 1: Trigger Recovery")
    try:
        r = requests.post(f"{BASE_URL}/api/admin/recover", timeout=10)
        print(f"Recovery response: {r.status_code} {r.text}")
        if r.status_code != 200:
            return False
    except Exception as e:
        print(f"Recovery trigger failed: {e}")
        return False
        
    print("Step 2: Monitor Queue & Diagnose")
    for i in range(12): # 2 mins max
        try:
            r = requests.get(f"{BASE_URL}/api/admin/diagnose", timeout=10)
            if r.status_code == 200:
                diag = r.json()
                print(f"Diagnose: {json.dumps(diag)}")
                
                # Check for errors
                if diag.get('last_error'):
                    print(f"FATAL: Worker reported error: {diag['last_error']}")
                    # Fetch detailed log
                    logs = requests.get(f"{BASE_URL}/api/admin/worker-log", timeout=10).json().get('log', [])
                    print("Worker Log Tail:")
                    print("".join(logs[-20:]))
                    return False
                
                # Check queue size
                if diag['queue_size'] == 0:
                     if diag['tasks_in_memory'] > 0:
                         print("Worker is processing (queue empty, tasks in memory)")
                     else:
                         print("Queue empty & memory empty? Check logs.")
                         # Fetch logs to see if it ran
                         logs = requests.get(f"{BASE_URL}/api/admin/worker-log", timeout=10).json().get('log', [])
                         print("Worker Log Tail:")
                         print("".join(logs[-20:]))
                         
                         return True # Maybe done?
            
            time.sleep(10)
        except Exception as e:
             print(f"Monitor failed: {e}")
             
    return True

if __name__ == "__main__":
    check()
