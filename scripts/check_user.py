import os
import psycopg2
from dotenv import load_dotenv

def check():
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    cur = conn.cursor()
    
    cur.execute("SELECT id, email FROM users WHERE id = 7")
    row = cur.fetchone()
    print(f"User 7: {row}")
    
    cur.execute("SELECT id, email FROM users ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    print("Latest users:")
    for r in rows:
        print(r)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
