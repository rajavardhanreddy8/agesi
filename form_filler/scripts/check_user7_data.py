"""
Query User 7's profile to check for NULL/empty fields
"""

from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Get User 7's full profile
cur.execute("""
    SELECT 
        u.id, u.full_name, u.roll_number, u.school, u.academic_year,
        u.programme, u.specialization,
        u.student_phone, u.student_email, u.email,
        u.parent1_name, u.parent1_phone, u.parent1_email,
        u.parent2_name, u.parent2_phone
    FROM users u
    WHERE u.id = 7
""")

user = cur.fetchone()

if user:
    print("=== USER 7 PROFILE ===")
    print(f"ID: {user[0]}")
    print(f"Name: {user[1]}")
    print(f"Roll: {user[2]}")
    print(f"School: {user[3]}")
    print(f"Academic Year: {user[4]}")
    print(f"Programme: {user[5]}")
    print(f"Specialization: {user[6]}")
    print(f"Student Phone: {user[7]}")
    print(f"Student Email: {user[8]}")
    print(f"Fallback Email: {user[9]}")
    print(f"Parent1 Name: {user[10]}")
    print(f"Parent1 Phone: {user[11]}")
    print(f"Parent1 Email: {user[12]}")
    print(f"Parent2 Name: {user[13]}")
    print(f"Parent2 Phone: {user[14]}")
    
    # Check for NULLs
    print("\n=== NULL FIELDS ===")
    fields = ['id', 'full_name', 'roll_number', 'school', 'academic_year',
              'programme', 'specialization', 'student_phone', 'student_email', 'email',
              'parent1_name', 'parent1_phone', 'parent1_email', 'parent2_name', 'parent2_phone']
    for i, val in enumerate(user):
        if val is None or val == '':
            print(f"  - {fields[i]}: NULL/EMPTY")
else:
    print("User 7 not found!")

conn.close()
