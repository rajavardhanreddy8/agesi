"""
Clean restart script:
1. Mark ALL today's pending/failed tasks as 'cancelled'
2. For each UNIQUE student (by email), create/update ONE clean pending task
   with full profile data from student_profiles
3. Restart is handled by the server
"""
import sys, json, uuid
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras
from datetime import datetime

conn = get_db_connection()

# Step 1: Cancel all today's non-completed tasks
cur = conn.cursor()
cur.execute("""
    UPDATE submission_history 
    SET status = 'cancelled', message = 'Cancelled for clean restart'
    WHERE submitted_at > CURRENT_DATE 
      AND status IN ('pending', 'failed', 'running', 'queued')
""")
cancelled = cur.rowcount
print(f"Cancelled {cancelled} stale tasks")
conn.commit()

# Step 2: Fetch TODAY's unique students to re-queue
# Get one entry per email with the latest leave dates
cur2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur2.execute("""
    SELECT DISTINCT ON (sh.user_id)
        sh.user_id, sh.leave_start_date, sh.leave_end_date, sh.form_url, sh.blob_name,
        sp.full_name, sp.roll_number, sp.school, sp.academic_year,
        sp.programme, sp.specialization, sp.student_phone, sp.student_email,
        sp.parent1_name, sp.parent1_email, sp.parent1_phone,
        sp.default_reason, sp.send_parent_email,
        u.email, u.outlook_password_encrypted
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN student_profiles sp ON sp.user_id = u.id
    WHERE sh.submitted_at > CURRENT_DATE
    ORDER BY sh.user_id, sh.submitted_at DESC
""")
unique_students = cur2.fetchall()
print(f"\nFound {len(unique_students)} unique students to re-queue")

# Step 3: Insert one fresh task per unique student
cur3 = conn.cursor()
inserted = 0
skipped = 0
for r in unique_students:
    if not r.get('full_name'):
        print(f"  SKIP {r['email']}: No student_profiles entry found")
        skipped += 1
        continue

    # Format dates
    def fmt(d):
        if not d: return None
        if hasattr(d, 'strftime'): return d.strftime("%Y-%m-%d")
        return str(d)[:10]

    s_date = fmt(r['leave_start_date']) or "2026-03-06"
    e_date = fmt(r['leave_end_date']) or "2026-03-08"

    form_data = {
        "student_name": r['full_name'],
        "roll_number": r['roll_number'],
        "school": r.get('school', ''),
        "academic_session": r.get('academic_year', ''),
        "programme": r.get('programme', ''),
        "specialization": r.get('specialization', ''),
        "student_phone": r.get('student_phone', ''),
        "student_email": r.get('student_email', ''),
        "parent_name": r.get('parent1_name', ''),
        "parent_email": r.get('parent1_email', ''),
        "parent_phone": r.get('parent1_phone', ''),
        "reason": r.get('default_reason') or 'Going home for personal work',
        "leave_start_date": s_date,
        "leave_end_date": e_date,
        "send_parent_email": r.get('send_parent_email', False)
    }

    task_id = f"restart_{r['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    form_url = r.get('form_url') or "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X62J9sRC8oxAu69or0JA3nxUNzUxN0ZFUUZIR0hLMU9XR1RaMVVHUkpQWS4u"

    cur3.execute("""
        INSERT INTO submission_history 
            (user_id, form_url, task_id, leave_start_date, leave_end_date, status, form_data, submitted_at)
        VALUES (%s, %s, %s, %s, %s, 'pending', %s, NOW())
    """, (r['user_id'], form_url, task_id, s_date, e_date, json.dumps(form_data)))
    inserted += 1
    print(f"  Queued: {r['full_name']} ({r['roll_number']}) | {s_date} to {e_date}")

conn.commit()
conn.close()
print(f"\nDone! Inserted {inserted} clean tasks, skipped {skipped}")
print("Now start the server and call /api/admin/reload-pending")
