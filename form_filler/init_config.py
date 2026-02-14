from db import get_db_connection
import logging

def init_system_config():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create config table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Default values
        defaults = {
            'form_link': 'https://forms.office.com/r/sXXXCpkSWY',
            'start_date': '',
            'end_date': '',
            'default_reason': 'Home Visit'
        }
        
        for key, val in defaults.items():
            cur.execute("""
                INSERT INTO system_config (key, value) 
                VALUES (%s, %s) 
                ON CONFLICT (key) DO NOTHING
            """, (key, val))
            
        conn.commit()
        conn.close()
        print("System config table initialized successfully.")
    except Exception as e:
        print(f"Error initializing system config: {e}")

if __name__ == "__main__":
    init_system_config()
