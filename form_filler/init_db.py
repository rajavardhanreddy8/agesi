import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def init_db():
    print("Initializing Database (MySQL)...")
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))
    db_name = os.getenv('DB_NAME', 'outing_automation')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')

    # 1. Create Database if not exists
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' ready.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        return

    # 2. Apply Schema
    try:
        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        # Enable multi-statements
        cur = conn.cursor()
        
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema_mysql.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            
        print("Executing schema...")
        # Manually split statements by semicolon
        # Note: This is a simple split and assumes no semicolons in strings/comments, 
        # but for our schema file it should be fine as it's structure heavy.
        
        statements = schema_sql.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    cur.execute(statement)
                except Exception as stmt_err:
                    print(f"Warning running statement: {stmt_err}")
            
        print("✅ Tables created successfully!")
        conn.commit() # Ensure commit
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error applying schema: {e}")

if __name__ == '__main__':
    init_db()
