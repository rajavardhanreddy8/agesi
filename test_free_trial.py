import os
import sys
import uuid
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv('.env')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'form_filler'))

from form_filler.auth_system_v2 import register_user, supabase

def test_trial():
    # Generate unique test data
    uid = str(uuid.uuid4())[:8]
    test_email = f"test_{uid}@example.com"
    data = {
        'email': test_email,
        'password': 'password123',
        'outlook_password': 'outlook_password123',
        'full_name': 'Test User Trial',
        'roll_number': f'12345{uid}',
        'school': 'SOET',
        'academic_year': '1st Year',
        'programme': 'B.Tech',
        'specialization': 'CSE',
        'student_phone': '9999999999',
        'parent1_name': 'Parent Test',
        'parent1_email': 'parent@example.com',
        'parent1_phone': '8888888888'
    }

    print(f"Testing registration for {test_email}...")
    res = register_user(data)
    print("Registration Result:", res)
    
    if not res.get('success'):
        print("Registration failed!")
        return

    # Check DB using Supabase
    try:
        user_id = res['user_id']
        sub_res = supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
        
        if sub_res.data:
            sub = sub_res.data[0]
            print("\nSubscription details:")
            print(f"Plan Type: {sub['plan_type']}")
            print(f"Monthly Limit: {sub['monthly_submissions_limit']}")
            print(f"Start: {sub['subscription_start']}")
            print(f"End: {sub['subscription_end']}")
            
            if sub['plan_type'] == 'basic' and sub['monthly_submissions_limit'] == 1:
                print("\nSUCCESS: User correctly received 1-week free trial with 1 submission.")
            else:
                print("\nFAILED: User did not receive correct free trial.")
        else:
            print("\nFAILED: No subscription found.")
            
    except Exception as e:
        print(f"DB Check Error: {e}")

if __name__ == "__main__":
    test_trial()
