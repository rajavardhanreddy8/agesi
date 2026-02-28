import os
import sys

# Ensure module finding
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'form_filler'))
sys.path.insert(0, BASE_DIR)

from form_filler.api import app, get_db_connection

def run_tests():
    app.config['TESTING'] = True
    client = app.test_client()
    
    # 1. Login
    print("--- 1. Testing Login ---")
    login_res = client.post('/api/auth/login', json={
        'email': 'adithya.test@example.com',
        'password': 'Password123!'
    })
    
    if login_res.status_code != 200:
        print(f"Login failed! Response: {login_res.json}")
        # Could be already registered from our previous script. We assume user exists.
        # Check if the DB connection is pointing to the right place.
        return
        
    token = login_res.json.get('token')
    headers = {'Authorization': f'Bearer {token}'}
    print("Login successful! Token acquired.\n")
    
    # 2. Setup standard user profile with defaults to clear previous runs
    print("--- 2. Resetting Original Data ---")
    reset_data = {
        'full_name': 'Test Adithya Initial',
        'send_parent_email': True,
        'parent1_name': 'Dummy Parent 1'
    }
    client.put('/api/profile', headers=headers, json=reset_data)
    
    
    # 3. Test Profile Update
    print("--- 3. Testing Profile Update (Saving) ---")
    update_data = {
        'full_name': 'Test Adithya Saved Update',
        'send_parent_email': False,
        'parent1_name': 'Updated Parent Dummy'
    }
    update_res = client.put('/api/profile', headers=headers, json=update_data)
    if update_res.status_code == 200:
        print("Profile update response: [SUCCESS]")
    else:
        print(f"Profile update failed: {update_res.json}")
        
    print("\n--- 4. Verifying Changes in DB (Fetching Profile) ---")
    profile_res = client.get('/api/profile', headers=headers)
    if profile_res.status_code == 200:
        data = profile_res.json.get('profile', {})
        print(f"DB full_name: {data.get('full_name')}")
        print(f"DB parent1_name: {data.get('parent1_name')}")
        print(f"DB send_parent_email: {data.get('send_parent_email')}")
        
        if (data.get('full_name') == 'Test Adithya Saved Update' and 
            data.get('send_parent_email') is False): # It might return falsy values based on DB
            print("DB Verification: [PASSED]")
        else:
            print("DB Verification: [FAILED] - Update did not persist.")
    else:
        print(f"Failed to fetch profile: {profile_res.status_code}")

    print("\n--- 5. Testing Mail Fetch Query Functionality ---")
    import mail_agent.gmail_service as gs
    try:
        # Note: This requires credentials.json and token.json to be set up in the same dir
        email = gs.get_latest_email_content('(subject:outing OR subject:pass)')
        if email:
            print(f"Email fetch returned subject: {email.get('subject')}")
            print(f"Found form links: {email.get('form_links')}")
            print("Mail fetch: [PASSED]")
        else:
            print("Mail fetch returned None, but did not crash! [READY]")
    except Exception as e:
        print(f"Mail fetch: [FAILED] Exception occurred - {e}")

if __name__ == '__main__':
    run_tests()
