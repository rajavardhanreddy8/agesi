import sys
import psycopg2.extras
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Find all users who had a 'failed' retry task today
cur.execute('''
    SELECT DISTINCT u.email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.task_id LIKE 'retry_paid_%' AND sh.status = 'failed'
''')
failed_users = [r['email'] for r in cur.fetchall()]

if not failed_users:
    print('No failed retry users found.')
    sys.exit(0)

print(f'Checking {len(failed_users)} users who failed the retry...')

# Check if these users ever had a 'completed' status
query = '''
    SELECT u.email, COUNT(*) as complete_count, MAX(sh.submitted_at) as last_completed
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE u.email = ANY(%s) AND sh.status = 'completed'
    GROUP BY u.email
'''
cur.execute(query, (failed_users,))
completed_history = cur.fetchall()

print('\nUsers with prior completions:')
for ch in completed_history:
    print(f"- {ch['email']} | Completed {ch['complete_count']} times | Last: {ch['last_completed']}")

completed_emails = {ch['email'] for ch in completed_history}
never_completed = set(failed_users) - completed_emails

print(f'\nUsers who NEVER completed successfully: {len(never_completed)}')
for nc in never_completed:
    print(f"- {nc}")

conn.close()
