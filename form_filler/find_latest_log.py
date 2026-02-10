
import os

search_dir = 'extracted_logs'
latest_file = None
latest_time = 0

for root, dirs, files in os.walk(search_dir):
    for file in files:
        if 'docker' in file.lower() and file.endswith('.log'):
            full_path = os.path.join(root, file)
            mtime = os.path.getmtime(full_path)
            if mtime > latest_time:
                latest_time = mtime
                latest_file = full_path

if latest_file:
    print(f"Latest Docker Log: {latest_file}")
    with open(latest_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print("".join(lines[-50:]))
else:
    print("No docker logs found.")
