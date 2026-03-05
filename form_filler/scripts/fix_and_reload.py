import sys, json, time
import urllib.request
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras
from datetime import datetime, timedelta

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Fetch all failed or pending tasks from today, with full student profile
cur.execute("""
    SELECT sh.task_id, sh.leave_start_date, sh.leave_end_date,
           sp.full_name, sp.roll_number, sp.school, sp.academic_year,
           sp.programme, sp.specialization, sp.student_phone, sp.student_email,
           sp.parent1_name, sp.parent1_email, sp.parent1_phone,
           sp.default_reason, sp.send_parent_email,
           u.outlook_password_encrypted
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN student_profiles sp ON sp.user_id = u.id
    WHERE sh.submitted_at > CURRENT_DATE 
      AND sh.status IN ('failed', 'pending')
""")
rows = cur.fetchall()

print(f"Fixing {len(rows)} tasks with real student_profiles data...")

count = 0
for r in rows:
    # Check if we have a profile
    if not r.get('full_name'):
        print(f"  SKIPPING task {r['task_id']}: no student_profiles entry found")
        continue

    start_date = r.get('leave_start_date')
    end_date = r.get('leave_end_date')

    def fmt_date(d):
        if not d: return None
        if hasattr(d, 'strftime'): return d.strftime("%Y-%m-%d")
        return str(d)[:10]

    s_date_str = fmt_date(start_date) or "2026-03-06"
    e_date_str = fmt_date(end_date) or "2026-03-08"

    # Build form_data from actual student_profiles
    form_data = {
        "student_name": r.get('full_name', ''),
        "roll_number": r.get('roll_number', ''),
        "school": r.get('school', ''),
        "academic_session": r.get('academic_year', ''),
        "programme": r.get('programme', ''),
        "specialization": r.get('specialization', ''),
        "student_phone": r.get('student_phone', ''),
        "student_email": r.get('student_email', ''),
        "parent_name": r.get('parent1_name', ''),
        "parent_email": r.get('parent1_email', ''),
        "parent_phone": r.get('parent1_phone', ''),
        "reason": r.get('default_reason', 'Going home for personal work'),
        "leave_start_date": s_date_str,
        "leave_end_date": e_date_str,
        "send_parent_email": r.get('send_parent_email', False)
    }

    cur2 = conn.cursor()
    cur2.execute(
        "UPDATE submission_history SET status='pending', form_data = %s WHERE task_id = %s",
        (json.dumps(form_data), r['task_id'])
    )
    print(f"  Fixed task {r['task_id']}: {r.get('full_name')} / {r.get('roll_number')} | {s_date_str} to {e_date_str}")
    count += 1

conn.commit()
conn.close()
print(f"\nFixed {count} tasks. Now triggering reload...")

# Trigger reload API
req = urllib.request.Request("http://localhost:5000/api/admin/reload-pending", method="POST")
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        print("Reload API response:", response.read().decode())
except Exception as e:
    print("API Error:", e)
