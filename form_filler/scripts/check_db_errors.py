import os
import psycopg2
import psycopg2.extras
from db import get_db_connection

try:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT task_id, email, status, error_details, created_at, message
        FROM submission_history sh
        JOIN users u ON sh.user_id = u.id
        WHERE status = 'failed'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} recent failed submissions:")
    for row in rows:
        print(f"[{row['created_at']}] {row['email']} -> {row['status']}")
        print(f"Error: {row['error_details']}")
        print(f"Message: {row['message']}")
        print("-" * 50)
        
except Exception as e:
    print(f"Database error: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
