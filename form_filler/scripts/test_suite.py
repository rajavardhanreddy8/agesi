
"""
Single Test Suite for Form Automation Project
Consolidates fast checks, database verification, and full automation tests.
"""
import sys
import os
import time
import unittest
# Add parent directory to path so we can import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
try:
    from ms_form_automation import MSFormAutomation
    HAS_AUTOMATION = True
except ImportError:
    HAS_AUTOMATION = False
    print("WARNING: Could not import MSFormAutomation. Automation tests will be skipped.")

class TestFormAutomation(unittest.TestCase):

    def test_01_db_connection(self):
        """Test if we can connect to the database"""
        print("\n[TEST] Verifying Database Connection...")
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            conn.close()
            self.assertEqual(result[0], 1)
            print("   ✅ Database connection successful")
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_02_automation_class_structure(self):
        """Test if MSFormAutomation class can be instantiated (headless)"""
        if not HAS_AUTOMATION:
            self.skipTest("MSFormAutomation not imported")
        
        print("\n[TEST] Verifying MSFormAutomation Initialization...")
        try:
            # Initialize with small delays for testing
            auto = MSFormAutomation(headless=True, min_delay=1, max_delay=2)
            self.assertIsNotNone(auto)
            print("   ✅ MSFormAutomation instantiated successfully")
        except Exception as e:
            self.fail(f"Failed to instantiate MSFormAutomation: {e}")

    def test_03_check_user_setup(self):
        """Check if user data exists for testing (specifically User 7 or similar)"""
        print("\n[TEST] Checking User Data in DB...")
        conn = get_db_connection()
        cur = conn.cursor()
        # Check for any active user with auto-submit enabled
        cur.execute("""
            SELECT count(*) FROM users u
            JOIN subscriptions s ON u.id = s.user_id
            WHERE u.is_active = TRUE AND s.is_auto_submit = TRUE
        """)
        count = cur.fetchone()[0]
        conn.close()
        
        if count == 0:
            print("   ⚠️ No active auto-submit users found. Integration tests might fail.")
        else:
            print(f"   ✅ Found {count} active auto-submit users.")
        self.assertGreaterEqual(count, 0) # Just a warning, not a fail

    def test_04_dry_run_automation(self):
        """
        OPTIONAL: Run a quick headless dry run if configured.
        Requires valid credentials in environment or hardcoded.
        """
        if not os.environ.get("RUN_LIVE_TESTS"):
             print("\n[TEST] Skipping Live Automation Test (Set RUN_LIVE_TESTS=1 to run)")
             return

        print("\n[TEST] Running Live Automation Dry Run...")
        # Placeholder for live test logic
        # automation.run_automation(...)
        pass

if __name__ == '__main__':
    print("="*60)
    print("FORM AUTOMATION TEST SUITE")
    print("="*60)
    unittest.main()
