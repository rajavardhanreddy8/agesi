"""
Re-trigger auto queue with correct dates (March 6-8, 2026) for this week's outing.
"""
import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('FLASK_ENV', 'production')

from api import _trigger_auto_queue

form_url = "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X62J9sRC8oxAu69or0JA3nxUNzUxN0ZFUUZIR0hLMU9XR1RaMVVHUkpQWS4u"
start_date = "2026-03-06"
end_date = "2026-03-08"

print(f"Re-queuing auto submissions for {start_date} -> {end_date}")
print(f"Form URL: {form_url}")

count = _trigger_auto_queue(form_url, start_date, end_date)
print(f"\n✅ Queued {count} tasks with correct dates")
