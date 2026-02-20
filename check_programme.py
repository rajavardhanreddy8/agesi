import psycopg2

conn = psycopg2.connect(
    host='aws-1-ap-northeast-1.pooler.supabase.com',
    dbname='postgres',
    user='postgres.uehkqlamchtdzcusqmhi',
    password='trZaKdFk6MMCb8NY',
    port=5432
)
cur = conn.cursor()
cur.execute("""
    SELECT sp.programme, sp.full_name, u.email 
    FROM student_profiles sp 
    JOIN users u ON sp.user_id = u.id 
    WHERE u.email = 'guntaka.reddy_2028@woxsen.edu.in'
""")
rows = cur.fetchall()
print(f"Results: {rows}")

# Also check all users' programme values
cur.execute("""
    SELECT u.email, sp.programme, sp.full_name 
    FROM student_profiles sp 
    JOIN users u ON sp.user_id = u.id
""")
all_rows = cur.fetchall()
print(f"\nAll users programme values:")
for row in all_rows:
    print(f"  {row[0]}: programme='{row[1]}', name='{row[2]}'")

conn.close()
