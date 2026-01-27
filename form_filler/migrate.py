import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def migrate():
    print("Migrating Database...")
    
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        database=os.getenv('DB_NAME', 'outing_automation'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', '')
    )
    cur = conn.cursor()

    # 1. Add is_admin to users if not exists
    try:
        cur.execute("SELECT is_admin FROM users LIMIT 1")
    except mysql.connector.Error:
        print("Adding is_admin column to users...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN is_admin TINYINT(1) DEFAULT 0")
        except Exception as e:
            print(f"Error adding column: {e}")

    # 2. Create payments table
    print("Creating payments table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            CONSTRAINT fk_pay_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            
            plan_type VARCHAR(50) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'INR',
            
            payment_gateway VARCHAR(50) DEFAULT 'razorpay',
            payment_order_id VARCHAR(255),
            payment_id VARCHAR(255),
            
            status VARCHAR(20) DEFAULT 'pending',
            
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Add Indexes
    try:
        cur.execute("CREATE INDEX idx_payments_user_id ON payments(user_id)")
        cur.execute("CREATE INDEX idx_payments_status ON payments(status)")
    except:
        pass # Indexes might exist

    # 4. Update views (re-run schema file views section or just copy paste)
    # The schema file views were updated, so we can re-create them.
    # We'll just read the schema file and run the View creation parts? 
    # Or just simpler to run the specific view updates here.
    
    print("Updating views...")
    try:
        cur.execute("""
            CREATE OR REPLACE VIEW v_user_profiles AS
            SELECT 
                u.id as user_id, u.email, u.is_verified, u.is_active, u.is_admin, u.last_login,
                sp.full_name, sp.roll_number, sp.school, sp.academic_year, sp.programme, sp.specialization,
                sp.student_phone, sp.parent1_name, sp.parent1_email, sp.parent1_phone,
                sp.parent2_name, sp.parent2_email, sp.parent2_phone,
                s.plan_type, s.is_auto_submit, s.monthly_submissions_limit, s.submissions_used
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN subscriptions s ON u.id = s.user_id
        """)
    except Exception as e:
        print(f"Error updating views: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Migration complete!")

if __name__ == '__main__':
    migrate()
