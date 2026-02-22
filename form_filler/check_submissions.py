import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Get column names
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'submission_history' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]

# Fetch latest rows 
cur.execute("SELECT * FROM submission_history ORDER BY id DESC LIMIT 5")
rows = cur.fetchall()

with open('submissions_dump.txt', 'w', encoding='utf-8') as f:
    f.write(f"Columns: {cols}\n\n")
    for r in rows:
        for c, v in zip(cols, r):
            f.write(f"  {c}: {v}\n")
        f.write("---\n")

print("Dumped to submissions_dump.txt")
conn.close()
