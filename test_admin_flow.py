import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'form_filler'))

from form_filler.api import app, get_db_connection

def run_admin_tests():
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Needs a real user to be an admin
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin = TRUE WHERE email = 'adithya.test@example.com'")
    conn.commit()
    conn.close()

    print("--- 1. Testing Admin Login ---")
    login_res = client.post('/api/auth/login', json={
        'email': 'adithya.test@example.com',
        'password': 'Password123!'
    })
    
    token = login_res.json.get('token')
    headers = {'Authorization': f'Bearer {token}'}

    print("--- 2. Testing /api/admin/update-form-settings ---")
    update_data = {
        'form_link': 'https://forms.office.com/test-admin-update',
        'start_date': '2026-10-10',
        'end_date': '2026-10-12',
        'default_reason': 'Test Reason Admin'
    }
    update_res = client.post('/api/admin/update-form-settings', headers=headers, json=update_data)
    print("Update Settings Response:", update_res.status_code, update_res.json)

    print("\n--- 3. Testing /api/config/active-outing (Getter) ---")
    get_res = client.get('/api/config/active-outing')
    print("Get Config Response:", get_res.status_code, get_res.json)

    print("\n--- 4. Testing /api/admin/sync-config-from-mail ---")
    sync_res = client.post('/api/admin/sync-config-from-mail', headers=headers)
    print("Sync Config from Mail Response:", sync_res.status_code, sync_res.json)

if __name__ == '__main__':
    run_admin_tests()
