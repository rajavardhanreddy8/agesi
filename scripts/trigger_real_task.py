import requests
import json
import time

def trigger():
    url = "https://outing-backend-api.azurewebsites.net/api/submit-form"
    
    # Use real user ID 7 (guntaka.reddy_2028@woxsen.edu.in)
    payload = {
        "user_id": 7,
        "form_url": "https://forms.office.com/r/sXXXCpkSWY", 
        "email": "guntaka.reddy_2028@woxsen.edu.in",
        "leave_start_date": "2026-02-20",
        "leave_end_date": "2026-02-21",
        "reason": "Testing fixed queue",
        "pdf_path": "https://sample-pdf.com/sample.pdf"
    }
    
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3LCJlbWFpbCI6Imd1bnRha2EucmVkZHlfMjAyOEB3b3hzZW4uZWR1LmluIiwiZXhwIjoxNzcxNzU3NzI5fQ.7G1Hgqpa51925O8767pvPD4USL3J3ct8g6mq8j1-Mi8'}
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
        print(f"Response: {response.status_code}")
        print(response.json())
        
        task_id = response.json().get('task_id')
        if task_id:
            print(f"Polling status for {task_id}...")
            for _ in range(5):
                time.sleep(10)
                status_url = f"https://outing-backend-api.azurewebsites.net/api/task-status/{task_id}"
                r = requests.get(status_url)
                print(f"Status: {r.json()}")
                if r.json().get('status') == 'running':
                    print("SUCCESS: Worker picked up the task!")
                    break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    trigger()
