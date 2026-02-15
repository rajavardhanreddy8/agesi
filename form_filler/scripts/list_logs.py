
import os
from datetime import datetime

log_dir = 'logs'
print(f"Listing files in '{log_dir}':")

for root, dirs, files in os.walk(log_dir):
    for file in files:
        full_path = os.path.join(root, file)
        try:
            mtime = os.path.getmtime(full_path)
            dt = datetime.fromtimestamp(mtime)
            print(f"{dt} - {full_path}")
        except Exception as e:
            print(f"ERROR accessing {full_path}: {e}")
