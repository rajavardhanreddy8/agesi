import os
import glob
from db import get_db_connection

# Check columns
try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM submission_history LIMIT 0")
    columns = [desc[0] for desc in cur.description]
    print("Columns in submission_history:")
    for col in columns:
        print(f"- {col}")
    conn.close()
except Exception as e:
    print(f"Error checking columns: {e}")

# Cleanup session files
files = glob.glob("browser_state_*.json")
for f in files:
    try:
        os.remove(f)
        print(f"Removed {f}")
    except Exception as e:
        print(f"Error removing {f}: {e}")
