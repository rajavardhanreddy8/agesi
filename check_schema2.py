import sys
sys.path.insert(0, 'form_filler')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Check FK constraints on student_profiles
cur.execute("""
    SELECT tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
    WHERE tc.table_name = 'student_profiles' AND tc.constraint_type = 'FOREIGN KEY'
""")
fks = cur.fetchall()
if fks:
    print("student_profiles FKs:")
    for fk in fks:
        print(f"FK: {fk[1]} -> {fk[2]}.{fk[3]}  ({fk[0]})")
else:
    print("NO foreign keys on student_profiles!")

conn.close()
