"""
Delete the failed GUNTAKA submission and re-queue all with correct dates.
Also restart the queue processing.
"""
import sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1. Delete failed GUNTAKA entries with Mar 6-8 dates
cur.execute("""
    DELETE FROM submission_history 
    WHERE status = 'failed' 
    AND leave_start_date = '2026-03-06'
    AND user_id = (SELECT id FROM users WHERE email ILIKE '%guntaka%' LIMIT 1)
""")
print(f"Deleted {cur.rowcount} failed GUNTAKA entries")

# 2. Also delete the completed one with old dates (Feb 13-14)
cur.execute("""
    DELETE FROM submission_history 
    WHERE status = 'completed' 
    AND leave_start_date = '2026-02-13'
    AND user_id = (SELECT id FROM users WHERE email ILIKE '%guntaka%' LIMIT 1)
""")
print(f"Deleted {cur.rowcount} old completed GUNTAKA entries")

conn.commit()

# 3. Check what's left in queue
cur.execute("""
    SELECT sh.status, sh.leave_start_date, sh.leave_end_date, u.email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id 
    WHERE sh.status IN ('queued') AND sh.leave_start_date = '2026-03-06'
    ORDER BY u.email
""")
rows = cur.fetchall()
print(f"\nCurrently queued for Mar 6-8: {len(rows)} tasks")
for r in rows:
    print(f"  {r['email']} | {r['leave_start_date']} -> {r['leave_end_date']}")

# 4. Check if GUNTAKA is in queue
cur.execute("""
    SELECT COUNT(*) as cnt FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE u.email ILIKE '%guntaka%' AND sh.leave_start_date = '2026-03-06' AND sh.status = 'queued'
""")
g = cur.fetchone()
if g['cnt'] == 0:
    print("\n⚠️ GUNTAKA not in queue - needs to be re-added")
else:
    print(f"\n✅ GUNTAKA already in queue")

conn.close()
