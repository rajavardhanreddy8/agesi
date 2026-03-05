import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT u.email, sp.full_name, sp.roll_number, sp.school, sp.programme, 
           sp.academic_year, sp.student_phone, sp.student_email,
           sp.parent1_name, sp.parent1_phone, sp.parent1_email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN student_profiles sp ON sp.user_id = u.id
    WHERE sh.submitted_at > CURRENT_DATE 
      AND sh.status IN ('failed', 'pending')
    GROUP BY u.email, sp.full_name, sp.roll_number, sp.school, sp.programme, 
             sp.academic_year, sp.student_phone, sp.student_email,
             sp.parent1_name, sp.parent1_phone, sp.parent1_email
""")
rows = cur.fetchall()
conn.close()

with open('profile_status.json', 'w') as f:
    json.dump([dict(r) for r in rows], f, indent=2, default=str)
print("Done, saved to profile_status.json")
