
import requests
import json
import os

def trigger_submission():
    url = "http://localhost:5000/api/submit-form"
    
    # Payload matching the frontend structure
    automation_data = {
        "form_url": "https://forms.office.com/Pages/ResponsePage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u",
        "email": "guntaka.reddy_2028@woxsen.edu.in",
        "password": "K@nni:18",
        "form_data": {
            "student_name": "GUNTAKA RAJAVARDHAN REDDY",
            "roll_number": "2024101123",
            "school": "School of Technology",
            "academic_session": "2024-2028",
            "programme": "B.Tech",
            "specialization": "Computer Science (CSE)",
            "reason": "Home Visit",
            "leave_start_date": "1/23/2026",
            "leave_end_date": "1/25/2026",
            "student_email": "guntaka.reddy_2028@woxsen.edu.in",
            "student_phone": "9876543210",
            "parent_email": "parent.guntaka@example.com",
            "parent_phone": "9123456789"
        }
    }
    
    files = {
        'pdf': ('test_outing.pdf', open(os.path.join('temp_uploads', 'test_outing.pdf'), 'rb'), 'application/pdf')
    }
    
    data = {
        'data': json.dumps(automation_data)
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        
        if response.status_code == 202:
            task_id = response.json().get('task_id')
            print(f"Task started: {task_id}")
            return task_id
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    trigger_submission()
