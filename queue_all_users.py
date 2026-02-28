import requests
import psycopg2.extras
from form_filler.db import get_db_connection

def queue_real_users():
    # 1. Extract 8 real working Woxsen users from DB
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('''
        SELECT email FROM users 
        WHERE email LIKE '%@woxsen.edu.in'
        AND email NOT IN (
            'newtest9876@woxsen.edu.in',
            'adithya.test@woxsen.edu.in',
            'testuser9999@woxsen.edu.in'
        )
    ''')
    users = cur.fetchall()
    conn.close()

    # 2. Queue them up via the webhook API
    form_url = 'https://forms.office.com/Pages/ResponsePage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u'
    
    success_count = 0
    print(f"Attempting to queue {len(users)} users via the backend API (port 5000)...")
    
    for u in users:
        email = u['email']
        print(f'Queueing {email}...')
        try:
            res = requests.post('http://127.0.0.1:5000/api/auto-submit-from-email', 
                json={
                    'email': email,
                    'form_url': form_url,
                    'leave_start_date': '04-10-2026',
                    'leave_end_date': '04-12-2026',
                    'reason': 'Testing Queue System Concurrency'
                }
            )
            if res.status_code == 200:
                success_count += 1
                print(f'  -> OK: {res.json()}')
            else:
                try:
                    err_msg = res.json()
                except:
                    err_msg = res.text
                print(f'  -> ERROR {res.status_code}: {err_msg}')
        except requests.exceptions.ConnectionError:
            print("  -> ERROR: Could not connect to the backend API. Is `app.py` running?")
        except Exception as e:
            print(f'  -> EXCEPTION: {e}')

    print(f'\nSuccessfully queued {success_count} requests to the backend worker.')

if __name__ == "__main__":
    queue_real_users()
