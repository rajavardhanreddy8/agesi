import sys
import os

sys.path.append(r'C:\Users\admin\Documents\outing\agent 4.0')
os.environ['DATABASE_URL'] = 'postgresql://postgres:QStaR3Ac39V8SDuf@db.uehkqlamchtdzcusqmhi.supabase.co:5432/postgres'

try:
    from form_filler.auth_system_v2 import register_user
    
    users_to_add = [
        {
            'email': 'adithya.test@example.com',
            'password': 'Password123!',
            'outlook_password': 'DummyOutlookPwd123',
            'full_name': 'Test Adithya (Adivers)',
            'roll_number': 'TEST-AD-001',
            'school': 'School of Technology',
            'academic_year': '1st Year',
            'programme': 'B.Tech',
            'specialization': 'CSE',
            'student_phone': '9999999991',
            'student_email': 'adithya.test@example.com',
            'parent1_name': 'Dummy Parent 1',
            'parent1_email': 'parent1@example.com',
            'parent1_phone': '9999999992',
            'parent1_relation': 'Father',
            'signature_data': None
        },
        {
            'email': 'chinnu.test@example.com',
            'password': 'Password123!',
            'outlook_password': 'DummyOutlookPwd123',
            'full_name': 'Test Chinnu (Adivers)',
            'roll_number': 'TEST-CH-002',
            'school': 'School of Technology',
            'academic_year': '1st Year',
            'programme': 'B.Tech',
            'specialization': 'CSE',
            'student_phone': '8888888881',
            'student_email': 'chinnu.test@example.com',
            'parent1_name': 'Dummy Parent 2',
            'parent1_email': 'parent2@example.com',
            'parent1_phone': '8888888882',
            'parent1_relation': 'Mother',
            'signature_data': None
        }
    ]

    for data in users_to_add:
        print(f"Creating user: {data['email']} - {data['full_name']}...")
        result = register_user(data)
        if result.get('success'):
            print(f"SUCCESS! User ID spawned: {result.get('user_id')}")
        else:
            print(f"FAILED: {result.get('error')}")

except Exception as e:
    print(f"Script Error: {e}")
