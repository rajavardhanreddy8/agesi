import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from dotenv import load_dotenv

load_dotenv('.env')

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', '5432')
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT sh.task_id, sh.status, sh.submitted_at, sh.completed_at, u.email 
        FROM submission_history sh 
        JOIN users u ON sh.user_id = u.id 
        WHERE u.email = 'guntaka.reddy_2028@woxsen.edu.in' 
        ORDER BY sh.submitted_at DESC LIMIT 5
    """)
    records = cur.fetchall()

    for r in records:
        print(f"Task ID: {r['task_id']}")
        print(f"Status: {r['status']}")
        print(f"Created: {r['submitted_at']}")
        print(f"Last Update: {r.get('completed_at') or 'N/A'}")
        print("-------------------")
        
except Exception as e:
    print(f"Error checking database: {e}")
