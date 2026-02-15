"""Query User 7 student profile"""
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

cur.execute("SELECT * FROM student_profiles WHERE user_id = 7")
row = cur.fetchone()

if row:
    cols = [desc[0] for desc in cur.description]
    print("=== USER 7 STUDENT PROFILE ===")
    nulls = []
    for i, col in enumerate(cols):
        val = row[i]
        print(f"{col}: {val}")
        if val is None or val == '':
            nulls.append(col)
    
    if nulls:
        print(f"\n⚠️ NULL/EMPTY FIELDS: {nulls}")
    else:
        print("\n✅ All fields populated!")
else:
    print("❌ No student_profile found for user_id=7")

conn.close()
