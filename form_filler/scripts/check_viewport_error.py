import os
import psycopg2
import psycopg2.extras
import json
from db import get_db_connection

try:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT status, error_details, message
        FROM submission_history 
        WHERE status = 'failed'
        ORDER BY submitted_at DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    
    with open('viewport_errors.json', 'w') as f:
        json.dump([dict(r) for r in rows], f, indent=2)
        
    print("Wrote to viewport_errors.json")
except Exception as e:
    print(f"Database error: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
