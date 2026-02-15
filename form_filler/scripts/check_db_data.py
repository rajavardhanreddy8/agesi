
import os
import psycopg2
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', 5432)

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        sslmode='require'
    )
    cur = conn.cursor()

    print("--- User Profiles (Signature Data) ---", flush=True)
    cur.execute("SELECT id, full_name, signature_data FROM student_profiles")
    profiles = cur.fetchall()
    for p in profiles:
        sig_val = p[2]
        if sig_val and len(sig_val) > 50:
             sig_preview = sig_val[:50] + "..."
        else:
             sig_preview = sig_val
        print(f"ID: {p[0]}, Name: {p[1]}, Signature: {sig_preview}", flush=True)
        
        # Check if file exists if it's a path
        if sig_val and not sig_val.startswith('data:image'):
            # It's a path
            full_path = os.path.abspath(sig_val)
            print(f"  -> Path check: {full_path} - Exists? {os.path.exists(full_path)}", flush=True)


    print("\n--- Latest Submission History ---", flush=True)
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'submission_history'")
    columns = [col[0] for col in cur.fetchall()]
    print(f"Columns: {columns}", flush=True)

    # We saw created_at in previous output (it was cut off but seemed to be there in the schema list hidden by the 'Error' message which was weird)
    # Let's just try to select everything and print dictionary
    cur.execute("SELECT * FROM submission_history ORDER BY id DESC LIMIT 5")
    submissions = cur.fetchall()
    
    for s in submissions:
        # Create a dictionary for better readability
        # Zip only if lengths match
        if len(s) == len(columns):
             s_dict = dict(zip(columns, s))
             print(f"Submission: {s_dict}", flush=True)
        else:
             print(f"Submission (Raw): {s}", flush=True)

    conn.close()

except Exception as e:
    print(f"Error: {e}", flush=True)
