import sys, json, uuid
from datetime import datetime
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras
import urllib.request

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get all students with profiles
cur.execute("""
    SELECT u.id as user_id, u.email, sp.full_name, sp.roll_number, sp.school, 
           sp.academic_year, sp.programme, sp.specialization, sp.student_phone, 
           sp.student_email, sp.parent1_name, sp.parent1_email, sp.parent1_phone, 
           sp.default_reason, sp.send_parent_email
    FROM users u
    JOIN student_profiles sp ON u.id = sp.user_id
""")
all_users = cur.fetchall()

# Get users who already have submissions today (completed, pending, or running)
cur.execute("""
    SELECT DISTINCT user_id 
    FROM submission_history 
    WHERE submitted_at > CURRENT_DATE 
      AND status IN ('pending', 'running', 'completed')
""")
already_queued_user_ids = {r['user_id'] for r in cur.fetchall()}

print(f"Total students found: {len(all_users)}")
print(f"Students already queued/processed today: {len(already_queued_user_ids)}")

cur_insert = conn.cursor()
inserted = 0

s_date = "2026-03-06"
e_date = "2026-03-08"
form_url = "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X62J9sRC8oxAu69or0JA3nxUNzUxN0ZFUUZIR0hLMU9XR1RaMVVHUkpQWS4u"

for user in all_users:
    if user['user_id'] in already_queued_user_ids:
        continue
        
    form_data = {
        "student_name": user['full_name'],
        "roll_number": user['roll_number'],
        "school": user.get('school', ''),
        "academic_session": user.get('academic_year', ''),
        "programme": user.get('programme', ''),
        "specialization": user.get('specialization', ''),
        "student_phone": user.get('student_phone', ''),
        "student_email": user.get('student_email', ''),
        "parent_name": user.get('parent1_name', ''),
        "parent_email": user.get('parent1_email', ''),
        "parent_phone": user.get('parent1_phone', ''),
        "reason": user.get('default_reason') or 'Going home for personal work',
        "leave_start_date": s_date,
        "leave_end_date": e_date,
        "send_parent_email": user.get('send_parent_email', False)
    }

    task_id = f"batch_{user['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    cur_insert.execute("""
        INSERT INTO submission_history 
            (user_id, form_url, task_id, leave_start_date, leave_end_date, status, form_data, submitted_at)
        VALUES (%s, %s, %s, %s, %s, 'pending', %s, NOW())
    """, (user['user_id'], form_url, task_id, s_date, e_date, json.dumps(form_data)))
    
    inserted += 1
    print(f"Queueing: {user['full_name']} ({user['roll_number']})")

conn.commit()
conn.close()

print(f"\\nSuccessfully queued {inserted} new tasks.")

if inserted > 0:
    print("Triggering reload HTTP endpoint...")
    req = urllib.request.Request("http://localhost:5000/api/admin/reload-pending", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print("Reload API response:", response.read().decode())
    except Exception as e:
        print("API Error:", e)
