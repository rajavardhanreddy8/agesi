import zipfile
import os
import glob
from datetime import datetime

zip_path = 'webapp_logs.zip'
extract_to = 'c:\\Users\\admin\\temp_logs'

if not os.path.exists(extract_to):
    os.makedirs(extract_to)

try:
    with zipfile.ZipFile(zip_path, 'r') as z:
        # List all files
        file_list = z.namelist()
        
        # Filter for docker logs, excluding scm logs
        docker_logs = [f for f in file_list if f.endswith('_docker.log') and '_scm_' not in f]
        
        if not docker_logs:
            print("No docker logs found.")
            # Try to list all files to see structure
            print("All files found:", file_list[:20])
        else:
            # Sort by modification time (heuristic based on usage, zip doesn't always have reliable mtime for sorting this way easily without info)
            # Better: list zip info
            infos = [z.getinfo(name) for name in docker_logs]
            # sort by date_time
            infos.sort(key=lambda x: x.date_time, reverse=True)
            
            latest_log = infos[0]
            print(f"Extracting latest log: {latest_log.filename}")
            z.extract(latest_log, extract_to)
            print(f"Extracted to {os.path.join(extract_to, latest_log.filename)}")

except Exception as e:
    print(f"Error: {e}")
